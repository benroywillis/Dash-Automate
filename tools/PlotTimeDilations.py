
import matplotlib.pyplot as plt
import RetrieveData as RD
import statistics

# plot parameters
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
           ( 198./255, 195./255, 71./255 , 255./255 ) ]# mustard yellow
markers = [ 'o', '^', '1', 's', '*', 'd', 'X', '>']

def plotTimeDilations(dataMap):
	
	# calculate dilations for each project
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
	ax.legend(frameon=False)
	RD.PrintFigure(plt, "TimeDilations")
	plt.show()


timingMap = RD.retrieveTimingData({"build"}, "/mnt/heorot-01/bwilli46/Dash/Dash-Automate/test/", "Timings.json")
plotTimeDilations(timingMap)

