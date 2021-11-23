import json
import pyodbc
import PickFileTree as pft
import statistics as st

def reportCompliant(project, keyName, dir, dic):
	ty = ""
	if "HC" in dir:
		ty = "HC"
	elif "2DMarkov" in dir:
		ty = "2DMarkov"
	else:
		ty = "Scops"

	if dic[ty].get(project) is None:
		dic[ty][project] = { "Compliant": set(), "Noncompliant": set() }
	dic[ty][project]["Compliant"].add(keyName+dir)

def reportNonCompliant(project, keyName, dir, dic, log=None):
	ty = ""
	if "HC" in dir:
		ty = "HC"
	elif "2DMarkov" in dir:
		ty = "2DMarkov"
	else:
		ty = "Scops"

	if dic[ty].get(project) is None:
		dic[ty][project] = { "Compliant": set(), "Noncompliant": set() }
	dic[ty][project]["Noncompliant"].add(keyName+dir)

buildFolders = { "buildHC11-21-21", "build2DMarkov11-21-21", "buildPollyScops11-20-21" }
dataMap = {}
pft.recurseIntoFolder("/mnt/heorot-10/Dash/Dash-Corpus", buildFolders, ["makeNative","Cartographer_"], dataMap)
#pft.recurseIntoFolder("/mnt/heorot-10/Dash/Dash-Corpus/Unittests", buildFolders, ["makeNative","Cartographer_"], dataMap)
# pairs all three types together
matchedData = {}
# tracks "compliance"
# compliance is defined as producing a result (any result) for a project
compliance = { "HC": {}, "2DMarkov": {}, "Scops": {} }
HCfound = 0
M2Dfound = 0
Scopsfound = 0
for project in dataMap:
	for keyName in dataMap[project]:
		# keys: directory information comes from, value: tuple( kernels, blockCoverage )
		d = dataMap[project][keyName]
		allFound = (set(d.keys()) == buildFolders) 
		for dir in d:
			if d[dir][0] == -1:
				allFound = False
				reportNonCompliant(project, keyName, dir, compliance)
			elif "HC" in dir:
				HCfound += 1
				reportCompliant(project, keyName, dir, compliance)
			elif "2DMarkov" in dir:
				M2Dfound += 1
				reportCompliant(project, keyName, dir, compliance)
			else:
				Scopsfound += 1
				reportCompliant(project, keyName, dir, compliance)
		if allFound:
			if matchedData.get(project) is None:
				matchedData[project] = dict()
			if matchedData[project].get(keyName) is None:
				# first index kernels, second index static block coverage
				matchedData[project][keyName] = { "HotCode": [0,0], "2DMarkov": [0,0] , "Scops": [0,0]} 
			for dir in d:
				if "HC" in dir:
					matchedData[project][keyName]["HotCode"] = list(d[dir])
				elif "2DMarkov" in dir:
					matchedData[project][keyName]["2DMarkov"] = list(d[dir])
				else:
					matchedData[project][keyName]["Scops"] = list(d[dir])

print("HC: "+str(HCfound)+" , 2DMarkov: "+str(M2Dfound)+" , Scops: "+str(Scopsfound))

with open("MatchedData.json","w") as f:
	json.dump(matchedData, f, indent=4)

directoryData = {"HC": {}, "2DMarkov": {}, "Scops": {}}
totalHCKs = 0
total2DMarkovKs = 0
totalScops = 0
for project in matchedData:
	if directoryData["HC"].get(project) is None:
		directoryData["HC"][project] = 0
	if directoryData["2DMarkov"].get(project) is None:
		directoryData["2DMarkov"][project] = 0
	if directoryData["Scops"].get(project) is None:
		directoryData["Scops"][project] = 0
	for key in matchedData[project]:
		newHC = matchedData[project][key]["HotCode"][0] if matchedData[project][key]["HotCode"][0] > 0 else 0
		directoryData["HC"][project] += newHC
		totalHCKs += newHC
		new2DMarkov = matchedData[project][key]["2DMarkov"][0] if matchedData[project][key]["2DMarkov"][0] > 0 else 0
		directoryData["2DMarkov"][project] += new2DMarkov
		total2DMarkovKs += new2DMarkov
		newScops = matchedData[project][key]["Scops"][0] if matchedData[project][key]["Scops"][0] > 0 else 0
		directoryData["Scops"][project] += newScops
		totalScops += newScops
directoryData["HC"]["Total"] = totalHCKs
directoryData["2DMarkov"]["Total"] = total2DMarkovKs
directoryData["Scops"]["Total"] = totalScops

latexString = "Directory & HotCode & 2DMarkov & Scop \\\\\n\hline\n"
for project in directoryData["HC"]:
	latexString += project+" & {} & {} & {} \\\\\n".format(directoryData["HC"][project],directoryData["2DMarkov"][project], directoryData["Scops"][project] )
with open("Dash-CorpusKernels.tex","w") as f:
	f.write(latexString)

for ty in compliance:
	for project in compliance[ty]:
		compliance[ty][project]["Compliance"] = float( float(len(compliance[ty][project]["Compliant"]))\
												/(float(len(compliance[ty][project]["Compliant"]))+float(len(compliance[ty][project]["Noncompliant"]))) )
	complianceMedian = st.mean( [compliance[ty][x]["Compliance"] for x in compliance[ty]] )
	compliance[ty]["Total"] = dict()
	compliance[ty]["Total"]["Compliance"] = complianceMedian

csvString = "Directory & HotCode & 2DMarkov & Scop \\\\\n"
for project in compliance["HC"]:
	csvString += project+" & {:.2%} & {:.2%} & {:.2%} \\\\\n".format(compliance["HC"][project]["Compliance"],compliance["2DMarkov"][project]["Compliance"],compliance["Scops"][project]["Compliance"])
with open("Compliance.tex","w") as f:
	f.write(csvString)

"""
RunID  = 0
drive  = "heorot-10"
build  = "buildHC"
date   = "11-19-21"
RunID2 = 0
drive2 = "heorot-10"
build2 = "build2DMarkov"
date2  = "11-19-21"
# list entries are (path, BC, TRC, density)
def parseReport(dic):
    timeDict = {}
    densityList = []
    for path in dic:
        if path != "Full Report":
            for BC in dic[path]:
                if BC != "Report":
                    for BC_name in dic[path][BC]:
                        if (BC_name != "Errors") and (BC_name != "Total"):
                            for NTV in dic[path][BC][BC_name]:
                                for TRC in dic[path][BC][BC_name][NTV]:
                                    if TRC.startswith("TRC"):
                                        # times information
                                        if timeDict.get(path, None) is None:
                                            timeDict[path] = dict()
                                        if timeDict[path].get(BC, None) is None:
                                            timeDict[path][BC] = dict()
                                        if timeDict[path][BC].get(NTV, None) is None:
                                            timeDict[path][BC][NTV] = dict()
                                        timeDict[path][BC][NTV][TRC] = dict()
                                        trcTime = dic[path][BC][BC_name][NTV][TRC]["TRCtime"]
                                        carTime = dic[path][BC][BC_name][NTV][TRC].get("CARtime", -1)
                                        kernels = dic[path][BC][BC_name][NTV][TRC].get("Cartographer Kernels", -1)
                                        timeDict[path][BC][NTV][TRC]["Kernels"] = kernels
                                        timeDict[path][BC][NTV][TRC]["trcTime"] = trcTime
                                        timeDict[path][BC][NTV][TRC]["carTime"] = carTime
                                        # kernel/time density of each trace
                                        densityList.append( (path, BC_name, NTV, TRC, kernels/(trcTime+carTime) if trcTime+carTime > 0 else 0) )
    return timeDict, densityList
			
dirData = {"HotCode": {}, "2DMarkov": {}, "Matched": {}}
## first the hot code data 
timeDict = {"HotCode": {}, "2DMarkov": {}, "Matched": {}}
densityList = {"HotCode": [], "2DMarkov": [], "Matched": []}
timeDict["HotCode"], densityList["HotCode"] = parseReport(json.load( open("/mnt/"+drive+"/Dash/Dash-Corpus/FULLREPORT_"+str(RunID)+"_"+build+date+".json","r") ))

for path in sorted(timeDict["HotCode"].keys(), key = lambda kv:kv[0]):
    mappedPath = path.split("/")[0]
    if dirData["HotCode"].get(mappedPath) is None:
        dirData["HotCode"][mappedPath] = { "Kernels": 0 }
    for BC in timeDict["HotCode"][path]:
        for NTV in timeDict["HotCode"][path][BC]:
            for TRC in timeDict["HotCode"][path][BC][NTV]:
                dirData["HotCode"][mappedPath]["Kernels"] += timeDict["HotCode"][path][BC][NTV][TRC]["Kernels"]

## second, 2nd order markov data
timeDict["2DMarkov"], densityList["2DMarkov"] = parseReport(json.load( open("/mnt/"+drive2+"/Dash/Dash-Corpus/FULLREPORT_"+str(RunID2)+"_"+build2+date2+".json","r") ))
# directory data
for path in sorted(timeDict["2DMarkov"].keys(), key = lambda kv:kv[0]):
    mappedPath = path.split("/")[0]
    if dirData["2DMarkov"].get(mappedPath) is None:
        dirData["2DMarkov"][mappedPath] = { "Kernels": 0 }
    for BC in timeDict["2DMarkov"][path]:
        for NTV in timeDict["2DMarkov"][path][BC]:
            for TRC in timeDict["2DMarkov"][path][BC][NTV]:
                dirData["2DMarkov"][mappedPath]["Kernels"] += timeDict["2DMarkov"][path][BC][NTV][TRC]["Kernels"]

# procedurally match cases, these are the usable results
for path in timeDict["2DMarkov"]:
    mappedPath = path.split("/")[0]
    if timeDict["Matched"].get(path) is None:
        # Hotcode also needs to have this entry for us to continue
        if timeDict["HotCode"].get(path) is not None:
             timeDict["Matched"][path] = dict()
        else:
             continue
    if dirData["Matched"].get(mappedPath) is None:
         dirData["Matched"][mappedPath] = dict()
         dirData["Matched"][mappedPath]["Kernels"] = {"HotCode": 0, "2DMarkov": 0}
    for BC in timeDict["2DMarkov"][path]:
        if timeDict["Matched"][path].get(BC) is None:
            if timeDict["HotCode"][path].get(BC) is not None:
                timeDict["Matched"][path][BC] = dict()
            else:
                 continue
        for NTV in timeDict["2DMarkov"][path][BC]:
            if timeDict["Matched"][path][BC].get(NTV) is None:
                if timeDict["HotCode"][path][BC].get(NTV) is not None:
                     timeDict["Matched"][path][BC][NTV] = dict()
                else:
                     continue
            for TRC in timeDict["2DMarkov"][path][BC][NTV]:
                if timeDict["Matched"][path][BC][NTV].get(TRC) is None:
                    if timeDict["HotCode"][path][BC][NTV].get(TRC) is not None:
                         timeDict["Matched"][path][BC][NTV][TRC] = dict()
                         timeDict["Matched"][path][BC][NTV][TRC]["Kernels"] = {"HotCode": 0, "2DMarkov": 0}
                    else:
                        continue
                timeDict["Matched"][path][BC][NTV][TRC]["Kernels"]["HotCode"]  += timeDict["HotCode"][path][BC][NTV][TRC]["Kernels"]
                timeDict["Matched"][path][BC][NTV][TRC]["Kernels"]["2DMarkov"] += timeDict["2DMarkov"][path][BC][NTV][TRC]["Kernels"]
                dirData["Matched"][mappedPath]["Kernels"]["HotCode"]  += timeDict["HotCode"][path][BC][NTV][TRC]["Kernels"]
                dirData["Matched"][mappedPath]["Kernels"]["2DMarkov"] += timeDict["2DMarkov"][path][BC][NTV][TRC]["Kernels"]
with open("Times.json","w") as f:
    json.dump(timeDict, f, indent=4)
with open("DirData.json","w") as f:
	json.dump(dirData, f, indent=4)
csvString = "Directory,HotCodeKernels,2DMarkovKernels\n"
for path in dirData["Matched"]:
    csvString += path+","+str(dirData["Matched"][path]["Kernels"]["HotCode"])+","+str(dirData["Matched"][path]["Kernels"]["2DMarkov"])+"\n"
with open("DirectoryKernels.csv","w") as f:
    f.write(csvString)
"""
"""
densityList.sort(key = lambda x: x[4])
# find most dense entry from every project
incProj = dict()
for entry in densityList:
    if incProj.get(entry[0], None) is not None:
        # resolve clash
        existing = incProj[entry[0]]
        if existing[4] < entry[4]:
            incProj[entry[0]] = entry
    else:
        incProj[entry[0]] = entry
csvString = "path\n"
for entry in incProj:
    csvString+=incProj[entry][0]+"/"+incProj[entry][1]+"/"+incProj[entry][2]+"/"+incProj[entry][3]+"\n"
with open("NightlyBuildProjectList_"+str(RunID)+"_"+drive+".csv","w") as f:
    f.write(csvString)

# scatter of each dir's avg trc&car time
avgTimeDict = dict()
for path in timeDict:
    timeList = []
    for BC in timeDict[path]:
        for NTV in timeDict[path][BC]:
            for TRC in timeDict[path][BC][NTV]:
                timeList.append(timeDict[path][BC][NTV][TRC]["trcTime"]+timeDict[path][BC][NTV][TRC]["carTime"])
    avgTimeDict[path] = sum(timeList)/len(timeList)
with open("AvgDirTime.csv","w") as f:
    csvString = ""
    for path in avgTimeDict:
        csvString += path+","+str(avgTimeDict[path])+"\n"
    f.write(csvString)

# histogram data
with open("TraceTimeHistogram.csv","w") as f:
    timeList = []
    for path in timeDict:
        for BC in timeDict[path]:
            for NTV in timeDict[path][BC]:
                for TRC in timeDict[path][BC][NTV]:
                    timeList.append(timeDict[path][BC][NTV][TRC]["trcTime"])
    f.write(",".join(str(x) for x in timeList) + "\n")

    timeList = []
    for path in timeDict:
        for BC in timeDict[path]:
            for NTV in timeDict[path][BC]:
                for TRC in timeDict[path][BC][NTV]:
                    timeList.append(timeDict[path][BC][NTV][TRC]["carTime"])
    f.write(",".join(str(x) for x in timeList)+"\n")

    timeList = []
    for path in timeDict:
        for BC in timeDict[path]:
            for NTV in timeDict[path][BC]:
                for TRC in timeDict[path][BC][NTV]:
                    timeList.append(timeDict[path][BC][NTV][TRC]["trcTime"]+timeDict[path][BC][NTV][TRC]["carTime"])
 
    f.write(",".join(str(x) for x in timeList))
"""
