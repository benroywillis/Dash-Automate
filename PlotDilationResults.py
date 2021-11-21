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

def plotProfileDilationResults():
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
#	sortedKeys = sorted( TimeMap, key = lambda Name: TimeMap[Name]["Natives"]["Median"] )
	sortedKeys = sorted( TimeMap )
	# 2D list of data points, for each entry Profile, FilePrint and 
	Dilations = []
	for i in range( len(sortedKeys) ):
		Dilations.append( [] )
		Dilations[i].append( TimeMap[sortedKeys[i]]["Profiles"]["Median"] )
		Dilations[i].append( TimeMap[sortedKeys[i]]["FilePrints"]["Median"] )

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
	ax.legend(["Profiles","FilePrints"], frameon=False)
	ax.set_yscale("log")
	plt.xticks(ticks=[x for x in range( len(xtickLabels) )], labels=xtickLabels, fontsize=axisFont, rotation=xtickRotation)
	#ax.tick_params(axis='x', colors='white')
	VTicks = [10**(-6), 10**-4, 10**-2, 10**0, 10**1, 10**2, 10**4]
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
	plt.savefig("ProfileTimeDilation.svg",format="svg")
	plt.savefig("ProfileTimeDilation.eps",format="eps")
	plt.savefig("ProfileTimeDilation.pdf",format="pdf")
	plt.savefig("ProfileTimeDilation.png",format="png")
	plt.show()

def plotSegmentationVTransformResults():
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
	#sortedKeys = sorted( TimeMap, key = lambda Name: TimeMap[Name]["Natives"]["Nodes"] )
	sortedKeys = sorted( TimeMap )
	# 2D list of data points, for each entry a list of dilations based on a given metric
	Dilations = []
	for i in range( len(sortedKeys) ):
		Dilations.append( [] )
		Dilations[i].append( st.median([TimeMap[sortedKeys[i]]["Transforms"]["Times"][j]/TimeMap[sortedKeys[i]]["Natives"]["Nodes"] for j in range( len(TimeMap[sortedKeys[i]]["Transforms"]["Times"] ) )]) )
		Dilations[i].append( st.median([TimeMap[sortedKeys[i]]["Segmentations"]["Times"][j]/TimeMap[sortedKeys[i]]["Natives"]["Nodes"] for j in range( len(TimeMap[sortedKeys[i]]["Segmentations"]["Times"] ) )]) )

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
		#ax.scatter([TimeMap[key]["Natives"]["Nodes"] for key in TimeMap], list(zip(*Dilations))[i], color = colors[i], marker = markers[i])
	ax.set_title("Transform vs Segmentation", fontsize=titleFont)
	ax.set_ylabel("Factor", fontsize=axisLabelFont)
	#ax.set_xlabel("", fontsize=axisLabelFont)
	ax.legend(["Transform", "Segmentation"], frameon=False)
	plt.xticks(ticks=[x for x in range( len(xtickLabels) )], labels=xtickLabels, fontsize=axisFont, rotation=xtickRotation)
	#ax.set_xscale("log")
	ax.set_yscale("log")
	#ax.tick_params(axis='x', colors='white')
	VTicks = [10**-6, 10**-4, 10**-2, 10**0]
	plt.yticks(VTicks, fontsize=axisFont)
	plt.hlines(VTicks, 0, len(xtickLabels), linestyle="dashed", colors=colors[-1])
	ax.set_yticks(VTicks)
	vLineLocs = []
	for i in range(len(xtickLabels)):
		if xtickLabels[i] != "":
			vLineLocs.append(i)
	plt.vlines(vLineLocs, VTicks[0], VTicks[-1], linestyle="dashed", colors=colors[-1])
	#ax.yaxis.label.set_color('white')
	#ax.xaxis.label.set_color('white')
	plt.savefig("SegmentationVsTransformsDilationFigure.svg",format="svg")
	plt.savefig("SegmentationVsTransformsDilationFigure.eps",format="eps")
	plt.savefig("SegmentationVsTransformsDilationFigure.pdf",format="pdf")
	plt.savefig("SegmentationVsTransformsDilationFigure.png",format="png")
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
	sortedKeys = sorted( TimeMap, key = lambda Name: TimeMap[Name]["Natives"]["Nodes"] )
	#sortedKeys = sorted( TimeMap )
	# 2D list of data points, for each entry a list of dilations based on a given metric
	Dilations = []
	for i in range( len(sortedKeys) ):
		Dilations.append( [] )
		#Dilations[i].append( st.median([TimeMap[sortedKeys[i]]["Segmentations"]["Times"][j]/TimeMap[sortedKeys[i]]["Natives"]["EndNodes"] for j in range( len(TimeMap[sortedKeys[i]]["Segmentations"]["Times"] ) )]) )
		#Dilations[i].append( st.median([TimeMap[sortedKeys[i]]["Segmentations"]["Times"][j]/TimeMap[sortedKeys[i]]["Natives"]["endEdges"] for j in range( len(TimeMap[sortedKeys[i]]["Segmentations"]["Times"] ) )]) )
		#Dilations[i].append( st.median([TimeMap[sortedKeys[i]]["Segmentations"]["Times"][j]/(TimeMap[sortedKeys[i]]["Natives"]["Kernels"]) for j in range( len(TimeMap[sortedKeys[i]]["Segmentations"]["Times"] ) )]) )
		Dilations[i].append( st.median([TimeMap[sortedKeys[i]]["Segmentations"]["Times"][j]/(TimeMap[sortedKeys[i]]["Natives"]["Kernels"]*TimeMap[sortedKeys[i]]["Natives"]["endEdges"]*TimeMap[sortedKeys[i]]["Natives"]["EndNodes"]) for j in range( len(TimeMap[sortedKeys[i]]["Segmentations"]["Times"] ) )]) )

	# construct xtick labels
	xtickLabels = [""]*len(sortedKeys)
	fig = plt.figure(frameon=False)
	fig.set_facecolor("white")
	ax = fig.add_subplot(1, 1, 1, frameon=False, fc="white")
	for i in range( len(Dilations[0]) ):
		#ax.scatter([TimeMap[key]["Natives"]["EndNodes"] for key in TimeMap], list(zip(*Dilations))[i], color = colors[i], marker = markers[i])
		#ax.scatter([TimeMap[key]["Natives"]["endEdges"] for key in TimeMap], list(zip(*Dilations))[i], color = colors[i], marker = markers[i])
		#ax.scatter([TimeMap[key]["Natives"]["Kernels"] for key in TimeMap], list(zip(*Dilations))[i], color = colors[i], marker = markers[i])
		ax.scatter([TimeMap[key]["Natives"]["EndNodes"]*TimeMap[key]["Natives"]["endEdges"]*TimeMap[key]["Natives"]["Kernels"] for key in TimeMap], list(zip(*Dilations))[i], color = colors[i], marker = markers[i])
	ax.set_title("Dilation", fontsize=titleFont)
	ax.set_ylabel("Factor", fontsize=axisLabelFont)
	#ax.set_xlabel("Vertices", fontsize=axisLabelFont)
	#ax.set_xlabel("Edges", fontsize=axisLabelFont)
	#ax.set_xlabel("Kernels", fontsize=axisLabelFont)
	ax.set_xlabel("Vertices*Edges*Kernels", fontsize=axisLabelFont)
	#ax.legend(["EndBlocks*Kernels","Transforms v Nodes","Transforms v Edges"], frameon=False)
	ax.set_xscale("log")
	ax.set_yscale("log")
	#VTicks = [10**-4, 10**-3, 10**-2, 10**-1, 10**-0]
	#VTicks = [10**-4, 10**-3, 10**-2, 10**-1, 10**-0]
	#VTicks = [10**-4, 10**-3, 10**-2, 10**-1, 10**-0]
	VTicks = [10**-8, 10**-7, 10**-6, 10**-5, 10**-4, 10**-3, 10**-2]
	plt.yticks(VTicks, fontsize=axisFont)
	ax.set_yticks(VTicks)
	#plt.hlines(VTicks, 0, max([TimeMap[key]["Natives"]["EndNodes"] for key in TimeMap]), linestyle="dashed", colors=colors[-1])
	#plt.hlines(VTicks, 0, max([TimeMap[key]["Natives"]["endEdges"] for key in TimeMap]), linestyle="dashed", colors=colors[-1])
	#plt.hlines(VTicks, 0, max([TimeMap[key]["Natives"]["Kernels"] for key in TimeMap]), linestyle="dashed", colors=colors[-1])
	plt.hlines(VTicks, 0, max([TimeMap[key]["Natives"]["EndNodes"]*TimeMap[key]["Natives"]["Kernels"]*TimeMap[key]["Natives"]["endEdges"] for key in TimeMap]), linestyle="dashed", colors=colors[-1])
	#plt.savefig("SegmentationDilationFigure.svg",format="svg")
	#plt.savefig("SegmentationDilationFigure_Vertices.png",format="png")
	#plt.savefig("SegmentationDilationFigure_Edges.png",format="png")
	#plt.savefig("SegmentationDilationFigure_Kernels.png",format="png")
	plt.savefig("SegmentationDilationFigure_VerticesEdgesKernels.png",format="png")
	plt.show()

def plotTransformDilationResults():
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
	sortedKeys = sorted( TimeMap, key = lambda Name: TimeMap[Name]["Natives"]["Nodes"] )
	# 2D list of data points, for each entry a list of dilations based on a given metric
	Dilations = []
	for i in range( len(sortedKeys) ):
		Dilations.append( [] )
		#Dilations[i].append( st.median([TimeMap[sortedKeys[i]]["Transforms"]["Times"][j]/TimeMap[sortedKeys[i]]["Natives"]["Nodes"] for j in range( len(TimeMap[sortedKeys[i]]["Transforms"]["Times"] ) )]) )
		#Dilations[i].append( st.median([TimeMap[sortedKeys[i]]["Transforms"]["Times"][j]/TimeMap[sortedKeys[i]]["Natives"]["Edges"] for j in range( len(TimeMap[sortedKeys[i]]["Transforms"]["Times"] ) )]) )
		Dilations[i].append( st.median([TimeMap[sortedKeys[i]]["Transforms"]["Times"][j]/(TimeMap[sortedKeys[i]]["Natives"]["Nodes"]*TimeMap[sortedKeys[i]]["Natives"]["Edges"]) for j in range( len(TimeMap[sortedKeys[i]]["Transforms"]["Times"] ) )]) )

	# construct xtick labels
	xtickLabels = [""]*len(sortedKeys)
	fig = plt.figure(frameon=False)
	fig.set_facecolor("white")
	ax = fig.add_subplot(1, 1, 1, frameon=False, fc="white")
	for i in range( len(Dilations[0]) ):
		#ax.scatter([TimeMap[key]["Natives"]["Nodes"] for key in TimeMap], list(zip(*Dilations))[i], color = colors[i], marker = markers[i])
		#ax.scatter([TimeMap[key]["Natives"]["Edges"] for key in TimeMap], list(zip(*Dilations))[i], color = colors[i], marker = markers[i])
		ax.scatter([TimeMap[key]["Natives"]["Nodes"]*TimeMap[key]["Natives"]["Edges"] for key in TimeMap], list(zip(*Dilations))[i], color = colors[i], marker = markers[i])
	ax.set_title("Dilation", fontsize=titleFont)
	ax.set_ylabel("Factor", fontsize=axisLabelFont)
	#ax.set_xlabel("Vertices", fontsize=axisLabelFont)
	#ax.set_xlabel("Edges", fontsize=axisLabelFont)
	ax.set_xlabel("Vertices*Edges", fontsize=axisLabelFont)
	#ax.legend(["Vertices"], frameon=False)
	ax.set_xscale("log")
	ax.set_yscale("log")
	#VTicks = [10**-6, 10**-4, 10**-2]
	#VTicks = [10**-6, 10**-4, 10**-2]
	VTicks = [10**-8, 10**-6, 10**-4]
	plt.yticks(VTicks, fontsize=axisFont)
	ax.set_yticks(VTicks)
	#plt.hlines(VTicks, 0, max([TimeMap[key]["Natives"]["Nodes"] for key in TimeMap]), linestyle="dashed", colors=colors[-1])
	#plt.hlines(VTicks, 0, max([TimeMap[key]["Natives"]["Edges"] for key in TimeMap]), linestyle="dashed", colors=colors[-1])
	plt.hlines(VTicks, 0, max([TimeMap[key]["Natives"]["Nodes"]*TimeMap[key]["Natives"]["Edges"] for key in TimeMap]), linestyle="dashed", colors=colors[-1])
	#plt.savefig("TransformDilationFigure.svg",format="svg")
	#plt.savefig("TransformDilationFigure_Vertices.png",format="png")
	#plt.savefig("TransformDilationFigure_Edges.png",format="png")
	plt.savefig("TransformDilationFigure_VerticesEdges.svg",format="svg")
	plt.savefig("TransformDilationFigure_VerticesEdges.eps",format="eps")
	plt.savefig("TransformDilationFigure_VerticesEdges.pdf",format="pdf")
	plt.savefig("TransformDilationFigure_VerticesEdges.png",format="png")
	plt.show()


# import timemaps we are interested in
#appendTimeMap("Dhry_and_whetstone") # have all the data we need (spade 11)
appendTimeMap("Armadillo") # 103 bitcodes remaining (spade 11)
appendTimeMap("Unittests") # done (spade 11)
appendTimeMap("PERFECT") # 2 bitcodes remaining (spade 10)
appendTimeMap("Artisan") # 27 bitcodes remaining (spade 09)
appendTimeMap("CortexSuite") # 9 bitcodes remaining (spade 07)
appendTimeMap("FFmpeg") # projects done (spade 06)
appendTimeMap("FEC") # 6 bitcodes remaining (spade 05)
appendTimeMap("FFTV") # 40 bitcodes remaining (spade 04)
appendTimeMap("GSL") # 114 bitcodes remaining (spade 03)

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
		if abs(TimeMap[key]["Transforms"]["Dilations"][i]-TimeMap[key]["Transforms"]["Mean"]) > 2*TimeMap[key]["Transforms"]["stdev"]:
			badIndices.append(i)
			continue
		if abs(TimeMap[key]["Segmentations"]["Dilations"][i]-TimeMap[key]["Segmentations"]["Mean"]) > 2*TimeMap[key]["Segmentations"]["stdev"]:
			badIndices.append(i)
			continue
	for i in range( len(badIndices) ):
		del TimeMap[key]["Natives"]["Times"][badIndices[i] - i]
		TimeMap[key]["Natives"]["Mean"] = st.mean(TimeMap[key]["Natives"]["Times"])
		TimeMap[key]["Natives"]["Median"] = st.median(TimeMap[key]["Natives"]["Times"])
		TimeMap[key]["Natives"]["stdev"] = st.pstdev(TimeMap[key]["Natives"]["Times"])
		del TimeMap[key]["Profiles"]["Times"][badIndices[i] - i]
		del TimeMap[key]["Profiles"]["Dilations"][badIndices[i] - i]
		TimeMap[key]["Profiles"]["Mean"] = st.mean(TimeMap[key]["Profiles"]["Dilations"])
		TimeMap[key]["Profiles"]["Median"] = st.median(TimeMap[key]["Profiles"]["Dilations"])
		TimeMap[key]["Profiles"]["stdev"] = st.pstdev(TimeMap[key]["Profiles"]["Dilations"])
		del TimeMap[key]["FilePrints"]["Times"][badIndices[i] - i]
		del TimeMap[key]["FilePrints"]["Dilations"][badIndices[i] - i]
		TimeMap[key]["FilePrints"]["Mean"] = st.mean(TimeMap[key]["FilePrints"]["Dilations"])
		TimeMap[key]["FilePrints"]["Median"] = st.median(TimeMap[key]["FilePrints"]["Dilations"])
		TimeMap[key]["FilePrints"]["stdev"] = st.pstdev(TimeMap[key]["FilePrints"]["Dilations"])
		del TimeMap[key]["Transforms"]["Times"][badIndices[i] - i]
		del TimeMap[key]["Transforms"]["Dilations"][badIndices[i] - i]
		TimeMap[key]["Transforms"]["Mean"] = st.mean(TimeMap[key]["Transforms"]["Dilations"])
		TimeMap[key]["Transforms"]["Median"] = st.median(TimeMap[key]["Transforms"]["Dilations"])
		TimeMap[key]["Transforms"]["stdev"] = st.pstdev(TimeMap[key]["Transforms"]["Dilations"])
		del TimeMap[key]["Segmentations"]["Times"][badIndices[i] - i]
		del TimeMap[key]["Segmentations"]["Dilations"][badIndices[i] - i]
		TimeMap[key]["Segmentations"]["Mean"] = st.mean(TimeMap[key]["Segmentations"]["Dilations"])
		TimeMap[key]["Segmentations"]["Median"] = st.median(TimeMap[key]["Segmentations"]["Dilations"])
		TimeMap[key]["Segmentations"]["stdev"] = st.pstdev(TimeMap[key]["Segmentations"]["Dilations"])
#with open("TimeMap_Processed.json","w") as f:
#	json.dump(TimeMap, f, indent=4)

# plot
"""
plotProfileDilationResults()
plotSegmentationVTransformResults()
plotSegmentationResults()
plotTransformDilationResults()
"""
# downsample TimeMap to a map of directories (unfiltered it is a map of individual applications)
DirectoryMap = {}
for app in TimeMap:
	dir = app.split("/")[0]
	if DirectoryMap.get(dir) is None:
		DirectoryMap[dir] = { "Apps": [], "Mean": 0.0, "Median": 0.0, "Stdev": 0.0 }
	appEntry = TimeMap[app]["Profiles"]
	DirectoryMap[dir]["Apps"].append( (appEntry["Mean"], appEntry["Median"], appEntry["stdev"]) )

for dir in DirectoryMap:
	DirectoryMap[dir]["Mean"] = st.median( [x[0] for x in DirectoryMap[dir]["Apps"]] )
	DirectoryMap[dir]["Median"] = st.median( [x[1] for x in DirectoryMap[dir]["Apps"]] )
	DirectoryMap[dir]["Stdev"] = st.median( [x[2] for x in DirectoryMap[dir]["Apps"]] )
DirectoryMap["Total"] = { "Mean": 0.0, "Median": 0.0, "Stdev": 0.0 }
DirectoryMap["Total"]["Mean"] = st.median( [DirectoryMap[dir]["Mean"] for dir in DirectoryMap] )
DirectoryMap["Total"]["Median"] = st.median( [DirectoryMap[dir]["Median"] for dir in DirectoryMap] )
DirectoryMap["Total"]["Stdev"] = st.median( [DirectoryMap[dir]["Stdev"] for dir in DirectoryMap] )

# make a latex table of the results
latexString = "Directory & Median & Mean & Stdev \\\\\n\hline\n"
for dir in DirectoryMap:
	latexString += dir+" & {:.2f} & {:.2f} & {:.2f} \\\\\n".format(DirectoryMap[dir]["Median"],DirectoryMap[dir]["Mean"],DirectoryMap[dir]["Stdev"])

with open("ProfileDilationDirectoryStats.tex","w") as f:
	f.write(latexString)
