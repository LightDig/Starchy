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
# ensure that this script is running as root
if [[ ! $EUID -eq 0 ]]; then
	echo "This script must be run as root!"
	exit 1
fi

# set a warning for running this script
[[ -z $warning ]] && warning=true
if [[ $warning = true ]]; then
	echo "This script runs with sudo privileges, please look carefully at any"
	echo "provided input and make sure that this script will work properly on"
	echo "your system! Malicious or improper configuration may lead to data loss!"

	printf "\nWould you like to continue?"
	read -rp " [y/N]: " yn
	case $yn in
		[Yy]*) continue=true ;;
	esac

	[[ $continue != true ]] && echo "Aborted" && exit 1
fi

# ensure that this script is running on Arch Linux
if ! grep -qiE '^ID(_LIKE)?=arch$' /etc/os-release; then
	echo "This system is intended to be run on an Arch based system."
	quit=true
fi

# check that script is running in bash
if [[ -z $BASH_VERSION ]]; then
	echo "This script may cause harm to your system if not executed correctly, please use bash."
	quit=true
fi

# ensure that arch-chroot and pacstrap are available on system
if ! command -v pacstrap > /dev/null; then
	echo "'arch-chroot' is required by this script!"
	echo "Please install 'extra/arch-install-scripts'."
	quit=true
fi

# ensure that that mksquashfs is available on system
if ! command -v mksquashfs > /dev/null; then
	echo "'mksquashfs' is required by this script!"
	echo "Please install extra/squashfs-tools"
	quit=true
fi

if [[ $mkinitcpio = true ]] && ! command -v mkinitcpio > /dev/null; then
	echo "Command 'mkinitcpio' not present on system"
	echo "Initramfs generation will be skipped!"
	mkinitcpio=false
fi

# if any errors occured, exit now
[[ $quit = true ]] && exit 1

# ### CONFIGURATION ###
# MISCONFIGURING THIS SCRIPT CAN RESULT IN DATA LOSS

## build options
[[ -z $wdir ]] && wdir=/tmp/recovery
[[ -z $odir ]] && odir="$wdir/output"
root=$wdir/system

## standard options
[[ -z $user ]] && user=john # username of unprivileged user
[[ -z $no_root_passwd ]] && no_root_passwd=false # whether to disable password for root user
[[ -z $timezone ]] && timezone="UTC" # path relative to /usr/share/zoneinfo
[[ -z $hostname ]] && hostname=$(cat /etc/hostname)
[[ -z $keymap ]] && keymap=$(cat /etc/vconsole.conf | grep "KEYMAP=" | sed 's/KEYMAP=//') # keymap for tty
[[ -z $user_shell ]] && user_shell="/usr/bin/bash"
[[ -z $root_shell ]] && root_shell="/usr/bin/bash"

## package flags
## uncomment to make any default to true
# [[ -z $recovery ]] && recovery=true
# [[ -z $network ]] && network=true
# [[ -z $media ]] && media=true
# [[ -z $yay ]] && yay=true

## compression options
[[ -z $compression ]] && compression="-comp zstd"

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

# set vars relating to initramfs
[[ -z $mdir ]] && mdir=$(pwd)/initcpio # dir with extra initcpio hooks
[[ -z $mkinitcpio ]] && mkinitcpio=false
[[ -z $mkinitcpio_modules ]] && mkinitcpio_modules="vfat"
[[ -z $mkinitcpio_binaries ]] && mkinitcpio_binaries=""
[[ -z $mkinitcpio_files ]] && mkinitcpio_binaries=""
[[ -z $mkinitcpio_hooks ]] && mkinitcpio_hooks="base microcode keyboard keymap autodetect udev block squashfs patch"
[[ -z $mkinitcpio_passwd ]] && mkinitcpio_passwd=""
[[ -z $mkinitcpio_cmdline_blacklist ]] && mkinitcpio_cmdline_blacklist=""

# set placeholder functions so that bash doesn't start throwing errors
pre_run() { true; }
pre_pacstrap() { true; }
pre_chroot() { true; }
post_chroot() { true; }

# source bash script for providing variables and functions
for i in "${scripts[@]}"; do
	source "$i"
done

pre_run

# if $only_mkinitcpio is true, then skip main part of script
if ! [[ $only_mkinitcpio = true ]]; then

# ### BASIC SETUP ###
# check that important vars are set
[[ -z $wdir ]] && echo "\$wdir is not set!" && exit 1
[[ -z $user ]] && echo "\$user is not set!" && exit 1

# make sure the working directory is not root
[[ $wdir = "/" ]] && echo "\$wdir is not allowed to be \"/\"!" && exit 1

# if yay is set to a user, check that that user actually exists
if [[ $yay ]] && ! compgen -u | grep -Eq "^$yay$"; then
	echo user \""$yay"\" for building yay does not exist on your system!
	exit 1
fi

## prepare dirs for building the image
[[ ! -d "$(dirname "$wdir")" ]] && echo "\"$(dirname "$wdir")\": folder does not exist" && exit 1
mkdir -p "$root" # $wdir/system
mkdir -p "$odir"
chmod 750 "$wdir" # don't allow other users to spy on our system

# build yay if user is set for building
if [[ $yay ]]; then
	mkdir -m 770 "$wdir/yay"
	chown "$yay":root "$wdir/yay"
	sudo -u "$yay" bash -c "cd $wdir/yay && git clone https://aur.archlinux.org/yay && cd yay && makepkg -s"
fi

# ### START BUILDING ###

# create bind mount for arch-chrooting later
! mount --bind "$root" "$root" && exit 1

## package groups for the installation
# you are encouraged to modify these lists to your needs

# packages to always install
base=(base vim zip unzip less pacman-contrib usbutils cryptsetup zstd strace which tree pciutils ethtool hwdetect dmidecode lm_sensors htop btop lsof git kmod wget locate sudo)

p_recovery=(arch-install-scripts efibootmgr squashfs-tools btrfs-progs e2fsprogs dosfstools exfatprogs ntfs-3g grub mokutil sbsigntools)

# network packages
p_network=(networkmanager dhcpcd)

# media viewers
p_media=(ristretto vlc vlc-plugin-ffmpeg)

# to be installed with yay
p_yay=(base-devel)

pre_pacstrap

# install system packages
pacstrap -K "$root" \
	${base[@]} \
	${extra_packages[@]} \
	${linux_firmware[@]} \
	$([[ $recovery ]] && echo ${p_recovery[@]}) \
	$([[ $yay ]] && echo ${p_yay[@]}) \
	$([[ $network = true ]] && echo ${p_network[@]}) \
	$([[ $media = true ]] && echo ${p_media[@]}) \

## copy kernel modules from host into system
mkdir "$root/lib/modules"
cp -r "/lib/modules/$(uname -r)" "$root/lib/modules/."
[[ ! $no_rm_kernel_build_dir = true ]] && rm -rf "$root"/lib/modules/*/{build,vdso}

# copy yay package files into system
[[ $yay ]] && bash -c "cd $yay && cp *.pkg\.tar\.zst $root/."

# copy tarball or folder into the root directory before running chroot
for i in "${copy_to_root[@]}"; do
	echo "copying $i to root directory..."
	if [[ -f "$i" ]]; then
		tar -xf "$i" -C "$root/"
	else
		cp -r "$i"/* "$root/"
	fi
done

# ### PRECONFIG ###
pre_chroot # which is no rather the pre-SYSTEM SETUP function as a proper chroot no longer occurs

# ### SYSTEM SETUP ###
# This used to be handled in a proper chroot but that
# caused some issues

if [[ ! $no_root_passwd = true ]]; then
	echo "Changing password of user root"
	while true; do passwd -R "$root" && break; done # set root password
fi

useradd -R "$root" -mG wheel "$user"
echo "Changing password of user $user"
while true; do passwd -R "$root" "$user" && break; done # set user password

# update locale.gen to include American English
sed -Ei "s/^#(en_US.UTF-8)/\1/" "$root/etc/locale.gen"
echo -e "LANG=en_US.UTF-8\nLC_ALL=en_US.UTF-8" > "$root/etc/locale.conf"

# Generate english locales
I18NPATH="$root/usr/share/i18n/" localedef --prefix="$root" -i en_US -f UTF-8 "$root/usr/share/locale/en_US"

[[ $systemd_enable ]] && systemctl --root "$root" enable ${systemd_enable[@]}
[[ $systemd_disable ]] && systemctl --root "$root" disable ${systemd_disable[@]}
[[ $systemd_mask ]] && systemctl --root "$root" mask ${systemd_mask}

systemctl --root "$root" mask tmp.mount
[[ $autologin ]] && systemctl --root "$root" enable greetd

# install yay
[[ $yay ]] && pacman -r "$root" -U yay-*.pkg.tar.zst

# Change user shell
sed -Ei "s/(^$user:x:.*)\/usr\/bin\/bash/\1$(echo "$user_shell" | sed 's/\//\\\//g')/" "$root/etc/passwd"

# Change root shell
sed -Ei "s/(^root:x:.*)\/usr\/bin\/bash/\1$(echo "$root_shell" | sed 's/\//\\\//g')/" "$root/etc/passwd"

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
cat <<EOF > "$root/usr/share/libalpm/hooks/10-remove-mkinitcpio-hooks.hook"
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
chown -R 1000:1000 "$root/home/$user"

# clear pacman cache as well as yay package files
rm "$root"/var/cache/pacman/pkg/*
[[ $yay ]] && rm "$root"/yay-*

# remove guile cache
[[ ! $no_rm_guile_cache = true ]] && rm -rf "$root"/usr/lib/guile/*/ccache/*

# remove all locales except en and en_US
sh -c "cd $root/usr/share/locale && rm -rf \$(ls | grep -vE \"^en$|^en_US$|^locale\.alias$\")"

# create pacman hook to clear cache after every install
# This doesn't work in its current form because it causes problems with yay
#cat <<EOF > "$root/usr/share/libalpm/hooks/paccache.hook"
#[Trigger]
#Operation = Upgrade
#Operation = Install
#Type = Package
#Target = *
#[Action]
#Description = Removing pacman cache
#When = PostTransaction
#Exec = /bin/bash -c '/sbin/paccache -rk0; rm -rf /home/*/.cache/yay/*'
#EOF

# delete pacman mkinitcpio hooks in case mkinitcpio has been installed on system
rm -f "$root/usr/share/libalpm/*/*mkinitcpio*"

# ### SQUASH SYSTEM ###

mksquashfs "$root"/ "$odir/system.sfs" $compression

fi # script continues here if $only_mkinitcpio = true

# ### INITRAMFS ###

if [[ $mkinitcpio = true ]]; then
# variable containing mkinitcpio.conf
# do not set if sourced script already provides this
[[ -z $mkinitcpio_conf ]] && mkinitcpio_conf=$(cat <<EOF
MODULES=(${mkinitcpio_modules[*]})
BINARIES=(${mkinitcpio_binaries[*]})
FILES=(${mkinitcpio_files[*]})
HOOKS=(${mkinitcpio_hooks[*]})
EOF
)


# generate mkinitcpio.conf
# overlay initcpio hooks
# the hooks are overlayed to prevent any chance of accidentally messing
# with the users system. This script is supposed to be able to run without
# any changes to the system, other than at the pwd, if it is configured correctly.
mkdir "$wdir/initcpio"

# create temporary filesystem for working on mkinitcpio hooks
mount -t tmpfs initcpio "$wdir/initcpio"

# copy mkinitcpio hooks into temporary directory
cp "$mdir"/{hooks,install,post} "$wdir/initcpio/"

if [[ ! $mkinitcpio_vanilla_hooks = true ]]; then # skip the following section for $mkinitcpio_vanilla_hooks = true
# check if password hash has been provided, set up password hook with hash
if [[ $mkinitcpio_passwd_hash ]]; then
	# place the hash in the file
	sed -Ei $(echo $mkinitcpio_passwd_hash | sed 's/  -//') "$wdir/initcpio/hooks/passwd"
# if no hash is provided, but password is desired, request entering password
elif [[ $mkinitcpio_passwd ]]; then
	while true; do
		read -rsp 'Enter boot password > ' pass1 # set password
		read -rsp 'Confirm password > ' pass2 # confirm password
		[[ "$pass1" = "$pass2" ]] && break # if they match, break loop
		echo "Passwords don't match! Try again."
	done
	pass1=$(echo "$pass1" | sed -E 's/\\/\\\\/g;s/  -$//') # fix backslashes for sed and clean output
	sed -Ei "s/PASSWD_HASH/$pass1/" "$wdir/initcpio/hooks/passwd" # place hash in hook
fi

# if cmdline parameter blacklist is provided
if [[ $mkinitcpio_cmdline_blacklist ]]; then
	$mkinitcpio_cmdline_blacklist=$(echo $mkinitcpio_cmdline_blacklist | sed 's/\\/\\\\/g')
	sed -Ei "s/CMDLINE_BLACKLIST/$mkinitcpio_cmdline_blacklist/" "$wdir/initcpio/hooks/cmdline-blacklist"
fi

mount -t overlay hooks -o "lowerdir=/etc/initcpio:$wdir/initcpio" /etc/initcpio

echo "$mkinitcpio_conf" > "$wdir/initcpio/mkinitcpio.conf"

fi # end if for $mkinitcpio_vanilla_hooks != true

mkinitcpio --config "$wdir/initcpio/mkinitcpio.conf" --generate "$odir/initramfs.img"

if [[ ! $mkinitcpio_vanilla_hooks ]]; then

# remove overlays
umount /etc/initcpio/hooks
umount /etc/initcpio/install
umount "$wdir/initcpio"

fi # end if for $mkinitcpio_vanilla_hooks != true

fi # end if for $mkinitcpio = true

# ### DONE ###
echo "FINISHED -- GOTO $odir/"
