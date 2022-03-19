import RetrieveData as RD
import matplotlib.pyplot as plt

## input data
# for testing
#CorpusFolder = "/mnt/heorot-10/Dash/Dash-Corpus/Unittests/"
#buildFolders = {"build2-23-2022_hc95"}

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
			appName = "/".join(x for x in kfPath.split("/")[:-1])+RD.getNativeName(kfPath, kernel=True)
			# if we haven't seen this app before, add an entry to the processed data array
			# this is a new application with a project, if this app isn't getting the project name as its xlabel give it a blank one
			if appName not in appNames:
				appNames[appName] = { "HC": set(), "HL": set(), "PaMul": set() }
				if not newProject:
					xtickLabels.append("")

			if "HotCode" in kfPath:
				appNames[appName]["HC"] = appNames[appName]["HC"].union( RD.Uniquify_static( kfPath, dataMap[kfPath]["Kernels"], trc=True ) )
			elif "HotLoop" in kfPath:
				appNames[appName]["HL"] = appNames[appName]["HL"].union( RD.Uniquify_static( kfPath, dataMap[kfPath]["Kernels"], trc=True ) )
			else:
				appNames[appName]["PaMul"] = appNames[appName]["PaMul"].union( RD.Uniquify_static( kfPath, dataMap[kfPath]["Kernels"], trc=True ) )

	# now that we have all the data sorted, we need to intersect the sets and come up with coverage bars to overlap
	setIntersections = {}
	for kfPath in appNames:
		HCset = appNames[kfPath]["HC"]
		HLset = appNames[kfPath]["HL"]
		PaMulset = appNames[kfPath]["PaMul"]
		setIntersections[kfPath] = { "NonPaMul": { "HCHL": 0.0, "HC": 0.0, "HL": 0.0 }, "PaMul": { "PaMulHC": 0.0, "PaMulHL": 0.0, "PaMul": 0.0, "PaMulHCHL": 0.0 } }
		# john: do this in reverse order bc that saves work
		HC        = HCset - HLset - PaMulset
		HL        = HLset - HCset - PaMulset
		PaMul     = PaMulset - HCset - HLset
		HCHL      = HCset.intersection(HLset) - PaMulset
		PaMulHC   = PaMulset.intersection(HCset) - HLset
		PaMulHL   = PaMulset.intersection(HLset) - HCset
		PaMulHCHL = PaMulset.intersection(HCset).intersection(HLset) 

		# use the above set arithmetic to calculate the PaMul overlap regions (above x-axis) and non-PaMul overlap regions (below x-axis)
		setIntersections[kfPath]["NonPaMul"]["HC"]     = len(HC) / len(PaMulset) if len(PaMulset) > 0 else len(HC)
		setIntersections[kfPath]["NonPaMul"]["HL"]     = len(HL) / len(PaMulset) if len(PaMulset) > 0 else len(HL)
		setIntersections[kfPath]["NonPaMul"]["HCHL"]   = len(HCHL) / len(PaMulset) if len(PaMulset) > 0 else len(HCHL)
		setIntersections[kfPath]["PaMul"]["PaMul"]     = len(PaMul) / len(PaMulset) if len(PaMulset) > 0 else len(PaMul)
		setIntersections[kfPath]["PaMul"]["PaMulHC"]   = len(PaMulHC) / len(PaMulset) if len(PaMulset) > 0 else len(PaMulHC)
		setIntersections[kfPath]["PaMul"]["PaMulHL"]   = len(PaMulHL) / len(PaMulset) if len(PaMulset) > 0 else len(PaMulHL)
		setIntersections[kfPath]["PaMul"]["PaMulHCHL"] = len(PaMulHCHL) / len(PaMulset) if len(PaMulset) > 0 else len(PaMulHCHL)
	print(setIntersections)
	# with the set intersections, we sort the data points into their respective positions
	# the 5 lists below represent the positions: lowest means most negative (highest non-PaMul), highest means most positive (highest PaMul overlap)

	PaMul     = [setIntersections[k]["PaMul"]["PaMul"] for k in setIntersections]
	PaMulHL   = [setIntersections[k]["PaMul"]["PaMulHL"] for k in setIntersections]
	PaMulHC   = [setIntersections[k]["PaMul"]["PaMulHC"] for k in setIntersections]
	PaMulHCHL = [setIntersections[k]["PaMul"]["PaMulHCHL"] for k in setIntersections]
	HC        = [-1*setIntersections[k]["NonPaMul"]["HC"] for k in setIntersections]
	HL        = [-1*setIntersections[k]["NonPaMul"]["HL"] for k in setIntersections]
	HCHL      = [-1*setIntersections[k]["NonPaMul"]["HCHL"] for k in setIntersections]
	#print(len(xtickLabels))
	#print(len(lowest))
	#print(len(secondLowest))
	#print(len(thirdHighest))
	#print(len(secondHighest))
	#print(len(highest))
	#ax.set_aspect("equal")
	ax.set_title("Per Application Block Coverage", fontsize=titleFont)
	ax.bar([x for x in range(len(xtickLabels))], PaMul, label="PaMul")
	ax.bar([x for x in range(len(xtickLabels))], PaMulHL, bottom = PaMul, label="PaMul & HL")
	ax.bar([x for x in range(len(xtickLabels))], PaMulHC, bottom = [PaMul[i]+PaMulHL[i] for i in range(len(PaMul))], label="PaMul & HC")
	ax.bar([x for x in range(len(xtickLabels))], PaMulHCHL, bottom = [PaMul[i]+PaMulHL[i]+PaMulHC[i] for i in range(len(PaMul))], label="PaMul & HL & HC")
	ax.bar([x for x in range(len(xtickLabels))], HC, label="HC")
	ax.bar([x for x in range(len(xtickLabels))], HL, bottom = HC, label="HL")
	ax.bar([x for x in range(len(xtickLabels))], HCHL, bottom = [HC[i]+HL[i] for i in range(len(HC))], label="HC & HL")
	ax.set_ylabel("%", fontsize=axisLabelFont)
	ax.set_xlabel("Application", fontsize=axisLabelFont)
	plt.xticks(ticks=[x for x in range( len(xtickLabels) )], labels=xtickLabels, fontsize=axisFont, rotation=xtickRotation)
	ax.legend()
	RD.PrintFigure(plt, "BasicBlockOverlap")
	plt.show()

dataMap = RD.retrieveKernelData(buildFolders, CorpusFolder, dataFileName, RD.readKernelFile)
refined = RD.refineBlockData(dataMap)
matched = RD.matchData(refined)
PlotCoverageBars(matched)

