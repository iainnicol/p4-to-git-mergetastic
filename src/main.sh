#!/bin/bash

# Copyright © 2023 Iain Nicol

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

set -eux -o pipefail

repoDir="$1"

myDir="$(realpath "$(dirname "${BASH_SOURCE[0]}")")"
dataDir="$(realpath "$myDir/../data/")"

p4-fusion --client "$P4CLIENT" --port "$P4PORT" --user "$P4USER" --path //depot/... --lookAhead 1000 --includeBinaries true --src "$repoDir"

cd "$repoDir"

# Get the filelog of every file, for creating the merges.
LANG="C" # So ‘.*’ includes the non-UTF-8 bits of commit messages
p4 changes -s submitted //depot/... | sed -E -e 's/^Change ([0-9]+) on .*/\1/' >changelists.txt
echo "Exporting list of files. This can take a couple minutes."
parallel <changelists.txt --will-cite -j4 -d'\n' -n1 "p4 describe -s {} | sed -e '1,/Affected files \.\.\./d' | grep '^\.\.\.' | sed -nE -e 's/ [a-z]+$//gp' | sed -nE -e 's/#[0-9]+$//gp' | sed -n -e 's/^\.\.\. //gp'" | sort | uniq >files.txt
filelogCheckProgressCmd="$(realpath --relative-to="$repoDir" "$myDir/filelogs-export-check-progress.sh")"
cat <<EOF
Exporting filelog. This can easily take ten minutes.
You can check the progress, in another terminal, by running:
  $filelogCheckProgressCmd
from the output git repo directory.
EOF
parallel <files.txt --will-cite -j8 -d'\n' --keep-order -n1 p4 filelog >filelogs.txt

# Get rid of the imaginary null-dated initial commit, created by
# p4-fusion.
secondCommit="$(git log --format="%H" | tail -n2 | head -n1)"
git replace --graft "$secondCommit"
# Our first call to filter-repo will not succeed without force.
git filter-repo --force

# Tweak commit messages.
git filter-repo --replace-message "$myDir/message-replacements-changeset-format.txt"
git filter-repo --replace-message "$dataDir/message-replacements-non-utf8.txt"

git branch --move __p4_export__everything_no_branches
"$myDir/split-branches.sh"

pdm run "$myDir/make_merges.py"
rm changelists.txt files.txt filelogs.txt
git filter-repo --replace-refs=delete-no-add

branches=$(git for-each-ref refs/heads/ --format="%(refname)" | grep -v -F '__p4_export__everything_no_branches')
longestBranch="$(echo "$branches" | parallel --will-cite -j1 -n1 "printf '%s ' {} && git rev-list --count {} --" | sort -nr -k2 | head -n1 | sed -E -e 's/ [0-9]+$//')"
defaultBranch="$longestBranch"
git symbolic-ref HEAD "$defaultBranch"

git branch -D __p4_export__everything_no_branches

# Delete email addresses for two reasons. First, p4-fusion may have
# given us placeholder email addresses instead of empty ones, where
# Perforce does not know the user’s email address. Second, I don’t think
# it’s fair to put email addresses into a git log without asking: git
# logs are more likely to be scraped by spammers than an old Perforce
# depot.
#
# However, if you want to keep email addresses, comment out the
# following line, or edit the mailmap.
git filter-repo --email-callback 'return b""'
# Convert from Perforce usernames, to full names.
git filter-repo --mailmap "$dataDir/mailmap.txt"

git gc --prune=now --aggressive

echo "Finished successfully!"
