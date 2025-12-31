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

# make sure we are running in bash
if [ -z "$BASH_VERSION" ]
then
	echo "Please use bash. Other shells may result in undefined behaviour."
	exit 1
fi

[[ $sourced_common = true ]] || source ./common.sh nolock

case "$1" in
	fetch) # function for moving the system and/or initramfs to folder
		[[ -f "$odir/system.sfs" ]] && mv "$odir/system.sfs" ./ || exit 1
		[[ -f "$odir/initramfs.img" ]] && mv "$odir/initramfs.img" ./ || exit 1
	;;
	mv|cp)
		[[ $2 ]] || err "don't know what to move."
		[[ $2 =~ initramfs|system ]] || err "item '$2' not recognised. Use initramfs or system."
		[[ $3 ]] || err "don't know where to move $2."

		# get path of file
		case $2 in system) mvfrom="$odir/system.sfs"; ;; initramfs) mvfrom="$odir/initramfs.img"; ;; esac

		# move file
		mv "$mvfrom" "$3" || exit 1
	;;
	*)
		umount /tmp/recovery/mount
		umount /etc/initcpio
		umount "$wdir/initcpio"
		rm -rf "$wdir"
		echo finished
	;;
esac
