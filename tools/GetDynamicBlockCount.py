
import RetrieveData as RD

profilesFileName = "Profiles_"+"".join(x for x in RD.CorpusFolder.split("/"))+list(RD.buildFolders)[0]+".json"

# profile data retrieval
profileMap = RD.retrieveProfiles(RD.buildFolders, RD.CorpusFolder, profilesFileName)

# holds the count of unique dynamically-executed blocks found in Dash-Corpus
# a "unique dynamically-executed block" satisfies the following two criteria:
# 1. it came from one and only one application executed in dash-corpus
# 2. it was seen by the dynamic profile instrumented in the execution of that application
executedBlocks = 0
# for each profile in the map (only use kernel_<name>.json, ignore HC and HL files) 
for p in profileMap:
	if ("HotCode" in p) or ("HotLoop" in p):
		continue
	# blocks specific to this profile
	pBlocks = set()
	for k, v in profileMap[p].items():
		# we pay attention to both the src and snk node of the profile
		src = int(k[0])
		snk = int(k[1])
		pBlocks.add(src)
		pBlocks.add(snk)
	executedBlocks += len(pBlocks)
print("Total dynamic blocks: "+str(executedBlocks))
exit(executedBlocks)
