import json
import os
import re
import statistics as st
import matplotlib.pyplot as plt

def readKernelFile(kf, log):
	returnDict = {}
	# first open the log to verify that the step ran 
	try:
		log = open(log,"r")
	except Exception as e:
		print("Could not open "+log+": "+str(e))
		return returnDict
	try:
		hj = json.load( open(kf, "r") )
	except Exception as e:
		print("Could not open "+kf+": "+str(e))
		return returnDict
	
	if hj.get("Kernels") is None:
		return returnDict
	if hj.get("ValidBlocks") is None:
		return returnDict
	kernelBlocks = set()
	for id in hj["Kernels"]:
		if hj["Kernels"][id].get("Blocks") is not None:
			kernelBlocks = kernelBlocks.union(set(hj["Kernels"][id]["Blocks"]))
	#return { "Kernels": len(hj["Kernels"]), "KernelBlocks": list(kernelBlocks), "ValidBlocks": hj["ValidBlocks"] }
	return { "Kernels": len(hj["Kernels"]), "KernelBlocks": len(list(kernelBlocks)) }

def readScops(log):
	return {}
	scops = -1
	try:
		logFile = open(log, "r")
	except Exception as e:
		print("Could not find logfile "+log+": "+str(e))
		return scops

	try:
		for line in logFile:
			scops += len(re.findall("Writing\sJScop\s", line))
	except Exception as e:
		print("Could not parse a line of "+log+": "+str(e))
		return scops

	return scops

# the functions in this file only work if the file tree project has Dash-Corpus in its root path
def findProject(path):
	project = ""
	l = path.split("/")
	for i in range(len(l)):
		if (i+1 < len(l)) and (l[i] == "Dash-Corpus"):
			project = l[i+1]
	return project

def recurseIntoFolder(path, BuildNames, stepStrings, dataMap):
	"""
	@brief 	   recursive algorithm to search through all branches of a directory tree for directories containing files of interest
	@param[in] path			Absolute path to a directory of interest. Initial call should be to to the root of the tree to be searched
	@param[in] BuildNames	Folder names that are being sought after. Likely build folder names
	@param[in] stepString   List of step descriptor substrings to match to log file name strings. This essentially dictates which pipeline steps you are interested in (for example, ["makeNative","Cartographer"])
	@param[in] dataMap      Hash of the data being processed. Contains [project][logFileName][Folder] key and 
	Steps:
	For the profiled builds
	1.) Find each profile log in the build folder (use its name to index dataMap
	2.) Regex the log for the profile time
	3.) Fill in the relevant category in the kernel map (either profiled or unprofiled time) for that project/profile combo
	Then do the same thing for the unprofiled builds, but make sure that for each new unprofiled entry there is a profiled entry (otherwise this profile did not work with the backend)
	"""
	currentFolder = path.split("/")[-1]
	path += "/"
	projectName   = findProject(path)
	if currentFolder in set(BuildNames):
		if dataMap.get(projectName) is None:
			dataMap[projectName] = dict()
		logFiles = []
		logs = path+"/logs/"
		files = os.scandir(logs)
		for stepString in stepStrings:
			for f in files:
				if f.name.startswith(stepString):
					logFiles.append(f.path)
		for log in logFiles:
			logFileName = log.split("/")[-1]
			refinedLogFileName = logFileName
			kernelFileName = "kernel_"+"_".join(x for x in refinedLogFileName.split("_")[1:]).split(".")[0]+".json"
			keyName     = ""
			for step in stepStrings:
				if logFileName.startswith(step):
					keyName = log.split("/")[-1].replace(step, "")
					break

			if dataMap[projectName].get(keyName) is None:
				dataMap[projectName][keyName] = { "HC": {}, "2DMarkov": {} }
			if "HC" in currentFolder:
				print("Hotcode: "+kernelFileName)
				dataMap[projectName][keyName]["HC"] = readKernelFile(path+kernelFileName, path+"/logs/"+logFileName)
			elif "2DMarkov" in currentFolder:
				print("2DMarkov: "+kernelFileName)
				dataMap[projectName][keyName]["2DMarkov"] = readKernelFile(path+kernelFileName, path+"/logs/"+logFileName)
			#elif "Polly" in currentFolder:
			#	print("Scops: "+logFileName)
			#	dataMap[projectName][keyName]["Scops"] = readScops(path+"/logs/"+logFileName)
			else:
				print("Could not categorize this directory: "+dir)
		
	directories = []
	for f in os.scandir(path):
		if f.is_dir():
			directories.append(f)

	for d in directories:
		dataMap = recurseIntoFolder(d.path, BuildNames, stepStrings, dataMap)
	return dataMap

def retrieveData(buildFolders):
	# maps project to application name to type (HC or 2DMarkov) to kernels
	dataMap = {}
	try:
		with open(CorpusFolder+"CollectedData.json","r") as f:
			dataMap = json.load( f )
	except FileNotFoundError:
		recurseIntoFolder(CorpusFolder, buildFolders, ["Cartographer_"], dataMap)
		#pft.recurseIntoFolder("/mnt/heorot-10/Dash/Dash-Corpus/Unittests", buildFolders, ["makeNative","Cartographer_"], dataMap)
		# sort the data into categories by build folder (we use abbreviations "HC" and "2DMarkov" to correspond to the build folder names)
		sortedDataMap = {}
		for project in dataMap:
			if sortedDataMap.get(project) is None:
				sortedDataMap[project] = {}
			for keyName in dataMap[project]:
				if sortedDataMap[project].get(keyName) is None:
					sortedDataMap[project][keyName] = { "HC": -1, "2DMarkov": -1 }
				d = dataMap[project][keyName]
				if sortedDataMap[project][keyName]["HC"] != -1:
					print("Keyname "+keyName+" already exists in project "+project)
				sortedDataMap[project][keyName]["HC"] = d["HC"]
				if sortedDataMap[project][keyName]["2DMarkov"] != -1:
					print("Keyname "+keyName+" already exists in project "+project)
				sortedDataMap[project][keyName]["2DMarkov"] = d["2DMarkov"]
				#if sortedDataMap[project][keyName]["Polly"] != -1:
				#	print("Keyname "+keyName+" already exists in project "+project)
				#sortedDataMap[project][keyName]["Polly"] = d[dir]

		with open(CorpusFolder+"CollectedData.json","w") as f:
			json.dump(dataMap, f, indent=4)
	return dataMap

def PlotKernelSizeCorrelation(dataMap):
	axisFont  = 10
	axisLabelFont  = 10
	titleFont = 16
	xtickRotation = 90
	colors = [ ( 50./255 , 162./255, 81./255 , 127./255 ),
               ( 255./255, 127./255, 15./255 , 127./255 ),
           	   ( 214./255, 39./255 , 40./255 , 127./255 ),
               ( 121./255, 154./255, 134./255, 127./255 ),
               ( 198./255, 195./255, 71./255 , 127./255 ),
               ( 1.      , 1.      , 1.      , 127./255 ),
               ( 0.8     , 0.8     , 0.8     , 127./255 ),
               ( 0.0     , 0.0     , 0.0     , 127./255 ),]
	markers = [ 'o', '^', '1', 's', '*', 'd', 'X', '>']
	fig = plt.figure(frameon=False)
	fig.set_facecolor("white")
	ax = fig.add_subplot(1, 1, 1, frameon=False, fc="white")
	HCList = []
	MarkovList = []
	for project in dataMap:
		for entry in dataMap[project]:
			if dataMap[project][entry].get("HC") is None:
				raise KeyError("Entry not found in hot code category: "+str(entry))
			if dataMap[project][entry].get("2DMarkov") is None:
				raise KeyError("Entry not found in 2DMarkov category: "+str(entry))
			if dataMap[project][entry]["HC"]["KernelBlocks"] > dataMap[project][entry]["2DMarkov"]["KernelBlocks"]:
				print("{}/{} had more hot code blocks than PaMul".format(project,entry))
			elif dataMap[project][entry]["HC"]["KernelBlocks"] > dataMap[project][entry]["2DMarkov"]["KernelBlocks"]:
				print("{}/{} had equal hot code blocks to PaMul".format(project,entry))
			HCList.append(dataMap[project][entry]["HC"]["KernelBlocks"])
			MarkovList.append(dataMap[project][entry]["2DMarkov"]["KernelBlocks"])
#[ [ [ x for x in dataMap["HC"][z][y]] for y in dataMap["HC"][z]] for z in dataMap["HC"] ]
	for i in range( len( HCList ) ):
		if HCList[i] > MarkovList[i]:
			ax.scatter( HCList[i], MarkovList[i], color = colors[2], marker = markers[0])
		elif HCList[i] == MarkovList[i]:
			ax.scatter( HCList[i], MarkovList[i], color = colors[1], marker = markers[0])
		else:
			ax.scatter( HCList[i], MarkovList[i], color = colors[0], marker = markers[0])
	ax.set_aspect("equal")
	ax.set_title("Block Coverage Correlation", fontsize=titleFont)
	ax.set_ylabel("PaMul Blocks", fontsize=axisLabelFont)
	ax.set_xlabel("HotCode Blocks", fontsize=axisLabelFont)
	ax.set_yscale("log")
	ax.set_xscale("log")
	#plt.xticks(ticks=[x for x in range( len(xtickLabels) )], labels=xtickLabels, fontsize=axisFont, rotation=xtickRotation)
	#ax.tick_params(axis='x', colors='white')
	VTicks = [10**0, 10**1, 10**3, 10**2, 10**4]
	plt.yticks(VTicks, fontsize=axisFont)
	HTicks = [10**0, 10**1, 10**3, 10**2, 10**4]
	plt.xticks(HTicks, fontsize=axisFont)
	#ax.set_yticks(VTicks)
	#plt.hlines(VTicks, 0, len(xtickLabels), linestyle="dashed", colors=colors[-1])
	#vLineLocs = []
	#for i in range(len(xtickLabels)):
#		if xtickLabels[i] != "":
#			vLineLocs.append(i)
#	plt.vlines(vLineLocs, VTicks[0], VTicks[-1], linestyle="dashed", colors=colors[-1])
	#ax.yaxis.label.set_color('white')
	#ax.xaxis.label.set_color('white')
	RD.PrintFigure(plt, "KernelCoverageCovariance")
	plt.show()

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

def pairData(dataMap, buildFolders):
	# pairs all types together
	matchedData = {}
	for project in dataMap:
		for keyName in dataMap[project]:
			# keys: directory information comes from, value: tuple( kernels, blockCoverage )
			d = dataMap[project][keyName]
			allFound = True
			for key in d:
				if d[key].get("Kernels") is None:
					allFound = False
			if allFound:
				if matchedData.get(project) is None:
					matchedData[project] = dict()
					# first index kernels, second index static block coverage
				#matchedData[project][keyName] = { "HC": d["HC"], "2DMarkov": d["2DMarkov"], "Scops": d["Scops"] }
				matchedData[project][keyName] = { "HC": d["HC"], "2DMarkov": d["2DMarkov"] }

	with open("MatchedData.json","w") as f:
		json.dump(matchedData, f, indent=4)
	return matchedData
	"""
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

def outputDirectoryKernels(matchedData):
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

CorpusFolder = "/mnt/heorot-10/Dash/Dash-Corpus/"
#CorpusFolder = "/mnt/heorot-10/Dash/Dash-Corpus/OpenCV/"
#CorpusFolder = "/home/bwilli46/Dash/Dash-Automate/testing/"
#CorpusFolder = "/mnt/heorot-10/Dash/Dash-Corpus/Unittests/"
#buildFolders = { "buildHC11-21-21", "build2DMarkov11-21-21", "buildPollyScops11-20-21" }
buildFolders = { "buildHC11-21-21", "build2DMarkov11-21-21" }
#buildFolders = { "buildHC", "build2DMarkov" }
dataMap = retrieveData(buildFolders)
matchedData = pairData(dataMap, buildFolders)
PlotKernelSizeCorrelation(matchedData)




""" for reading in full report files in the long format, I don't like to do things this way because the long reports screw up the automation flow for some reason
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
