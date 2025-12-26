#!/usr/bin/bash

# Copyright (C) 2025 LightDig

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# SOFTWARE.

# This script looks to establish a persistant storage for Starchy
# It starts by looping through home directories and seeing if it provides
# them in its own /persistant/ folder. If not, it creates the folder
# with the appropriate permissions and user/group ids.
# Finally it creates a symlink from the persistant home directories
# into each user's home directories.

# additionally it also symlinks the NetworkManager config to enable
# remembering network connections

mkdir /new_root/persistant
[[ ! -d $patch/persistant/home ]] && mkdir -p "$patch/persistant/home"
[[ ! -d $patch/persistant/NetworkManager ]] && mkdir -p "$patch/persistant/NetworkManager"
mount --bind $patch/persistant /new_root/persistant
for i in $(basename /new_root/home/*); do
	if [[ ! -d "$patch/persistant/home/$i" ]]; then
		ugid=$(ls -dn /new_root/home/$i | awk '{print($3,$4)}' | tr ' ' ':')
		mkdir -m 750 $patch/persistant/home/$i
		chown $ugid "$patch/persistant/home/$i"
	fi
	ln -s /persistant/home/$i /new_root/home/$i/Persistant
done

rm -rf /new_root/etc/NetworkManager/
ln -sf /persistant/NetworkManager /new_root/etc/NetworkManager
