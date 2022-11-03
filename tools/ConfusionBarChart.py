
import json
import matplotlib.pyplot as plt
import RetrieveData as RD
#import BasicBlockCorrespondence as BBC

# dataFileName defines the name of the file that will store the data specific to this script (once it is generated)
loopDataFileName = "Loops_"+"".join(x for x in RD.CorpusFolder.split("/"))+list(RD.buildFolders)[0]+".json"
profileDataFileName = "Profiles_".join(x for x in RD.CorpusFolder.split("/"))+list(RD.buildFolders)[0]+".json"
kernelDataFileName= "Kernels_"+"".join(x for x in RD.CorpusFolder.split("/"))+list(RD.buildFolders)[0]+".json"
instanceDataFileName = "Instance_"+"".join(x for x in RD.CorpusFolder.split("/"))+list(RD.buildFolders)[0]+".json"

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

def PrintProjectInstances(dataMap):
	"""
	@brief Prints a .json file of all applications, kernels and hot instances
	"""

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
	with open("Data/RegionOverlaps_"+str(list(RD.buildFolders)[0])+".csv", "w") as f:
		f.write(csvString)

	# generate bar chart
	bars = [ len(deadCode), len(HConly), len(HLonly), len(PaMulonly), len(Instanceonly), \
			  len(HCdeadcode), len(HLdeadcode), len(PaMuldeadcode), len(Instancedeadcode), \
			  len(HCHLset), len(HCPaMulset), len(HCInstanceset), len(HLPaMulset), len(HLInstanceset), len(PaMulInstanceset), \
			  len(HCHLPaMulset), len(HCHLInstanceset), len(HCPaMulInstanceset), len(HLPaMulInstanceset), \
			  len(HCHLPaMulInstanceset) ]
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
	RD.PrintFigure(plt, "ConfusionBarChart")
	plt.show()
	

loopData     = RD.retrieveStaticLoopData(RD.buildFolders, RD.CorpusFolder, loopDataFileName, RD.readLoopFile)
profileData  = RD.retrieveProfiles(RD.buildFolders, RD.CorpusFolder, profileDataFileName)
kernelData   = RD.retrieveKernelData(RD.buildFolders, RD.CorpusFolder, kernelDataFileName, RD.readKernelFile)
instanceData = RD.retrieveInstanceData(RD.buildFolders, RD.CorpusFolder, instanceDataFileName, RD.readKernelFile)

refinedLoopData     = RD.refineBlockData(loopData, loopFile=True)
refinedProfileData  = profileData#RD.refineBlockData(profileData)
refinedKernelData   = RD.refineBlockData(kernelData)
refinedInstanceData = RD.refineBlockData(instanceData)
combined = RD.combineData( loopData = refinedLoopData, profileData = refinedProfileData, kernelData = refinedKernelData, instanceData = refinedInstanceData )
GenerateOverlapRegions(combined)
