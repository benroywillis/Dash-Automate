import json
import os
import re
import statistics as st
import matplotlib.pyplot as plt
import matplotlib_venn   as pltv
import venn
import RetrieveData as RD

# for testing
#CorpusFolder = "/mnt/heorot-10/Dash/Dash-Corpus/Unittests/"
#buildFolders = { "build_noHLconstraints_hc98" }

# most recent build
CorpusFolder = "/mnt/heorot-10/Dash/Dash-Corpus/"
#buildFolders = { "build1-30-2022_noHLconstraints" }
buildFolders = { "build1-31-2022_noHLconstraints_hc95" }
#buildFolders = { "build_noHLconstraints_hc98" } # started 1-31-22

# dataFileName defines the name of the file that will store the data specific to this script (once it is generated)
dataFileName = "".join(x for x in CorpusFolder.split("/"))+"build_noHLconstraints_hc95_data.json"
loopFileName = "".join(x for x in CorpusFolder.split("/"))+"build_noHLconstraints_hc95_loopdata.json"

# maps build folder names to hotcode, hotloop, pamul
NameMap = { "build2DMarkov": "2DMarkov", "build2DMarkov11-21-21": "2DMarkov", "buildHC": "HC", "buildHC11-21-21": "HC" }

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

def PlotKernelCorrespondence(dataMap):
	fig = plt.figure(frameon=False)
	fig.set_facecolor("white")
	ax = fig.add_subplot(1, 1, 1, frameon=False, fc="white")

	# we need to go through each application and find the overlap of the blocks from the application
	# 1. uniquify the BBIDs across all project,application,blocks sets
	# 2. categorize the hotcode blocks, hot loop blocks and pamul blocks
	# 3. throw these sets into the venn3 call and see what happens

	HC = set()
	HL = set()
	PaMul = set()
	for file in dataMap:
		if "HotCode" in file:
			HC = HC.union( RD.Uniquify(file, dataMap[file]["Kernels"]) )
		elif "HotLoop" in file:
			HL = HL.union( RD.Uniquify(file, dataMap[file]["Kernels"]) )
		else:
			PaMul = PaMul.union( RD.Uniquify(file, dataMap[file]["Kernels"]) )
	print(" HC: {}, HL: {}, PaMul: {} ".format(len(HC), len(HL), len(PaMul), len(Loops)))
	pltv.venn3([HC, HL, PaMul], ("HC", "HL", "PaMul"))
	plt.savefig("BasicBlockCorrespondence.svg",format="svg")
	plt.savefig("BasicBlockCorrespondence.eps",format="eps")
	plt.savefig("BasicBlockCorrespondence.png",format="png")
	plt.show()

def PlotKernelCorrespondence_static(dataMap, loopMap):
	fig = plt.figure(frameon=False)
	fig.set_facecolor("white")
	ax = fig.add_subplot(1, 1, 1, frameon=False, fc="white")

	# we need to go through each application and find the overlap of the blocks from the application
	# 1. uniquify the BBIDs across all project,application,blocks sets
	# 2. categorize the hotcode blocks, hot loop blocks and pamul blocks
	# 3. throw these sets into the venn3 call and see what happens

	HC = set()
	HL = set()
	PaMul = set()
	Loops = set()
	for file in dataMap:
		if "HotCode" in file:
			HC = HC.union( RD.Uniquify_static(file, dataMap[file]["Kernels"], trc=True) )
		elif "HotLoop" in file:
			HL = HL.union( RD.Uniquify_static(file, dataMap[file]["Kernels"], trc=True) )
		else:
			PaMul = PaMul.union( RD.Uniquify_static(file, dataMap[file]["Kernels"], trc=True) )
	for file in loopMap:
		Loops = Loops.union( RD.Uniquify_static(file, loopMap[file]) )
	print(" HC: {}, HL: {}, PaMul: {}, Loops: {} ".format(len(HC), len(HL), len(PaMul), len(Loops)))
	types = { "HotCode": HC, "HotLoop": HL, "PaMul": PaMul, "Loop": Loops }
	venn.venn(types)
	plt.savefig("BasicBlockCorrespondence_static.svg",format="svg")
	plt.savefig("BasicBlockCorrespondence_static.eps",format="eps")
	plt.savefig("BasicBlockCorrespondence_static.png",format="png")
	plt.show()

def ExclusionZones(dataMap, loopMap):
	exclusions = { 
				   "HC": [], \
				   "HC,HL": [], \
				   "HL": []
				 }
	# observe the unique blocks of each data file and create the sets for each segmentation type
	uniqueBlocks = {}
	HC = set()
	HL = set()
	PaMul = set()
	Loops = set()
	for file in dataMap:
		uniqueBlocks[file] = RD.Uniquify(file, dataMap[file])
		if "HotCode" in file:
			HC = HC.union( uniqueBlocks[file] )
		elif "HotLoop" in file:
			HL = HL.union( uniqueBlocks[file] )
		else:
			PaMul = PaMul.union( uniqueBlocks[file] )
	# find files that contribute to the exclusion zones
	# find hotcode blocks that are not in hotloop or pamul
	for file in uniqueBlocks:
		if "HotCode" in file:
			# overlap the blocks here with the PaMul set, if we don't have a complete overlap we have hotblocks not in PaMul
			intersect_p = uniqueBlocks[file].intersection(PaMul)
			intersect_l = uniqueBlocks[file].intersection(HL)
			if (len(intersect_p) < len(uniqueBlocks[file])) and (len(intersect_l) < len(uniqueBlocks[file])):
				exclusions["HC"].append(file)
			else:
				continue
		else:
			continue
	with open("ExclusiveHC.json", "w") as f:
		json.dump(exclusions, f, indent=4)

dataMap = RD.retrieveKernelData(buildFolders, CorpusFolder, dataFileName, RD.readKernelFile)
loopMap = RD.retrieveStaticLoopData(buildFolders, CorpusFolder, loopFileName)
refined = RD.refineBlockData(dataMap)
#matched = RD.matchData(refined)
#PlotKernelCorrespondence(refined, loopMap)
PlotKernelCorrespondence_static(refined, loopMap)
ExclusionZones(dataMap, loopMap)
