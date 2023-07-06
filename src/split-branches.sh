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

# Note: No RDOS-b2, because sort of same root as RDOS. And the root
# doesn't exist for RDOS-br1.
#
# Note: We don't make a F77_DLL branch because the folder
# openwatcom/bld/f77_dll was never used

git branch openwatcom
git filter-repo --refs refs/heads/openwatcom --prune-empty=always --subdirectory-filter openwatcom/

git branch CVDebug_dev
git filter-repo --refs CVDebug_dev --prune-empty=always --subdirectory-filter ow_devel/CVDebug_dev5/

git branch F2003_Development
git filter-repo --refs F2003_Development --prune-empty=always --subdirectory-filter ow_devel/fortran.F03.dev/

git branch F95_Development
git filter-repo --refs F95_Development --prune-empty=always --subdirectory-filter ow_devel/fortran.F95.dev/

git branch RDOS
git filter-repo --refs RDOS --prune-empty=always --subdirectory-filter ow_devel/rdos/

git branch V2
git filter-repo --refs refs/heads/V2 --prune-empty=always --subdirectory-filter V2/

git branch WASM
git filter-repo --refs WASM --prune-empty=always --subdirectory-filter ow_devel/bld/wasm/ --commit-callback "
  # accidental move of wasm and wmake.dev (in addition to zdos), then
  # reverted.
  if commit.message.endswith(b'P4:31816') or commit.message.endswith(b'P4:31829'):
    commit.file_changes = []
"

git branch ZDOS
# An experiment in branching, plus accidental commit. The proper branch
# was soon created as ow_devel/zdos.
# ignore: ow_devel/zdos19/
git filter-repo --refs ZDOS --prune-empty=always --subdirectory-filter ow_devel/zdos/ --path ow_devel/bld/build/ --path ow_devel/bld/clib/ --path ow_devel/bld/hdr/ --path ow_devel/binnt/ --path ow_devel/binw/ --path ow_devel/binz/wlink.lnk --path ow_devel/docs/ --path-rename "ow_devel/:" --commit-callback "
  # this commit is not required. zdos files were moved from src to dst
  # (in addition to accidentally moving wasm and wmake.dev). but we are
  # merging src and dst, so we don't want the delete commit to delete
  # files from the merged dir. (the files will remain until 31834)
  if commit.message.endswith(b'P4:31816'):
    commit.file_changes = []
  # along with the proper move of the zdos branch directory (which we
  # keep), wasm and wmake.dev files were accidentally moved to the zdos
  # branch (which was reverted shortly afterwards) we'll delete the
  # improper move, and the now-unneeded move back, of wasm and
  # wmake.dev.
  elif commit.message.endswith(b'P4:31813') or commit.message.endswith(b'P4:31829'):
    commit.file_changes = [fc for fc in commit.file_changes if not fc.filename.startswith(b'bld/wasm') and not fc.filename.startswith(b'bld/wmake.dev')]
"
# Mistakenly created when moving zdos branch from ow_devel/binz/ (etc)
# to ow_devel/zdos/binz/
# ignore ow_devel/binz/zdos/wlink.lnk
# Typoed path (missing slash in bld/hdr) which was immediately deleted
# ignore ow_devel/bldhdr/watcom/zapi.mh

git branch dwarf3
git filter-repo --refs dwarf3 --prune-empty=always --subdirectory-filter ow_devel/dwarf3/

git branch long_double
git filter-repo --refs long_double --prune-empty=always --subdirectory-filter ow_devel/long_double/

git branch openwatcom_1.0
git filter-repo --refs openwatcom_1.0 --prune-empty=always --subdirectory-filter ow_release/1.0/

git branch openwatcom_bld_devel
git filter-repo --refs openwatcom_bld_devel --prune-empty=always --subdirectory-filter ow_devel/intel_owl/

git branch plusplus.dev
git filter-repo --refs plusplus.dev --prune-empty=always --subdirectory-filter ow_devel/plusplus.dev/

git branch plusplus.ext
git filter-repo --refs plusplus.ext --prune-empty=always --subdirectory-filter ow_devel/plusplus.ext/

git branch wmake.dev
git filter-repo --refs wmake.dev --prune-empty=always --subdirectory-filter ow_devel/bld/wmake.dev/ --commit-callback "
  # accidental move of wasm and wmake.dev (in addition to zdos), then
  # reverted.
  if commit.message.endswith(b'P4:31816') or commit.message.endswith(b'P4:31829'):
    commit.file_changes = []
"

# No p4 branchspec exists, but the folder's there.
git branch wlink
git filter-repo --refs wlink --prune-empty=always --subdirectory-filter ow_devel/bld/wl --commit-callback "
  # an accidental branch to ow_devel/bld/ which was shortly deleted.
  if commit.message.endswith(b'P4:32369') or commit.message.endswith(b'P4:32374'):
    commit.file_changes = []
  # belongs in zdos as opposed to wlink branch. in fact for simplicity
  # (path wise) this commit won't end up in zdos, but that's okay
  # because this has a faulty commit (for the adjacent commit) and the
  # files were added to the main zdos branch root in 31813.
  elif commit.message.endswith(b'P4:31811') or commit.message.endswith(b'P4:31816') :
    commit.file_changes = []
"

# Part of the commit 32369 (which is mentioned above). In contrast to
# ow_devel/bld/wl, these folders here NEVER had anything interesting.
# ignore: ow_devel/bld/cvpack
# ignore: ow_devel/bld/watcom

# No branchspec either, but an interesting historical curiosity. Nothing
# ever merged from this branch, but there were several starts, stops,
# and restarts. But given there are a few edits, it's fair to call this
# a 'genuine' attempt at something (as opposed to an experimentation in
# branching).
git branch fortran.dev
git filter-repo --refs fortran.dev --prune-empty=always --subdirectory-filter ow_devel/fortran.dev/
# Nonetheless, exclude //depot/ow_devel/fortran.dev/bld/F03/c/*.c. Those
# files were added and deleted in separate commits to the rest of
# fortran.dev, and this was done just to understand p4 branching.
git filter-repo --refs fortran.dev --prune-empty=always --path 'bld/F03/c/' --invert-paths

# A file copied into the wrong location; it was deleted, and copied
# (from the original source) into the correct location.
# ignore: ow_release/bld/wipfc/cpp/fts.cpp

# 4OS2 command shell
# ignore: public/4os2/

# Tool by Neil Russell to give p4 a CVS feel
# ignore: public/c4/

# OpenGL man page conversion tool
# ignore: public/convman/

# dmake, a make implementation
# ignore: public/dmake/

# NASM assembler
# ignore: public/nasm/

# A helpdesk/knowledge base app
# ignore: public/ozh/

# Project files for Open Watcom libc, for Visual Slick Edit. But never
# part of an Open Watcom release.
# ignore: public/wcclibc/

# A non-trivial Linux hello world app for Open Watcom. However, it was
# never distributed as part of the tarballs.
# ignore: public/wcclinux/

# Word Perfect VESA driver
# ignore public/wp51vesa/

# Robots.txt for the depot.
# ignore robots.txt
