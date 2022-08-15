import json

runDict = json.load( open("FULLREPORT_2303_build6-20-2021.json","r") )

dirDict = {}
dirs = set()
for path in runDict:
    if path != "Full Report":
        dirName = path.split("/")[0]
        dirs.add(dirName)
for dir in dirs:
    dirDict[dir] = { "Profiles": 0, "Kernels": 0 }
    
for path in runDict:
    if path != "Full Report":
        dirName = path.split("/")[0]
        for BC in runDict[path]:
            if BC == "Report":
                dirDict[dirName]["Profiles"] += runDict[path][BC]["Profiles"]
                dirDict[dirName]["Kernels"] += runDict[path][BC]["Cartographer Kernels"]

# sum totals
dirDict["Total"] = { "Profiles": 0, "Kernels": 0 }
for dir in dirDict:
    if dir == "Total": 
        continue
    dirDict["Total"]["Profiles"] += dirDict[dir]["Profiles"]
    dirDict["Total"]["Kernels"]  += dirDict[dir]["Kernels"]

with open("ProfileKernelCounts.json","w") as f:
    json.dump(dirDict, f, indent=4)

with open("ProfileKernelCounts.csv","w") as f:
    f.write("Directory,Profiles,Kernels\n")
    f.write( "\n".join( [dir+","+str(dirDict[dir]["Profiles"])+","+str(dirDict[dir]["Kernels"]) for dir in dirDict] ) )
