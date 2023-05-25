
import matplotlib.pyplot as plt
import RetrieveData as RD
import statistics

# timing file name
timingDataFile = "Timings_"+"".join(x for x in RD.CorpusFolder.split("/"))+list(RD.buildFolders)[0]+".json"

# plot parameters
axisFont  = 10
axisLabelFont  = 10
titleFont = 16
xtickRotation = 45
colors = [ ( 50./255 , 162./255, 81./255 , 100./255 ), # leaf green
           ( 255./255, 127./255, 15./255 , 100./255 ), # crimson red
       	   ( 214./255, 39./255 , 40./255 , 255./255 ), # orange
           ( 121./255, 154./255, 134./255, 255./255 ), # olive green
           ( 190./255, 10./255 , 255./255, 255./255 ), # violet
           ( 180./255, 90./255 , 0.0     , 255./255 ), # brown
           ( 255./255, 10./255 , 140./255, 255./255 ), # hot pink
           ( 198./255, 195./255, 71./255 , 255./255 ) ]# mustard yellow
markers = [ 'o', '^', '1', 's', '*', 'd', 'X', '>']

def NormalizeAndFilter(dataMap):
	filtered = {}
	for k, v in dataMap.items():
		markovMedian = statistics.median([v["Markov"][s]/v["Timing"][s] for s in v["Markov"]])
		memoryMedian = statistics.median([v["Memory"][s]/v["Timing"][s] for s in v["Memory"]])
		if markovMedian < 1.0:
			continue
		if memoryMedian < 1.0:
			continue
		filtered[k] = { "Markov": markovMedian, "Memory": memoryMedian }
	return filtered

def getProjectDilations(dataMap):
	dilations = {}
	for entry in dataMap:
		dilations[entry] = { "Markov": 0.0, "Memory": 0.0 }
		# we take the median of each sample set
		markovs = []
		memories = []
		for sample in dataMap[entry]["Timing"]:
			markovs.append( dataMap[entry]["Markov"][sample] / dataMap[entry]["Timing"][sample] )
			memories.append( dataMap[entry]["Memory"][sample] / dataMap[entry]["Timing"][sample] )
		dilations[entry]["Markov"] = statistics.median(markovs)
		dilations[entry]["Memory"] = statistics.median(memories)
	# make a total dilation stat
	appSamples = { "Markov": [], "Memory": [] }
	for entry in dilations:
		appSamples["Markov"].append(dilations[entry]["Markov"])
		appSamples["Memory"].append(dilations[entry]["Memory"])
	dilations["Total"] = { "Markov": statistics.median(appSamples["Markov"]), "Memory": statistics.median(appSamples["Memory"]) }
	print("Overall dilations: "+str(dilations["Total"]))
	return dilations

def plotTimeDilations(dataMap):
	# calculate dilations for each project
	dilations = getProjectDilations(dataMap)
	# scatter them
	fig = plt.figure(frameon=False)
	fig.set_facecolor("black")
	ax = fig.add_subplot(1, 1, 1, frameon=False, fc="black")

	ax.set_title("Dynamic Time Dilation Is Manageable", fontsize=titleFont)
	ax.scatter([x for x in range(len(dilations.keys()))], \
			   [dilations[x]["Markov"] for x in sorted(dilations, key = lambda x : dilations[x]["Markov"]) ], \
			   label="Markov", color=colors[0], marker=markers[0])
	ax.scatter([x for x in range(len(dilations.keys()))], \
			   [dilations[x]["Memory"] for x in sorted(dilations, key = lambda x : dilations[x]["Markov"]) ], \
			   label="Memory", color=colors[1], marker=markers[1])
	ax.set_ylabel("Dilation", fontsize=axisLabelFont)
	ax.set_xlabel("Application", fontsize=axisLabelFont)
	plt.tick_params(axis="x", which="both", bottom=False, top=False, labelbottom=False)
	ax.legend(frameon=False)
	RD.PrintFigure(plt, "TimeDilations")
	plt.show()

def binIt(entry, bins):
	for bin in bins:
		if entry >= bin[0] and entry <= bin[1]:
			bins[bin].append(entry)

def plotTimeDilationHistogram(dilations):
	# count of the number of histogram bins we want
	bins = 15
	# histogram each dilation factor within pre-defined bins
	# break up the data to bin within 10 categories
	markovMin = 1000
	markovMax = 0
	memoryMin = 1000
	memoryMax = 0
	for p in dilations:
		if dilations[p]["Markov"] < markovMin:
			markovMin = dilations[p]["Markov"]
		if dilations[p]["Markov"] > markovMax:
			markovMax = dilations[p]["Markov"]
		if dilations[p]["Memory"] < memoryMin:
			memoryMin = dilations[p]["Memory"]
		if dilations[p]["Memory"] > memoryMax:
			memoryMax = dilations[p]["Memory"]
	markovBins = {}
	memoryBins = {}
	difference = markovMax - markovMin
	for i in range(bins):
		markovBins[ (markovMin+i*difference/bins, markovMin+(i+1)*difference/bins) ] = []
	difference = memoryMax - memoryMin
	for i in range(bins):
		memoryBins[ (memoryMin+i*difference/bins, memoryMin+(i+1)*difference/bins) ] = []
	for p in dilations:
		binIt(dilations[p]["Markov"], markovBins)
		binIt(dilations[p]["Memory"], memoryBins)
	
	# markov histogram
	fig = plt.figure(frameon=False)
	fig.set_facecolor("black")
	ax = fig.add_subplot(1, 1, 1, frameon=False, fc="black")
	ax.bar([x for x in range(bins)], [len(markovBins[p]) for p in markovBins])
	ax.set_ylabel("Application Count", fontsize=axisLabelFont)
	ax.set_xlabel("Profile Dilation", fontsize=axisLabelFont)
	#plt.xticks(ticks=[x for x in range(bins)], labels=["{:4.1f}-{:4.1f}".format(x[0],x[1]) for x in list(markovBins.keys())], fontsize=axisFont, rotation=xtickRotation)
	plt.xticks(ticks=[x for x in range(bins)], labels=[str( int(x[0] + (x[0]+x[1])/20) ) for x in list(markovBins.keys())], fontsize=axisFont, rotation=xtickRotation)
	RD.PrintFigure(plt, "TimeDilationHistogram_Markov")

	# memory histogram
	fig = plt.figure(frameon=False)
	fig.set_facecolor("black")
	ax = fig.add_subplot(1, 1, 1, frameon=False, fc="black")
	ax.bar([x for x in range(bins)], [len(memoryBins[p]) for p in memoryBins])
	ax.set_xlabel("Profile Dilation", fontsize=axisLabelFont)
	#plt.xticks(ticks=[x for x in range(bins)], labels=["{:4.1f}-{:4.1f}".format(x[0],x[1]) for x in list(memoryBins.keys())], fontsize=axisFont, rotation=xtickRotation)
	plt.xticks(ticks=[x for x in range(bins)], labels=[str( int(x[0] + (x[0]+x[1])/20) ) for x in list(memoryBins.keys())], fontsize=axisFont, rotation=xtickRotation)

	ax.legend(frameon=False)
	RD.PrintFigure(plt, "TimeDilationHistogram_Memory")
	plt.show()

timingMap = RD.retrieveTimingData( RD.buildFolders, RD.CorpusFolder, timingDataFile )
# filter nonsensical answers
dilations = NormalizeAndFilter(timingMap)
#plotTimeDilations(timingMap)
plotTimeDilationHistogram(dilations)

