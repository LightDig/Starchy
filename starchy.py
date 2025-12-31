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
from operator import itemgetter
from pathlib import Path
import subprocess
import sys

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
	help="What compression options to pass to mksquashfs (Default = zstd)",
	dest="compression"
)
parser.add_argument('-e','--systemd-enable',
	nargs="*",
	type=str,
	help="Systemd services to enable",
	metavar="SERVICES",
	dest="sd_enable_arr"
)
parser.add_argument('-d','--systemd-disable',
	nargs="*",
	type=str,
	help="Systemd services to disable",
	metavar="SERVICES",
	dest="sd_disable_arr"
)
parser.add_argument('-m','--systemd-mask',
	nargs='*',
	type=str,
	help="What systemd services to mask (Default = hibernate.target)",
	metavar="SERVICES",
	dest="sd_mask_arr"
)
parser.add_argument('-x','--extra-packages',
	nargs='*',
	type=str,
	help="Extra packages to include",
	metavar="PACKAGES",
	dest="extra_packages_arr"
)
parser.add_argument('-f','--flags',
	nargs='*',
	type=str,
	help="A set of flags for things to include in the system. The only flag that is supported by default is 'populate' which fills the home directory with standard folders like Downloads and Documents."
)
parser.add_argument('-i','--install','--package-groups',
	nargs='*',
	type=str,
	help="Set of package groups to install. By default these options are available: base, texteditors, recovery, netowrk, media, yay. By default base and texteditors are enabled."
)
parser.add_argument('-S','--scripts',
	nargs='*',
	type=str,
	help="Path of script with functions to be executed at certain times during the build process",
	dest="scripts_arr"
)
parser.add_argument('-F','--firmware',
	nargs='*',
	type=str,
	help="Which firmware packages to add (Default = linux-firmware)",
	metavar="FIRMWARE",
	dest="firmware_arr"
)
parser.add_argument('-C','--copy-to-root','--copy-to-root',
	nargs="*",
	type=str,
	help="Which directories or tarballs to write into the root of the system in order",
	metavar="SOURCES",
	dest="copy_to_root_arr"
)
parser.add_argument('-M','-I','--mkinitcpio','--initramfs',
	action='store_const',
	const=Switch,
	help="Whether to build an initramfs"
)
parser.add_argument('--MM','--mkinitcpio-modules',
	nargs="*",
	type=str,
	help="Which mkinitcpio modules to add",
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
	type=str,
	help="Which mkinitcpio files to add. Specify a string with format FILE1;FILE2 or FILE1:LOCATION1;FILE2 and so on.",
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
parser.add_argument('--MC','--mkinitcpio_compression',
	type=str,
	help="Compression to use for initramfs generation. (Default = zstd)",
	metavar="COMPRESSION",
	dest="mkinitcpio_compression",
	choices=("zstd","gzip","bzip2","lzma","xz","lzop","lz4")
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
parser.add_argument('-X','--skip-system','--only-initramfs',
	action='store_const',
	const=Switch,
	help="Skip building the system and go straight to initramfs generation"
)
#parser.add_argument('-b','--path',
#	type=str,
#	help="Path of the build script (Default = ./starchy.sh)"
#)
parser.add_argument('-p','--preset',
	default=None,
	type=str,
	help="TOML preset files"
)
parser.add_argument('--export',
	type=str,
	help="Export options as a preset file"
)
parser.add_argument('--export-bash','--bash-export',
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
# function for checking illegal characters
def validate_opt(i,n):
	if type(n) is list: # parse all options in list
		for x in n:
			validate_opt(i,x)
	elif type(n) is not str:
		sys.exit("".join(('Key "',i,'" contains illegal data type!')))
	elif not (set(i).isdisjoint('$()[]|;<>') and set((n)).isdisjoint('$()[]|;<>')):
		sys.exit("".join(("Following pair contains illegal characters: ",i,'="',n,'"')))
	return n

# functions for reading json file
def reject_constant(x):
	sys.exit("".join(("JSON decode error: constant ",x," is not allowed!")))

# function to read json file
def json_file(f):
	with open(f) as file:
		try:
			return json.load(file,parse_constant=reject_constant)
		except json.decoder.JSONDecodeError as err:
			print("JSON decode error:",err)
			sys.exit(1)

# continue prompt
def prompt_continue(q="Continue"):
	try:
		continue_=input("".join((q,' [y/N]> ')))
	except KeyboardInterrupt:
		sys.exit("\r\33[2Kexit")
	except EOFError:
		sys.exit("\r\33[2Kexit")

	if continue_.lower() not in ('y','yes','yae'):
		sys.exit("exit")

# function to ask before overwriting file
def prompt_overwrite(f):
	if f.is_file():
		print("".join(('File "',str(f),'" already exists')))
		prompt_continue("Overwrite?")

# function to return a subset of a dictionary
def getitems(dictionary,*keys):
	return dict(zip(keys,itemgetter(*keys)(dictionary)))

# function to delete a list of keys from a dictionary
def delkeys(dictionary,*keys):
	for x in keys:
		dictionary.pop(x)

# function for reassigning a dictionary key to a new name
def reassignkey(dictionary,key,target):
	dictionary.update({target: dictionary[key]})
	dictionary.pop(key)

# looped version for multiple keys
def reassignkeys(dictionary,key,target):
	for i,x in zip(key,target):
		reassignkey(dictionary,i,x)

def cpvalues(dict1,dict2,*keys):
	for x in keys:
		dict2.update({x: dict1[x]})

# function to expand paths in a string or list
def expandpaths(p):
	if p == "":
		return None
	if type(p) is str:
		return Path(p).expanduser().absolute()
	elif type(p) is list:
		return [Path(x).expanduser().absolute() for x in p]
	else:
		raise TypeError("Can only expand string or list")

default_opts = {
	"yay": "",
	"user": "",
	"no_root_passwd": False,
	"timezone": host_timezone,
	"hostname": host_hostname,
	"keymap": host_keymap,
	"user_shell": "/usr/bin/bash",
	"root_shell": None,
	"compression": "zstd",
	"sd_enable_arr": [],
	"sd_disable_arr": [],
	"sd_mask_arr": ["hibernate.target"],
	"extra_packages_arr": [],
	"flags": [],
	"install": ["base", "texteditors"],
	"scripts_arr": [],
	"firmware": ["linux-firmware"],
	"copy_to_root_arr": [],
	"mkinitcpio": False,
	"mkinitcpio_modules": [],
	"mkinitcpio_binaries": [],
	"mkinitcpio_files": "",
	"mkinitcpio_hooks": ["base","microcode","keyboard","keymap","autodetect","udev","block","squashfs","patch"],
	"mkinitcpio_passwd": "",
	"mkinitcpio_cmdline_blacklist": [],
	"mkinitcpio_compression": "zstd",
	"skip_system": False,
	"mkinitcpio_dir": "./initcpio",
	"no_patch": False,

	"build_dir": "/tmp/recovery",
	"output_dir": "",
#	"path": "./starchy.sh",
	"preset": "",
	"export": "",
	"export_bash": ""
}

opts=args.__dict__ # make args accessible as dict

sources=[] # list for storing options sources

## preset
if args.preset:
	# check that preset exists
	preset_file=Path(args.preset).expanduser().absolute()
	if not preset_file.is_file():
		sys.exit("".join(("Preset file '",str(preset_file),"' not found")))

	# load preset
	args.preset = Path(args.preset).expanduser().absolute()
	if not args.preset.is_file():
		sys.exit("".join(('Preset file "',str(args.preset),'" does not exist')))
	preset=json_file(args.preset) # read preset file
	sources.append(preset) # add preset as source
sources.append(default_opts) # add default options as source

# process options
for source in sources:
	for key,item in source.items():
		if key in opts:
			if opts[key] is Placeholder:
				opts[key]=item
			elif opts[key] is Switch:
				opts[key]=bool(item)^bool(opts[key])

# create dictionary with unexpanded paths for export-bash feature
paths = ["build_dir","output_dir","export","export_bash","copy_to_root_arr","scripts_arr","mkinitcpio_dir"]
unexpanded=getitems(opts,*paths)

# expand paths
for x in paths:
	opts.update({x: expandpaths(opts[x])})

# create settings dictionary and remove those values from opts
settings_keys = ("build_dir","output_dir","preset","export","export_bash","export_settings","mkinitcpio_dir")
settings = getitems(opts,*settings_keys)
delkeys(opts,*settings_keys)

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

path_checker = {1: "is_file", 2: "is_dir", 3: "exists"}

# check that paths exist
for path_list,mode in zip(getitems(opts,"scripts_arr","copy_to_root_arr").values(),(1,2)):
	for x in path_list:
		if not x.__getattribute__(path_checker[mode])():
			sys.exit("".join(("Path '",str(x),"' does not exist")))

# replace dashes with underscores in flags and install
for x in "flags","install":
	opts[x] = [x.replace('-','_') for x in opts[x]]

# list of flags that may not be set using the -f or -i options
illegal_flags = {"wdir","odir","mdir","yay","user","no_root_passwd","timezone","hostname","keymap",
	"user_shell","root_shell","compression","sd_enable_arr","sd_disable_arr","sd_mask_arr","root"
	"extra_packages_arr","scripts_arr","firmware_arr","copy_to_root_arr","sd_enable",
	"sd_disable","sd_mask","extra_packages","scripts","firmware","copy_to_root","warning","quit",
	"mkinitcpio_conf"
}

# ensure no illegal flags or package groups are present
# ensure no illegal flags are present
quit=False
for i,n in zip(("flags","install"),("Flag","Package group name")):
	for x in opts[i]:
		if x in illegal_flags or x.count(" "):
			print("".join((n,': "',x,'" is not allowed!')))
			quit=True
		elif x[:8] in ("install_","pkgroup_"):
			if i == "flags":
				print("".join(('Flag: "',x,'" is not allowed!')))
				quit=True

if quit:
	sys.exit(1)

# ### SYSTEM CONFIG PROCESSING ###
# add prefix to all install flags
opts.update({"install": ["".join(("install_",x)) for x in args.install]})

# make sure at least one user will have a password
if args.no_root_passwd and not args.user:
	sys.exit("You have no unprivileged user account, yet root password is disabled!")

# if root-shell is not set, make the same as shell
if opts["root_shell"] is None:
	opts["root_shell"] = opts["user_shell"]

# if skip-system is enabled, force mkinitcpio
if args.skip_system:
	args.mkinitcpio = True

# ### SHOW OPTIONS ###
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
	print("".join(('\33[1m',i.capitalize().replace('_',' ').replace(' arr',''),':\33[0m ',display_item(x))))
print()

# add export message if export provided
for i in settings["export"],settings["export_bash"]:
	if i:
		print("".join(('The above options will be exported to: "',str(i),'"')))

if settings["export_settings"]:
	print("Build directory and export path will be exported to settings.json")

if any((settings["export"],settings["export_bash"],settings["export_settings"])):
	print("Execution will stop after the exports complete")
prompt_continue()

# ### EXPORT OPTIONS ###
## export functions
# bash export
def parse_bash_object(i,x):
	if type(x) is list:
		return "".join(('('," ".join(["".join(('"',y,'"')) for y in x]),')'))
	elif type(x) is bool:
		return str(x).lower()
	else:
		return "".join(('"',str(x),'"'))

if settings["export_settings"]:
	settings_path=Path("settings.json").absolute()
	prompt_overwrite(settings_path)
	with open(settings_path,'w') as file:
		json.dump(getitems(unexpanded,"build_dir","output_dir"),file,indent=2,allow_nan=False)

if settings["export_bash"]:
	prompt_overwrite(settings["export_bash"])
	bash_export = opts.copy() # make a copy of the options
	bash_export.update(unexpanded) # replace full paths with unexpanded paths
	reassignkeys(bash_export,("build_dir","output_dir","mkinitcpio_dir"),("wdir","odir","mdir"))
	delkeys(bash_export,"flags","install") # remove flags and pkgroups so they can be added seperately
	with open(settings["export_bash"],'w') as file: # start writing file
		file.write("#!/usr/bin/env bash\n") # write shebang
		file.write("# this is a generated wrapper script for starchy.sh\n") # header comment
		for i,x in bash_export.items(): # write all options as variable declarations
			file.write("".join((i,'=',parse_bash_object(i,x),'\n')))
		for category in "flags","install": # add flags and package groups seperately
			if opts[category]: # if flags or install is provided at all
				file.write("".join(('\n# ',category,'\n'))) # write comment
				for x in opts[category]: # write all flags as <value>=true
					file.write("".join((x,"=true\n")))
		file.write("""
# Run script
if [[ ! $skip_system = true ]]; then
	if [[ -f starchy.sh ]]; then
		source starchy.sh
	else
		echo starchy.sh not found!
	fi
fi

if [[ $mkinitcpio = true ]]; then
	if [[ -f mkinitcpio.sh ]]; then
		source mkinitcpio.sh
	else
		echo starchy.sh not found!
	fi
fi
""")
		settings["export_bash"].chmod(0o755)

if settings["export"]:
	prompt_overwrite(settings["export"])
	json_export = opts.copy()
	cpvalues(unexpanded,json_export,"scripts_arr","copy_to_root_arr")
	json_export.update({"install": [x[8:] for x in opts["install"]]}) # strip install_ prefixes from pkgroups
	with open(settings["export"],'w') as file: # write json file
		json.dump(json_export,file,indent=2,allow_nan=False)

if any((settings["export"],settings["export_bash"],settings["export_settings"])):
	sys.exit()

# ### RUN PROGRAM ###
# function that turns an array into a string seperated by 0x1b.
def script_array(array):
	return "\33".join(array)

# create function for turning options into environment variables
def envify(x):
	if type(x) is list:
		return script_array(x)
	elif type(x) is bool:
		return str(x).lower()
	else:
		return str(x)

# create dictionary for environment variables
env = {}

# add flags and pkgroups
for category in "flags","install":
	for x in opts[category]:
		env.update({x: "true"})

# delete original lists
delkeys(opts,"flags","install")

# add unexpanded paths to environment variables
env.update(unexpanded)

# reassign keys to their script names
reassignkeys(env,("build_dir","output_dir","mkinitcpio_dir"),("wdir","odir","mdir"))

# turn values into environment variable strings
for i,x in opts.items():
	if i not in env:
		env.update({i:envify(x)})
	elif type(x) is list:
		env[i] = envify(env[i])

# run script
subprocess.run(("bash",Path("starchy.sh").absolute()),env=env)
