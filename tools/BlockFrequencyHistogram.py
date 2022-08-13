
import RetrieveData as RD

dataFileName = "Profiles_"+"".join(x for x in RD.CorpusFolder.split("/"))+list(RD.buildFolders)[0]+"_data.json"

freqHist = {}
def histFreq(blockFreq):
	for freq in blockFreq.values():
		if freqHist.get(freq) is None:
			freqHist[freq] = 1
		else:
			freqHist[freq] += 1

dataMap = RD.retrieveProfiles(RD.buildFolders, RD.CorpusFolder, dataFileName)
refined = RD.refineBlockData(dataMap)
for entry in dataMap:
	histFreq(dataMap[entry])
print(freqHist)
