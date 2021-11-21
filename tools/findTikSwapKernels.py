import json

RunID = 2236
build = "build8-25-20"

n10 = json.load( open("/mnt/nobackup-10/Dash/Dash-Corpus/FULLREPORT_"+str(RunID)+"_"+build+".json","r") )
n11 = json.load( open("/mnt/nobackup-11/Dash/Dash-Corpus/FULLREPORT_"+str(RunID)+"_"+build+".json","r") )

numbers = dict()
for path in n10:
    if path != "FullReport":
        refinedPath = path.split("/")[0]
        if numbers.get(refinedPath, None) is None:
            numbers[refinedPath] = dict()
            numbers[refinedPath]["Kernels"] = 0
            numbers[refinedPath]["Tik Kernels"] = 0
            numbers[refinedPath]["TikSwap Kernels"] = 0
            numbers[refinedPath]["Kernels Percent - Tik"] = 0
            numbers[refinedPath]["Kernels Percent - Cartographer"] = 0
            numbers[refinedPath]["Traces"] = 0
            numbers[refinedPath]["Successful TikSwap Traces"] = 0
            numbers[refinedPath]["Traces Percent"] = 0
        for BC in n10[path]:
            if BC == "Report":
                numbers[refinedPath]["Kernels"] += n10[path][BC]["Kernels"] 
                numbers[refinedPath]["Tik Kernels"] += n10[path][BC]["TikKernels"] 
                numbers[refinedPath]["TikSwap Kernels"] += n10[path][BC]["TikSwapKernels"] 
                numbers[refinedPath]["Kernels Percent - Tik"] = ( numbers[refinedPath]["TikSwap Kernels"] / numbers[refinedPath]["Tik Kernels"] * 100 ) if numbers[refinedPath]["Tik Kernels"] > 0 else 0
                numbers[refinedPath]["Kernels Percent - Cartographer"] = ( numbers[refinedPath]["TikSwap Kernels"] / numbers[refinedPath]["Kernels"] * 100 ) if numbers[refinedPath]["Kernels"] > 0 else 0
                numbers[refinedPath]["Traces"] += n10[path][BC]["Traces"] 
                numbers[refinedPath]["Successful TikSwap Traces"] += n10[path][BC]["TikBinarySuccess"] 
                numbers[refinedPath]["Traces Percent"] = ( numbers[refinedPath]["Successful TikSwap Traces"] / numbers[refinedPath]["Traces"] * 100 ) if numbers[refinedPath]["Traces"] > 0 else 0

for path in n11:
    if path != "FullReport":
        refinedPath = path.split("/")[0]
        if numbers.get(refinedPath, None) is None:
            numbers[refinedPath] = dict()
            numbers[refinedPath]["Kernels"] = 0
            numbers[refinedPath]["Tik Kernels"] = 0
            numbers[refinedPath]["TikSwap Kernels"] = 0
            numbers[refinedPath]["Kernels Percent - Tik"] = 0
            numbers[refinedPath]["Kernels Percent - Cartographer"] = 0
            numbers[refinedPath]["Traces"] = 0
            numbers[refinedPath]["Successful TikSwap Traces"] = 0
            numbers[refinedPath]["Traces Percent"] = 0
        for BC in n11[path]:
            if BC == "Report":
                numbers[refinedPath]["Kernels"] += n11[path][BC]["Kernels"] 
                numbers[refinedPath]["Tik Kernels"] += n11[path][BC]["TikKernels"] 
                numbers[refinedPath]["TikSwap Kernels"] += n11[path][BC]["TikSwapKernels"] 
                numbers[refinedPath]["Kernels Percent - Tik"] = ( numbers[refinedPath]["TikSwap Kernels"] / numbers[refinedPath]["Tik Kernels"] * 100 ) if numbers[refinedPath]["Tik Kernels"] > 0 else 0
                numbers[refinedPath]["Kernels Percent - Cartographer"] = ( numbers[refinedPath]["TikSwap Kernels"] / numbers[refinedPath]["Kernels"] * 100 ) if numbers[refinedPath]["Kernels"] > 0 else 0
                numbers[refinedPath]["Traces"] += n11[path][BC]["Traces"]
                numbers[refinedPath]["Successful TikSwap Traces"] += n11[path][BC]["TikBinarySuccess"] 
                numbers[refinedPath]["Traces Percent"] = ( numbers[refinedPath]["Successful TikSwap Traces"] / numbers[refinedPath]["Traces"] * 100 ) if numbers[refinedPath]["Traces"] > 0 else 0

with open("TikSwapNumbers_"+str(RunID)+"_"+build+".json","w") as f:
    json.dump(numbers, f, indent=4)

# sort the dictionary keys so we get the same output order each time
sortedDictNames=sorted(numbers.keys(), key=lambda x:x)
csvString = "Directory,TikSwap Kernels,Tik Kernels,Cartographer Kernels,%,%,Successful TikSwap Traces,Traces,%\n"
for path in sortedDictNames:
    csvString += path+","+str(numbers[path]["TikSwap Kernels"])+","+str(numbers[path]["Tik Kernels"])+","+str(numbers[path]["Kernels"])+","+str(numbers[path]["Kernels Percent - Tik"])+","+str(numbers[path]["Kernels Percent - Cartographer"])+","+str(numbers[path]["Successful TikSwap Traces"])+","+str(numbers[path]["Traces"])+","+str(numbers[path]["Traces Percent"])+"\n"
with open("TikSwapNumbers_"+str(RunID)+"_"+build+".csv","w") as f:
    f.write(csvString)
