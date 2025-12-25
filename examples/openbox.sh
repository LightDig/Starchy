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

pre_pacstrap() {
	# openbox packages
	p_openbox=(openbox xorg-xinit polybar dunst hsetroot gnome-disk-utility lxterminal lxrandr qalculate-gtk gucharmap pcmanfm baobab pulseaudio pavucontrol sof-firmware blueman rofi xcape xorg-server file-roller slop xorg-xprop wmctrl alsa-utils gedit lxqt-policykit slock libinput)

	# packages for zsh shell
	p_zsh=(zsh zsh-syntax-highlighting zsh-autosuggestions fzf)

	# register packages if needed
	[[ $openbox = true ]] && extra_packages+=("${p_openbox[@]}")
	[[ $shell = zsh ]] && extra_packages+=("${p_zsh[@]}")
}

post_chroot() {
	mv "$root/home/user" "$root/home/$user"

	# Download and modify dunstrc example from dikiaap/dotfiles
	wget https://raw.githubusercontent.com/dikiaap/dotfiles/master/.dunst/dunstrc -O "$root/home/$user/.config/dunst/dunstrc"
	sed -Ei 's/Paper/AdwaitaLegacy/g' "$root/home/$user/.config/dunst/dunstrc"

	# Download example desktop background image (https://unsplash.com/photos/volcano-erupting-with-glowing-lava-and-smoke-OV3rAjhb8r0)
	wget https://images.unsplash.com/photo-1760710003079-03415284552a\?q=80\&w=1471\&auto=format\&fit=crop\&ixlib=rb-4.1.0\&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D -O "$root/home/$user/.config/dunst/dunstrc"

	# Download and configure polywins script from https://github.com/uniquepointer/polywins
	wget https://raw.githubusercontent.com/uniquepointer/polywins/refs/heads/master/polywins.sh -O "$root/home/$user/.config/polybar/scripts/polywins.sh"
	sed -Ei 's/(active_text_color="#)250F0B/\1F0EEF0/;s/(active_underline="#)ECB3B2/\1F0C6F0/;s/(inactive_text_color="#)250F0B/\1A5A8A6/' "$root/home/$user/.config/polybar/scripts/polywins.sh"
	chmod +x "$root/home/$user/.config/polybar/scripts/polywins.sh"

	# create power command that prints battery percentage as a number
	echo -e "#!/usr/bin/bash\ncat /sys/class/power_supply/BAT0/capacity" > "$root/usr/local/bin/power"
	chmod 755 "$root"/usr/local/bin/power

	# Make sfsinfo command
	cat <<INFOEOF > "$root/usr/local/bin/sfsinfo"
cat <<EOF
Squashed Arch Recovery System, $(date +%B) image:
Kernel: \$(uname -r)

build date:$r $(date +%Y-%m-%d)
age: \$(expr \( \$(date +%s) - $(date +%s) \) / 1440) days
EOF
INFOEOF
	ln -s /usr/local/bin/sfsinfo "$root/usr/local/bin/sinfo"
	ln -s /usr/local/bin/sfsinfo "$root/usr/local/bin/info"
	ln -s /usr/local/bin/sfsinfo "$root/usr/local/bin/sfs"
	chmod +x "$root/usr/local/bin/sfsinfo"

	# Create systemd service for locking screen when user suspends
	# Only when $openbox is set to true
	[[ $openbox = true ]] && cat <<EOF > "$root/etc/systemd/system/slock@.service"
[Unit]
Description=Lock X session using slock for user %i
Before=sleep.target

[Service]
User=%i
Environment=DISPLAY=:0
ExecStart=/usr/bin/slock

[Install]
WantedBy=sleep.target
EOF

	arch-chroot "$root" <<EOF
# Enable slock service
[[ $openbox ]] && echo "systemctl enable slock@$user"

# set up shell
if [[ "$shell" = zsh ]]; then
	# install zsh-syntax-highlighting and zsh-autosuggestions plugins
	sudo -u "$user" sh -c "\$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"
	sudo -u "$user" sh -c "cd ~/.oh-my-zsh/plugins && git clone https://github.com/zsh-users/zsh-syntax-highlighting.git && git clone https://github.com/zsh-users/zsh-autosuggestions"
fi
EOF

	# clear dotfiles in homes
	rm -rf "$root"/root/.*
	rm "$root"/home/*/.{bash*,zcomp*}
}
