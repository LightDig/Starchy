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

class Placeholder:
	pass

class Switch:
	pass

# ### ARGUMENTS ###
## Gather defaults

# get timezone
etc_localtime = Path('/etc/localtime')
if etc_localtime.is_symlink():
	host_timezone = "/".join(etc_localtime.readlink().parts[4:])
else:
	host_timezone = "UTC"

# get hostname
if Path('/etc/hostname').is_file():
	with open('/etc/hostname') as file:
		host_hostname=(file.read().strip())
else:
	host_hostname="recovery"

## We might as well use a shell here since this is a wrapper for a shell script anyways
# get keymap of parent system
host_keymap = subprocess.run("cat /etc/vconsole.conf | grep KEYMAP= | sed 's/KEYMAP=//'",capture_output=True,shell=True).stdout.strip().decode('UTF')

parser = ArgumentParser(
	prog='starchy.py',
	description="Squashed Arch Recovery System Environment Variable Generator\n\nThis program allows you to specify the many environment variables as command line arguments.",
	epilog="If you need an argument value to contain a dash at the beginning (-), use -arg=\"-phrase1 phrase2\"",
	argument_default=Placeholder
)
parser.add_argument('-o','--build-dir',
	type=str,
	help="Directory in which the environment will be created. This folder will be created for you. (Default = /tmp/recovery)"
)
parser.add_argument('-O','--output-dir',
	type=str,
	help="Alternative directory for placing completed images"
)
parser.add_argument('-y','--yay',
	type=str,
	help="Install yay. Set to the name of the user that will be compiling yay"
)
parser.add_argument('-u','--user',
	type=str,
	help="The username of the login user. When not set, no unprivileged user will be added."
)
parser.add_argument('-P','--no-root-passwd',
	action='store_const',
	const=Switch,
	help="Do not set a root password and require logging in through unprivileged user (can still use sudo -u)"
)
parser.add_argument('-t','--timezone',
	type=str,
	help="".join(("Timezone for system. (Default = ",host_timezone,")"))
)
parser.add_argument('-H','--hostname',
	type=str,
	help="".join(("Hostname of system (Default = ",host_hostname,")"))
)
parser.add_argument('-k','--keymap',
	type=str,
	help="".join(("Keymap for the tty (Default = ",host_keymap,")"))
)
parser.add_argument('-s','--shell',
	type=str,
	help="Default shell on system (Default = /usr/bin/bash)",
	dest="user_shell"
)
parser.add_argument('--root-shell',
	type=str,
	help="Set a separate shell for the root user."
)
parser.add_argument('-c','--comp','--compression',
	type=str,
	help="What compression options to pass to mksquashfs (Default = -comp zstd)",
	dest="compression"
)
parser.add_argument('-e','--systemd-enable',
	nargs="*",
	type=str,
	help="Systemd services to enable",
	metavar="SERVICES"
)
parser.add_argument('-d','--systemd-disable',
	nargs="*",
	type=str,
	help="Systemd services to disable",
	metavar="SERVICES"
)
parser.add_argument('-m','--systemd-mask',
	nargs='*',
	type=str,
	help="What systemd services to mask (Default = hibernate.target)",
	metavar="SERVICES"
)
parser.add_argument('-x','--extra-packages',
	nargs='*',
	type=str,
	help="Extra packages to include",
	metavar="PACKAGES"
)
parser.add_argument('-f','--flags',
	nargs='*',
	type=str,
	help="A set of flags for things to include in the system. The only flag that is supported by default is 'populate' which fills the home directory with standard folders like Downloads and Documents."
)
parser.add_argument('-S','--scripts',
	nargs='*',
	type=str,
	help="Path of script with functions to be executed at certain times during the build process"
)
parser.add_argument('-F','--firmware',
	nargs='*',
	type=str,
	help="Which firmware packages to add (Default = linux-firmware)",
	metavar="FIRMWARE"
)
parser.add_argument('-C','--copy-to-root','--copy-to-root',
	nargs="*",
	type=str,
	help="Which directories or tarballs to write into the root of the system in order",
	metavar="SOURCES"
)
parser.add_argument('-M','-I','--mkinitcpio','--initramfs',
	action='store_const',
	const=Switch,
	help="Whether to build an initramfs"
)
parser.add_argument('--MM','--mkinitcpio-modules',
	nargs="*",
	type=str,
	help="Which mkinitcpio modules to add (Default = vfat)",
	metavar="MODULES",
	dest="mkinitcpio_modules"
)
parser.add_argument('--MB','--mkinitcpio-binaries',
	nargs="*",
	type=str,
	help="Which mkinitcpio binaries to add",
	metavar="BINARIES",
	dest="mkinitcpio_binaries"
)
parser.add_argument('--MF','--mkinitcpio-files',
	nargs="*",
	type=str,
	help="Which mkinitcpio files to add",
	metavar="FILES",
	dest="mkinitcpio_files"
)
parser.add_argument('--MH','--mkinitcpio-hooks',
	nargs="*",
	type=str,
	help="Which mkinitcpio hooks to use (Defaut = base microcode keyboard keymap autodetect udev block squashfs patch)",
	metavar="HOOKS",
	dest="mkinitcpio_hooks"
),
parser.add_argument('--MP','--mkinitcpio-passwd',
	nargs="?",
	type=str,
	help="Add passwd hook to initramfs to require password before booting system. Useful if you are able to edit cmdline parameters in bootloader before booting to prevent setting init=/bin/bash to get past login prompt. You will be prompted to enter a password or you can provide a sha512sum hash. This hook will be placed after keymap if it is present, otherwise it will be placed after keyboard.",
	metavar="HASH",
	dest="mkinitcpio_passwd"
),
parser.add_argument('--ML','--mkinitcpio-cmdline-blacklist',
	nargs="+",
	type=str,
	help="List of kernel cmdline options to not allow for booting. Useful to prevent people setting init=/bin/bash to get past login prompt. As of right now you can only specify whether an option is allowed to be set at all and not which values it may be set to.",
	metavar="CMDLINE_BLACKLIST",
	dest="mkinitcpio_cmdline_blacklist"
)
parser.add_argument('--MD','--mkinitcpio-dir',
	type=str,
	help="Directory in which the additional initcpio hooks are stored",
	metavar="MKINITCPIO_DIR",
	dest="mkinitcpio_dir"
)
parser.add_argument('--no-patch',
	action='store_const',
	const=Switch,
	help="Whether to remove the patch system (removes the mkinitcpio hook)"
)
parser.add_argument('--only-mkinitcpio','--only-initramfs',
	action='store_const',
	const=Switch,
	help="Skip building the system and go straight to initramfs generation"
)
parser.add_argument('-b','--path',
	type=str,
	help="Path of the build script (Default = ./starchy.sh)"
)
parser.add_argument('-p','--preset',
	default=None,
	type=str,
	help="TOML preset files"
)
parser.add_argument('--export',
	type=str,
	help="Export options as a preset file"
)
parser.add_argument('--export-bash',
	type=str,
	help="Export options as a bash script"
)
parser.add_argument('--export-settings',
	default=False,
	action='store_true',
	help="Export settings as json file. (--build-dir, --output-dir, --path)"
)

args = parser.parse_args()

# ### MAIN FUNCTIONS ###
# create function for checking illegal characters
def validate_opt(i,n):
	#print(n)
	if type(n) is list:
		for x in n:
			validate_opt(i,x)
	elif type(n) is list:
		sys.exit("".join(('Key "',i,'" contains illegal data type!')))
	elif type(n) is not str:
		pass
	elif not (set(i).isdisjoint('$()[]|;<>') and set((n)).isdisjoint('$()[]|;<>')):
		sys.exit("".join(("Following pair contains illegal characters: ",i,'="',n,'"')))
	return n

# functions for reading json file
def reject_constant(x):
	sys.exit("".join(("JSON decode error: constant ",x," is not allowed!")))

def json_file(f):
	with open(f) as file:
		try:
			return json.load(file,parse_constant=reject_constant)
		except json.decoder.JSONDecodeError as err:
			print("JSON decode error:",err)
			sys.exit(1)

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

# ### Defaults ###
# to be able to properly handle loading presets with argument overrides
# defaults must be kept seperate

default_opts = {
	"yay": "",
	"user": "",
	"no_root_passwd": False,
	"timezone": host_timezone,
	"hostname": host_hostname,
	"keymap": host_keymap,
	"user_shell": "/usr/bin/bash",
	"root_shell": None,
	"compression": "-comp -zstd",
	"systemd_enable": [],
	"systemd_disable": [],
	"systemd_mask": ["hibernate.target"],
	"extra_packages": [],
	"flags": [],
	"scripts": [],
	"firmware": ["linux-firmware"],
	"copy_to_root": [],
	"mkinitcpio": False,
	"mkinitcpio_modules": ["vfat"],
	"mkinitcpio_binaries": [],
	"mkinitcpio_files": [],
	"mkinitcpio_hooks": ["base","microcode","keyboard","keymap","autodetect","udev","block","squashfs","patch"],
	"mkinitcpio_passwd": "",
	"mkinitcpio_cmdline_blacklist": [],
	"mkinitcpio_dir": "./initcpio",
	"no_patch": False,
	"only_mkinitcpio": False
}

default_settings = {
	"build_dir": "/tmp/recovery",
	"output_dir": "",
	"path": "./starchy.sh",
	"preset": "",
	"export": "",
	"export_bash": ""
}

# create list with sources for options and sources for settings respectively
# options are for standard configurations
# and settings are for meta things, such as output_dir
sources=[[], []]

# expand paths
settings_path = Path('./settings').absolute() # establich settings path

## Load preset
if args.preset:
	args.preset = Path(args.preset).expanduser().absolute()
	if not args.preset.is_file():
		sys.exit("".join(('Preset file "',str(args.preset),'" does not exist!')))
	preset=json_file(args.preset) # read preset file
	sources[0].append(preset) # add preset as source
sources[0].append(default_opts) # add default options as source

## Load settings
if settings_path.is_file(): # check that settings file exists
	settings_file=json_file(settings_path) # read settings file
	sources[1].append(settings_file) # add file as source
sources[1].append(default_settings) # add default options as source

# set opts to dictionary of args
opts=args.__dict__.copy()
settings={} # dict for settings such as build and output directories
for x in 'build_dir','output_dir','path','preset','export','export_bash','export_settings':
	settings.update({x:opts[x]})
	opts.pop(x)

# categories are the dictionaries that contain the actual options for later
categories = [opts, settings]

# establish all options in this monstrous construct
for source,category in zip(sources,categories): # loop through sources bundled with categories
	for options in source: # loop through each dictionary in given source
		for index,item in category.items(): # loop through the key/value pairs of each dictionary
			if index in category: # check if option is supported by the category (opts/settings)
				if item is Placeholder: # check if item is placeholder value
					category[index]=options[index] # replace placeholder value with real value
				elif item is Switch: # check if item is a Switch object
					category[index]=bool(item)^bool(options[index]) # toggle boolean option
					# I forgot why this works, but it works; it turns a flag into a toggle
					# so that if it is given in a preset it can be toggled back off

# check for invalid options
for category in categories:
	for i,x in category.items():
		validate_opt(i,x)

# NOTE I have a feeling there is a slightly more efficient way to do all the above
# TODO find it

# ### EXPAND SETTINGS PATHS + EXPORT SETTINGS ###
# keep an unexpanded path string if a bash script export needs to take place
if settings["export_bash"]:
	path_str=settings["path"]

# expand paths in settings
for x in settings:
	if settings[x] and type(settings[x]) is str:
		settings[x] = Path(settings[x]).expanduser().absolute()

# expand output directory
# if none provided, output dir is ${build_dir}/output
if settings["output_dir"]:
	settings["output_dir"] = Path(settings["output_dir"]).expanduser().absolute()
else:
	settings["output_dir"] = Path("".join((str(settings["build_dir"]),"/output")))

if args.export_settings:
	export_path = Path('./settings.json').absolute()
	settings_export = {"build_dir": str(settings["build_dir"]), "output_dir": str(settings["output_dir"]), "path": str(settings["path"])}
	prompt_overwrite(export_path)
	with open(export_path,'w') as file:
		json.dump(settings_export,file,indent=2,allow_nan=False)
	sys.exit()

# ### WARNING ###
print("WARNING: This is a python wrapper that runs shell scripts on basis of USER INPUT as ROOT.")
print("It is very easy for malicious input to cause harm to your system!")
print("Do not enter any commands or run any scripts from people you do not trust!")
print("Once you press enter, all user input will be displayed for inspection.")
print("It is still a good idea to look through preset and script files.")
print()
print("This program is licenced under GPLv3 (C) LightDig")
print("Go to <https://github.com/LightDig/Starchy/wiki/Running-starchy.py>")
print()
prompt_continue()

# ### ARG PROCESSING ###

## Paths
# expand path of mkinitcpio directory stored in opts
if opts['mkinitcpio_dir']:
	opts['mkinitcpio_dir'] = Path(opts['mkinitcpio_dir']).expanduser().absolute()

# expand path lists in opts
for x in 'scripts','copy_to_root':
	if opts[x]:
		opts[x] = [Path(y).expanduser().absolute() for y in opts[x]]

# Scripts
# check that provided scripts exists
for x in opts["scripts"]:
	if not x.is_file():
		sys.exit("".join(('Script file \33[33m"',str(x),'"\33[0m does not exist!')))

# Copy to root
# check that tarballs/folders exist
for x in opts["copy_to_root"]:
	if not x.exists():
		sys.exit("".join(('File/folder \33[33m"',str(x),'"\33[0m does not exist!')))

if settings["export"]:
	settings["export"] = Path(settings["export"]).expanduser().absolute()

## Mkinitcpio
# remove patch if specified
if opts["no_patch"]:
	opts["mkinitcpio_hooks"].remove("patch")

# add passwd hook if specified
if opts["mkinitcpio_passwd"] != "":
	if "keyboard" not in opts["mkinitcpio_hooks"]:
		sys.exit("The keyboard hook must be in mkinitcpio hooks to use passwd!\nIt is also recommended to put keymap after keyboard if you use a non-US layout.")
	hook_before_passwd = ("keymap" if "keymap" in opts["mkinitcpio_hooks"] else "keyboard")
	opts["mkinitcpio_hooks"].insert(args.mkinitcpio_hooks.index(hook_before_passwd)+1,"passwd")

## Flags
# list of flags that may not be set using the -f option
illegal_flags = {"wdir","odir","mdir","yay","user","no_root_passwd","timezone","hostname","keymap",
	"user_shell","root_shell","compression","sd_enable_arr","sd_disable_arr","sd_mask_arr","root"
	"extra_packages_arr","scripts_arr","firmware_arr","copy_to_root_arr","sd_enable","linux_firmware",
	"sd_disable","sd_mask","extra_packages","scripts","firmware","copy_to_root","warning","quit",
	"mkinitcpio_conf","p_network","p_media","p_yay"
}

quit=False
for x in opts["flags"]:
	if x in illegal_flags:
		print("".join(('Flag: "',x,'" is not allowed!')))
		quit=True

if quit:
	sys.exit(1)

## General Config

if opts["no_root_passwd"] and not opts["user"]:
	sys.exit("You have no unprivileged user account, yet root password is disabled!")

# if no hostname is set, get from host
if opts["hostname"] is None:
	opts["hostname"] = open('/etc/hostname').read().strip()

# if root-shell is not set, make the same as shell
if opts["root_shell"] is None:
	opts["root_shell"] = opts["user_shell"]

# print the directory in which all the work will be done
print("".join(("\33[1mBuilding squashfs with directory:\33[0m \33[33m","".join(('"',str(settings["build_dir"]),'"\33[0m')))))

# if a preset is given, show the location of the preset
if settings["preset"]:
	print("".join(('\33[1mFrom preset:\33[0m \33[33m"',str(settings["preset"]),'"\33[0m')))
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
for i in settings["export"],settings["export_bash"]:
	if i:
		print("".join(('The above options will be exported to: "',str(i),'"')))
prompt_continue()

# replace Paths with strings
opts.update({
	"scripts": [str(x) for x in opts["scripts"]],
	"copy_to_root": [str(x) for x in opts["copy_to_root"]],
	"mkinitcpio_dir": str(opts["mkinitcpio_dir"])
})

# export options to a json file
if settings["export"]:
	# check if file exists, ask to overwrite if it does
	prompt_overwrite(settings["export"])
	# write json file
	with open(settings["export"],'w') as file:
		json.dump(opts,file,indent=2,allow_nan=False)
	# if a bash export also needs to take place, don't stop execution yet
	if not settings["export_bash"]:
		sys.exit()

# export options as a bash script
if settings["export_bash"]:
	# check if file exists, ask to overwrite if it does
	prompt_overwrite(settings["export_bash"])
	# simple function for processing arrays and boolean values
	def parse_object(i,x):
		if type(x) is list:
			return "".join(('('," ".join(x),')'))
		elif type(x) is bool:
			return str(x).lower()
		else:
			return "".join(('"',str(x),'"'))
	# create main part of script
	exports="\n".join(["".join((i,'=',parse_object(i,x))) for i,x in opts.items() if i != "flags"])
	flags="\n".join(["".join((x,'=true')) for x in opts["flags"]])
	# open file for writing
	with open(settings["export_bash"],'w') as file:
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
	settings["export_bash"].chmod(0o755)
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

## Set up environment variables
# add relevant directories
opts.update({'wdir': settings["build_dir"], 'odir': settings["output_dir"], 'mdir': opts["mkinitcpio_dir"]})
env = {i:envify(i,x) for i,x in opts.items()}

# Disable warning in script
env.update({'warning':'false'})

# Add flags seperately to array
env.update({x:"true" for x in opts["flags"]})

print("\n---\n")
if settings["path"].is_file():
#	subprocess.run(('sudo','bash',settings["path"]),env=env)
	subprocess.run(('echo','Not ready yet'),env=env)
else:
	print("".join(('Could not find build script at: "',str(settings["path"]),'"')))
	sys.exit(1)
