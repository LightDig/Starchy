THIS IS A WORK IN PROGRES AND IS NOT READY TO BE USED YET

# Starchy
A small project written in shell and python that aims to create a usable Arch Linux system as a SquashFS and provide the necessary means to make this system bootable, either directly from a computer's hard drive or from a removable medium. The project's aim is more towards creativity rather than absolute necessity.

This project provides a shell script `starchy.sh` and a wrapper script `starchy.py` that can be used to easily pass arguments onto the shell script and load/save presets.

## Warning
This is a program that MUST be run as root. Since these are scripts that can take user input, make sure you don't copy and paste malicious code or misconfigure the scripts. Common sense should go a long way in making sure your system stays intact. When running python wrapper you are given an overview of all the options. Running the bash script directly gives you a warning but no overview.

## Features
- Generate a SquashFS filesystem with a functional Arch Linux Installation with:
- - A root user and one unprivileged user
  - An option to write folders and tarballs into the filesystem
  - Many configuration options
  - Sourcing a custom script that contains user-defined functions to do basically anything
- Generate an initramfs that can mount the SFS with support for:
- - A tmpfs overlay for writing temporary changes in memory
  - An option to use zram so that changes in memory are compressed
  - A patch system that allows loading a script + files to make changes to your system without fully rebuilding
  - - The patch system can be used to set up a persistant storage
    - The patch can be on an encrypted partition
    - The patch system starts out in the initramfs but has a function for registering a script as a simple systemd service for anything that can not be done from the initramfs
  - A `copy_to_ram` feature to allow faster reading + detaching the removable medium containing the image
  - Automatic poweroff of the system if the removable medium is removed without `copy_to_ram`.
  - A boot password
  - Booting the SFS from a file or from a partition
  - Booting the SFS from a file on an encrypted partition

Since there are a lot of options and no one correct way to do things, information on how to use this project is available [in the wiki](https://github.com/LightDig/Starchy/wiki).
