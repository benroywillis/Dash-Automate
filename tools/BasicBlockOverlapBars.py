import RetrieveData as RD
import matplotlib.pyplot as plt
import json

# dataFileName defines the name of the file that will store the data specific to this script (once it is generated)
dataFileName = "Kernels_"+"".join(x for x in RD.CorpusFolder.split("/"))+list(RD.buildFolders)[0]+".json"

# set of project names I'm interested in
# if this is empty we take all projects
InterestingProjects = {}

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

def SetIntersections(appNames):
	# we need to go through each application and find the overlap of the blocks from the application
	# 1. for each application, intersect the block sets. This will yield exclusive and overlap regions
	# 2. for regions that overlap with PaMul, sort their magnitudes and make an entry for that application
	# 3. for regions that do not overlap PaMul, sort their magnitudes, flip the sign, and make and entry for that application

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
	return setIntersections

def outputProblemProjects(setIntersections):
	# sort by size of non-PaMul code
	sortedKeys = sorted( setIntersections, key=lambda x: setIntersections[x]["NonPaMul"]["HC"]+setIntersections[x]["NonPaMul"]["HL"]+setIntersections[x]["NonPaMul"]["HCHL"], reverse=True)
	sortedIntersections = {}
	for key in sortedKeys:
		sortedIntersections[key] = setIntersections[key]
	with open("Data/BadPaMulStructureProjects.json", "w") as f:
		json.dump(sortedIntersections, f, indent=4)

def PlotCoverageBars():
	"""
	@brief This function shows a per-application breakdown of what Hotcode, Hotloop and PaMul capture (in terms of basic blocks)
	This figure should be used in conjunction with a Venn diagram showing the overall basic blocks captured by each strategy
	This figure should be color-matched to the Venn diagram
	For places of overlap with PaMul, each strategy should be shown in stacked bars above the x-axis in least-greatest order
	For BBs that do not overlap with PaMul, each strategy should be shown in stacked bars below the x-axis in least-greatest order
	"""
	dataMap = RD.retrieveKernelData(RD.buildFolders, RD.CorpusFolder, dataFileName, RD.readKernelFile)
	refined = RD.refineBlockData(dataMap)
	matched = RD.matchData(refined)
	appMap, xtickLabels = RD.SortAndMap_App(matched, InterestingProjects)
	setIntersections = SetIntersections(appMap)
	outputProblemProjects(setIntersections)

	fig = plt.figure(frameon=False)
	fig.set_facecolor("black")
	ax = fig.add_subplot(1, 1, 1, frameon=False, fc="black")

	# with the set intersections, we sort the data points into their respective positions
	# the 5 lists below represent the positions: lowest means most negative (highest non-PaMul), highest means most positive (highest PaMul overlap)

	PaMul     = [setIntersections[k]["PaMul"]["PaMul"]*100 for k in setIntersections]
	PaMulHL   = [setIntersections[k]["PaMul"]["PaMulHL"]*100 for k in setIntersections]
	PaMulHC   = [setIntersections[k]["PaMul"]["PaMulHC"]*100 for k in setIntersections]
	PaMulHCHL = [setIntersections[k]["PaMul"]["PaMulHCHL"]*100 for k in setIntersections]
	HC        = [-1*setIntersections[k]["NonPaMul"]["HC"]*100 for k in setIntersections]
	HL        = [-1*setIntersections[k]["NonPaMul"]["HL"]*100 for k in setIntersections]
	HCHL      = [-1*setIntersections[k]["NonPaMul"]["HCHL"]*100 for k in setIntersections]

	#ax.set_aspect("equal")
	ax.set_title("Per Application Block Coverage", fontsize=titleFont)
	ax.bar([x for x in range(len(xtickLabels))], PaMulHCHL, label="PaMul & HL & HC", color=colors[0])
	ax.bar([x for x in range(len(xtickLabels))], PaMulHL, bottom = PaMulHCHL, label="PaMul & HL", color=colors[1])
	ax.bar([x for x in range(len(xtickLabels))], PaMulHC, bottom = [PaMulHCHL[i]+PaMulHL[i] for i in range(len(PaMul))], label="PaMul & HC", color=colors[2])
	ax.bar([x for x in range(len(xtickLabels))], PaMul, bottom = [PaMulHCHL[i]+PaMulHL[i]+PaMulHC[i] for i in range(len(PaMul))], label="PaMul", color=colors[3])
	ax.bar([x for x in range(len(xtickLabels))], HC, label="HC", color=colors[4])
	ax.bar([x for x in range(len(xtickLabels))], HL, bottom = HC, label="HL", color=colors[5])
	ax.bar([x for x in range(len(xtickLabels))], HCHL, bottom = [HC[i]+HL[i] for i in range(len(HC))], label="HC & HL", color=colors[6])
	ax.set_ylabel("%", fontsize=axisLabelFont)
	ax.set_xlabel("Application", fontsize=axisLabelFont)
	plt.xticks(ticks=[x for x in range( len(xtickLabels) )], labels=xtickLabels, fontsize=axisFont, rotation=xtickRotation)
	ax.legend(frameon=False)
	RD.PrintFigure(plt, "BasicBlockOverlap")
	plt.show()

def PlotCoverageBars_paper(dataMap):
	"""
	"""
	# maps each application to its overlap categories
	xtickLabels = RD.getProjectAxisLabels(dataMap)
	overlapMap = {}
	for entry in sorted(dataMap):
		overlapMap[entry] = { "HC": 0.0, "HL": 0.0, "Instance": 0.0, "HCHL": 0.0, "HCInstance": 0.0, "HLInstance": 0.0, "HCHLInstance": 0.0 }
		HC    = RD.Uniquify( entry, dataMap[entry]["hotcode"], tn=False )
		HL    = RD.Uniquify( entry, dataMap[entry]["hotloop"], tn=False )
		PaMul = RD.Uniquify( entry, dataMap[entry]["instance"], tn=False )
		Alive = RD.Uniquify( entry, dataMap[entry]["livecode"], tn=False, blocks=True )
		Dead  = RD.Uniquify( entry, dataMap[entry]["deadcode"], tn=False, blocks=True )
		
		HConly    = HC - HL - PaMul
		HLonly    = HL - HC - PaMul
		PaMulonly = PaMul - HC - HL
		HCHL = HC.intersection(HL) - PaMul
		HCPaMul = HC.intersection(PaMul) - HL
		HLPaMul = HL.intersection(PaMul) - HC
		HCHLPaMul = HC.intersection(HL).intersection(PaMul)

		NotHC = HL.union(PaMul) - HC
		HLonlyalive = HL - HC - PaMul - Dead

		# here we construct two datasets for two plots to be viewed in parallel
		# 1. normalized to HC, fraction of HC covered by HL and PaMul, PaMul inclusive is positive, PaMul exclusive is negative
		# +
		overlapMap[entry]["HCHLInstance"] = float(len(HCHLPaMul)) / float(len(HC)) if len(HC) > 0 else 0.0
		overlapMap[entry]["HCInstance"] = float(len(HCPaMul)) / float(len(HC)) if len(HC) > 0 else 0.0
		# -
		overlapMap[entry]["HCHL"] = float(len(HCHL)) / float(len(HC)) if len(HC) > 0 else 0.0
		# 2. normalized to live code, non-hot code structured by pamul and HL, PaMul inclusive positive, PaMul exclusive negative
		# +
		overlapMap[entry]["Instance"] = float(len(PaMulonly)) / float(len(Alive)) if len(Alive) > 0 else 0.0
		overlapMap[entry]["HLInstance"] = float(len(HLPaMul)) / float(len(Alive)) if len(Alive) > 0 else 0.0
		# -
		overlapMap[entry]["HL"] = float(len(HLonlyalive)) / float(len(Alive)) if len(Alive) > 0 else 0.0

	# now categorize each entry in the overlap map by its project
	projectMap = {}
	for entry in overlapMap:
		project = RD.getProjectName(entry, baseName="GSL")
		if projectMap.get(project) is None:
			projectMap[project] = {}
		projectMap[project][entry] = overlapMap[entry]
	
	# then, for a given project, sort each entry by the objective function (PaMulinclusive0 + PaMulinclusive1) / (PaMulexclusive)
	for p in projectMap:
		entries = projectMap[p]
		projectMap[p] = { k: v for k, v in sorted( entries.items(), key = lambda item: \
					    ( item[1]["HCHLInstance"]+item[1]["HCInstance"])/item[1]["HCHL"] if item[1]["HCHL"] > 0.0 else 1.0 ) }
	
	# these codes construct the lists of values for each bar
	# they sort the y axis two ways from greatest to least:
	# 1. by project (implicit in the overlap map)
	# 2. within each project, 
	HCHLPaMul 	= [ value for sublist in \
				  [ [projectMap[p][app]["HCHLInstance"]*100 for app in projectMap[p]] for p in projectMap ] \
					for value in sublist ]
	HCPaMul 	= [ value for sublist in \
				  [ [projectMap[p][app]["HCInstance"]*100 for app in projectMap[p]] for p in projectMap ]
					for value in sublist ]
	HCHL 		= [ -1*value for sublist in \
				  [ [projectMap[p][app]["HCHL"]*100 for app in projectMap[p]] for p in projectMap]
					for value in sublist ]

	PaMul 		= [ value for sublist in \
				  [ [projectMap[p][app]["Instance"]*100 for app in projectMap[p]] for p in projectMap]
					for value in sublist ]
	HLPaMul 	= [ value for sublist in \
				  [ [projectMap[p][app]["HLInstance"]*100 for app in projectMap[p]] for p in projectMap]
					for value in sublist ]
	HL 			= [ -1*value for sublist in \
				  [ [projectMap[p][app]["HL"]*100 for app in projectMap[p]] for p in projectMap]
					for value in sublist ]
	#HCHLPaMul 	= [ overlapMap[entry]["HCHLInstance"]*100 for entry in sorted( overlapMap, key=lambda entry : (overlapMap[entry]["HCHLInstance"]+overlapMap[entry]["HCInstance"])/overlapMap[entry]["HCHL"] if overlapMap[entry]["HCHL"] > 0.0 else 100 ) ]
	#HCPaMul 	= [ overlapMap[entry]["HCInstance"]*100 for entry in sorted( overlapMap, key=lambda entry : (overlapMap[entry]["HCHLInstance"]+overlapMap[entry]["HCInstance"])/overlapMap[entry]["HCHL"] if overlapMap[entry]["HCHL"] > 0.0 else 100 )]
	#HCHL 		= [ -1*overlapMap[entry]["HCHL"]*100 for entry in sorted( overlapMap, key=lambda entry : (overlapMap[entry]["HCHLInstance"]+overlapMap[entry]["HCInstance"])/overlapMap[entry]["HCHL"] if overlapMap[entry]["HCHL"] > 0.0 else 100 )]

	#PaMul 		= [ overlapMap[entry]["Instance"]*100 for entry in sorted( overlapMap, key=lambda entry : (overlapMap[entry]["HCHLInstance"]+overlapMap[entry]["HCInstance"])/overlapMap[entry]["HCHL"] if overlapMap[entry]["HCHL"] > 0.0 else 100 )]
	#HLPaMul 	= [ overlapMap[entry]["HLInstance"]*100 for entry in sorted( overlapMap, key=lambda entry : (overlapMap[entry]["HCHLInstance"]+overlapMap[entry]["HCInstance"])/overlapMap[entry]["HCHL"] if overlapMap[entry]["HCHL"] > 0.0 else 100 )]
	#HL 			= [ -1*overlapMap[entry]["HL"]*100 for entry in sorted( overlapMap, key=lambda entry : (overlapMap[entry]["HCHLInstance"]+overlapMap[entry]["HCInstance"])/overlapMap[entry]["HCHL"] if overlapMap[entry]["HCHL"] > 0.0 else 100 )]

	fig, (ax0, ax1) = plt.subplots(1, 2, sharex=True, sharey=True, frameon=False)
	fig.set_facecolor("black")
	fig.suptitle("Correspondence of Structured Basic Blocks")
	
	ax0.barh( [x for x in range(len(xtickLabels))], HCHLPaMul, label="HC & HL & PaMul", color=colors[0] )
	ax0.barh( [x for x in range(len(xtickLabels))], HCPaMul, left=HCHLPaMul, label="HC & PaMul", color=colors[1] )
	ax0.barh( [x for x in range(len(xtickLabels))], HCHL, label="HC & HL", color=colors[2] )
	ax0.set_xlabel("% (Normalized to hot code)")
	ax0.set_ylabel("Application")
	ax0.legend(frameon=False)

	ax1.barh( [x for x in range(len(xtickLabels))], PaMul, label="PaMul", color=colors[3] )
	ax1.barh( [x for x in range(len(xtickLabels))], HLPaMul, left=PaMul, label="HL & PaMul", color=colors[4] )
	ax1.barh( [x for x in range(len(xtickLabels))], HL, label="HL", color=colors[5] )
	ax1.set_xlabel("% (normalized to live code)")
	ax1.legend(frameon=False)

	plt.yticks(ticks=[x for x in range(len(xtickLabels))], labels=xtickLabels, fontsize=axisFont, rotation=xtickRotation)
	RD.PrintFigure(plt, "BasicBlockOverlap_Horizontal")
	plt.show()

data = RD.RetrieveData(livecode=True, deadcode=True, hotcode=True, hotloop=True, instance=True)
PlotCoverageBars_paper(data)
