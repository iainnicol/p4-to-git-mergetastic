#!/usr/bin/python3

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

from pathlib import PurePosixPath
from typing import Optional

from git import Branch
from p4.filelog import ChangeList


def get_branch_for_path(
    path: PurePosixPath, changelist: ChangeList
) -> Optional[Branch]:
    assert str(path).startswith("//depot/")
    rel_path = str(path).removeprefix("//depot/")
    if rel_path.startswith("openwatcom/"):
        return Branch("openwatcom")
    if rel_path.startswith("ow_devel/CVDebug_dev5/"):
        return Branch("CVDebug_dev")
    if rel_path.startswith("ow_devel/fortran.F03.dev/"):
        return Branch("F2003_Development")
    if rel_path.startswith("ow_devel/fortran.F95.dev/"):
        return Branch("F95_Development")
    if rel_path.startswith("ow_devel/rdos/"):
        return Branch("RDOS")
    if rel_path.startswith("V2/"):
        return Branch("V2")
    if rel_path.startswith("ow_devel/bld/wasm/"):
        if changelist in {ChangeList(31816), ChangeList(31829)}:
            return None
        return Branch("WASM")
    if rel_path.startswith("ow_devel/zdos19/"):
        return None
    if (
        rel_path.startswith("ow_devel/zdos/")
        or rel_path.startswith("ow_devel/bld/build/")
        or rel_path.startswith("ow_devel/bld/clib/")
        or rel_path.startswith("ow_devel/bld/hdr/")
        or rel_path.startswith("ow_devel/binnt/")
        or rel_path.startswith("ow_devel/binw/")
        or rel_path == "ow_devel/binz/wlink.lnk"
        or rel_path.startswith("ow_devel/docs/")
    ):
        if changelist in {
            # Added files from ow_devel/ to ow_devel/zdos, so these
            # disappear because we merge those into the one dir/branch.
            ChangeList(31810),
            ChangeList(31812),
            # The files were then deleted in the original dir; we
            # deleted that commit because, again, we merged the dirs.
            ChangeList(31816),
        }:
            return None
        if changelist in {
            # In addition to legit changes, wasm and wmake.dev were
            # accidentally removed
            ChangeList(31813),
            ChangeList(31829),  # And this accidental change was undone.
        }:
            if rel_path.startswith("ow_devel/zdos/bld/wasm/") or rel_path.startswith(
                "ow_devel/zdos/bld/wmake.dev/"
            ):
                return None
        return Branch("ZDOS")
    if rel_path == "ow_devel/binz/zdos/wlink.lnk":
        return None
    if rel_path == "ow_devel/bldhdr/watcom/zapi.mh":
        return None
    if rel_path.startswith("ow_devel/dwarf3/"):
        return Branch("dwarf3")
    if rel_path.startswith("ow_devel/long_double/"):
        return Branch("long_double")
    if rel_path.startswith("ow_release/1.0/"):
        return Branch("openwatcom_1.0")
    if rel_path.startswith("ow_devel/intel_owl/"):
        return Branch("openwatcom_bld_devel")
    if rel_path.startswith("ow_devel/plusplus.dev/"):
        return Branch("plusplus.dev")
    if rel_path.startswith("ow_devel/plusplus.ext/"):
        return Branch("plusplus.ext")
    if rel_path.startswith("ow_devel/bld/wmake.dev/"):
        if changelist in {ChangeList(31816), ChangeList(31829)}:
            return None
        return Branch("wmake.dev")
    if rel_path.startswith("ow_devel/bld/wl/"):
        if changelist in {
            ChangeList(31811),
            ChangeList(31816),
            ChangeList(32369),
            ChangeList(32374),
        }:
            return None
        return Branch("wlink")
    if rel_path.startswith("ow_devel/bld/cvpack/") or rel_path.startswith(
        "ow_devel/bld/watcom/"
    ):
        return None
    if rel_path.startswith("ow_devel/fortran.dev/"):
        if rel_path.startswith("ow_devel/fortran.dev/bld/F03/c/"):
            return None
        return Branch("fortran.dev")
    if rel_path == "ow_release/bld/wipfc/cpp/fts.cpp":
        return None
    if rel_path.startswith("public/4os2/"):
        return None
    if rel_path.startswith("public/c4/"):
        return None
    if rel_path.startswith("public/convman/"):
        return None
    if rel_path.startswith("public/dmake/"):
        return None
    if rel_path.startswith("public/nasm/"):
        return None
    if rel_path.startswith("public/ozh/"):
        return None
    if rel_path.startswith("public/wcclibc/"):
        return None
    if rel_path.startswith("public/wcclinux/"):
        return None
    if rel_path.startswith("public/wp51vesa/"):
        return None
    if rel_path == "robots.txt":
        return None
    raise ValueError(path, changelist)
