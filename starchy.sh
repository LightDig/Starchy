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

#############################

# ### NOTICE ###

# USE THIS SCRIPT AT YOUR OWN RISK
# RUN AS ROOT
# ALWAYS RUN WITH BASH OR RISK BREAKING YOUR SYSTEM
# PRODUCES IMAGE AT ${odir}/system.sfs
# READ THROUGH SCRIPT AND/OR DOCUMENTATION BEFORE RUNNING

# it is recommended to use a wrapper, such as the provided python
# wrapper, for setting environment variables to control the script,
# however values can also be set by modifying this script.

# ### INITIAL CHECKS ###

# check that script is running in bash
# tested by invoking ksh, busybox ash, dash, tcsh, osh and zsh from bash.
# now I have too many shells on my computer
if [ -z "$BASH_VERSION" ]
then
	echo "Please use bash. Other shells may result in undefined behaviour."
	exit 1
fi

[[ $sourced_common ]] || source ./common.sh # source common functions

# package groups
package_groups=(base texteditors recovery network media yay)
register_package_group() {
	local name=$(sed 's/ /_/g' <<< "$1")
	package_groups+=("$name")
	eval "pkgroup_$name=(${*:2})"
}

# ### CONTINUE CHECKS ###

# set a warning for running this script

# check dependencies
check_dependencies arch-install-scripts squashfs-tools

if ! opt_dependency mkinitcpio; then
	warn "command 'mkinitcpio' not present on system. Initramfs generation will be skipped!"
	mkinitcpio=false
fi


# ### CONFIGURATION ###

# MISCONFIGURING THIS SCRIPT CAN RESULT IN DATA LOSS

## standard options
# default user john # username of unprivileged user
default no_root_passwd false # whether to disable password for root user
default timezone "$(readlink /etc/localtime)"
timezone=${timezone/\/usr\/share\/zoneinfo\//} # strip zoneinfo path from timezone
default hostname "$(cat /etc/hostname)"
default keymap "$(cat /etc/vconsole.conf | grep "KEYMAP=" | sed 's/KEYMAP=//')" # keymap for tty
default user_shell /usr/bin/bash
default root_shell /usr/bin/bash

## package flags
## uncomment to make any default to true
# default install_recovery true
# default install_network true
# default install_media true

## compression options
# available algorithms: gzip, lzo, lz4, xz, zstd
default compression zstd

# Whether to build initramfs
# uncomment to enable by default
# [[ -z $mkinitcpio ]] && mkinitcpio=true

## ARRAYS
# process arrays from python wrapper
AD=$(echo -e "\e")
arrays=(sd_enable sd_disable sd_mask extra_packages scripts firmware copy_to_root)
for x in "${arrays[@]}"; do
	DA="$x"_arr
	IFS=$AD read -ra "${x?}" <<< "${!DA}"
done

# set placeholder functions so that bash doesn't start throwing errors
pre_run() { true; }
pre_chroot() { true; }
post_chroot() { true; }

# source bash script for providing variables and functions
for i in "${scripts[@]}"; do
	source "$i"
done

# ### BASIC SETUP ###
# check that important vars are set
[[ -z $wdir ]] && err "\$wdir is not set!"

# make sure the working directory is not root
[[ $wdir = "/" ]] && err "\$wdir is not allowed to be \"/\"!"

# if yay is set to a user, check that that user actually exists
if [[ $yay ]] && [[ ! $(compgen -u) =~ ^"$yay"$ ]]; then
	echo user \""$yay"\" for building yay does not exist on your system!
	exit 1
fi

# build yay if user is set for building
if [[ $yay ]]; then
	mkdir -m 770 "$wdir/yay"
	chown "$yay":root "$wdir/yay"
	sudo -u "$yay" bash -c "cd $wdir/yay && git clone https://aur.archlinux.org/yay && cd yay && makepkg -s"
fi

# ### START BUILDING ###

pre_run

## package groups for the installation
# you are encouraged to modify these lists to your needs

# packages to always install
default install_base true # install by default, unless explicitly disabled
default_arr pkgroup_base base zip unzip less pacman-contrib usbutils cryptsetup zstd strace which tree pciutils ethtool hwdetect dmidecode lm_sensors htop btop lsof git kmod wget locate sudo

default install_texteditors true # install by default, unless explicitly disabled
pkgroup_texteditors=(vim nano)

default_arr pkgroup_recovery arch-install-scripts efibootmgr squashfs-tools btrfs-progs e2fsprogs dosfstools exfatprogs ntfs-3g grub mokutil sbsigntools mkinitcpio

# network packages
default_arr pkgroup_network networkmanager dhcpcd

# media viewers
default_arr pkgroup_media ristretto vlc vlc-plugin-ffmpeg

# to be installed with yay
default_arr pkgroup_yay base-devel

# create package array
for i in "${package_groups[@]}"; do
	name=install_$i
	[[ ${!name} ]] && eval "pacstrap+=(\${pkgroup_$i[@]})"
done

pacstrap+=("${firmware[@]}")

# install system packages
pacstrap "$root" "${pacstrap[@]}" # install packages

# fetch kernel
# this will do an "improper" installation and extract the kernel from the package
# as updating the linux kernel package is not possible in a read-only system

# Ask if kernel should be copied or downloaded
echo "Would you like to copy your kernel modules over or pull the latest kernel from pacman?"
echo "Fetching with pacman will put the kernel in your local system's cache."
echo "You will be given the option to remove it if you wish."
echo "1) Pacman (recommended)"
echo "2) Copy"
echo "Default = 1"
echo
while true; do # ask until valid input
	read -rp '> ' prompt
	[[ $prompt =~ [12] ]] && break
	[[ -z $prompt ]] && prompt=1 && break
done

if [[ $prompt -eq 1 ]]; then # if kernel should be downloaded
	kernel=$(pacman -Ss ^linux$ --noconfirm | grep -Eo '([0-9.-]|arch)+') # fetch latest kernel name
	pacman -Sddw linux # download kernel package to cache
	# install kernel on child system
	# extract the kernel into the root filesystem
	(cd "$root" && tar -xf /var/cache/pacman/pkg/linux-"$kernel"*.pkg.tar.zst usr/lib/modules)
	read -rp "Remove kernel from cache? [y/N]> " prompt
	[[ ${prompt:0:1} =~ y|Y ]] && rm /var/cache/pacman/pkg/linux-"$kernel"*.pkg.tar.zst*
else # if kernel should be copied
	kernels=(/usr/lib/modules/*)
	if [[ ${#kernels} -gt 1 ]]; then
		echo "Multiple kernels found!"
		echo "Which one would you like to copy over?"
		echo
		i=1
		for x in "${kernels[@]}"; do
			echo "$i) $(basename "$x")"
			((i+=1))
		done
		while true; do
			read -rp '> ' prompt
			if [[ $prompt =~ [0-9]+ ]]; then
				((prompt-=1))
				[[ $prompt -lt ${#kernels} ]] && kernel="${kernels[$prompt]}" && break
			fi
		cp -r "/usr/lib/modules/$kernel" "$root/usr/lib/modules/"
		done
	else
		kernel="${kernels[0]}" # store kernel for later
		cp -r "/usr/lib/modules/$kernel" "$root/usr/lib/modules/"
	fi
	kernel_folders=(/usr/lib/modules/$kernel/*/)
	echo "Additional folders have been copied over."
	echo "These are likely not necessary. Would you like to remove them?"
	echo
	for x in "${kernel_folders[@]}"; do
		[[ $x != kernel ]] && echo "${x/$root/}" # print path of folders within the system to be removed
	done
	echo
	read -rp "[Y/n] > " prompt # prompt to remove the unnecessary folders
	[[ ! $prompt =~ n|N ]] && (cd "$root/usr/lib/modules/$kernel" && rm -rf !(kernel)/)
fi

# copy yay package files into system
[[ $yay ]] && bash -c "cd $yay && cp *.pkg\.tar\.zst $root/."

# copy tarball or folder into the root directory before running chroot
for i in "${copy_to_root[@]}"; do
	echo "copying $i to root directory..."
	if [[ -f "$i" ]]; then
		(cd "$root" && tar -xf "$i")
	else
		cp -r "$i"/* "$root/"
	fi
done

# ### SYSTEM SETUP ###

# This used to be handled in a proper chroot but that
# caused some issues

pre_chroot # There is no more proper chroot but the idea remains

if [[ ! $no_root_passwd = true ]]; then
	echo "Changing password of user root"
	while true; do passwd -R "$root" && break; done # set root password
fi

if [[ $user ]]; then
	useradd -R "$root" -mG wheel "$user"
	echo "Changing password of user $user"
	while true; do passwd -R "$root" "$user" && break; done # set user password
fi

# update locale.gen to include American English
sed -Ei "s/^#(en_US.UTF-8)/\1/" "$root/etc/locale.gen"
echo -e "LANG=en_US.UTF-8\nLC_ALL=en_US.UTF-8" > "$root/etc/locale.conf"

# Generate english locales
#I18NPATH="$root/usr/share/i18n/" localedef --prefix="$root" -i en_US -f UTF-8 "$root/usr/share/locale/en_US"
chroot "$root" locale-gen

[[ $systemd_enable ]] && systemctl --root "$root" enable ${systemd_enable[@]}
[[ $systemd_disable ]] && systemctl --root "$root" disable ${systemd_disable[@]}
[[ $systemd_mask ]] && systemctl --root "$root" mask ${systemd_mask}

systemctl --root "$root" mask tmp.mount
[[ $autologin ]] && systemctl --root "$root" enable greetd

# install yay
[[ $yay ]] && pacman -r "$root" -U yay-*.pkg.tar.zst

# Change user shell
sed -Ei "s/(^$user:x:.*)\/usr\/bin\/bash/\1$(sed 's/\//\\\//g' <<< "$user_shell")/" "$root/etc/passwd"

# Change root shell
sed -Ei "s/(^root:x:.*)\/usr\/bin\/bash/\1$(sed 's/\//\\\//g' <<< "$root_shell")/" "$root/etc/passwd"

# set system's hostname
echo "$hostname" > "$root/etc/hostname"

# set tty font
echo "KEYMAP=$keymap" > "$root/etc/vconsole.conf"

# make sudo use wheel group and never prompt password
sed -Ei 's/# (%wheel ALL=\(ALL:ALL\) ALL)/\1/' "$root/etc/sudoers"
chmod 660 "$root/etc/sudoers"
echo "Defaults lecture = never" >> "$root/etc/sudoers"
chmod 440 "$root/etc/sudoers"

if ! ls "$root/usr/share/zoneinfo/$timezone" &> /dev/null; then
	echo
	echo Your selected timezone \"$timezone\" does not appear to be available on the system!
	echo If you\'d like, you may type in a new time zone and check if it is valid.
	echo Alternatively type \"continue\" to leave it as is.
	while true; do
		read -rp '> ' timezone
		if [[ "$timezone" = continue ]]; then
			break
		elif ls "$root/usr/share/zoneinfo/$timezone" &> /dev/null; then
			ln -sf "/usr/share/zoneinfo/$timezone" "$root/etc/localtime"
			break
		else
			echo "The provided input still seems to be invalid!"
		fi
	done
fi

# Populate home folders if needed
if [[ $populate = true ]]; then
	for i in "$root"/home/*; do
		mkdir "$i"/{Downloads,Documents,Pictures,Videos,Music,Applications}
	done
fi

# populate root home folder if needed
[[ $populate_root = true ]] && mkdir "$root"/root/{Downloads,Documents,Pictures,Videos,Music,Applications}

# enable autologin on boot if selected
[[ $autologin = true ]] && cat <<EOF > "$root/etc/greetd/config.toml"
[terminal]
# The VT to run the greeter on. Can be "next", "current" or a number
# designating the VT.
vt = 1

# The default session, also known as the greeter.
[default_session]

# \`agreety\` is the bundled agetty/login-lookalike. You can replace \`/bin/sh\`
# with whatever you want started, such as \`sway\`.
command = "agreety --cmd $user_shell"

# The user to run the command as. The privileges this user must have depends
# on the greeter. A graphical greeter may for example require the user to be
# in the \`video\` group.
user = "$user"

[initial_session]
command = "$user_shell"
user = "$user"
EOF

# create hook to delete mkinitcpio hook
# initramfs should not be autogenerated
cat <<EOF > "$root/usr/share/libalpm/hooks/10-remove-initcpio-hooks.hook"
[Trigger]
Operation = Upgrade
Operation = Install
Type = Package
Target = *
[Action]
Description = Removing pacman mkinitcpio hooks
When = PostTransaction
Exec = /bin/bash -c 'rm -f /usr/share/libalpm/*/*mkinitcpio*'
EOF

# ### POST-CHROOT ###

post_chroot

# Set all files in home folder to be owned by unprivileged user
[[ $user ]] && chown -R 1000:1000 "$root/home/$user"

# clear pacman cache as well as yay package files
rm "$root"/var/cache/pacman/pkg/*
[[ $yay ]] && rm "$root"/yay-*

# remove guile cache
[[ ! $no_rm_guile_cache = true ]] && rm -rf "$root"/usr/lib/guile/*/ccache/*

# remove all locales except en and en_US
sh -c "cd $root/usr/share/locale && rm -rf \$(ls | grep -vE \"^en$|^en_US$|^locale\.alias$\")"

# create pacman hook to clear cache after every install
# This doesn't work in its current form because it causes problems with yay
[[ $paccache_hook ]] && cat <<EOF > "$root/usr/share/libalpm/hooks/paccache.hook"
[Trigger]
Operation = Upgrade
Operation = Install
Type = Package
Target = *
[Action]
Description = Removing pacman cache
When = PostTransaction
Exec = /bin/bash -c '/sbin/paccache -rk0; rm -rf /home/*/.cache/yay/*'
EOF

# delete pacman mkinitcpio hooks in case mkinitcpio has been installed on system
rm -f "$root"/usr/share/libalpm/*/*mkinitcpio*

# ### SQUASH SYSTEM ###

mksquashfs "$root"/ "$odir/system.sfs" -comp $compression

# ### DONE ###
echo "FINISHED -- GOTO $odir/"
