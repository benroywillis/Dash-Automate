
import subprocess
import os
import re
import json

def compileHeader(f):
    """
    @brief  Compiles a header and returns the result (success or error)
    @param[in]  f   Absolute path to file header
    @retval     True    The header compiled with error
                False   The header did not compile with error
    """
    ## make main.c
    # gen include statement for header
    mainScript = "#include "+'"'+str(f)+'"\n'+"\nint main() {\n\treturn 0;\n}"
    with open("testmain.c","w") as mainfile:
        mainfile.write(mainScript)

    # call subprocess and compile
    proc = subprocess.Popen("clang testmain.c", stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    output = []
    while proc.poll() is None:
        output.append(proc.stdout.readline().decode("utf-8"))
    os.remove("./testmain.c")
    errString = " ".join(x for x in output)
    # parse the output to look for error
    errors = re.findall(".*error.*", errString)

    # return either 1 for error or 0 for success
    if len(errors):
        return True
    else:
        return False

def recurseIntoFolder(path, errors):
    """
    @brief  Recurses into each subdirectory, finds tik headers and compile tests them
    @param[in]  errors  Dictionary mapping file path to compilation success (bool)
    """
    # list all elements in a folder
    files = os.scandir(path)
    # if headers
    directories = []
    for f in files:
        if f.name.endswith(".ll.h"):
            errors[f.path] = compileHeader(f)
        elif f.is_dir():
            directories.append(f)

    for dir in directories:
        recurseIntoFolder(dir, errors)

def main():
    errors = {}
    recurseIntoFolder(os.getcwd(), errors)
    with open("HeaderCompilationResults.json","w") as output:
        json.dump(errors, output, indent=4)

if __name__=="__main__":
    main()

