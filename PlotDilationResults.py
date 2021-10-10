import matplotlib.pyplot as plt
import json
import statistics as st

# root path to where all the TimeMaps will be
rootPath = "/mnt/heorot-10/Dash/Dash-Corpus/"
# global data map
TimeMap = {}

def appendTimeMap(path):
	try:
		with open(rootPath+path+"/TimeMap.json", "r") as f:
			d = json.load(f)
			for key, value in d.items():
				TimeMap[path+"/"+key] = value
	except FileNotFoundError:
		print("Could not find file: "+rootPath+path+"/TimeMap.json. Skipping...")
	except json.decoder.JSONDecodeError:
		print("JSON file not valid: "+rootPath+path+"/TimeMap.json. Skipping...")

def plotDilationResults():
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
	# sort TimeMap by block count (starting block count
	applicationMap = {}
#	sortedKeys = sorted( TimeMap, key = lambda Name: TimeMap[Name]["Natives"]["Median"] )
	sortedKeys = sorted( TimeMap )
	# 2D list of data points, for each entry Profile, FilePrint and 
	Dilations = []
	for i in range( len(sortedKeys) ):
		Dilations.append( [] )
		Dilations[i].append( TimeMap[sortedKeys[i]]["Profiles"]["Median"] )
		Dilations[i].append( TimeMap[sortedKeys[i]]["FilePrints"]["Median"] )
		Dilations[i].append( TimeMap[sortedKeys[i]]["Segmentations"]["Median"] )

	# construct xtick labels
	xtickLabels = [""]*len(sortedKeys)
	last = ""
	for i in range( len(sortedKeys) ):
		directory = sortedKeys[i].split("/")[0]
		if last != directory:
			xtickLabels[i] = directory
			last = directory
	fig = plt.figure(frameon=False)
	fig.set_facecolor("white")
	ax = fig.add_subplot(1, 1, 1, frameon=False, fc="white")
	for i in range( len(Dilations[0]) ):
		ax.scatter([x for x in range( len(Dilations) )], list(zip(*Dilations))[i], color = colors[i], marker = markers[i])
	ax.set_title("Time Dilation", fontsize=titleFont)
	ax.set_ylabel("Factor", fontsize=axisLabelFont)
	ax.legend(["Profiles","FilePrints","Segmentations"], frameon=False)
	plt.xticks(ticks=[x for x in range( len(xtickLabels) )], labels=xtickLabels, fontsize=axisFont, rotation=xtickRotation)
	#ax.tick_params(axis='x', colors='white')
	VTicks = [10**(-6), 10**-4, 10**-2, 10**0, 10**2, 10**4, 10**6]
	plt.yticks(VTicks, fontsize=axisFont)
	ax.set_yticks(VTicks)
	plt.hlines(VTicks, 0, len(xtickLabels), linestyle="dashed", colors=colors[-1])
	vLineLocs = []
	for i in range(len(xtickLabels)):
		if xtickLabels[i] != "":
			vLineLocs.append(i)
	plt.vlines(vLineLocs, VTicks[0], VTicks[-1], linestyle="dashed", colors=colors[-1])
	#ax.yaxis.label.set_color('white')
	#ax.xaxis.label.set_color('white')
	#ax.set_xscale("log")
	ax.set_yscale("log")
	plt.savefig("ProfileTimeDilation.svg",format="svg")
	plt.savefig("ProfileTimeDilation.png",format="png")
	plt.show()

def plotSegmentationResults():
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
	# sort TimeMap by block count (starting block count
	applicationMap = {}
	sortedKeys = sorted( TimeMap, key = lambda Name: TimeMap[Name]["Natives"]["Nodes"] )
	#sortedKeys = sorted( TimeMap )
	# 2D list of data points, for each entry a list of dilations based on a given metric
	Dilations = []
	for i in range( len(sortedKeys) ):
		Dilations.append( [] )
#		Dilations[i].append( st.median([TimeMap[sortedKeys[i]]["Segmentations"]["Times"][j]/TimeMap[sortedKeys[i]]["Natives"]["Nodes"] for j in range( len(TimeMap[sortedKeys[i]]["Segmentations"]["Times"] ) )]) )
		Dilations[i].append( st.median([TimeMap[sortedKeys[i]]["Segmentations"]["Times"][j]/TimeMap[sortedKeys[i]]["Natives"]["EndNodes"] for j in range( len(TimeMap[sortedKeys[i]]["Segmentations"]["Times"] ) )]) )
		Dilations[i].append( st.median([TimeMap[sortedKeys[i]]["Segmentations"]["Times"][j]/TimeMap[sortedKeys[i]]["Natives"]["endEdges"] for j in range( len(TimeMap[sortedKeys[i]]["Segmentations"]["Times"] ) )]) )
		Dilations[i].append( st.median([TimeMap[sortedKeys[i]]["Segmentations"]["Times"][j]/TimeMap[sortedKeys[i]]["Natives"]["EndEntropy"] for j in range( len(TimeMap[sortedKeys[i]]["Segmentations"]["Times"] ) )]) )

	# construct xtick labels
	xtickLabels = [""]*len(sortedKeys)
	""" for sorting x axis by directory
	last = ""
	for i in range( len(sortedKeys) ):
		directory = sortedKeys[i].split("/")[0]
		if last != directory:
			xtickLabels[i] = directory
			last = directory
	"""
	fig = plt.figure(frameon=False)
	fig.set_facecolor("white")
	ax = fig.add_subplot(1, 1, 1, frameon=False, fc="white")
	for i in range( len(Dilations[0]) ):
		#ax.scatter([x for x in range( len(Dilations) )], list(zip(*Dilations))[i], color = colors[i], marker = markers[i])
		ax.scatter([TimeMap[key]["Natives"]["Nodes"] for key in TimeMap], list(zip(*Dilations))[i], color = colors[i], marker = markers[i])
	ax.set_title("Dilation", fontsize=titleFont)
	ax.set_ylabel("Factor", fontsize=axisLabelFont)
	ax.legend(["EndBlocks","EndEdges","EndEntropy"], frameon=False)
	# for sorting x axis by directoryplt.xticks(ticks=[x for x in range( len(xtickLabels) )], labels=xtickLabels, fontsize=axisFont, rotation=xtickRotation)
	#ax.tick_params(axis='x', colors='white')
	VTicks = [10**(-6), 10**-4, 10**-2, 10**0, 10**2, 10**4, 10**6]
	plt.yticks(VTicks, fontsize=axisFont)
	ax.set_yticks(VTicks)
	plt.hlines(VTicks, 0, max([TimeMap[key]["Natives"]["Nodes"] for key in TimeMap]), linestyle="dashed", colors=colors[-1])
	"""for sorting x axis by directory
	vLineLocs = []
	for i in range(len(xtickLabels)):
		if xtickLabels[i] != "":
			vLineLocs.append(i)
	plt.vlines(vLineLocs, VTicks[0], VTicks[-1], linestyle="dashed", colors=colors[-1])
	"""
	#ax.yaxis.label.set_color('white')
	#ax.xaxis.label.set_color('white')
	ax.set_xscale("log")
	ax.set_yscale("log")
	plt.savefig("SegmentationDilationFigure.svg",format="svg")
	plt.savefig("SegmentationDilationFigure.png",format="png")
	plt.show()

# import timemaps we are interested in
appendTimeMap("Unittests") # have all the data we need (spade 10)
appendTimeMap("Dhry_and_whetstone") # have all the data we need (spade 11)
#appendTimeMap("Armadillo") # lots of data, probably all done (spade 11)
appendTimeMap("GSL") # lots of data, probably not done (spade 03)
appendTimeMap("CortexSuite") # (spade 07)
appendTimeMap("FFmpeg") # doesn't appear to be done (spade 06)
appendTimeMap("FEC") # doesn't appear to be done (spade 05)
appendTimeMap("FFTV") # not quite done, but we have data (spade 04)
appendTimeMap("Artisan") # appears to be done, may be missing some (spade 09)
appendTimeMap("PERFECT") # (spade 10)

## data processing
# get rid of outliers
for key in TimeMap:
	badIndices = []
	for i in range( len(TimeMap[key]["Natives"]["Times"]) ):
		if abs(TimeMap[key]["Natives"]["Times"][i]-TimeMap[key]["Natives"]["Mean"]) > 2*TimeMap[key]["Natives"]["stdev"]:
			badIndices.append(i)
			continue
		if abs(TimeMap[key]["Profiles"]["Dilations"][i]-TimeMap[key]["Profiles"]["Mean"]) > 2*TimeMap[key]["Profiles"]["stdev"]:
			badIndices.append(i)
			continue
		if abs(TimeMap[key]["FilePrints"]["Dilations"][i]-TimeMap[key]["FilePrints"]["Mean"]) > 2*TimeMap[key]["FilePrints"]["stdev"]:
			badIndices.append(i)
			continue
		if abs(TimeMap[key]["Segmentations"]["Dilations"][i]-TimeMap[key]["Segmentations"]["Mean"]) > 2*TimeMap[key]["Segmentations"]["stdev"]:
			badIndices.append(i)
			continue
	for i in range( len(badIndices) ):
		del TimeMap[key]["Natives"]["Times"][badIndices[i] - i]
		TimeMap[key]["Natives"]["Mean"] = st.mean(TimeMap[key]["Natives"]["Times"])
		TimeMap[key]["Natives"]["Mean"] = st.median(TimeMap[key]["Natives"]["Times"])
		TimeMap[key]["Natives"]["Mean"] = st.pstdev(TimeMap[key]["Natives"]["Times"])
		del TimeMap[key]["Profiles"]["Times"][badIndices[i] - i]
		del TimeMap[key]["Profiles"]["Dilations"][badIndices[i] - i]
		TimeMap[key]["Profiles"]["Mean"] = st.mean(TimeMap[key]["Profiles"]["Dilations"])
		TimeMap[key]["Profiles"]["Mean"] = st.median(TimeMap[key]["Profiles"]["Dilations"])
		TimeMap[key]["Profiles"]["Mean"] = st.pstdev(TimeMap[key]["Profiles"]["Dilations"])
		del TimeMap[key]["FilePrints"]["Times"][badIndices[i] - i]
		del TimeMap[key]["FilePrints"]["Dilations"][badIndices[i] - i]
		TimeMap[key]["FilePrints"]["Mean"] = st.mean(TimeMap[key]["FilePrints"]["Dilations"])
		TimeMap[key]["FilePrints"]["Mean"] = st.median(TimeMap[key]["FilePrints"]["Dilations"])
		TimeMap[key]["FilePrints"]["Mean"] = st.pstdev(TimeMap[key]["FilePrints"]["Dilations"])
		del TimeMap[key]["Segmentations"]["Times"][badIndices[i] - i]
		del TimeMap[key]["Segmentations"]["Dilations"][badIndices[i] - i]
		TimeMap[key]["Segmentations"]["Mean"] = st.mean(TimeMap[key]["Segmentations"]["Dilations"])
		TimeMap[key]["Segmentations"]["Mean"] = st.median(TimeMap[key]["Segmentations"]["Dilations"])
		TimeMap[key]["Segmentations"]["Mean"] = st.pstdev(TimeMap[key]["Segmentations"]["Dilations"])
#with open("TimeMap_Processed.json","w") as f:
#	json.dump(TimeMap, f, indent=4)

# plot
#plotDilationResults()
plotSegmentationResults()
