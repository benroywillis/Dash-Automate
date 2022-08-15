import matplotlib.pyplot as plt
import RetrieveData as RD

profilesFileName = "Profiles_"+"".join(x for x in RD.CorpusFolder.split("/"))+list(RD.buildFolders)[0]+".json"
kernelsFileName = "Kernels_"+"".join(x for x in RD.CorpusFolder.split("/"))+list(RD.buildFolders)[0]+".json"

# plot parameters
figDim = (19.2,10.8) # in inches
figDPI = 100 # creates 1920x1080 image
axisFont  = 10
axisLabelFont  = 10
titleFont = 16
xtickRotation = 90
colors = [ ( 50./255 , 162./255, 81./255 , 255./255 ), # leaf green
           ( 255./255, 127./255, 15./255 , 255./255 ), # crimson red
           ( 214./255, 39./255 , 40./255 , 255./255 ), # orange
           ( 121./255, 154./255, 134./255, 255./255 ), # olive green
           ( 190./255, 10./255 , 255./255, 255./255 ), # violet
           ( 180./255, 90./255 , 0.0     , 255./255 ), # brown
           ( 255./255, 10./255 , 140./255, 255./255 ), # hot pink
           ( 198./255, 195./255, 71./255 , 255./255 ), # mustard yellow
           ( 204./255, 153./255, 255./255, 255./255 ), # light violet
           ( 255./255, 178./255, 100./255, 255./255 ) ]# tan
markers = [ 'o', '^', '1', 's', '*', 'd', 'X', '>']

# maps a frequency count to the number of basic blocks that have that frequency count
def histFreq(blockFreq):
	hist = {}
	for freq in blockFreq.values():
		if hist.get(freq) is None:
			hist[freq] = 1
		else:
			hist[freq] += 1
	return hist

def histFreqMem(blockFreq):
	hist = {}
	for block, freq in blockFreq.items():
		if hist.get(freq) is None:
			hist[freq] = set()
		hist[freq].add(block)
	return hist

# maps a frequency count to a map of each category of basic block correspondence ie { count: { "HL": 2, "HC": 1, "HCHL": 3, etc... } }
# this data can be used to create a stacked bar histogram, where each bar has each BB correspondence category stacked on each other
freqPlotData = {}
def freqPlotParse(dataPoint, segHist):
	# first separate BBs into categories
	HC, HL, PaMul, HCHL, HCPaMul, HLPaMul, HCHLPaMul = RD.OverlapRegions(dataPoint["Kernels"]["HC"], dataPoint["Kernels"]["HL"], dataPoint["Kernels"]["PaMul"])
	#print(HC)
	#print(HL)
	#print(PaMul)
	#print(HCHL)
	#print(HCPaMul)
	#print(HLPaMul)
	#print(HCHLPaMul)
	#print()
	# second histogram the counts
	hist = histFreqMem(dataPoint["Profile"])
	# third generate the segmented histogram
	for freq in hist:
		if segHist.get(freq) is None:
			segHist[freq] = { "HC": 0, "HL": 0, "PaMul": 0, "HCHL": 0, "HCPaMul": 0, "HLPaMul": 0, "HCHLPaMul": 0, "None": 0 }
		for b in hist[freq]:
			if b in HC:
				segHist[freq]["HC"] += 1
			elif b in HL:
				segHist[freq]["HL"] += 1
			elif b in PaMul:
				segHist[freq]["PaMul"] += 1
			elif b in HCHL:
				segHist[freq]["HCHL"] += 1
			elif b in HCPaMul:
				segHist[freq]["HCPaMul"] += 1
			elif b in HLPaMul:
				segHist[freq]["HLPaMul"] += 1
			elif b in HCHLPaMul:
				segHist[freq]["HCHLPaMul"] += 1
			else:
				segHist[freq]["None"] += 1
	return segHist

def plotSegmentedHistogram(segHist, min=0, max=0):
	"""
	@param segHist	Maps a frequency to a map of each category magnitude ie { 20: { "HC": 4, "HL": 10, ... } }
	@param min		Minimum frequency to plot (inclusive)
	@param max		Maximum frequency to plot (exclusive). If 0 the entire length of the data is considered
	"""
	fig = plt.figure(figsize=figDim, dpi=figDPI, frameon=False)
	ax = fig.add_subplot(1, 1, 1, frameon=False)

	if max:
		dataLength = max
	else:
		dataLength = len(list(segHist.keys()))

	# x axis labels
	# only put 100 ticks total on the axis
	if dataLength > 100 :
		tickInterval = int(dataLength / 100)
	else:
		tickInterval = 1
	xtickLabels = []
	for i in range(dataLength):
		if (i % tickInterval) == 0:
			xtickLabels.append( str(sorted(list(segHist.keys()))[i]) )
		else:
			xtickLabels.append("")

	HC        = [segHist[f]["HC"] for f in sorted(segHist)]
	HL        = [segHist[f]["HL"] for f in sorted(segHist)]
	PaMul     = [segHist[f]["PaMul"] for f in sorted(segHist)]
	HCHL      = [segHist[f]["HCHL"] for f in sorted(segHist)]
	HCPaMul   = [segHist[f]["HCPaMul"] for f in sorted(segHist)]
	HLPaMul   = [segHist[f]["HLPaMul"] for f in sorted(segHist)]
	HCHLPaMul = [segHist[f]["HCHLPaMul"] for f in sorted(segHist)]
	Non       = [segHist[f]["None"] for f in sorted(segHist)]

	ax.set_title("Frequency Histogram", fontsize=titleFont)

	ax.bar([x for x in range(dataLength)], HC[:dataLength], label="HC", color=colors[0])
	ax.bar([x for x in range(dataLength)], HL[:dataLength], bottom=HC[:dataLength], label="HL", color=colors[1])
	ax.bar([x for x in range(dataLength)], PaMul[:dataLength], bottom=[HC[i]+HL[i] for i in range(dataLength)], label="PaMul", color=colors[2])
	ax.bar([x for x in range(dataLength)], HCHL[:dataLength], bottom=[HC[i]+HL[i]+PaMul[i] for i in range(dataLength)], label="HCHL", color=colors[3])
	ax.bar([x for x in range(dataLength)], HCPaMul[:dataLength], bottom=[HC[i]+HL[i]+PaMul[i]+HCHL[i] for i in range(dataLength)], label="HCPaMul", color=colors[4])
	ax.bar([x for x in range(dataLength)], HLPaMul[:dataLength], bottom=[HC[i]+HL[i]+PaMul[i]+HCHL[i]+HCPaMul[i] for i in range(dataLength)], label="HCHLPaMul", color=colors[5])
	ax.bar([x for x in range(dataLength)], HCHLPaMul[:dataLength], bottom=[HC[i]+HL[i]+PaMul[i]+HCHL[i]+HCPaMul[i]+HLPaMul[i] for i in range(dataLength)], label="HCHLPaMul", color=colors[6])
	ax.bar([x for x in range(dataLength)], Non[:dataLength], bottom=[HC[i]+HL[i]+PaMul[i]+HCHL[i]+HCPaMul[i]+HLPaMul[i]+HCHLPaMul[i] for i in range(dataLength)], label="None", color=colors[7])
	ax.set_ylabel("MembershipCount", fontsize=axisLabelFont)
	ax.set_xlabel("Frequency", fontsize=axisLabelFont)
	plt.xticks(ticks=[x for x in range( len(xtickLabels) )], labels=xtickLabels, fontsize=axisFont, rotation=xtickRotation)
	ax.legend(frameon=False)
	RD.PrintFigure(plt, "BasicBlockFrequencyHistogram")
	plt.show()

# profile data retrieval
profileMap = RD.retrieveProfiles(RD.buildFolders, RD.CorpusFolder, profilesFileName)
refinedProfiles = RD.refineBlockData(profileMap)
# we are only interested in block frequencies, so sum along the columns of the profile data to get block frequency
blockFrequencies = {}
for path in refinedProfiles:
	blockFrequencies[path] = {}
	for edge in refinedProfiles[path]:
		if blockFrequencies[path].get(edge[1]) is None:
			blockFrequencies[path][edge[1]] = refinedProfiles[path][edge]
		else:
			blockFrequencies[path][edge[1]] += refinedProfiles[path][edge]
			
# kernel data retrieval
kernelMap = RD.retrieveKernelData(RD.buildFolders, RD.CorpusFolder, kernelsFileName, RD.readKernelFile)
refinedBlocks = RD.refineBlockData(kernelMap)
matchedKernels = RD.matchData(refinedBlocks)

# now combine the profile and kernel data
dataMap = {}
for path in blockFrequencies:
	matchPath = "/".join(x for x in path.split("/")[:-1]) + path.split("/")[-1].split(".")[0]
	for path2 in matchedKernels:
		matchPath2 = "/".join(x for x in path2.split("/")[:-1]) + path2.split("/")[-1].split(".")[0].split("kernel_")[1]
		if matchPath == matchPath2:
			if dataMap.get(matchPath) is None:
				dataMap[matchPath] = {}
			if dataMap[matchPath].get("Profile") is None:
				dataMap[matchPath]["Profile"] = blockFrequencies[path]
			if dataMap[matchPath].get("Kernels") is None:
				dataMap[matchPath]["Kernels"] = {}
			if "HotCode" in path2:
				dataMap[matchPath]["Kernels"]["HC"] = matchedKernels[path2]["Kernels"]
			elif "HotLoop" in path2:
				dataMap[matchPath]["Kernels"]["HL"] = matchedKernels[path2]["Kernels"]
			else:
				dataMap[matchPath]["Kernels"]["PaMul"] = matchedKernels[path2]["Kernels"]
			print("Matched "+path+" and "+path2)
			if (dataMap[matchPath]["Kernels"].get("HC") is not None) and (dataMap[matchPath]["Kernels"].get("HL") is not None) and (dataMap[matchPath]["Kernels"].get("PaMul") is not None):
				break

# generate segmented histogram
segHist = {}
for entry in dataMap:
	segHist = freqPlotParse(dataMap[entry], segHist)

plotSegmentedHistogram(segHist, max=100)
