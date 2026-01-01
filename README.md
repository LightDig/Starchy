THIS IS A WORK IN PROGRES AND IS NOT READY TO BE USED YET

# Starchy
A small project written in shell and python that aims to create a usable Arch Linux system as a SquashFS and provide the necessary means to make this system bootable, either directly from a computer's hard drive or from a removable medium. The project's aim is more towards creativity rather than absolute necessity.

This project provides a shell script `starchy.sh` and a wrapper script `starchy.py` that can be used to easily pass arguments onto the shell script and load/save presets.

## Warning
This is a program that MUST be run as root. Since it's mostly written in shell, it is trivially easy to input malicious arbitrary code. Common sense should go a long way in making sure your system stays intact. When running the python wrapper you are given an overview of all the options and the characters `$()[]&|;` are considered invalid input, however this might not be enough to fully preclude all attacks. Running the bash script directly gives you a warning but no overview.

## Features
- Generate a SquashFS filesystem with a functional Arch Linux Installation with:
  - A root user and one unprivileged user
  - An option to write folders and tarballs into the filesystem
  - Many configuration options
  - Sourcing a custom script that contains user-defined functions to do basically anything
- Generate an initramfs that can mount the SFS with support for:
  - A tmpfs overlay for writing temporary changes in memory
  - An option to use zram so that changes in memory are compressed
  - A patch system that allows loading a script + files to make changes to your system without fully rebuilding
    - The patch system can be used to set up a persistant storage
    - The patch can be on an encrypted partition
    - The patch system starts out in the initramfs but has a function for registering a script as a simple systemd service for anything that can not be done from the initramfs
  - A `copy_to_ram` feature to allow faster reading + detaching the removable medium containing the image
  - Automatic poweroff of the system if the removable medium is removed without `copy_to_ram`.
  - A boot password
  - Booting the SFS from a file or from a partition
  - Booting the SFS from a file on an encrypted partition
- Store/load json presets or export bash wrapper scripts to recreate your system
  - Json presets require the python wrapper but can easily be configured and have options overriden from the command line.
  - Bash presets can run without python but the file needs to be manually edited to make changes.

Since there are a lot of options and no one correct way to do things, information on how to use this project is available [in the wiki](https://github.com/LightDig/Starchy/wiki).

## Prerequisites
This program only supports Arch Linux because it depends on Arch-specific packages. If you want to run it on an Arch-based distribution, you must uncomment some lines in `starchy.sh`. Do this at your own risk! Since Arch-based distributions have different repositories, it will likely not result a vanilla Arch system, but rather a minimal Arch derivative.

It is possible to run this script from the official Arch installation medium if you do not have an Arch system installed (use `iwctl` to connect to WiFi).

**Package requirements**
|Package|Use|
|-|-|
|`arch-install-scripts`|To pacstrap the system|
|`squashfs-tools`|Make the SquashFS file|
|`mkinitcpio`|Build the initramfs|
|`python`|For running the wrapper script|

Note that you probably already have `mkinitcpio` and `python` as `mkinitcpio` is the default initramfs dependency of the `linux` package and `python` is required for a lot of other programs.

## Todo
- [ ] Write more wiki pages
- [ ] Finish working on mkinitcpio portion of script
