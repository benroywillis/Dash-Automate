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
colors = [ 
           ( 255./255,  95./255,  95./255, 255./255 ), # HC, orangish red
           (  50./255, 162./255,  81./255, 255./255 ), # HL, leaf green
           ( 190./255,  10./255, 255./255, 255./255 ), # PaMul, violet
           ( 255./255, 153./255,  51./255, 255./255 ), # HCHL, lite brown
           ( 255./255, 102./255, 178./255, 255./255 ), # HCPaMul, pink
           (  51./255, 153./255, 255./255, 255./255 ), # HLPaMul, sky blue
           ( 153./255, 153./255, 255./255, 255./255 ), # HCHLPaMul, brown-purple 
           ( 255./255, 178./255, 100./255, 255./255 ), # None, tan
           ( 121./255, 154./255, 134./255, 255./255 ), # olive green
           ( 198./255, 195./255,  71./255, 255./255 ), # mustard yellow
           ( 204./255, 153./255, 255./255, 255./255 )  # light violet
         ]
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

def plotSegmentedHistogram(segHist, plotHC=True, plotHL=True, plotPaMul=True, plotHCHL=True, plotHCPaMul=True, plotHLPaMul=True, plotHCHLPaMul=True, plotNone=True, limitTicks=True, min=0, max=0, show=True):
	"""
	@param segHist			Maps a frequency to a map of each category magnitude ie { 20: { "HC": 4, "HL": 10, ... } }
	@param plotHC    		Include basic blocks that belong exclusively to the HC kernel segmentation strategy
	@param plotHL    		Include basic blocks that belong exclusively to the HL kernel segmentation strategy
	@param plotPaMul    	Include basic blocks that belong exclusively to the PaMul kernel segmentation strategy
	@param plotHCHL    		Include basic blocks that belong to both the HC and HL kernel segmentation strategies
	@param plotHCPaMul		Include basic blocks that belong to both the HC and PaMul kernel segmentation strategies
	@param plotHLPaMul		Include basic blocks that belong to both the HL and PaMul kernel segmentation strategies
	@param plotHCHLPaMul	Include basic blocks that belong to the HC, HL, and PaMul kernel segmentation strategies
	@param plotNone			Include basic blocks that do not belong to any kernel segmentation strategy
	@param limitTicks 		Cap ticks on the xaxis of the plot to 100 in equal intervals
	@param min				Minimum frequency to plot (inclusive)
	@param max				Maximum frequency to plot (exclusive). If 0 the entire length of the data is considered
	@param show				Render figure after generation
	"""
	fig = plt.figure(figsize=figDim, dpi=figDPI, frameon=False)
	ax = fig.add_subplot(1, 1, 1, frameon=False)

	# put data into an array
	frequencies = sorted(list(segHist.keys()))
	allData     = []
	dataLabels  = []
	dataColors  = []
	if plotHC:
		HC        = [segHist[f]["HC"] for f in sorted(segHist)]
		allData.append(HC)
		dataLabels.append( "HC" )
		dataColors.append( colors[0] )
	if plotHL:
		HL        = [segHist[f]["HL"] for f in sorted(segHist)]
		allData.append(HL)
		dataLabels.append( "HL" )
		dataColors.append( colors[1] )
	if plotPaMul:
		PaMul     = [segHist[f]["PaMul"] for f in sorted(segHist)]
		allData.append(PaMul)
		dataLabels.append( "PaMul" )
		dataColors.append( colors[2] )
	if plotHCHL:
		HCHL      = [segHist[f]["HCHL"] for f in sorted(segHist)]
		allData.append(HCHL)
		dataLabels.append( "HCHL" )
		dataColors.append( colors[3] )
	if plotHCPaMul:
		HCPaMul   = [segHist[f]["HCPaMul"] for f in sorted(segHist)]
		allData.append(HCPaMul)
		dataLabels.append( "HCPaMul" )
		dataColors.append( colors[4] )
	if plotHLPaMul:
		HLPaMul   = [segHist[f]["HLPaMul"] for f in sorted(segHist)]
		allData.append(HLPaMul)
		dataLabels.append( "HLPaMul" )
		dataColors.append( colors[5] )
	if plotHCHLPaMul:
		HCHLPaMul = [segHist[f]["HCHLPaMul"] for f in sorted(segHist)]
		allData.append(HCHLPaMul)
		dataLabels.append( "HCHLPaMul" )
		dataColors.append( colors[6] )
	if plotNone:
		Non       = [segHist[f]["None"] for f in sorted(segHist)]
		allData.append(Non)
		dataLabels.append( "None" )
		dataColors.append( colors[7] )

	# take out all non-zero entries (along the columns, all entries of a row have to be 0 for the row to be eliminated)
	toRemove = []
	for j in range(len(allData[0])):
		allzero = True
		for i in range(len(allData)):
			if allData[i][j] > 0:
				allzero = False
				break
		if allzero:
			toRemove.append( j )
	offset = 0
	for i in range(len(toRemove)):
		del frequencies[toRemove[i] - offset]
		for r in range(len(allData)):
			del allData[r][toRemove[i] - offset]
		offset += 1

	# length of the data
	if max:
		dataLength = max
	else:
		dataLength = len(allData[0])

	# x axis labels
	# only put 100 ticks total on the axis
	if dataLength > 100 :
		tickInterval = int(dataLength / 100)
	else:
		tickInterval = 1
	xtickLabels = []
	for i in range(dataLength):
		if limitTicks:
			if (i % tickInterval) == 0:
				xtickLabels.append( str(frequencies[i]) )
			else:
				xtickLabels.append("")
		else:
			xtickLabels.append( str(frequencies[i]) )

	ax.set_title("Frequency Histogram", fontsize=titleFont)
	for i in range(len(allData)):
		if i == 0:
			ax.bar([x for x in range(dataLength)], allData[i][:dataLength], label=dataLabels[i], color=dataColors[i])
		else:
			barBottom = []
			for j in range(dataLength):
				sum = 0
				for k in range(i):
					sum += allData[k][j]
				barBottom.append( sum )
			ax.bar([x for x in range(dataLength)], allData[i][:dataLength], bottom=barBottom, label=dataLabels[i], color=dataColors[i])
	"""
	if plotHC:
		ax.bar([x for x in range(dataLength)], HC[:dataLength], label="HC", color=colors[0])
	if plotHL:
		ax.bar([x for x in range(dataLength)], HL[:dataLength], bottom=HC[:dataLength], label="HL", color=colors[1])
	if plotPaMul:
		ax.bar([x for x in range(dataLength)], PaMul[:dataLength], bottom=[HC[i]+HL[i] for i in range(dataLength)], label="PaMul", color=colors[2])
	if plotHCHL:
		ax.bar([x for x in range(dataLength)], HCHL[:dataLength], bottom=[HC[i]+HL[i]+PaMul[i] for i in range(dataLength)], label="HCHL", color=colors[3])
	if plotHCPaMul:
		ax.bar([x for x in range(dataLength)], HCPaMul[:dataLength], bottom=[HC[i]+HL[i]+PaMul[i]+HCHL[i] for i in range(dataLength)], label="HCPaMul", color=colors[4])
	if plotHLPaMul:
		ax.bar([x for x in range(dataLength)], HLPaMul[:dataLength], bottom=[HC[i]+HL[i]+PaMul[i]+HCHL[i]+HCPaMul[i] for i in range(dataLength)], label="HLPaMul", color=colors[5])
	if plotHCHLPaMul:
		ax.bar([x for x in range(dataLength)], HCHLPaMul[:dataLength], bottom=[HC[i]+HL[i]+PaMul[i]+HCHL[i]+HCPaMul[i]+HLPaMul[i] for i in range(dataLength)], label="HCHLPaMul", color=colors[6])
	if plotNone:
		ax.bar([x for x in range(dataLength)], Non[:dataLength], bottom=[HC[i]+HL[i]+PaMul[i]+HCHL[i]+HCPaMul[i]+HLPaMul[i]+HCHLPaMul[i] for i in range(dataLength)], label="None", color=colors[7])
	"""
	ax.set_ylabel("MembershipCount", fontsize=axisLabelFont)
	ax.set_xlabel("Frequency", fontsize=axisLabelFont)
	plt.xticks(ticks=[x for x in range( len(xtickLabels) )], labels=xtickLabels, fontsize=axisFont, rotation=xtickRotation)
	ax.legend(frameon=False)
	figureName = "BasicBlockFrequencyHistogram"
	if not plotHC:
		figureName += "_NoHC"
	if not plotHL:
		figureName += "_NoHL"
	if not plotPaMul:
		figureName += "_NoPaMul"
	if not plotHCHL:
		figureName += "_NoHCHL"
	if not plotHCPaMul:
		figureName += "_NoHCPaMul"
	if not plotHLPaMul:
		figureName += "_NoHLPaMul"
	if not plotHCHLPaMul:
		figureName += "_NoHCHLPaMul"
	if not plotNone:
		figureName += "_NoNone"
	if min:
		figureName += "_min_"+str(min)
	if max:
		figureName += "_max_"+str(max)
	if limitTicks:
		figureName += "_limitedTicks"
	RD.PrintFigure(plt, figureName)
	if show:
		plt.show()
	else:
		print("Completed "+figureName)

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

# the hotloop data is going to contain a bunch of dead code (frequency 0 blocks, which never appeared in the profiles)
# we add that information to the block data here
for path in matchedKernels:
	if "HotLoop" in path:
		profileName = path.split("/")[-1].split("kernel_")[1].split(".json")[0]+".bin"
		chop = path.split("/")[:-1]
		while "" in chop:
			chop.remove("")
		profilePath = "/"+"/".join( chop )+"/"+profileName
		if blockFrequencies.get(profilePath) is not None:
			for kernel in kernelMap[path]["Kernels"]:
				for block in kernelMap[path]["Kernels"][kernel]:
					if blockFrequencies[profilePath].get(block) is None:
						blockFrequencies[profilePath][block] = 0
		else:
			print("No profile file: "+profilePath)

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
			if (dataMap[matchPath]["Kernels"].get("HC") is not None) and (dataMap[matchPath]["Kernels"].get("HL") is not None) and (dataMap[matchPath]["Kernels"].get("PaMul") is not None):
				break
print("Matched files for "+str(len(dataMap))+" projects")

# generate segmented histogram
segHist = {}
for entry in dataMap:
	segHist = freqPlotParse(dataMap[entry], segHist)

plotSegmentedHistogram(segHist, max=100, show=False)
plotSegmentedHistogram(segHist, plotNone=False, max=100, show=False)
plotSegmentedHistogram(segHist, plotNone=False, max=1000, show=False)
plotSegmentedHistogram(segHist, plotHL=False, plotPaMul=False, plotHCHL=False, plotHCPaMul=False, plotHLPaMul=False, plotHCHLPaMul=False, plotNone=False, show=False)
plotSegmentedHistogram(segHist, plotHC=False, plotHL=False, plotPaMul=False, plotHCPaMul=False, plotHLPaMul=False, plotHCHLPaMul=False, plotNone=False, show=True)
