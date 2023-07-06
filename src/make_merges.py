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

import itertools
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import NewType, Optional

import more_itertools
import networkx as nx

from branchmap import get_branch_for_path
from git import Branch, git
from p4.filelog import ChangeList, ChangedFile, get_path_to_changed_file

GitHash = NewType("GitHash", str)


@dataclass(frozen=True)
class Commit:
    changelist: ChangeList
    branch: Branch
    hash: GitHash

    def __str__(self):
        return f"{self.changelist} {self.branch}"


def get_branches() -> list[Branch]:
    branches = [
        Branch(branch.replace("*", "").strip())
        for branch in git(["branch", "--list"]).splitlines()
    ]
    return [
        branch for branch in branches if branch != "__p4_export__everything_no_branches"
    ]


def get_branch_to_commits(branches: list[Branch]) -> dict[Branch, set[Commit]]:
    branch_to_commits: dict[Branch, set[Commit]] = dict()
    for branch in branches:
        commits = set()
        lines = git(
            ["log", "--reverse", "--format=%H%n%w(9999,1,1)%b", branch, "--"]
        ).split("\n")
        lines = [line for line in lines if line != ""]
        chunks = more_itertools.split_before(
            lines, lambda line: not line.startswith(" ")
        )
        for chunk in chunks:
            hash = GitHash(chunk[0])
            changelist = None
            for line in chunk:
                match = re.match(" P4:([0-9]+)$", line)
                if match:
                    changelist = ChangeList(int(match.group(1)))
                    break
            if changelist is None:
                raise Exception(
                    f"""unknown p4 changeset for git hash {hash} in branch {branch}.

chunks: {chunk}"""
                )
            commit = Commit(changelist=changelist, branch=branch, hash=hash)
            commits.add(commit)
        branch_to_commits[branch] = commits
    return branch_to_commits


def get_commit_to_deps(
    path_to_changed_file: dict[PurePosixPath, ChangedFile],
    branch_to_commits: dict[Branch, set[Commit]],
) -> defaultdict[Commit, set[Commit]]:
    commit_lookup_table = dict(
        ((commit.changelist, branch), commit)
        for (branch, commits) in branch_to_commits.items()
        for commit in commits
    )

    def find_commit(changelist: ChangeList, branch: Branch) -> Optional[Commit]:
        return commit_lookup_table.get((changelist, branch))

    commit_to_deps = defaultdict[Commit, set[Commit]](set)
    for changed_file in path_to_changed_file.values():
        for file_change in changed_file.file_changes:
            branch = get_branch_for_path(changed_file.path, file_change.changelist)
            if branch is None:
                continue
            commit = find_commit(file_change.changelist, branch)
            if commit is None:
                # This check is required because p4 lets you
                # make empty changes, to specific files. In
                # git these just disappear.
                continue
            for sub_change in file_change.sub_changes:
                match sub_change.action:
                    case "branch from" | "copy from" | "delete from" | "edit from" | "merge from":
                        file_version = max(sub_change.path_revs)
                        dep_file_change = more_itertools.one(
                            [
                                file_change
                                for file_change in path_to_changed_file[
                                    sub_change.path
                                ].file_changes
                                if file_change.version == file_version
                            ]
                        )
                        dep_branch = get_branch_for_path(
                            sub_change.path, dep_file_change.changelist
                        )
                        if dep_branch is not None:
                            dep_commit = find_commit(
                                dep_file_change.changelist, dep_branch
                            )
                            if dep_commit is None:
                                # Required check, as above.
                                continue
                            commit_to_deps[commit].add(dep_commit)
                    case "ignored":
                        # This could have been called "ignored from".
                        #
                        # I think it's a bit subjective whether or not
                        # we should consider these merges in git. The
                        # obvious argument against is nothing is copied
                        # over. An argument for is that nonethless,
                        # future merges do not need to reconsider the
                        # same change again.
                        #
                        # In the end I somewhat arbitrarily decided not
                        # to bother considering representing these as
                        # git merges. Later I saw, with Open Watcom in
                        # changelist 29653, a bunch of file changes
                        # which were ignored. However this was after
                        # those exact same file changes had previously
                        # been copied or integrated! So ignoring the
                        # ignores turned out to be the better decision,
                        # at least for that example.
                        pass
                    case "branch into" | "copy into" | "delete into" | "edit into" | "merge into":
                        # We look at the from side, which means the into
                        # side doesn’t tell us anything new.
                        pass
                    case "add into":
                        # We don’t need to look at this, like the other
                        # intos. However, we take the opportunity to
                        # note there is no "add from". Interestingly,
                        # sometimes "add into" (and not "branch into")
                        # is the opposite of "branch from". With Open
                        # Watcom we saw this with
                        # //depot/ow_devel/fortran.dev/bld/F03/c/blderr.c.
                        pass
                    case "ignored by":
                        # This could have been called "ignored into". We
                        # don’t look at this, just like the other intos.
                        pass
    return commit_to_deps


def main() -> None:
    path_to_changed_file: dict[PurePosixPath, ChangedFile] = get_path_to_changed_file()
    branches: list[Branch] = get_branches()
    branch_to_commits: dict[Branch, set[Commit]] = get_branch_to_commits(branches)
    # We start off with each branch's boring linear history.
    G = nx.DiGraph()
    for branch in branches:
        commits = sorted(
            branch_to_commits[branch], key=lambda commit: commit.changelist
        )
        G.add_nodes_from(commits)
        G.add_edges_from(itertools.pairwise(commits))
    # Now we look at dependencies of each commit, as calculated from the
    # Perforce actions.
    commit_to_deps: defaultdict[Commit, set[Commit]] = get_commit_to_deps(
        path_to_changed_file, branch_to_commits
    )
    # We will make a couple simplifications.
    for commit, all_deps in commit_to_deps.items():
        # IMHO the commit graph would be unhelpfully complex if we
        # considered in-branch actions as merges. We especially see this
        # in Open Watcom with
        # //depot/openwatcom/bld/helpcomp/nt386/makefile: the file is
        # clearly renamed to this in #18641, not merged. So exclude the
        # target branch from being a source branch.
        all_deps = {dep for dep in all_deps if dep.branch != commit.branch}
        deps_by_branch = more_itertools.bucket(all_deps, lambda dep: dep.branch)
        for branch in deps_by_branch:
            deps_in_branch: list[Commit] = list(deps_by_branch[branch])
            deps_in_branch = [
                dep for dep in deps_in_branch if dep.changelist != commit.changelist
            ]
            # Take the latest relevant commit in the branch as the
            # dependency, as opposed to all of them. This is just to
            # avoid overcomplicating the git commit graph.
            latest_dep = max(deps_in_branch, key=lambda commit: commit.changelist)
            G.add_edge(latest_dep, commit)
    assert nx.is_directed_acyclic_graph(G)
    branch_starts = set(
        min(commits, key=lambda commit: commit.changelist)
        for commits in branch_to_commits.values()
    )
    # Rewrite parents (to get merges)
    H = G.reverse()
    for cmt in nx.topological_sort(H):
        adj = H.adj[cmt]
        if len(adj) > 1 or cmt in branch_starts:
            new_parents = [a.hash for a in adj]
            # Somebody will need to call git filter-repo, to make these
            # replacements permanent.
            git(["replace", "--graft", cmt.hash] + new_parents)


if __name__ == "__main__":
    main()
