import json
import os
import re
import statistics as st
import matplotlib.pyplot as plt
import matplotlib_venn   as pltv

# for testing
CorpusFolder = "/home/bwilli46/Dash/Dash-Automate/testing/"
buildFolders = {"build2DMarkov", "buildHC"}

#CorpusFolder = "/mnt/heorot-10/Dash/Dash-Corpus/"
#CorpusFolder = "/mnt/heorot-10/Dash/Dash-Corpus/OpenCV/"
#CorpusFolder = "/mnt/heorot-10/Dash/Dash-Corpus/Unittests/"
#buildFolders = { "buildHC11-21-21", "build2DMarkov11-21-21", "buildPollyScops11-20-21" }
#buildFolders = { "buildHC11-21-21", "build2DMarkov11-21-21" }
#buildFolders = { "buildHC", "build2DMarkov" }

# most recent build
#CorpusFolder = "/mnt/heorot-10/bwilli46/Dash-Corpus/"
#buildFolders = {"buildQPR13_12-20-21"}

# maps build folder names to hotcode, hotloop, pamul
NameMap = { "build2DMarkov": "2DMarkov", "buildHC": "HC" }

# plot parameters
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

UniqueIDMap = {}
UniqueID = 0

def Uniquify(project, app, t, kernels):
	"""
	Uniquifies the basic block IDs such that no ID overlaps with another ID from another distict application
	"""
	global UniqueID
	mappedBlocks = set()
	if UniqueIDMap.get(project) is None:
		UniqueIDMap[project] = {}
	if UniqueIDMap[project].get(app) is None:
		UniqueIDMap[project][app] = {}
	for k in kernels:
		for block in kernels[k]:
			mappedID = -1
			if UniqueIDMap[project][app].get(block) is None:
				UniqueIDMap[project][app][block] = UniqueID
				mappedID = UniqueID
				UniqueID += 1
			else:
				mappedID = UniqueIDMap[project][app][block]
			if mappedID == -1:
				raise Exception("Could not map the block ID for {},{},{}!".format(project,app,block))
			mappedBlocks.add(mappedID)
	return mappedBlocks

def PlotKernelCorrespondence(dataMap):
	fig = plt.figure(frameon=False)
	fig.set_facecolor("white")
	ax = fig.add_subplot(1, 1, 1, frameon=False, fc="white")

	# we need to go through each application and find the overlap of the blocks from the application
	# 1. uniquify the BBIDs across all project,application,blocks sets
	# 2. categorize the hotcode blocks, hot loop blocks and pamul blocks
	# 3. throw these sets into the venn3 call and see what happens

	HC = set()
	PaMul = set()
	for project in dataMap:
		for entry in dataMap[project]:
			for t in dataMap[project][entry]:
				if t == "HC":
					HC = HC.union( Uniquify(project, entry, "HC", dataMap[project][entry][t]["Kernels"]) )
				else:
					PaMul = PaMul.union( Uniquify(project, entry, "2DMarkov", dataMap[project][entry][t]["Kernels"]) )
	pltv.venn2([HC, PaMul], ("HC", "PaMul"))
	"""
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
	plt.savefig("KernelCoverageCovariance.svg",format="svg")
	plt.savefig("KernelCoverageCovariance.eps",format="eps")
	#plt.savefig("KernelCoverageCovariance.pdf",format="pdf")
	plt.savefig("KernelCoverageCovariance.png",format="png")
	"""
	plt.show()

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
	returnDict["Kernels"] = {}
	for k in hj["Kernels"]:
		if hj["Kernels"][k].get("Blocks") is None:
			returnDict["Kernels"][k] = {}
		else:
			returnDict["Kernels"][k] = list(hj["Kernels"][k]["Blocks"])
	return returnDict

# the functions in this file only work if the file tree project has Dash-Corpus in its root path
def findProject(path):
	project = ""
	l = path.split("/")
	i = 0
	while i < len(l):
		if l[i] == "":
			del l[i]
		i += 1
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
	BuildNames = set(BuildNames)
	currentFolder = path.split("/")[-1]
	path += "/"
	projectName   = findProject(path)
	if currentFolder in BuildNames:
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
				dataMap[projectName][keyName] = {}
				for bf in BuildNames:
					dataMap[projectName][keyName][bf] = {}
			dataMap[projectName][keyName][currentFolder] = readKernelFile(path+kernelFileName, path+"/logs/"+logFileName)
		
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
		with open(CorpusFolder+"BasicBlockData.json","r") as f:
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
					sortedDataMap[project][keyName] = {}
				for f in buildFolders:
					if sortedDataMap[project][keyName].get(f) is None:
						sortedDataMap[project][keyName][f] = -1
					d = dataMap[project][keyName]
					if sortedDataMap[project][keyName][f] != -1:
						print("Keyname "+keyName+" already exists in project "+project)
					sortedDataMap[project][keyName][f] = d[f]

		with open(CorpusFolder+"BasicBlockData.json","w") as f:
			json.dump(sortedDataMap, f, indent=4)

	return dataMap


dataMap = retrieveData(buildFolders)
print(dataMap)
PlotKernelCorrespondence(dataMap)
