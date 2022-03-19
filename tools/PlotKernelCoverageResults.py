import matplotlib.pyplot as plt
import json

def plotKernelCoverageResults():
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
	# sort DataMap by block count (starting block count
#	sortedKeys = sorted( DataMap, key = lambda Name: DataMap[Name]["Natives"]["Median"] )
	sortedKeys = sorted( DataMap )
	numApps = 0
	# 2D list of data points, for each entry Profile, FilePrint and 
	HCCoverages = []
	M2Coverages = []
	for i in range( len(sortedKeys) ):
		HCCoverages.append( [] )
		M2Coverages.append( [] )
		for app in DataMap[sortedKeys[i]]:
			HCCoverages[i].append( DataMap[sortedKeys[i]][app]["HotCode"][1] )
			M2Coverages[i].append( DataMap[sortedKeys[i]][app]["2DMarkov"][1] )

	# construct xtick labels
	xtickLabels = [""]*numApps
	xtickLabels[0] = sortedKeys[i].split("/")[0]
	last = xTicklabels[0]
	appCount = 0
	for i in range( len(sortedKeys) ):
		directory = sortedKeys[i].split("/")[0]
		if last != directory:
			xtickLabels[i] = directory
			last = directory
	fig = plt.figure(frameon=False)
	fig.set_facecolor("white")
	ax = fig.add_subplot(1, 1, 1, frameon=False, fc="white")
	
	for i in range( len(HCCoverages) ):
		ax.scatter([x for x in range( len(HCCoverages[i]) )], HCCoverages[i], color = colors[0], marker = markers[0])
		ax.scatter([x for x in range( len(M2Coverages[i]) )], M2Coverages[i], color = colors[1], marker = markers[1])
	ax.set_title("Time Dilation", fontsize=titleFont)
	ax.set_ylabel("Factor", fontsize=axisLabelFont)
	ax.legend(["Hot Code","PaMul"], frameon=False)
	ax.set_yscale("log")
	plt.xticks(ticks=[x for x in range( len(xtickLabels) )], labels=xtickLabels, fontsize=axisFont, rotation=xtickRotation)
	#ax.tick_params(axis='x', colors='white')
	#VTicks = [10**(-6), 10**-4, 10**-2, 10**0, 10**1, 10**2, 10**4]
	#plt.yticks(VTicks, fontsize=axisFont)
	#ax.set_yticks(VTicks)
	#plt.hlines(VTicks, 0, len(xtickLabels), linestyle="dashed", colors=colors[-1])
	#vLineLocs = []
	#for i in range(len(xtickLabels)):
	#	if xtickLabels[i] != "":
	#		vLineLocs.append(i)
	#plt.vlines(vLineLocs, VTicks[0], VTicks[-1], linestyle="dashed", colors=colors[-1])
	#ax.yaxis.label.set_color('white')
	#ax.xaxis.label.set_color('white')
	RD.PrintFigure(plt, "KernelCoverage")
	plt.show()

DataMap = json.load( open("tools/MatchedData.json","r") )
plotKernelCoverageResults()
