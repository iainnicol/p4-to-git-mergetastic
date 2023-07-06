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

function downloadAndBuildP4ClientAppAndLibrary() {
    if ! [[ -f p4source.tgz ]]; then
        curl --silent --show-error --fail --location https://ftp.perforce.com/perforce/r23.1/bin.tools/p4source.tgz -o p4source.tgz
    fi
    echo "efdc59bf1443a6709998299cdff3a9cc52c5a6de790602ecb6ad70c6f509a496 p4source.tgz" | sha256sum --check --quiet
    tar --extract --file p4source.tgz

    rm -rf p4-bin/
    pushd p4source-*/
    jam -sOSVER=26 -sMALLOC_OVERRIDE=no -sUSE_MIMALLOC=no -sUSE_SMARTHEAP=no -sUSE_EXTENSIONS=no -sSSLLIB="-lssl" -sCRYPTOLIB="-lcrypto" p4
    jam -sOSVER=26 -sMALLOC_OVERRIDE=no -sUSE_MIMALLOC=no -sUSE_SMARTHEAP=no -sUSE_EXTENSIONS=no -sPRODUCTION=1 p4api.tar
    popd
}

function downloadAndBuildP4Fusion() {
    if ! [[ -d p4-fusion/ ]]; then
        git clone https://github.com/salesforce/p4-fusion
    fi
    pushd p4-fusion/
    git switch --detach 3ee482466464c18e6a635ff4f09cd75a2e1bfe0f # v1.12

    cd vendor/
    mkdir -p helix-core-api/linux/
    cd helix-core-api/linux/
    ln --symbolic --force ../../../../p4-bin/bin.linux26*/p4api-*/{include,lib}/ ./
    cd ../../../

    ./generate_cache.sh Release
    ./build.sh

    popd
}

myDir="$(realpath "$(dirname "${BASH_SOURCE[0]}")")"
cd "$myDir"
downloadAndBuildP4ClientAppAndLibrary
downloadAndBuildP4Fusion
