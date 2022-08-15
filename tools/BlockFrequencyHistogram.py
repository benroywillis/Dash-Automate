
import RetrieveData as RD

profilesFileName = "Profiles_"+"".join(x for x in RD.CorpusFolder.split("/"))+list(RD.buildFolders)[0]+"_data.json"
kernelsFileName = "Kernels_"+"".join(x for x in RD.CorpusFolder.split("/"))+list(RD.buildFolders)[0]+"_data.json"

freqHist = {}
def histFreq(blockFreq):
	for freq in blockFreq.values():
		if freqHist.get(freq) is None:
			freqHist[freq] = 1
		else:
			freqHist[freq] += 1

# profile data retrieval
profileMap = RD.retrieveProfiles(RD.buildFolders, RD.CorpusFolder, profilesFileName)
refinedProfiles = RD.refineBlockData(profileMap)
# kernel data retrieval
kernelMap = RD.retrieveKernelData(RD.buildFolders, RD.CorpusFolder, kernelsFileName, RD.readKernelFile)
refinedBlocks = RD.refineBlockData(kernelMap)
matchedKernels = RD.matchData(refinedBlocks)

# now combine the profile and kernel data
dataMap = {}
for path in profileMap:
	matchPath = "/".join(x for x in path.split("/")[:-1]) + path.split("/")[-1].split(".")[0]
	for path2 in matchedKernels:
		matchPath2 = "/".join(x for x in path2.split("/")[:-1]) + path2.split("/")[-1].split(".")[0].split("kernel_")[1]
		if matchPath == matchPath2:
			dataMap[matchPath] = {}
			dataMap[matchPath]["Profile"] = profileMap[path]
			dataMap[matchPath]["Kernels"] = matchedKernels[path2]
			print("Matched "+path+" and "+path2)
			break

# generate histogram of block frequencies
for entry in dataMap:
	histFreq(dataMap[entry])

