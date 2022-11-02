
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
	combinedMap = {}
	for path in dataMap:
		matchPath = "/".join(x for x in path.split("/")[:-1]) + path.split("/")[-1].split("_")[1].split(".")[0]
		if combinedMap.get(matchPath) is None:
			combinedMap[matchPath] = { "HC": {}, "HL": {}, "Instance": {} }
		if "HotCode" in path:
			combinedMap[matchPath]["HC"] = RD.Uniquify(path, dataMap[path]["Kernels"])
		elif "HotLoop" in path:
			combinedMap[matchPath]["HL"] = RD.Uniquify(path, dataMap[path]["Kernels"])
		else:
			combinedMap[matchPath]["Instance"] = RD.Uniquify(path, dataMap[path]["Kernels"])
	HCset           = set()
	HConly 		    = set()
	HLset           = set()
	HLonly 	        = set()
	Instanceset     = set()
	Instanceonly    = set()
	HCHLset         = set()
	HCInstanceset   = set()
	HLInstanceset   = set()
	HCHLInstanceset = set()
    # john: do this in reverse order bc that saves work

	for path in combinedMap:
		HCset = HCset.union(combinedMap[path]["HC"])
		HLset = HLset.union(combinedMap[path]["HL"])
		Instanceset = Instanceset.union(combinedMap[path]["Instance"])
		HCHLset = HCHLset.union(combinedMap[path]["HC"].intersection(combinedMap[path]["HL"]))
		HCInstanceset = HCInstanceset.union(combinedMap[path]["HC"].intersection(combinedMap[path]["Instance"]))
		HLInstanceset = HLInstanceset.union(combinedMap[path]["HL"].intersection(combinedMap[path]["Instance"]))
		HCHLInstanceset = HCHLInstanceset.union(combinedMap[path]["HC"].intersection(combinedMap[path]["HL"]).intersection(combinedMap[path]["Instance"]))
		HConly = HCset - HLset - Instanceset
		HLonly = HLset - HCset - Instanceset
		Instanceonly = Instanceset - HLset - HCset

	# output a csv of the table
	csvString = "HCOnly,"+str(len(HConly))+"\n"
	csvString += "HLOnly,"+str(0)+","+str(len(HLonly))+"\n"
	csvString += "InstanceOnly,"+str(len(Instanceonly))+"\n"
	csvString += "HC & HL,"+str(len(HCHLset))+"\n"
	csvString += "HC & Instance,"+str(len(HCInstanceset))+"\n"
	csvString += "HL & Instance,"+str(len(HLInstanceset))+"\n"
	csvString += "HC & HL & Instance,"+str(len(HCHLInstanceset))+"\n"
	with open("Data/InstanceConfusionMatrix_"+str(list(RD.buildFolders)[0])+".csv", "w") as f:
		f.write(csvString)

loopData     = RD.retrieveStaticLoopData(RD.buildFolders, RD.CorpusFolder, loopDataFileName, RD.readLoopFile)
profileData  = RD.retrieveProfiles(RD.buildFolders, RD.CorpusFolder, profileDataFileName)
kernelData   = RD.retrieveKernelData(RD.buildFolders, RD.CorpusFolder, kernelDataFileName, RD.readKernelFile)
instanceData = RD.retrieveInstanceData(RD.buildFolders, RD.CorpusFolder, instanceDataFileName, RD.readKernelFile)

refinedLoopData     = RD.refineBlockData(loopData, loopFile=True)
refinedProfileData  = RD.refineBlockData(profileData)
refinedKernelData   = RD.refineBlockData(kernelData)
refinedInstanceData = RD.refineBlockData(instanceData)
combined = RD.combineData( loopData = refinedLoopData, profileData = refinedProfileData, kernelData = refinedKernelData, instanceData = refinedInstanceData )
matched = RD.matchData(refinedKernelData, instanceMap=refinedInstanceData, instance=True)
GenerateOverlapRegions(matched)
