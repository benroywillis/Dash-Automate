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
# if this is empty we take all projects
InterestingProjects = {}

# plot parameters
axisFont  = 10
axisLabelFont  = 10
titleFont = 16
xtickRotation = 90
colors = [ ( 50./255 , 162./255, 81./255 , 255./255 ),
           ( 255./255, 127./255, 15./255 , 255./255 ),
       	   ( 214./255, 39./255 , 40./255 , 255./255 ),
           ( 121./255, 154./255, 134./255, 255./255 ),
           ( 198./255, 195./255, 71./255 , 255./255 ),
           ( 255./255, 0.0     , 0.0     , 255./255 ),
           ( 0.8     , 255./255, 0.0     , 255./255 ),
           ( 0.0     , 0.0     , 255./255, 255./255 ),]
markers = [ 'o', '^', '1', 's', '*', 'd', 'X', '>']

def PlotCoverageBars(appNames, xtickLabels):
	"""
	@brief This function shows a per-application breakdown of what Hotcode, Hotloop and PaMul capture (in terms of basic blocks)
	This figure should be used in conjunction with a Venn diagram showing the overall basic blocks captured by each strategy
	This figure should be color-matched to the Venn diagram
	For places of overlap with PaMul, each strategy should be shown in stacked bars above the x-axis in least-greatest order
	For BBs that do not overlap with PaMul, each strategy should be shown in stacked bars below the x-axis in least-greatest order
	"""
	fig = plt.figure(frameon=False)
	fig.set_facecolor("black")
	ax = fig.add_subplot(1, 1, 1, frameon=False, fc="black")

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
	ax.legend()
	RD.PrintFigure(plt, "BasicBlockOverlap")
	plt.show()

dataMap = RD.retrieveKernelData(buildFolders, CorpusFolder, dataFileName, RD.readKernelFile)
refined = RD.refineBlockData(dataMap)
matched = RD.matchData(refined)
appMap, xaxis  = RD.SortAndMap_App(matched, InterestingProjects)
PlotCoverageBars(appMap, xaxis)

