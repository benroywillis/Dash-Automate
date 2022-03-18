import RetrieveData as RD
import matplotlib.pyplot as plt

## input data
# for testing
#CorpusFolder = "/mnt/heorot-10/Dash/Dash-Corpus/Unittests/"
#buildFolders = {"build_noHLconstraints_hc98"}

# most recent build
CorpusFolder = "/mnt/heorot-10/Dash/Dash-Corpus/"
buildFolders = {"build2-23-2022_hc95"}

# dataFileName defines the name of the file that will store the data specific to this script (once it is generated)
dataFileName = "Coverage_"+"".join(x for x in CorpusFolder.split("/"))+list(buildFolders)[0]+"_data.json"
loopFileName = "Coverage_"+"".join(x for x in CorpusFolder.split("/"))+list(buildFolders)[0]+"_loop.json"

# set of project names I'm interested in
InterestingProjects = { "Armadillo" }

# plot parameters
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

def PlotCoverageBars(dataMap):
	"""
	@brief This function shows a per-application breakdown of what Hotcode, Hotloop and PaMul capture (in terms of basic blocks)
	This figure should be used in conjunction with a Venn diagram showing the overall basic blocks captured by each strategy
	This figure should be color-matched to the Venn diagram
	For places of overlap with PaMul, each strategy should be shown in stacked bars above the x-axis in least-greatest order
	For BBs that do not overlap with PaMul, each strategy should be shown in stacked bars below the x-axis in least-greatest order
	"""
	fig = plt.figure(frameon=False)
	fig.set_facecolor("white")
	ax = fig.add_subplot(1, 1, 1, frameon=False, fc="white")

	# we need to go through each application and find the overlap of the blocks from the application
	# 1. uniquify the BBIDs across all applications
	# 2. categorize the hotcode blocks, hot loop blocks and pamul blocks
	# 3. for each application, intersect the block sets. This will yield exclusive and overlap regions
	# 4. for regions that overlap with PaMul, sort their magnitudes and make an entry for that application
	# 5. for regions that do not overlap PaMul, sort their magnitudes, flip the sign, and make and entry for that application

	# sorted list of absolute kernel file paths
	sortedKeys = sorted(dataMap)
	# list of labels that mark the beginnings and ends of each project in the x-axis applications
	xtickLabels = list()
	# set of projectNames that have been seen in the input data
	projectNames = set()
	# maps an application name to its HC, HL and PaMul data (each label has a set of uniquified basic block IDs
	appNames = dict()
	# for each trace
	for kfPath in sortedKeys:
		# make sure it is part of the projects we are interested in, and make an entry for it if it doesn't yet exist in our data
		if dataMap[kfPath].get("Kernels"):
			project = RD.getProjectName(kfPath, "Dash-Corpus")
			if project not in InterestingProjects:
				continue
			newProject = False
			if project not in projectNames:
				xtickLabels.append(project)
				projectNames.add(project)
				newProject = True

			# TODO: this is by trace, do by application
			# once that change is made, we will map multiple traces to one application... so you have to take the union of all traces for each application
			appName = "/".join(x for x in kfPath.split("/")[:-1])+RD.getTraceName(kfPath)
			# if we haven't seen this app before, add an entry to the processed data array
			# this is a new application with a project, if this app isn't getting the project name as its xlabel give it a blank one
			if appName not in appNames:
				appNames[appName] = { "HC": -1, "HL": -1, "PaMul": -1 }
				if not newProject:
					xtickLabels.append("")

			if "HotCode" in kfPath:
				appNames[appName]["HC"] = RD.Uniquify_static( kfPath, dataMap[kfPath]["Kernels"], trc=True )
			elif "HotLoop" in kfPath:
				appNames[appName]["HL"] = RD.Uniquify_static( kfPath, dataMap[kfPath]["Kernels"], trc=True )
			else:
				appNames[appName]["PaMul"] = RD.Uniquify_static( kfPath, dataMap[kfPath]["Kernels"], trc=True )

	# now that we have all the data sorted, we need to intersect the sets and come up with coverage bars to overlap
	setIntersections = {}
	for kfPath in appNames:
		HCset = appNames[kfPath]["HC"]
		HLset = appNames[kfPath]["HL"]
		PaMulset = appNames[kfPath]["PaMul"]
		setIntersections[kfPath] = { "NonPaMul": { "HC": 0.0, "HL": 0.0 }, "PaMul": { "HC": 0.0, "HL": 0.0, "PaMul": 1.0 } }
		# john: do this in reverse order bc that saves work
		HC         = HCset - HCset.intersection(HLset) - HCset.intersection(PaMulset)
		HL         = HLset - HLset.intersection(HCset) - HLset.intersection(PaMulset)
		PaMul      = PaMulset - PaMulset.intersection(HCset) - PaMulset.intersection(HLset)
		#HCHL       = HC.intersection(HL) - HC.intersection(PaMul) - HL.intersection(PaMul)
		PaMulHC    = PaMulset.intersection(HCset) - PaMulset.intersection(HLset).intersection(HCset)
		PaMulHL    = PaMulset.intersection(HLset) - PaMulset.intersection(HLset).intersection(HCset)
		#PaMulHCHL  = PaMul.intersection(HC) + PaMul.intersection(HL)

		# use the above set arithmetic to calculate the PaMul overlap regions (above x-axis) and non-PaMul overlap regions (below x-axis)
		setIntersections[kfPath]["NonPaMul"]["HC"] = len(HC) / len(PaMulset) if len(PaMulset) > 0 else len(HC)
		setIntersections[kfPath]["NonPaMul"]["HL"] = len(HL) / len(PaMulset) if len(PaMulset) > 0 else len(HL)
		setIntersections[kfPath]["PaMul"]["HC"] = len(PaMulHC) / len(PaMulset) if len(PaMulset) > 0 else len(PaMulHC)
		setIntersections[kfPath]["PaMul"]["HL"] = len(PaMulHL) / len(PaMulset) if len(PaMulset) > 0 else len(PaMulHL)
	print(setIntersections)
	# with the set intersections, we sort the data points into their respective positions
	# the 5 lists below represent the positions: lowest means most negative (highest non-PaMul), highest means most positive (highest PaMul overlap)
	lowest        = []
	secondLowest  = []
	highest       = []
	secondHighest = []
	thirdHighest  = []

	for kf in setIntersections:
		if setIntersections[kf]["NonPaMul"]["HC"] > setIntersections[kf]["NonPaMul"]["HL"]:
			lowest.append( -1*setIntersections[kf]["NonPaMul"]["HC"] )
			secondLowest.append( -1*setIntersections[kf]["NonPaMul"]["HL"] )
		else:
			lowest.append( -1*setIntersections[kf]["NonPaMul"]["HL"] )
			secondLowest.append( -1*setIntersections[kf]["NonPaMul"]["HC"] )
		if setIntersections[kf]["PaMul"]["HC"] > setIntersections[kf]["NonPaMul"]["HL"]:
			secondHighest.append( setIntersections[kf]["PaMul"]["HC"] )
			thirdHighest.append( setIntersections[kf]["PaMul"]["HL"] )
		else:
			secondHighest.append( setIntersections[kf]["PaMul"]["HL"] )
			thirdHighest.append( setIntersections[kf]["PaMul"]["HC"] )
		highest.append( setIntersections[kf]["PaMul"]["PaMul"] )

	#print(len(xtickLabels))
	#print(len(lowest))
	#print(len(secondLowest))
	#print(len(thirdHighest))
	#print(len(secondHighest))
	#print(len(highest))
	ax.set_aspect("equal")
	ax.set_title("Per Application Block Coverage", fontsize=titleFont)
	ax.bar([x for x in range(len(xtickLabels))], highest, label="PaMul")
	ax.bar([x for x in range(len(xtickLabels))], secondHighest, label="HotLoop")
	ax.bar([x for x in range(len(xtickLabels))], thirdHighest, label="HotCode")
	ax.bar([x for x in range(len(xtickLabels))], secondLowest, label="HCNoPaMul")
	ax.bar([x for x in range(len(xtickLabels))], lowest, label="HLNoPaMul")
	ax.set_ylabel("%", fontsize=axisLabelFont)
	ax.set_xlabel("Application", fontsize=axisLabelFont)
	plt.xticks(ticks=[x for x in range( len(xtickLabels) )], labels=xtickLabels, fontsize=axisFont, rotation=xtickRotation)
	ax.legend()
	plt.savefig("BasicBlockOverlaps.svg",format="svg")
	plt.savefig("BasicBlockOverlaps.eps",format="eps")
	plt.savefig("BasicBlockOverlaps.png",format="png")
	plt.show()

dataMap = RD.retrieveKernelData(buildFolders, CorpusFolder, dataFileName, RD.readKernelFile)
refined = RD.refineBlockData(dataMap)
matched = RD.matchData(refined)
PlotCoverageBars(matched)

