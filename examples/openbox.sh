#!/usr/bin/bash

pre_chroot() {
	# openbox packages
	p_openbox=(openbox xorg-xinit polybar dunst hsetroot gnome-disk-utility lxterminal lxrandr qalculate-gtk gucharmap pcmanfm baobab pulseaudio pavucontrol sof-firmware blueman rofi xcape xorg-server file-roller slop xorg-xprop wmctrl alsa-utils gedit lxqt-policykit slock libinput)

	# packages for zsh shell
	p_zsh=(zsh zsh-syntax-highlighting zsh-autosuggestions fzf)

	# register packages if needed
	[[ $openbox = true ]] && extra_packages+=("${p_openbox[@]}")
	[[ $shell = zsh ]] && extra_packages+=("${p_zsh[@]}")

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

}

post_chroot() {
	# Download a dunstrc example from dikiaap/dotfiles
	wget https://raw.githubusercontent.com/dikiaap/dotfiles/master/.dunst/dunstrc -O "$root/home/$user/.config/dunst/dunstrc"
	sed -Ei 's/Paper/AdwaitaLegacy/g' "$root/home/$user/.config/dunst/dunstrc"

	# clear dotfiles in homes
	rm -r "$root"/root/.*
	rm "$root"/home/*/.{bash*,zcomp*}

	# remove guile cache
	rm -rf "$root"/usr/lib/guile/3.0/ccache/*

	# create power command that prints battery percentage as a number
	echo -e "#!/usr/bin/bash\ncat /sys/class/power_supply/BAT0/capacity" > "$root"/usr/local/bin/power
	chmod 755 "$root"/usr/local/bin/power

	# Install catpuccin-mocha-pink-cursor onto the system
	bash -c "cd \"$root/home/$user/.icons/\" && unzip \"$(pwd)/catppuccin-mocha-pink-cursors.zip\""

	# enable autologin on boot if selected
	[[ $autologin = true ]] && cat <<EOF > "$root"/etc/greetd/config.toml
[terminal]
# The VT to run the greeter on. Can be "next", "current" or a number
# designating the VT.
vt = 1

# The default session, also known as the greeter.
[default_session]

# \`agreety\` is the bundled agetty/login-lookalike. You can replace \`/bin/sh\`
# with whatever you want started, such as \`sway\`.
command = "agreety --cmd $shell"

# The user to run the command as. The privileges this user must have depends
# on the greeter. A graphical greeter may for example require the user to be
# in the \`video\` group.
user = "$user"

[initial_session]
command = "$shell"
user = "$user"
EOF

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
}
