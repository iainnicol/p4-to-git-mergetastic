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

import datetime
import itertools
import sys
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Iterable

import more_itertools
from branchmap import get_branch_for_path

from git import git
from p4.filelog import ChangeList


@dataclass
class Label:
    label: str
    update: datetime.datetime
    owner: str
    description: str
    view: list[PurePosixPath]
    changelist: ChangeList


def parse_label(lines: list[str]) -> Label:
    def read_simple_field(fieldname: str) -> str:
        prefix = f"{fieldname}:\t"
        for line in lines:
            if line.startswith(prefix):
                ret = line.removeprefix(prefix)
                return ret
        raise Exception(f"Could not find field {fieldname}")

    def read_multiline_field(fieldname: str) -> str:
        field_lines: Iterable[str] = list(lines)
        field_lines = itertools.dropwhile(
            lambda line: not line.startswith(f"{fieldname}:"), field_lines
        )
        next(field_lines)  # Drop fieldname header
        field_lines = itertools.takewhile(
            lambda line: line.startswith("\t"), field_lines
        )
        field_lines = [line[1:] for line in field_lines]  # Skip tab
        return "\n".join(field_lines)

    label = read_simple_field("Label")
    update = datetime.datetime.strptime(
        read_simple_field("Update"), "%Y/%m/%d %H:%M:%S"
    )
    owner = read_simple_field("Owner")
    description = read_multiline_field("Description")
    view = [PurePosixPath(path) for path in read_multiline_field("View").split("\n")]
    changelist = ChangeList(int(read_simple_field("Changelist")))
    return Label(label, update, owner, description, view, changelist)


def create_git_tag(lbl: Label) -> None:
    changelist_pattern = f"^P4:{lbl.changelist}$"
    branches = {
        get_branch_for_path(view_path, lbl.changelist) for view_path in lbl.view
    }
    branch = more_itertools.one(branches)
    tag_name = lbl.label
    commits = git(
        ["log", f"--grep={changelist_pattern}", "--format=%H", branch, "--"]
    ).splitlines()
    commit = more_itertools.one(commits)
    env = {
        "GIT_COMMITTER_DATE": lbl.update.strftime("%Y-%m-%d %H:%M:%S"),
        "GIT_COMMITTER_NAME": lbl.owner,
        "GIT_COMMITTER_EMAIL": "",
    }
    git(
        ["tag", "--file=-", tag_name, commit],
        input=lbl.description.encode("utf-8"),
        env=env,
    )


def process_spec(lines: list[str]) -> None:
    label: Label = parse_label(lines)
    create_git_tag(label)


def main(args: list[str]) -> None:
    filenames = args
    for filename in filenames:
        with open(filename, "rt") as f:
            process_spec([line.rstrip("\n") for line in f])


if __name__ == "__main__":
    main(sys.argv[1:])
