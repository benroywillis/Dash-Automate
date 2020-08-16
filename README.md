#### Dash Automate

Dash Automate is an automation tool for the TraceAtlas toolchain. It uses the SLLURM workload manager to generate static and dynamic program data and enter that data into a database. Only SLURM is supported. This program has only been tested on Ubuntu Server 18.04.

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

## Getting Started
#### compile.json
An input json file is required to inform Dash-Automate about compile-time and runtime flags specific to the project.

#### Makefile
The makefile must respect the TraceAtlas environment variables. This is required for the TraceAtlas toolchain to work correctly. Currently only GNU Makefiles are supported.

