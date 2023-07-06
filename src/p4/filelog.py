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
import re
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import NewType, Optional, Self, TextIO, final

from branchmap import Branch

FileVersion = NewType("FileVersion", int)


@final
@dataclass(frozen=True)
class SubChange:
    action: str
    path: PurePosixPath
    path_revs: frozenset[FileVersion]

    def __str__(self) -> str:
        path_revs = ",".join(f"#{rev}" for rev in sorted(self.path_revs))
        return f"... ... {self.action} {self.path}{path_revs}"

    __regex = re.compile(
        "\.\.\. \.\.\. "
        "([a-z]+ into|[a-z]+ from|ignored|ignored by)"
        " //([^#]+)((#[0-9]+,)*#[0-9]+)$"
    )

    @classmethod
    def parse_line(cls, line: str) -> Self:
        match = SubChange.__regex.match(line)
        if match is None:
            raise Exception(f"no match for line: {line}")
        action = match.group(1)
        path = f"//{match.group(2)}"
        revs = frozenset(
            FileVersion(int(rev[len("#") :])) for rev in match.group(3).split(",")
        )
        return SubChange(action, PurePosixPath(path), revs)


ChangeList = NewType("ChangeList", int)


@final
@dataclass
class FileChange:
    version: FileVersion
    changelist: ChangeList
    action: str
    when: datetime.datetime
    author: str
    chmod: str
    description: str
    sub_changes: list[SubChange]

    def __str__(self) -> str:
        when = self.when.strftime("%Y/%m/%d")
        lines = [
            f"... #{self.version} change {self.changelist} {self.action}"
            f" on {when} by {self.author} ({self.chmod}) '{self.description}'"
        ]
        lines += [str(sub_change) for sub_change in self.sub_changes]
        return "\n".join(lines)

    __regex = re.compile(
        "... #([0-9]+) change ([0-9]+) ([a-z]+)"
        " on ([0-9]+/[0-9]{2}/[0-9]{2}) by ([^ ]+) \(((binary|text)(\+[xFw])?)\) '(.*?)'$"
    )

    @classmethod
    def __parse_line(cls, line: str) -> Self:
        match = FileChange.__regex.match(line)
        if match is None:
            raise Exception(f"no match for line: {line}")
        version = int(match.group(1))
        changelist = int(match.group(2))
        action = match.group(3)
        when = datetime.datetime.strptime(match.group(4), "%Y/%m/%d")
        author = match.group(5)
        chmod = match.group(6)
        description = match.group(9)
        # The subchanges need to be added elsewhere; they are on other
        # lines.
        subchanges: list[SubChange] = []
        return FileChange(
            FileVersion(version),
            ChangeList(changelist),
            action,
            when,
            author,
            chmod,
            description,
            subchanges,
        )

    @classmethod
    def parse_lines(cls, lines: list[str]) -> Iterator[Self]:
        file_change: Optional[FileChange] = None

        def mk_file_change() -> FileChange:
            nonlocal file_change
            assert file_change is not None
            file_change2 = file_change
            file_change = None
            return file_change2

        for line in lines:
            if line.startswith("... #"):
                if file_change is not None:
                    yield mk_file_change()
                bh = FileChange.__parse_line(line)
                file_change = bh
            else:
                assert file_change is not None
                file_change.sub_changes.append(SubChange.parse_line(line))
        if file_change is not None:
            yield mk_file_change()


@final
@dataclass
class ChangedFile:
    path: PurePosixPath
    file_changes: list[FileChange]

    def __str__(self) -> str:
        return "\n".join(
            [str(self.path)] + [str(change) for change in self.file_changes]
        )

    @classmethod
    def parse(cls, f: TextIO) -> Iterator[Self]:
        path = ""
        body: list[str] = []

        def mk_changed_file() -> ChangedFile:
            nonlocal path, body
            path2 = path
            body2 = body
            path = ""
            body = []
            return ChangedFile(
                PurePosixPath(path2), list(FileChange.parse_lines(body2))
            )

        for line in f:
            line = line.rstrip()
            if line.startswith("//"):
                if path != "":
                    yield mk_changed_file()
                path = line
            else:
                body.append(line)
        if path != "":
            yield mk_changed_file()


GitHash = NewType("GitHash", str)


@dataclass(frozen=True)
class Commit:
    changelist: ChangeList
    branch: Branch
    hash: GitHash

    def __str__(self):
        return f"{self.changelist} {self.branch}"


def get_path_to_changed_file() -> dict[PurePosixPath, ChangedFile]:
    # Encoding errors need to be non-fatal, because the filelog contains
    # changeset descriptions, and these might not all be UTF-8.
    with open("filelogs.txt", "rt", errors="replace") as f:
        path_to_changed_file: dict[PurePosixPath, ChangedFile] = {}
        for changed_file in ChangedFile.parse(f):
            path_to_changed_file[changed_file.path] = changed_file
    return path_to_changed_file
