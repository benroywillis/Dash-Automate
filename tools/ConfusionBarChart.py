
import json
import matplotlib.pyplot as plt
import RetrieveData as RD
#import BasicBlockCorrespondence as BBC

# dataFileName defines the name of the file that will store the data specific to this script (once it is generated)
loopDataFileName = "Loops_"+"".join(x for x in RD.CorpusFolder.split("/"))+list(RD.buildFolders)[0]+".json"
profileDataFileName = "Profiles_".join(x for x in RD.CorpusFolder.split("/"))+list(RD.buildFolders)[0]+".json"
kernelDataFileName= "Kernels_"+"".join(x for x in RD.CorpusFolder.split("/"))+list(RD.buildFolders)[0]+".json"
instanceDataFileName = "Instance_"+"".join(x for x in RD.CorpusFolder.split("/"))+list(RD.buildFolders)[0]+".json"
deadBlocksFileName = "DeadBlocks_"+"".join(x for x in RD.CorpusFolder.split("/"))+list(RD.buildFolders)[0]+".json"

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

def GenerateOverlapRegions_QPR(dataMap):
	# John: TODO
	# 1. find out how many dead blocks are in the entire corpus, not just the structured code
	# 2. (DONE) We need multiple symbols in the confusion matrix to represent the "type" of bar being presented
	#    - green check denotes an intersection with that structuring type
	#    - red ex represents an exclusion of that structure from the bar (ie HC&!HL&PaMul&!Instance gets a green-red-green-red column)
	# 3. the "zero" and "near-zero" columns are hard...
	#   - idea: change plot to log-linear bar (cringey, but if anyone complains we can change it)
	# 4. change "PaMul" to something else and change "Instance" to PaMul
	#   - we should work through the granular difference of the cartographer analysis vs. the instance analysis in the paper
	# 5. Categories for the QPR
	# HConly - what is the "error" ie code that matters that is getting rejected for some reason
	# HC & HL   - what is the worthless stuff that your HC static loop detector is finding
	# HC & Instance  - here are the hot things that actually matter, after our analysis
	# !HC & HL - loop components that are not hot (gigantic number because dead code is in here)
	# !HC & HL & !Dead - after we get rid of the dead code we find that alive loop components are actually very small
	# !HC & Inst - this is our answer to cold loop structures, and none of it is dead, and this category is small
	# !HC & HL & Instance - this is the set that our tool agrees with SoA techniques
	# HC & HL & Instance  - this is very close to the Intersectset size (because most of what Instance finds is important)
	# Deadcode overall - number lying around for when somebody asks
	# code overall - number lying around for when somebody asks

	# overall
	HCset       = set()
	HLset       = set()
	Instanceset = set()
	Deadcodeset = set()
	Livecodeset = set()
	Overallset  = set()

	for path in dataMap:
		HCset = HCset.union( RD.Uniquify(path, dataMap[path]["HotCode"], tn=False) )
		HLset = HLset.union( RD.Uniquify(path, dataMap[path]["HotLoop"], tn=False) )
		Instanceset = Instanceset.union( RD.Uniquify(path, dataMap[path]["Instance"], tn=False) )
		Deadcodeset = Deadcodeset.union( RD.Uniquify(path, dataMap[path]["DeadBlocks"], tn=False, blocks=True) )
		Livecodeset = Livecodeset.union( RD.Uniquify(path, dataMap[path]["LiveBlocks"], tn=False, blocks=True) )
		Overallset  = Deadcodeset.union(Livecodeset)
	
	# QPR categories
	HC   = set()
	HCHL = set()
	HCInstance = set()
	NotHCHL = set()
	NotHCHLNotDead = set()
	NotHCInstance = set()
	NotHCHLInstance = set()
	HCHLInstance = set()

	HC 				= HCset
	HCHL            = HCset.intersection(HLset)
	HCInstance      = HCset.intersection(Instanceset)
	NotHCHL         = HLset - HCset
	NotHCHLNotDead  = NotHCHL - Deadcodeset
	NotHCInstance   = Instanceset - HCset
	NotHCHLInstance = HLset.intersection(Instanceset) - HCset
	HCHLInstance    = HCset.intersection(HLset).intersection(Instanceset)
	
	# dump
	csvString  = "HC,"+str(len(HC))+"\n"
	csvString += "HCHL,"+str(len(HCHL))+"\n"
	csvString += "HCInstance,"+str(len(HCInstance))+"\n"
	csvString += "NotHCHL,"+str(len(NotHCHL))+"\n"
	csvString += "NotHCHLNotDead,"+str(len(NotHCHLNotDead))+"\n"
	csvString += "NotHCInstance,"+str(len(NotHCInstance))+"\n"
	csvString += "NotHCHLInstance,"+str(len(NotHCHLInstance))+"\n"
	csvString += "HCHLInstance,"+str(len(HCHLInstance))
	csvString += "TotalLive,"+str(len(Livecodeset))
	csvString += "TotalDead,"+str(len(Deadcodeset))
	csvString += "Overall,"+str(len(Overallset))
	with open("Data/RegionOverlaps_qpr_"+str(list(RD.buildFolders)[0])+".csv", "w") as f:
		f.write(csvString)
	with open("Data/RegionOverlaps_qpr_"+str(list(RD.buildFolders)[0])+".json", "w") as f:
		outputDict = { "HC": len(HC), "HCHL": len(HCHL), "HCInstance": len(HCInstance), "HCHLInstance": len(HCHLInstance), \
					   "NotHCHL": len(NotHCHL), "NotHCHLNotDead": len(NotHCHLNotDead), "NotHCInstance": len(NotHCInstance), \
					   "NotHCHLInstance": len(NotHCHLInstance), "TotalLive": len(Livecodeset), "TotalDead": len(Deadcodeset), \
					   "Overall": len(Overallset) }
		json.dump(outputDict, f, indent=4)

def GenerateOverlapRegions(dataMap):
	"""
	@brief Plots the correspondence between different structuring techniques: hotcode, hotloop, PaMul and memory instance pass
	"""
	# the confusion matrix codifies set intersections among the rows and columns
	# for example, the entry at the HC row and the PaMul & !HL column represents the intersection of HC and PaMul blocks that are not structured by PaMul (pink region)
	
	# overall
	HCset                = set()
	HLset                = set()
	PaMulset             = set()
	Instanceset          = set()
	# singles
	HConly 		         = set()
	HLonly 	             = set()
	PaMulonly            = set()
	Instanceonly         = set()
	# doubles
	HCHLset              = set()
	HCPaMulset           = set()
	HCInstanceset        = set()
	HLPaMulset           = set()
	HLInstanceset        = set()
	PaMulInstanceset     = set()
	# triples
	HCHLPaMulset         = set()
	HCHLInstanceset      = set()
	HCPaMulInstanceset   = set()
	HLPaMulInstanceset   = set()
	# quadruple
	HCHLPaMulInstanceset = set()

	for path in dataMap:
		HCset = HCset.union( RD.Uniquify(path, dataMap[path]["HotCode"], tn=False) )
		HLset = HLset.union( RD.Uniquify(path, dataMap[path]["HotLoop"], tn=False) )
		PaMulset = PaMulset.union( RD.Uniquify(path, dataMap[path]["PaMul"], tn=False) )
		Instanceset = Instanceset.union( RD.Uniquify(path, dataMap[path]["Instance"], tn=False) )
	# singles
	HConly = HCset - HLset - PaMulset - Instanceset
	HLonly = HLset - HCset - PaMulset - Instanceset
	PaMulonly = PaMulset - HCset - HLset - Instanceset
	Instanceonly = Instanceset - HCset - HLset - PaMulset
	# doubles
	HCHLset = HCset.intersection(HLset) - PaMulset - Instanceset
	HCPaMulset = HCset.intersection(PaMulset) - HLset - Instanceset
	HCInstanceset = HCset.intersection(Instanceset) - HLset - PaMulset
	HLPaMulset    = HLset.intersection(PaMulset) - HCset - Instanceset
	HLInstanceset = HLset.intersection(Instanceset) - HCset - PaMulset
	PaMulInstanceset = PaMulset.intersection(Instanceset) - HCset - HLset
	# triples
	HCHLPaMulset = HCset.intersection(HLset).intersection(PaMulset) - Instanceset
	HCHLInstanceset = HCset.intersection(HLset).intersection(Instanceset) - PaMulset
	HCPaMulInstanceset = HCset.intersection(PaMulset).intersection(Instanceset) - HLset
	HLPaMulInstanceset = HLset.intersection(PaMulset).intersection(Instanceset) - HCset
	# quadruple
	HCHLPaMulInstanceset = HCset.intersection(HLset).intersection(PaMulset).intersection(Instanceset)

	# John
	# we believe we are finding the important things and ignoring the unimportant things
	# Hotcode: clearly this stuff is important*
	# * unless you are a high frequency shared task
	#  - how much of the hotcode actually matters? 
	#  - HC & HL -> hotcode comes from static loops
	#  - HC & Instance -> hotcode comes from local hot loops
	#    -- the big HC & HL category shows how much crap you acrue if you just look at hotcode within loops
	#    -- the second smaller category HC & Instance is much more refined and to the point ie what should be optimized is this
	# - kernels are not entirely hot, so how do you find these control structures that you need to add in?
	#   -- HL & !HC & !Deadcode -> dump all the stuff that never ran... but that actually requires that you do that analysis at a finer grain than dead functions
	#	  --- loop as an abstraction will not do a great job at finding non-hot stuff that matters
	# - instance & !HC 
	#  -- not only are we finding things that matter, we are also throwing away stuff that doesn't matter
	#    --- two kinds of deadcode
	#      ---- I actually needed that but it didn't execute
	#      ---- error/exception handling, I/O, memory allocation/deallocation, logging
	# - HC & HL & Instance and !HC & HL & Instance
	#  -- we are hoping that Instanceset is close to HC & HL & Instance

	# lastly, we have to generate the deadcode section, which should only overlap HLOnly
	# to do this, we go through all hotloop blocks and see if they are in the corresponding profile data (if not they're dead)
	deadCode = set()
	for path in dataMap:
		deadBlocks    = set()
		profileBlocks = set()
		#print(dataMap[path]["Profile"])
		for entry in dataMap[path]["Profile"]:
			profileBlocks.add(entry[0])
			profileBlocks.add(entry[1])
		for k in dataMap[path]["HotCode"]:
			for b in dataMap[path]["HotCode"][k]:
				if b not in profileBlocks:
					deadBlocks.add(b)
		for k in dataMap[path]["HotLoop"]:
			for b in dataMap[path]["HotLoop"][k]:
				if b not in profileBlocks:
					deadBlocks.add(b)
		for k in dataMap[path]["PaMul"]:
			for b in dataMap[path]["PaMul"][k]:
				if b not in profileBlocks:
					deadBlocks.add(b)
		for k in dataMap[path]["Instance"]:
			for b in dataMap[path]["Instance"][k]:
				if b not in profileBlocks:
					deadBlocks.add(b)
		deadCode = deadCode.union( RD.Uniquify( path, { "0": list(deadBlocks) }, tn=False ) )

	# verification, the only set that should overlap with dead code is HL
	HCdeadcode = HCset.intersection(deadCode)
	HLdeadcode = HLset.intersection(deadCode)
	PaMuldeadcode = PaMulset.intersection(deadCode)
	Instancedeadcode = Instanceset.intersection(deadCode)

	# output a csv of the table
	# singles
	csvString  = "DeadCode,"+str(len(deadCode))+"\n"
	csvString += "HCOnly,"+str(len(HConly))+"\n"
	csvString += "HLOnly,"+str(len(HLonly))+"\n"
	csvString += "PaMulOnly,"+str(len(PaMulonly))+"\n"
	csvString += "InstanceOnly,"+str(len(Instanceonly))+"\n"
	# doubles
	csvString += "HC & DeadCode,"+str(len(HCdeadcode))+"\n"
	csvString += "HL & DeadCode,"+str(len(HLdeadcode))+"\n"
	csvString += "PaMul & DeadCode,"+str(len(PaMuldeadcode))+"\n"
	csvString += "Instance & DeadCode,"+str(len(Instancedeadcode))+"\n"
	csvString += "HC & HL,"+str(len(HCHLset))+"\n"
	csvString += "HC & PaMul ,"+str(len(HCPaMulset))+"\n"
	csvString += "HC & Instance,"+str(len(HCInstanceset))+"\n"
	csvString += "HL & PaMul,"+str(len(HLPaMulset))+"\n"
	csvString += "HL & Instance,"+str(len(HLInstanceset))+"\n"
	csvString += "PaMul & Instance,"+str(len(PaMulInstanceset))+"\n"
	# triples
	csvString += "HC & HL & PaMul,"+str(len(HCHLPaMulset))+"\n"
	csvString += "HC & HL & Instance,"+str(len(HCHLInstanceset))+"\n"
	csvString += "HC & PaMul & Instance,"+str(len(HCPaMulInstanceset))+"\n"
	csvString += "HL & PaMul & Instance,"+str(len(HLPaMulInstanceset))+"\n"
	# quadruple
	csvString += "HC & HL & PaMul & Instance,"+str(len(HCHLPaMulInstanceset))+"\n"

	# dump
	with open("Data/RegionOverlaps_"+str(list(RD.buildFolders)[0])+".csv", "w") as f:
		f.write(csvString)
	with open("Data/RegionOverlaps_"+str(list(RD.buildFolders)[0])+".json", "w") as f:
		outputDict = { "HC": len(HConly), "HL": len(HLonly), "PaMul": len(PaMulonly), "Instance": len(Instanceonly), \
					   "HCHL": len(HCHLset), "HCPaMul": len(HCPaMulset), "HCInstance": len(HCInstanceset), 
					   "HLPaMul": len(HLPaMulset), "HLPaMul": len(HLPaMulset), "HLInstance": len(HLInstanceset), \
					   "PaMulInstance": len(PaMulInstanceset), "HCHLPaMul": len(HCHLPaMulset), "HCHLInstance": len(HCHLInstanceset),\
					   "HCPaMulInstance": len(HCPaMulInstanceset), "HLPaMulInstance": len(HLPaMulInstanceset), \
					   "HCHLPaMulInstance": len(HCHLPaMulInstanceset), "Deadcode": len(deadCode), "HCDead": len(HCdeadcode), \
					   "HLDead": len(HLdeadcode), "PaMulDead": len(PaMuldeadcode), "Instancedead": len(Instancedeadcode) }
		json.dump(outputDict, f, indent=4)

def plotBars_qpr():
	try:
		with open("Data/RegionOverlaps_qpr_"+str(list(RD.buildFolders)[0])+".json", "r") as f:
			dataMap = json.load(f)
	except FileNotFoundError:
		print("Could not find data file ./Data/RegionOverlaps_qpr_"+str(list(RD.buildFolders)[0])+".json for plotting Confusion bars!")
		return
	# generate bar chart
	HC   = dataMap["HC"]
	HCHL = dataMap["HCHL"]
	HCInstance = dataMap["HCInstance"]
	NotHCHL = dataMap["NotHCHL"]
	NotHCHLNotDead = dataMap["NotHCHLNotDead"]
	NotHCInstance  = dataMap["NotHCInstance"]
	NotHCHLInstance  = dataMap["NotHCHLInstance"]
	HCHLInstance = dataMap["HCHLInstance"]
	bars =        [ HC, HCHL, HCInstance, HCHLInstance, NotHCHL, NotHCHLNotDead, NotHCInstance, NotHCHLInstance ]
	xtickLabels = [ "HC", "HCHL", "HCInstance", "HCHLInstance", "NotHCHL", "NotHCHLNotDead", "NotHCInstance", "NotHCHLInstance" ]
	
	fig = plt.figure(frameon=False)
	fig.set_facecolor("black")
	ax = fig.add_subplot(1, 1, 1, frameon=False, fc="black")

	ax.set_title("Structuring Correspondence", fontsize=titleFont)
	#ax.bar([x for x in range(len(bars))], bars)
	ax.scatter([x for x in range(len(bars))], bars)
	ax.set_ylabel("Count", fontsize=axisLabelFont)
	ax.set_ylim([1, 500000000])
	ax.set_yscale("log")
	plt.xticks(ticks=[x for x in range( len(xtickLabels) )], labels=xtickLabels, fontsize=axisFont, rotation=xtickRotation)
	ax.legend(frameon=False)
	RD.PrintFigure(plt, "ConfusionBarChart_qpr")
	plt.show()

def plotBars_paper():
	try:
		with open("Data/RegionOverlaps_"+str(list(RD.buildFolders)[0])+".json", "r") as f:
			dataMap = json.load(f)
	except FileNotFoundError:
		print("Could not find data file ./Data/RegionOverlaps_"+str(list(RD.buildFolders)[0])+".json for plotting Confusion bars!")
		return
	# generate bar chart
	deadCode          = dataMap["Deadcode"]
	HCdeadcode        = dataMap["HCDead"]
	HLdeadcode        = dataMap["HLDead"]
	PaMuldeadcode     = dataMap["PaMulDead"]
	Instancedeadcode  = dataMap["InstanceDead"]
	HConly            = dataMap["HC"]
	HLonly            = dataMap["HL"]
	PaMulonly         = dataMap["PaMul"]
	Instanceonly      = dataMap["Instance"]
	HCHL              = dataMap["HCHL"]
	HCPaMul           = dataMap["HCPaMul"]
	HCInstance        = dataMap["HCInstance"]
	HLPaMul           = dataMap["HLPaMul"]
	HLInstance        = dataMap["HLInstance"]
	PaMulInstance     = dataMap["PaMulInstance"]
	HCHLPaMul         = dataMap["HCHLPaMul"]
	HCHLInstance      = dataMap["HCHLInstance"]
	HCPaMulInstance   = dataMap["HCPaMulInstance"]
	HLPaMulInstance   = dataMap["HLPaMulInstance"]
	HCHLPaMulInstance = dataMap["HCHLPaMulInstance"]
	bars = [ deadCode, HConly, HLonly, PaMulonly, Instanceonly, \
			  HCdeadcode, HLdeadcode, PaMuldeadcode, Instancedeadcode, \
			  HCHL, HCPaMul, HCInstance, HLPaMul, HLInstance, PaMulInstance, \
			  HCHLPaMul, HCHLInstance, HCPaMulInstance, HLPaMulInstance, \
			  HCHLPaMulInstance ]
	xtickLabels = [ "Deadcode", "HConly", "HLonly", "PaMulonly", "Instanceonly", \
					"HCdeadcode", "HLdeadcode", "PaMuldeadcode", "Instancedeadcode", \
					"HCHL", "HCPaMul", "HCInstance", "HLPaMul", "HLInstance", "PaMulInstance", \
					"HCHLPaMul", "HCHLInstance", "HCPaMulInstance", "HLPaMulInstance", "HCHLPaMulInstance" ]
	
	fig = plt.figure(frameon=False)
	fig.set_facecolor("black")
	ax = fig.add_subplot(1, 1, 1, frameon=False, fc="black")

	ax.set_title("Structuring Correspondence", fontsize=titleFont)
	ax.bar([x for x in range(len(bars))], bars)
	ax.set_ylabel("Count", fontsize=axisLabelFont)
	plt.xticks(ticks=[x for x in range( len(xtickLabels) )], labels=xtickLabels, fontsize=axisFont, rotation=xtickRotation)
	ax.legend(frameon=False)
	ax.set_ylim([0, 500000])
	RD.PrintFigure(plt, "ConfusionBarChart")
	plt.show()
	
"""
loopData     = RD.retrieveStaticLoopData(RD.buildFolders, RD.CorpusFolder, loopDataFileName, RD.readLoopFile)
profileData  = RD.retrieveProfiles(RD.buildFolders, RD.CorpusFolder, profileDataFileName)
kernelData   = RD.retrieveKernelData(RD.buildFolders, RD.CorpusFolder, kernelDataFileName, RD.readKernelFile)
instanceData = RD.retrieveInstanceData(RD.buildFolders, RD.CorpusFolder, instanceDataFileName, RD.readKernelFile)
deadBlocks   = RD.retrieveDeadCode(RD.buildFolders, RD.CorpusFolder, deadBlocksFileName, profileData)

refinedLoopData     = RD.refineBlockData(loopData, loopFile=True)
refinedProfileData  = profileData
refinedDeadBlocks   = RD.refineBlockData(deadBlocks, deadCodeFile=True)
refinedKernelData   = RD.refineBlockData(kernelData)
refinedInstanceData = RD.refineBlockData(instanceData)
combined 			= RD.combineData( loopData = refinedLoopData, profileData = refinedProfileData, kernelData = refinedKernelData, instanceData = refinedInstanceData, deadBlocksData = refinedDeadBlocks )

GenerateOverlapRegions_QPR(combined)
GenerateOverlapRegions(combined)
"""

plotBars_qpr()
