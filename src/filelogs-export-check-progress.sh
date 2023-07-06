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

# No -o pipefail today: head causes grep to error, because head closes
# the pipeline as it has read enough lines.
set -eu

lastCompleteFile="$(tac filelogs.txt | grep '^//' | head -n2 | tail -n1)"
fileNum="$(grep -nF -e "$lastCompleteFile" files.txt | cut -f1 -d:)"
numFiles="$(wc -l files.txt | grep --only-matching -E -e "[0-9]+")"
awk -vx="$fileNum" -vy="$numFiles" 'BEGIN{printf("%.1f%%\n", x/y*100)}'
