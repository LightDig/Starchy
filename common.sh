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

# ensure that this script is running on Arch Linux
if ! grep -qiE '^ID(_LIKE)?=arch$' /etc/os-release; then
	echo "This system is intended to be run on an Arch based system."
	exit 1
fi

# ensure that this script is running as root
if [[ ! $EUID -eq 0 ]]; then
	echo "This script must be run as root!"
	exit 1
fi

[[ -z $warning ]] && warning=true
if [[ $warning = true ]]; then
	echo "This script runs with sudo privileges, please look carefully at any"
	echo "provided input and make sure that this script will work properly on"
	echo "your system! Malicious or improper configuration may lead to data loss!"

	printf "\nWould you like to continue?"
	read -rp " [y/N]: " yn
	[[ ! $yn =~ [Yy] ]] && echo "Aborted" && exit 1
fi

# ### FUNCTIONS ###
err() { echo "Error: $*"; exit 1; } # fatal error messages
warn() { echo "Warning: $*"; } # warning messages

# dependency checking
check_dependencies() {
	for i in $@; do
		if ! pacman -Q "$1" &> /dev/null; then
			echo "dependency: '$1' not satisfied"
			quit=true
		fi
	done
	[[ $quit = true ]] && exit 1
}

# optional dependency checking
opt_dependency() { pacman -Q "$1" &> /dev/null; }

default() { eval "[[ \$$1 ]] || $1='${*:2}'"; } # function for setting default values
default_arr() { eval "[[ \$$1 ]] || $1=(${*:2})"; } # function for setting default array value

shopt -s extglob # enable extended globbing

# build options
default wdir /tmp/recovery
odir="$wdir/output"
root="$wdir/system"

[[ $1 != nolock ]] && [[ -d $wdir ]] && err "$wdir already exists!"

## prepare dirs for building
if [[ ! $(basename "$0") = cleanup.sh ]]; then
	[[ ! -d "$(dirname "$wdir")" ]] && err "\"$(dirname "$wdir")\": folder does not exist"
	mkdir -p "$root"
	mkdir -p "$odir"
	chmod 750 "$wdir" # don't allow other users to spy on our system
fi

sourced_common=true
