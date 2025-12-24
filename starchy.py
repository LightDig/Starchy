#!/usr/bin/python3

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

from argparse import ArgumentParser
import json
from pathlib import Path
import subprocess
import sys
import tomllib

# ### ARGUMENTS ###

parser = ArgumentParser(
	prog='starchy.py',
	description="Squashed Arch Recovery System Environment Variable Generator\n\nThis program allows you to specify the many environment variables as command line arguments.",
	epilog="If you need an argument value to contain a dash at the beginning (-), use -arg=\"-phrase1 phrase2\""
)
parser.add_argument('-o','--build-dir',
	default="/tmp/recovery",
	type=str,
	help="Directory in which the environment will be created. This folder will be created for you. (Default = /tmp/recovery)"
)
parser.add_argument('-O','--output-dir',
	default="",
	type=str,
	help="Alternative directory for placing completed images"
)
parser.add_argument('-y','--yay',
	default="",
	type=str,
	help="Install yay. Set to the name of the user that will be compiling yay"
)
parser.add_argument('-u','--user',
	default="",
	type=str,
	help="The username of the login user. When not set, no unprivileged user will be added."
)
parser.add_argument('-P','--no-root-passwd',
	action='store_true',
	help="Do not set a root password and require logging in through unprivileged user (can still use sudo -u)"
)
parser.add_argument('-t','--timezone',
	default="UTC",
	type=str,
	help="Timezone for system. (Default = UTC)"
)
parser.add_argument('-H','--hostname',
	default=None,
	type=str,
	help="Hostname of system (Default = value in your /etc/hostname)"
)
parser.add_argument('-k','--keymap',
	default=None,
	type=str,
	help="Keymap for the tty (Default = KEYMAP option in your vconsole.conf)"
)
parser.add_argument('-s','--shell',
	default="/usr/bin/bash",
	type=str,
	help="Default shell on system (Default = /usr/bin/bash)",
	dest="user_shell"
)
parser.add_argument('--root-shell',
	default=None,
	type=str,
	help="Set a separate shell for the root user."
)
parser.add_argument('-c','--comp','--compression',
	default="-comp zstd",
	type=str,
	help="What compression options to pass to mksquashfs (Default = -comp zstd)",
	dest="compression"
)
parser.add_argument('-e','--systemd-enable',
	nargs="*",
	default=[],
	type=str,
	help="Systemd services to enable",
	metavar="SERVICES"
)
parser.add_argument('-d','--systemd-disable',
	nargs="*",
	default=[],
	type=str,
	help="Systemd services to disable",
	metavar="SERVICES"
)
parser.add_argument('-m','--systemd-mask',
	nargs='*',
	default=["hibernate.target"],
	type=str,
	help="What systemd services to mask (Default = hibernate.target)",
	metavar="SERVICES"
)
parser.add_argument('-x','--extra-packages',
	nargs='*',
	default=[],
	type=str,
	help="Extra packages to include",
	metavar="PACKAGES"
)
parser.add_argument('-f','--flags',
	nargs='*',
	default=[],
	type=str,
	help="A set of flags for things to include in the system. The only flag that is supported by default is 'populate' which fills the home directory with standard folders like Downloads and Documents."
)
parser.add_argument('-S','--scripts',
	nargs='*',
	default=[],
	type=str,
	help="Path of script with functions to be executed at certain times during the build process"
)
parser.add_argument('-F','--firmware',
	nargs='*',
	default=["linux-firmware"],
	type=str,
	help="Which firmware packages to add (Default = linux-firmware)",
	metavar="FIRMWARE"
)
parser.add_argument('-C','--copy-to-root','--copy-to-root',
	nargs="*",
	default=[],
	type=str,
	help="Which directories or tarballs to write into the root of the system in order",
	metavar="SOURCES"
)
parser.add_argument('-M','-I','--mkinitcpio','--initramfs',
	action='store_true',
	help="Whether to build an initramfs"
)
parser.add_argument('--MM','--mkinitcpio-modules',
	nargs="*",
	default=["vfat"],
	type=str,
	help="Which mkinitcpio modules to add (Default = vfat)",
	metavar="MODULES",
	dest="mkinitcpio_modules"
)
parser.add_argument('--MB','--mkinitcpio-binaries',
	nargs="*",
	default=[],
	type=str,
	help="Which mkinitcpio binaries to add",
	metavar="BINARIES",
	dest="mkinitcpio_binaries"
)
parser.add_argument('--MF','--mkinitcpio-files',
	nargs="*",
	default=[],
	type=str,
	help="Which mkinitcpio files to add",
	metavar="FILES",
	dest="mkinitcpio_files"
)
parser.add_argument('--MH','--mkinitcpio-hooks',
	nargs="*",
	default=["base","microcode","keyboard","keymap","autodetect","udev","block","squashfs","patch"],
	type=str,
	help="Which mkinitcpio hooks to use (Defaut = base microcode keyboard keymap autodetect udev block squashfs patch)",
	metavar="HOOKS",
	dest="mkinitcpio_hooks"
),
parser.add_argument('--MP','--mkinitcpio-passwd',
	nargs="?",
	default="",
	type=str,
	help="Add passwd hook to initramfs to require password before booting system. Useful if you are able to edit cmdline parameters in bootloader before booting to prevent setting init=/bin/bash to get past login prompt. You will be prompted to enter a password or you can provide a sha512sum hash. This hook will be placed after keymap if it is present, otherwise it will be placed after keyboard.",
	metavar="HASH",
	dest="mkinitcpio_passwd"
),
parser.add_argument('--ML','--mkinitcpio-cmdline-blacklist',
	nargs="*",
	default=[],
	type=str,
	help="List of kernel cmdline options to not allow for booting. Useful to prevent people setting init=/bin/bash to get past login prompt. As of right now you can only specify whether an option is allowed to be set at all and not which values it may be set to.",
	metavar="CMDLINE_BLACKLIST",
	dest="mkinitcpio_cmdline_blacklist"
)
parser.add_argument('--MD','--mkinitcpio-dir',
	default="./initcpio",
	type=str,
	help="Directory in which the additional initcpio hooks are stored",
	metavar="MKINITCPIO_DIR",
	dest="mkinitcpio_dir"
)
parser.add_argument('--no-patch',
	action='store_true',
	help="Whether to remove the patch system (removes the mkinitcpio hook)"
)
parser.add_argument('--only-mkinitcpio','--only-initramfs',
	action='store_true',
	help="Skip building the system and go straight to initramfs generation"
)
parser.add_argument('-b','--path',
	default="starchy.sh",
	type=str,
	help="Path of the build script (Default = ./starchy.sh)"
)
parser.add_argument('-p','--preset',
	default="",
	type=str,
	help="TOML preset files"
)
parser.add_argument('--export',
	default="",
	type=str,
	help="Export options as a preset file"
)
parser.add_argument('--export-bash',
	default="",
	type=str,
	help="Export options as a bash script"
)

args = parser.parse_args()

# ### PROMPT FUNCTIONS ###

def prompt_continue(q="Continue"):
	try:
		continue_=input("".join((q,' [y/N]> ')))
	except KeyboardInterrupt:
		sys.exit("\r\33[2Kexit")
	except EOFError:
		sys.exit("\r\33[2Kexit")

	if continue_.lower() not in ('y','yes','yae'):
		sys.exit("exit")

def prompt_overwrite(f):
	if f.is_file():
		print("".join(('File "',str(f),'" already exists')))
		prompt_continue("Overwrite?")

# ### WARNING ###
print("WARNING: This is a python wrapper that runs shell scripts on basis of USER INPUT as ROOT.")
print("It is very easy for malicious input to cause harm to your system!")
print("Do not enter any commands or run any scripts from people you do not trust!")
print("Once you press enter, all user input will be displayed for inspection.")
print("It is still a good idea to look through preset and script files.")
print()
print("This program is licenced under GPLv3 (C) LightDig")
print()
prompt_continue()

# ### ARG PROCESSING ###

## Paths
# keep path string in case of --export-bash
path_str=args.path

# expand paths of script, build directory and mkinitcpio directory
for x in 'path','build_dir','mkinitcpio_dir','export','export_bash','preset':
	if args.__getattribute__(x):
		args.__setattr__(x,Path(args.__getattribute__(x)).expanduser().absolute())

# expand path lists
for x in 'scripts','copy_to_root':
	if args.__getattribute__(x):
		args.__setattr__(x,[Path(y).expanduser().absolute() for y in args.__getattribute__(x)])

## Scripts
# check that provided scripts exists
for x in args.scripts:
	if not x.is_file():
		sys.exit("".join(('Script file \33[33m"',str(x),'"\33[0m does not exist!')))

## Copy to root
# check that tarballs/folders exist
for x in args.copy_to_root:
	if not x.exists():
		sys.exit("".join(('File/folder \33[33m"',str(x),'"\33[0m does not exist!')))

# expand output directory
# if none provided, output dir is ${build_dir}/output
if args.output_dir:
	args.output_dir = Path(args.output_dir).expanduser().absolute()
else:
	args.output_dir = Path("".join((str(args.build_dir),"/output")))

## Mkinitcpio
# remove patch if specified
if args.no_patch:
	args.mkinitcpio_hooks.remove("patch")

# add passwd hook if specified
if args.mkinitcpio_passwd != "":
	if "keyboard" not in args.mkinitcpio_hooks:
		sys.exit("The keyboard hook must be in mkinitcpio hooks to use passwd!\nIt is also recommended to put keymap after keyboard if you use a non-US layout.")
	hook_before_passwd = ("keymap" if "keymap" in args.mkinitcpio_hooks else "keyboard")
	args.mkinitcpio_hooks.insert(args.mkinitcpio_hooks.index(hook_before_passwd)+1,"passwd")

## Flags
# list of flags that may not be set using the -f option
illegal_flags = {"wdir","odir","mdir","yay","user","no_root_passwd","timezone","hostname","keymap",
	"user_shell","root_shell","compression","sd_enable_arr","sd_disable_arr","sd_mask_arr","root"
	"extra_packages_arr","scripts_arr","firmware_arr","copy_to_root_arr","sd_enable","linux_firmware",
	"sd_disable","sd_mask","extra_packages","scripts","firmware","copy_to_root","warning","quit",
	"mkinitcpio_conf","p_network","p_media","p_yay"
}

quit=False
for x in args.flags:
	if x in illegal_flags:
		print("".join(('Flag: "',x,'" is not allowed!')))
		quit=True

if quit:
	sys.exit(1)

## General Config

if args.no_root_passwd and not args.user:
	sys.exit("You have no unprivileged user account, yet root password is disabled!")

# if no hostname is set, get from host
if args.hostname is None:
	args.hostname = open('/etc/hostname').read().strip()

# if no keymap is set, get from host
if args.keymap is None:
	args.keymap = subprocess.run("cat /etc/vconsole.conf | grep KEYMAP= | sed 's/KEYMAP=//'",capture_output=True,shell=True).stdout.strip().decode('UTF')

# if root-shell is not set, make the same as shell
if args.root_shell is None:
	args.root_shell = args.user_shell

if args.export:
	args.export = Path(args.export).expanduser().absolute()

opts={}
## Load preset
if args.preset:
	with open(args.preset) as file:
		opts.update(json.load(file))

## Copy opts to dict for display
opts.update(args.__dict__)
for x in 'build_dir','output_dir','export','export_bash','path','preset':
	opts.pop(x)

# print the directory in which all the work will be done
print("".join(("\33[1mBuilding squashfs with directory:\33[0m \33[33m","".join(('"',str(args.build_dir),'"\33[0m')))))

# if a preset is given, show the location of the preset
if args.preset:
	print("".join(('\33[1mFrom preset:\33[0m \33[33m"',str(args.preset),'"\33[0m')))
print()

# function to display each item properly in the confirmation prompt
def display_item(i):
	if i == "":
		return "\33[31mnull\33[0m"
	elif i == []:
		return "\33[31mnone\33[0m"
	elif type(i) is list:
		return "".join(('(\33[34m',", ".join([display_item(x) for x in i]),'\33[0m)'))
	elif type(i) is bool:
		return {True:'\33[32myes\33[0m',False:'\33[31mno\33[0m'}[i]
	elif isinstance(i,Path):
		return "".join(('\33[33m"',str(i),'"\33[0m'))
	else:
		return "".join(('"',str(i),'"'))

# Show all options
for i,x in opts.items():
	print("".join(('\33[1m',i.capitalize().replace('_',' '),':\33[0m ',display_item(x))))
print()

# add export message if export provided
for i in args.export,args.export_bash:
	if i:
		print("".join(('The above options will be exported to: "',str(i),'"')))
prompt_continue()

# replace Paths with strings
opts.update({
	"scripts": [str(x) for x in args.scripts],
	"copy_to_root": [str(x) for x in args.copy_to_root],
	"mkinitcpio_dir": str(args.mkinitcpio_dir)
})

# export options to a json file
if args.export:
	# check if file exists, ask to overwrite if it does
	prompt_overwrite(args.export)
	# write json file
	with open(args.export,'w') as file:
		json.dump(opts,file,indent=2,allow_nan=False)
	# if a bash export also needs to take place, don't stop execution yet
	if not args.export_bash:
		sys.exit()

# remove flags array
opts.pop('flags')

# create function for checking illegal characters
def validate_opt(i,n):
	if not (set(i).isdisjoint('$()[]|;<>') and set((n)).isdisjoint('$()[]|;<>')):
		sys.exit("".join(("Following pair contains illegal characters: ",i,'="',n,'"')))
	return n

# export options as a bash script
if args.export_bash:
	# check if file exists, ask to overwrite if it does
	prompt_overwrite(args.export_bash)
	# simple function for processing arrays and boolean values
	def parse_object(i,x):
		if type(x) is list:
			return "".join(('(',validate_opt(i," ".join(x)),')'))
		elif type(x) is bool:
			return str(x).lower()
		else:
			return validate_opt(i,"".join(('"',str(x),'"')))
	# create main part of script
	exports="\n".join(["".join((i,'=',parse_object(i,x))) for i,x in opts.items() if i != "flags"])
	flags="\n".join(["".join((validate_opt('flag',x),'=true')) for x in args.flags])
	# open file for writing
	with open(args.export_bash,'w') as file:
		# write header
		file.write("""#!/usr/bin/bash
# This is an generated script that establishes a set of options for building an Arch Linux system

# Options
"""
		)
		file.write(exports) # write main options
		file.write("\n\n# Flags\n")
		file.write(flags) # write flags
		# write section to source script
		file.write("".join(('\n\n# Run script\nif [[ -f "',path_str,'" ]]; then\n\tsource "',path_str,'"\nelse\n\techo Script not found!\n\texit 1\nfi')))
	# make file executable
	args.export_bash.chmod(0o755)
	sys.exit()

# Function to turn list into a 0x1b separated array that can later be turned back into a bash array
# null separation throws an Exception in bash :/
def script_array(array):
	return " ".join([x.replace(' ','\33') for x in array])

# create function for turning options into environment variables
def envify(i,x):
	if type(x) is list:
		return script_array(x)
	elif type(x) is bool:
		return str(x).lower()
	else:
		return str(x)

# Set up environment variables
env = {i:validate_opt(i,envify(i,x)) for i,x in opts.items()}

# Disable warning in script
env.update({'warning':'false'})

# Add flags seperately to array
env.update({x:"true" for x in args.flags})

print("\n---\n")
if args.path.is_file():
#	subprocess.run(('sudo','bash',args.path),env=env)
	subprocess.run(('echo','Not ready yet'),env=env)
else:
	print("".join(('Could not find build script at: "',str(args.path),'"')))
	sys.exit(1)
