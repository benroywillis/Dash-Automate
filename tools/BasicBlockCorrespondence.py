import json
import matplotlib.pyplot as plt
import matplotlib_venn   as pltv
import venn
import RetrieveData as RD

# dataFileName defines the name of the file that will store the data specific to this script (once it is generated)
dataFileName = "Kernels_"+"".join(x for x in RD.CorpusFolder.split("/"))+list(RD.buildFolders)[0]+".json"
loopFileName = "Loops_"+"".join(x for x in RD.CorpusFolder.split("/"))+list(RD.buildFolders)[0]+".json"

# set that selects projects we want to be included in the input data
# if this set is empty we select all available projects
InterestingProjects = {}

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

def PlotKernelCorrespondence(dataMap):
	fig = plt.figure(frameon=False)
	fig.set_facecolor("white")
	ax = fig.add_subplot(1, 1, 1, frameon=False, fc="white")

	# we need to go through each application and find the overlap of the blocks from the application
	# 1. uniquify the BBIDs across all project,application,blocks sets
	# 2. categorize the hotcode blocks, hot loop blocks and pamul blocks
	# 3. throw these sets into the venn3 call and see what happens

	HC = set()
	HL = set()
	PaMul = set()
	for file in dataMap:
		if len(InterestingProjects):
			if RD.getProjectName(file, "Dash-Corpus") not in InterestingProjects:
				continue
		if dataMap[file].get("Kernels"):
			if "HotCode" in file:
				HC = HC.union( RD.Uniquify(file, dataMap[file]["Kernels"]) )
			elif "HotLoop" in file:
				HL = HL.union( RD.Uniquify(file, dataMap[file]["Kernels"]) )
			else:
				PaMul = PaMul.union( RD.Uniquify(file, dataMap[file]["Kernels"]) )
	print(" HC: {}, HL: {}, PaMul: {} ".format(len(HC), len(HL), len(PaMul)))
	v = pltv.venn3([HC, HL, PaMul], ("HC", "HL", "PaMul"))
	RD.PrintFigure(plt, "BasicBlockCorrespondence")
	plt.show()

def PlotKernelCorrespondence_Manual(dataMap):
	zoneMags = { "HC": 0, "HL": 0, "PaMul": 0, "HCHL": 0, "HCPaMul": 0, "HLPaMul": 0, "HCHLPaMul": 0 }
	combinedMap = {}
	for path in dataMap:
		matchPath = "/".join(x for x in path.split("/")[:-1]) + path.split("/")[-1].split(".")[0]
		if combinedMap.get(matchPath) is None:
			combinedMap[matchPath] = { "HC": {}, "HL": {}, "PaMul": {} }
		if "HotCode" in path:
			combinedMap[matchPath]["HC"] = dataMap[path]["Kernels"]
		elif "HotLoop" in path:
			combinedMap[matchPath]["HL"] = dataMap[path]["Kernels"]
		else:
			combinedMap[matchPath]["PaMul"] = dataMap[path]["Kernels"]

	# record projects that have exclusive HC and HCHL blocks
	exclusionRegions = { "HC": [], "HCHL": [] }
	for path in combinedMap:
		HC, HL, PaMul, HCHL, HCPaMul, HLPaMul, HCHLPaMul = RD.OverlapRegions(combinedMap[path]["HC"], combinedMap[path]["HL"], combinedMap[path]["PaMul"])
		zoneMags["HC"] += len(HC)
		if len(HC):
			exclusionRegions["HC"].append( [path, list(HC)] )
		zoneMags["HL"] += len(HL)
		zoneMags["PaMul"] += len(PaMul)
		zoneMags["HCHL"] += len(HCHL)
		if len(HCHL):
			exclusionRegions["HCHL"].append( [path, list(HCHL)] )
		zoneMags["HCPaMul"] += len(HCPaMul)
		zoneMags["HLPaMul"] += len(HLPaMul)
		zoneMags["HCHLPaMul"] += len(HCHLPaMul)
	print("Manual correspondence region magnitudes:")
	print(zoneMags)
	with open("Data/ExclusionRegions_"+list(RD.buildFolders)[0]+".json", "w") as f:
		json.dump(exclusionRegions, f, indent=4)

def PlotKernelCorrespondence_static(dataMap, loopMap):
	fig = plt.figure(frameon=False)
	fig.set_facecolor("white")
	ax = fig.add_subplot(1, 1, 1, frameon=False, fc="white")

	# we need to go through each application and find the overlap of the blocks from the application
	# 1. uniquify the BBIDs across all project,application,blocks sets
	# 2. categorize the hotcode blocks, hot loop blocks and pamul blocks
	# 3. throw these sets into the venn3 call and see what happens

	HC = set()
	HL = set()
	PaMul = set()
	Loops = set()
	for file in dataMap:
		if dataMap[file].get("Kernels"):
			if "HotCode" in file:
				HC = HC.union( RD.Uniquify_static(file, dataMap[file]["Kernels"], trc=True) )
			elif "HotLoop" in file:
				HL = HL.union( RD.Uniquify_static(file, dataMap[file]["Kernels"], trc=True) )
			else:
				PaMul = PaMul.union( RD.Uniquify_static(file, dataMap[file]["Kernels"], trc=True) )
	for file in loopMap:
		Loops = Loops.union( RD.Uniquify_static(file, loopMap[file]) )
	print(" HC: {}, HL: {}, PaMul: {}, Loops: {} ".format(len(HC), len(HL), len(PaMul), len(Loops)))
	types = { "HotCode": HC, "HotLoop": HL, "PaMul": PaMul, "Loop": Loops }
	venn.venn(types)
	RD.PrintFigure(plt, "BasicBlockCorrespondence")
	plt.show()

def ExclusionZones(dataMap, loopMap):
	exclusions = { 
					# hotcode not captured by PaMul
				   "HC": [], \
					# hotcode and hotloop not captured by PaMul
				   "HC,HL": [], \
					# hotloop not captured by PaMul
				   "HL": []
				 }
	# observe the unique blocks of each data file and create the sets for each segmentation method
	HC = set()
	HL = set()
	PaMul = set()
	Loops = set()
	for file in dataMap:
		if "HotCode" in file:
			HC = HC.union( RD.Uniquify(file, dataMap[file]["Kernels"]) )
		elif "HotLoop" in file:
			HL = HL.union( RD.Uniquify(file, dataMap[file]["Kernels"]) )
		else:
			PaMul = PaMul.union( RD.Uniquify(file, dataMap[file]["Kernels"]) )
	# find files that contribute to the exclusion zones
	for file in dataMap:
		uniqueBlocks = RD.Uniquify(file, dataMap[file]["Kernels"])
		if "HotCode" in file:
			# overlap the blocks with the PaMul set and the hotloop set
			intersect_p = uniqueBlocks.intersection(PaMul)
			intersect_l = uniqueBlocks.intersection(HL)
			onlyHC = uniqueBlocks - intersect_p - intersect_l
			# if the overlaps are not the size of the file coverage in both cases, there are unique blocks in the hotcode result that are not in either the paMul or hotloop coverage
			if len(onlyHC):
				exclusions["HC"].append( (file,list(RD.reverseUniquify(onlyHC, file))) )
			else:
				continue
		elif "HotLoop" in file:
			intersect_p = uniqueBlocks.intersection(PaMul)
			intersect_c = uniqueBlocks.intersection(HC)
			onlyHL = uniqueBlocks - intersect_p - intersect_c
			if len(onlyHL):
				exclusions["HL"].append( (file,list(RD.reverseUniquify(onlyHL, file))) )
			else:
				continue
		else:
			continue
		
	with open("Data/ExclusiveRegions.json", "w") as f:
		json.dump(exclusions, f, indent=4)

dataMap = RD.retrieveKernelData(RD.buildFolders, RD.CorpusFolder, dataFileName, RD.readKernelFile)
loopMap = RD.retrieveStaticLoopData(RD.buildFolders, RD.CorpusFolder, loopFileName, RD.readLoopFile)
refined = RD.refineBlockData(dataMap)
matched = RD.matchData(refined)
PlotKernelCorrespondence_Manual(matched)
PlotKernelCorrespondence(matched)
#PlotKernelCorrespondence_static(matched, loopMap)
#ExclusionZones(matched, loopMap)
