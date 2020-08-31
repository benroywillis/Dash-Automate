# Dash Automate
Dash Automate is an automation tool for the TraceAtlas toolchain using the SLURM workload manager. It also facilitates pushing data to Dash-Database. Only SLURM is supported. This program has only been tested on Ubuntu Server 18.04.

## Use
To run simply type

        python3 DashAutomate.py

Or you can use the forwarding script

        dashAutomate

+ Add the install path of Dash-Automate to $PATH.
+ Make sure you have python3 in /usr/local/, or change the path of the interpreter in the script to your liking.

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
Dash-Automate requires 2 things from the user: a compile.json file, and a GNU Makefile that uses the Dash-Ontology environment.
#### Vocabulary
First a little vocabulary. We will be using the following terms frequently in this guide.
1. Bitcode: a special kind of output from a clang compiler pass. This file must end with either the `.bc` or `.o` file suffix. The contents of this file is LLVM-IR and can be confirmed by running the following command on the file
```
file output.bc
```
   - If the output of this command starts with `ELF`, this is not a bitcode file.
   - If the output of this command has `LLVM IR bitcode` in it, this is a bitcode file.
2. dynamic links: any flag in a compiler command that starts with `-l`. The use of dynamic links in your compilation flow should only be used when absolutely necessary.
3. bitcode archive: A static library of LLVM IR objects. They have a `.a` suffix. The use of these archives should be used to the fullest extent possible in your compilation flow.
#### Simple Project Criteria
If you satisfy the following criteria then you only need to read the first bullet of the `Build` and `User` keys of the `compile.json` section, then you may move on to the `Makefile` section.
- You are building a single project that has no subdirectories.
- You only require the command `make` to build your project.
- You are not using any dynamic links in your compilation flow.
- Your binary requires no runtime arguments.
#### compile.json
An input json file is required to inform Dash-Automate about compile-time and runtime flags specific to the project. Dash-Automate will, by default, look for a file called compile.json. This name can be changed with the ` -i ` flag.

Your compile.json file can contain up to four fields.
1. Build
   * This key must be defined to instruct Dash-Automate to build the project in this directory. It may be empty if you satisfy the Simple Project Criteria. `Build` can contain up to two keys: `LFLAGS` and `Commands`. 
     - LFLAGS: instructs Dash-Automate about any dynamic links used in the compilation flow of your project. There are two cases to be aware of
       - All bitcodes use the same dynamic links in the Makefile: define a key in the `LFLAGS` field called `default`, and set its value to be a string. If there are multiple ways to build this project with dynamic links, set the value to be a list, where each list entry is a complete string of all dynamic links required.
       - One or more bitcodes have to be compiled with special dynamic links: define a key in the `LFLAGS` field called `default`, set its value as stated above. This key will be used for all bitcode files that are not explicitly enumerated as a key. They will share the dynamic links defined here. Next, for each special case, create a key named after the bitcode file ***without the file suffix, meaning everything before the .o or .bc***. The file that maps to a key will be compiled with the defined dynamic links.
     - Command: instructs Dash-Automate to build the Makefile in your project with special flags. This key does not have to be defined if no special flags are necessary. The value of this key, when defined, may only be a string, and will be used as the command to call your Makefile (Dash-Automate does not support building a Makefile multiple times. To get around this limitation, consider a for loop within the Makefile. Remember that if you do this, ***each bitcode must have a unique name***).
2. Run
   * This key defines the runtime arguments of each binary produced from the build flow. 
3. Subdirectories
   * This key defines the subdirectories to recurse to. 
4. User
   * Defines the user information. There are four fields, all are required:
     - Author: Value must be a string. 
     - Libraries: Value must be a list of strings. Define all APIs used here.
     - Comments: Provide a brief summary of what this project is doing.
     - Date: Any form.
     
#### Makefile
The makefile must respect the TraceAtlas environment variables. This is required for the TraceAtlas toolchain to work correctly. Currently only GNU Makefiles are supported.