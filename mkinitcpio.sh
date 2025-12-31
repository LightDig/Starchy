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

# ### INITIAL CHECKS ###

# make sure we are running in bash
if [ -z "$BASH_VERSION" ]
then
	echo "Please use bash. Other shells may result in undefined behaviour."
	exit 1
fi

[[ $sourced_common = true ]] || source ./common.sh

# make sure mkinitcpio is installed
check_dependencies mkinitcpio

# ### CONFIGURATION ###
# set vars relating to initramfs
default mdir "$(pwd)/initcpio" # the directory with extra initcpio hooks
default mkinitcpio false
default mkinitcpio_modules vfat
# default mkinitcpio_binaries
# default mkinitcpio_files
default mkinitcpio_hooks "base microcode keyboard keymap autodetect udev block squashfs patch"
# default mkinitcpio_passwd
# default mkinitcpio_cmdline_blacklist
default mkinitcpio_compression zstd

# if kernel from local device is specified
# as an argument then use that one.
if [[ $1 ]]; then
	kernel="$1"
fi

# ### INITRAMFS GENERATION ###

# variable containing mkinitcpio.conf
# do not set if sourced script already provides this
[[ -z $mkinitcpio_conf ]] && mkinitcpio_conf=$(cat <<EOF
MODULES=(${mkinitcpio_modules[*]})
BINARIES=(${mkinitcpio_binaries[*]})
FILES=(${mkinitcpio_files[*]})
HOOKS=(${mkinitcpio_hooks[*]})
COMPRESSION="$mkinitcpio_compression"
EOF
)

# the hooks are overlayed to prevent any chance of accidentally messing
# with the users system. This script is supposed to be able to run without
# any changes to the system, other than at the pwd, if it is configured correctly.

# create temporary filesystem for working on mkinitcpio hooks
mount -t tmpfs initcpio "$wdir/initcpio"

# copy mkinitcpio hooks into temporary directory
cp -r "$mdir"/{hooks,install,post} "$wdir/initcpio/"

if [[ ! $mkinitcpio_vanilla_hooks = true ]]; then # skip the following section for $mkinitcpio_vanilla_hooks = true
# check if password hash has been provided, set up password hook with hash
if [[ $mkinitcpio_passwd_hash ]]; then
	# place the hash in the file
	sed -Ei "s/$(sed 's/  -//' <<< "$mkinitcpio_passwd_hash")/PASSWD_HASH" "$wdir/initcpio/hooks/passwd"
# if no hash is provided, but password is desired, request entering password
elif [[ $mkinitcpio_passwd ]]; then
	while true; do
		read -rsp 'Enter boot password > ' pass1 # set password
		read -rsp 'Confirm password > ' pass2 # confirm password
		[[ "$pass1" = "$pass2" ]] && break # if they match, break loop
		echo "Passwords don't match! Try again."
	done
	pass1=$(sed -E 's/\\/\\\\/g;s/  -$//' <<< "$pass1") # fix backslashes for sed and clean output
	sed -Ei "s/PASSWD_HASH/$pass1/" "$wdir/initcpio/hooks/passwd" # place hash in hook
fi

# if cmdline parameter blacklist is provided
if [[ $mkinitcpio_cmdline_blacklist ]]; then
	mkinitcpio_cmdline_blacklist=$(sed 's/\\/\\\\/g' <<< "$mkinitcpio_cmdline_blacklist")
	sed -Ei "s/CMDLINE_BLACKLIST/$mkinitcpio_cmdline_blacklist/" "$wdir/initcpio/hooks/cmdline-blacklist"
fi

mount -t overlay hooks -o "lowerdir=/etc/initcpio:$wdir/initcpio" /etc/initcpio

echo "$mkinitcpio_conf" > "$wdir/initcpio/mkinitcpio.conf"

fi # end if for $mkinitcpio_vanilla_hooks != true

# mkinitcpio --config "$wdir/initcpio/mkinitcpio.conf" --generate "$odir/initramfs.img"

back="$(pwd)"
if [[ ! $kernel ]]; then
	echo "This script hasn't been passed a kernel location yet"
	echo "Please specify a path to your system image to fetch"
	echo "the kernel or press enter to select a local kernel"
	echo
	if [[ $wrapper = true ]]; then
		echo "Please note that if you are running this script standalone"
		echo "that it may not inherit the options you passed to any"
		echo "previous scripts."
		echo "It is recommended you use a wrapper with a preset to run"
		echo "this script."
	fi
	while true; do
		read -rp '> ' prompt
		if [[ ! $prompt ]]; then
			cd /usr/lib/modules || exit 1
			break
		fi
		if [[ -f $prompt ]]; then
			mkdir "$wdir/mount" || exit 1
			mount "$prompt" "$wdir/mount" || exit 1
			cd "$wdir/mount/usr/lib/modules" || exit 1
			break
		else
			cd "/usr/lib/modules" || exit 1
			break
		fi
	done
	kernels=(*)
	if [[ ${#kernels[@]} -gt 1 ]]; then
		echo "Multiple kernel folders found!"
		echo "Which one would you like to use?"
		echo
		i=1
		for kernel in "${kernels[@]}"; do
			echo "$i) $kernel"
			((i+=1))
		done
		while true; do
			read -rp '> ' prompt
			if [[ $prompt =~ [0-9]+ ]]; then
				((prompt-=1))
				[[ $prompt -lt ${#kernels} ]] && break
			fi
		done
		kernel="$(pwd)/${kernels[$prompt]}/vmlinuz"
	else
		kernel="$(pwd)/${kernels[0]}/vmlinuz"
	fi
fi

if ! cd "$back"; then
	echo "Failed to return to pwd ($back)"
	exit 1
fi

mkinitcpio --config "$wdir/initcpio/mkinitcpio.conf" --generate "$odir/initramfs.img" --kernel "$kernel"

# unmount
errs=()

umount /tmp/recovery/mount; errs+=($?)
umount /etc/initcpio; errs+=($?)
umount "$wdir/initcpio"; err+=($?)

for e in "${errs[@]}"; do
	[[ ! $e -eq 0 ]] && echo "At least one umount failed. Try again with ./cleanup"; break
done
