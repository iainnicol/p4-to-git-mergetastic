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

if ((EUID == 0)); then
    echo >&1 "Do not run this script as root. We will later install Python packages, and doing that as a normal user is safer than as root."
    exit 1
fi

commonSystemPkgs=(curl jam g++ cmake parallel git git-filter-repo python3 pipx)
if command -v dnf >/dev/null 2>&1; then
    sudo dnf install -y "${commonSystemPkgs[@]}" openssl-devel libstdc++-static
elif command -v apt >/dev/null 2>&1; then
    sudo apt update
    sudo apt install -y "${commonSystemPkgs[@]}" libssl-dev
else
    echo >&2 "Unsupported package manager/distro."
    exit 1
fi

myDir="$(realpath "$(dirname "${BASH_SOURCE[0]}")")"
cd "$myDir"

pdmPath="$(realpath pdm-bin/)"
PIPX_HOME="pipx-home/" PIPX_BIN_DIR="$pdmPath" pipx install pdm==2.7.4

pushd ../
PATH="$pdmPath:$PATH"
pdm install --no-self
popd
