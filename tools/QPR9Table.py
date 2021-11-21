import json

RunID = 2255
build0 = "build10-04-20.json"
build1 = "build10-07-20.json"
build2 = "build10-08-20.json"
build3 = "build10-08-20_2.json"
build4 = "build10-08-20_3.json"
build5 = "build10-08-20_4.json"

root = "/mnt/nobackup-09/Dash/Dash-Corpus/FULLREPORT_"+str(RunID)+"_"
paths = [root+build0, root+build1, root+build2, root+build3, root+build4, root+build5]
reports = []
for f in paths:
    reports.append( json.load( open(f,"r") ) )

# conglomerate all reports together by taking the max value for each entry
conDic = dict()
for rep in reports:
    for path in rep:
        if path != "Full Report":
            if conDic.get(path) is None:
                conDic[path] = dict()
            for BC in rep[path]:
                if BC != "Report":
                    if conDic[path].get(BC) is None:
                        conDic[path][BC] = dict()
                        conDic[path][BC]["Total"] = dict()
                        conDic[path][BC]["Total"]["Cartographer Kernels"] = 0
                        conDic[path][BC]["Total"]["Tik Kernels"] = 0
                        conDic[path][BC]["Total"]["Tik Success Kernels"] = 0
                        conDic[path][BC]["Total"]["Traces"] = 0
                        conDic[path][BC]["Total"]["Tik Traces"] = 0
                        conDic[path][BC]["Total"]["Tik Successes"] = 0
                    conDic[path][BC]["Total"]["Cartographer Kernels"] = rep[path][BC]["Total"]["Cartographer Kernels"] if conDic[path][BC]["Total"]["Cartographer Kernels"] < rep[path][BC]["Total"]["Cartographer Kernels"] else conDic[path][BC]["Total"]["Cartographer Kernels"]
                    conDic[path][BC]["Total"]["Tik Kernels"] = rep[path][BC]["Total"]["Tik Kernels"] if conDic[path][BC]["Total"]["Tik Kernels"] < rep[path][BC]["Total"]["Tik Kernels"] else conDic[path][BC]["Total"]["Tik Kernels"]
                    conDic[path][BC]["Total"]["Tik Success Kernels"] = rep[path][BC]["Total"]["Tik Success Kernels"] if conDic[path][BC]["Total"]["Tik Success Kernels"] < rep[path][BC]["Total"]["Tik Success Kernels"] else conDic[path][BC]["Total"]["Tik Success Kernels"]
                    conDic[path][BC]["Total"]["Traces"] = rep[path][BC]["Total"]["Traces"] if conDic[path][BC]["Total"]["Traces"] < rep[path][BC]["Total"]["Traces"] else conDic[path][BC]["Total"]["Traces"]
                    conDic[path][BC]["Total"]["Tik Traces"] = rep[path][BC]["Total"]["Tik Traces"] if conDic[path][BC]["Total"]["Tik Traces"] < rep[path][BC]["Total"]["Tik Traces"] else conDic[path][BC]["Total"]["Tik Traces"]
                    conDic[path][BC]["Total"]["Tik Successes"] = rep[path][BC]["Total"]["Tik Successes"] if conDic[path][BC]["Total"]["Tik Successes"] < rep[path][BC]["Total"]["Tik Successes"] else conDic[path][BC]["Total"]["Tik Successes"]

numbers = dict()
for path in conDic:
    if path != "Full Report":
        refinedPath = path.split("/")[0]
        if numbers.get(refinedPath, None) is None:
            numbers[refinedPath] = dict()
            numbers[refinedPath]["Cartographer Kernels"] = 0
            numbers[refinedPath]["Tik Kernels"] = 0
            numbers[refinedPath]["Tik Success Kernels"] = 0
            numbers[refinedPath]["Kernels Percent - Tik"] = 0
            numbers[refinedPath]["Kernels Percent - Cartographer"] = 0
            numbers[refinedPath]["Traces"] = 0
            numbers[refinedPath]["Tik Traces"] = 0
            numbers[refinedPath]["Tik Successes"] = 0
            numbers[refinedPath]["Traces Percent"] = 0
        for BC in conDic[path]:
            if BC != "Full Report":
                numbers[refinedPath]["Cartographer Kernels"] += conDic[path][BC]["Total"]["Cartographer Kernels"] 
                numbers[refinedPath]["Tik Kernels"] += conDic[path][BC]["Total"]["Tik Kernels"] 
                numbers[refinedPath]["Tik Success Kernels"] += conDic[path][BC]["Total"]["Tik Success Kernels"] 
                numbers[refinedPath]["Kernels Percent - Tik"] = ( numbers[refinedPath]["Tik Success Kernels"] / numbers[refinedPath]["Tik Kernels"] * 100 ) if numbers[refinedPath]["Tik Kernels"] > 0 else 0
                numbers[refinedPath]["Kernels Percent - Cartographer"] = ( numbers[refinedPath]["Tik Success Kernels"] / numbers[refinedPath]["Cartographer Kernels"] * 100 ) if numbers[refinedPath]["Cartographer Kernels"] > 0 else 0
                numbers[refinedPath]["Traces"] += conDic[path][BC]["Total"]["Traces"] 
                numbers[refinedPath]["Tik Traces"] += conDic[path][BC]["Total"]["Tik Traces"] 
                numbers[refinedPath]["Tik Successes"] += conDic[path][BC]["Total"]["Tik Successes"] 
                numbers[refinedPath]["Traces Percent"] = ( numbers[refinedPath]["Tik Successes"] / numbers[refinedPath]["Traces"] * 100 ) if numbers[refinedPath]["Traces"] > 0 else 0

numbers["Total"] = dict()
numbers["Total"]["Cartographer Kernels"] = 0
numbers["Total"]["Tik Kernels"] = 0
numbers["Total"]["Tik Success Kernels"] = 0
numbers["Total"]["Kernels Percent - Tik"] = 0
numbers["Total"]["Kernels Percent - Cartographer"] = 0
numbers["Total"]["Traces"] = 0
numbers["Total"]["Tik Traces"] = 0
numbers["Total"]["Tik Successes"] = 0
numbers["Total"]["Traces Percent"] = 0
for key in numbers:
    if key != "Total":
        numbers["Total"]["Cartographer Kernels"] += numbers[key]["Cartographer Kernels"]
        numbers["Total"]["Tik Kernels"] += numbers[key]["Tik Kernels"]
        numbers["Total"]["Tik Success Kernels"] += numbers[key]["Tik Success Kernels"]
        numbers["Total"]["Traces"] += numbers[key]["Traces"]
        numbers["Total"]["Tik Traces"] += numbers[key]["Tik Traces"]
        numbers["Total"]["Tik Successes"] += numbers[key]["Tik Successes"]
numbers["Total"]["Kernels Percent - Tik"] = ( numbers["Total"]["Tik Success Kernels"] / numbers["Total"]["Tik Kernels"] * 100 ) if numbers["Total"]["Tik Kernels"] > 0 else 0
numbers["Total"]["Kernels Percent - Cartographer"] = ( numbers["Total"]["Tik Success Kernels"] / numbers["Total"]["Cartographer Kernels"] * 100 ) if numbers["Total"]["Cartographer Kernels"] > 0 else 0
numbers["Total"]["Traces Percent"] = ( numbers["Total"]["Tik Successes"] / numbers["Total"]["Traces"] * 100 ) if numbers["Total"]["Traces"] > 0 else 0


with open("TikSwapNumbers_"+str(RunID)+"_QPR9.json","w") as f:
    json.dump(numbers, f, indent=4)

# sort the dictionary keys so we get the same output order each time
sortedDictNames=sorted(numbers.keys(), key=lambda x:x)
csvString = "Directory,Tik Success Kernels,Tik Kernels,Cartographer Kernels,%,%,TikSwap Traces,Traces,%\n"
for path in sortedDictNames:
    csvString += path+","+str(numbers[path]["Tik Success Kernels"])+","+str(numbers[path]["Tik Kernels"])+","+str(numbers[path]["Cartographer Kernels"])+","+str(numbers[path]["Kernels Percent - Tik"])+","+str(numbers[path]["Kernels Percent - Cartographer"])+","+str(numbers[path]["Tik Traces"])+","+str(numbers[path]["Traces"])+","+str(numbers[path]["Traces Percent"])+"\n"
with open("TikSwapNumbers_"+str(RunID)+"_QPR9.csv","w") as f:
    f.write(csvString)
