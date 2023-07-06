# Synopsis

For converting p4 to git, preserving branches & merges.

# Background

This application, p4-to-git-mergetastic, is for converting a Perforce
(p4) depot into a git repository, with high fidelity. Not only do we map
branches. We also make special effort to represent Perforce copy, branch
and merge actions as merges between git branches. As far as we know,
that sets this tool apart from the alternatives.

This was specifically written for converting Open Watcom 1.9, but could
reasonably be adapted to other depots.

# Usage

Use a Linux machine. The package installation script was tested on
Debian 12, Fedora 38, and Ubuntu 22.04; you may need to tweak it for
other, or newer, distros.

Clone this repository. Then, inside your local copy, run:

```bash
# The installation script will prompt for your password, using sudo:
./build/install-packages.sh
./build/build-dependencies.sh

export P4PORT=server:1666
export P4CLIENT=client
export P4USER=user
export P4PASSWD="password"
./p4-to-git-mergetastic -o repo.git/
```

# License

Copyright © 2023 Iain Nicol

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

Note the license of this software has no effect on the license of your git
repository.

# Alternatives

Even leaving merges aside, there are not many tools for converting from Perforce
to Git:

* Perforce Git Fusion: proprietary and no longer available.
* [git-p4](https://git-scm.com/docs/git-p4): slow with large depots.
* Salesforce [p4-fusion](https://github.com/salesforce/p4-fusion):
  incredibly fast, but the work-in-progress branch support was not
  flexible enough for our needs. Nonetheless, p4-fusion is so good we
  use it internally.
