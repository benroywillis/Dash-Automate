# Dash Automate
Dash Automate is an automation tool for the TraceAtlas toolchain using the SLURM workload manager. It also facilitates pushing data to Dash-Database. Only SLURM is supported. This program has only been tested on Ubuntu Server 18.04.

## Use
To run simply type

        python3 DashAutomate.py

Or you can use the forwarding script

        dashAutomate

+ Add the install path of Dash-Automate to $PATH.
+ Make sure you have python3 in /usr/local/, or change the path of the interpreter in the script to your system.

## Modules and Dependencies
* python3.x
* pyodbc
* os
* shutil
* json
* ctypes
* time
* logging
* threading
* sys
* subprocess
* re
* argparse
* collections
* SLURM

## Quick-Start Guide
Dash-Automate requires 2 things from the user: a compile.json file, and a GNU Makefile that uses the TraceAtlas environment.
### Vocabulary
We will be using the following terms frequently in this guide.
1. Bitcode: a special kind of output file from a clang compiler pass. This file must end with either the `.bc` or `.o` file suffix. The contents of this file is LLVM-IR and can be confirmed by running the following command on the file
```
file output.bc
```
   - If the output of this command starts with `ELF`, this is not a bitcode file.
   - If the output of this command has `LLVM IR bitcode` in it, this is a bitcode file.
2. dynamic links: any flag in a compiler command that starts with `-l`. The use of dynamic links in your compilation flow should only be used when absolutely necessary.
3. bitcode archive: A static library of LLVM IR objects. They have a `.a` suffix. The use of these archives should be done to the fullest extent possible in your compilation flow.
4. TraceAtlas environment: A set of environment variables that must be set and respected by your project build flow in order for Dash-Automate to work correctly.
### Simple Project Criteria
If you satisfy the following criteria then you only need to read the first bullet of the `Build` and `User` keys of the `compile.json` section, then you may move on to the `Makefile` section.
- You are building a single project that has no subdirectories.
- You only require the command `make` to build your project.
- You are not using any dynamic links in your compilation flow.
- Your binary requires no runtime arguments.
### compile.json
An input json file is required to inform Dash-Automate about compile-time and runtime flags specific to the project. Dash-Automate will, by default, look for a file called compile.json. This name can be changed with the ` -i ` flag.

Your compile.json file can contain up to four fields.
1. Build
   * This key must be defined to instruct Dash-Automate to build the project in this directory. It may be empty if you satisfy the Simple Project Criteria. `Build` can contain up to two keys: `LFLAGS` and `Commands`. 
     - LFLAGS: instructs Dash-Automate about any dynamic links used in the compilation flow of your project. There are two cases to be aware of
       - All bitcodes use the same dynamic links in the Makefile: define a key in the `LFLAGS` field called `default`, and set its value to be a string. If there are multiple ways to build this project with dynamic links, set the value to be a list, where each list entry is a complete string of all dynamic links required.
       - One or more bitcodes have to be compiled with special dynamic links: define a key in the `LFLAGS` field called `default`, set its value as stated above. This key will be used for all bitcode files that are not explicitly enumerated as a key. They will share the dynamic links defined here. Next, for each special case, ***create a key named after the bitcode file without the file suffix, meaning everything before the .o or .bc***. The file that maps to a key will be compiled with the defined dynamic links.
     - Command: instructs Dash-Automate to build the Makefile in your project with special flags. This key does not have to be defined if no special flags are necessary. The value of this key, when defined, may only be a string, and will be used as the command to call your Makefile (Dash-Automate does not support building a Makefile multiple times. To get around this limitation, consider a for loop within the Makefile. Remember that if you do this, ***each bitcode must have a unique name***).
2. Run
   * This key defines the runtime arguments of each binary produced from the build flow. If `Run` is defined, it must be a dictionary with the key `Commands`, and `Commands` must be a dictionary with at least one key entry. A key needs to be the name of a bitcode file without the suffix, as described when `Build: LFLAGS: {}` is a dictionary. The value can be a string, list of strings, or dictionary. Each individual string should define exactly the command, or commands, you would use to run your project. The binary name you call in your command must be preceded by `./`.
     - As a string: When defining a lone string, this will be used to run all bitcodes that come out of your Makefile.
     - As a list of strings: Each string will be applied to every bitcode coming out of your Makefile. For example, if 1 bitcode is produced by the Makefile, and a list of three strings is defined here, that bitcode will be run three times, each time with a unique list entry as the arguments. In another example, if 3 bitcodes are produced by your Makefile, and a list of three strings is defined here, then each bitcode will be run 3 times, for a total of 9 traces.
     - As a dictionary of keys: Each key in the dictionary should refer to a bitcode name from the Makefile, just like the dictionary defined for the LFLAGS section. The values of these keys can be either lists of strings or just a string. 
3. Subdirectories
   * This key defines the subdirectories for Dash-Automate to recurse into. It is not required to be defined. If it is defined, it must be a list of strings. Each string should be a relative path to a child directory, treating the current directory as root.
4. User
   * Defines the user information. There are four fields, all are required:
     - Author: Value must be a string. 
     - Libraries: Value must be a list of strings. Define all APIs used here.
     - Comments: Provide a brief summary of what this project is doing.
     - Date: Must be a string.

### Makefile
In this section the rules for project buildflow and file I/O are defined. If these rules are not respected, undefined behavior will occur.

1. Buildflow
   * Currently, only GNU Makefiles are supported. Your Makefile must use the TraceAtlas environment variables. We recommend that you define the variables yourself using the syntax in the following example:
```
CC ?= gcc
```
   * This is doing two things: first it is defining the buildflow to be whatever your development demands that it be. Second, when the TraceAtlas  environment has been set, the `?=` allows the global environment to override your definition with TraceAtlas's definition.
   * There are five variables your buildflow must respect
     - CC: C compiler variable 
     - CXX: C++ compiler variable
     - LFLAGS: linker flags necessary for TraceAtlas
     - DASH_ROOT: path to the TraceAtlas install. This is required when you are including headers for bitcode archives.
     - DASH_DATA: path to the DashData install. This environment variable should be used for file pointers and file paths present in runtime arguments.

   Below is an example of a simple GNU Makefile that respects the TraceAtlas environment for its compiler, include paths, bitcode archives, and file pointers:
```
CC ?= clang
CXX ?= clang++

CFLAGS += -DDASH_DATA=\"$(DASH_DATA)\"

LIBDIR = $(DASH_ROOT)/alib/
LIBS = \
$(LIBDIR)libopencv_imgproc.a\
$(LIBDIR)libgsl.a\
$(LIBDIR)liblibpng.a\

INCLUDE = -I$(DASH_ROOT)include/opencv4

all:
   $(CC) $(LDFLAGS) $(INCLUDE) $(LIBS) $(CFLAGS) main.cpp -o affineTransform.bc

.PHONY: clean
   rm -rf *.bc *.o *.native *.tr*  
```
   * There are a few key takeaways here:
     1. No dynamic link flags. These should be defined in the `LFLAGS` section of your compile.json. If they are used here, they may cause important parts of the program to go untraced.
     2. Annotated bitcodes and the include path are defined using $DASH_ROOT.
     3. Notice the variables that do not have `?=`. These variables are fixed because they do not come from the TraceAtlas environment. Only the TraceAtlas variables need to be overridable.
     4. The bitcode name is representative of the project, not the name of the source code file it came from.

2. File I/O
   * When using file pointers or stdin and stdout to import and export data from your program, DASH_DATA must be used. There are two reasons for this:
     1. Dash-Automate will be running your program in directories far away from the relative one. If you use relative paths in your source code or runtime arguments, they will break.
     2. Keeping large data files out of Dash-Corpus decreases the repository size and increases its organization.
   * Notice the `CFLAGS` variable defined in the above GNU Makefile example. It is used to define the DASH_DATA path as a compiler macro in your program. This is the recommended method to integrate this environment variable into your source code. Below is an example of how to do this:
```

.
.
.

// relative path from the DASH_DATA install folder to the folder targeted at your project
#define PROGPATH DASH_DATA "Dash-RadioCorpus/STAP_GMTI/"
// individual definitions for various input/output file pointers
#define RADARCONF PROGPATH "config.txt"
#define RAWDAT PROGPATH "rxPulses.dat"
#define TRNDAT PROGPATH "trnPulses.dat"
#define ANTPOS PROGPATH "AntPos.txt"
#define TARGET PROGPATH "tgtAng.txt"
#define OUTFILE PROGPATH "ySTAP.txt"

.
.
.

// use the macro strings to facilitate file pointers
FILE* f = fopen(OUTFILE,"w");

.
.
.

fclose(f);

.
.
.

```
   * Here is an example of using $DASH_DATA for runtime args. This string is also an example of how your runtime arguments should be defined in the compile.json.
```
./affineTransform.bc < $DASH_DATA/opencv/input.jpg > $DASH_DATA/opencv/output.jpg
```