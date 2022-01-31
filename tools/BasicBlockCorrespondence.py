import json
import os
import re
import statistics as st
import matplotlib.pyplot as plt
import matplotlib_venn   as pltv
import RetrieveData as RD

# dataFileName defines the name of the file that will store the data specific to this script (once it is generated)
dataFileName = "BasicBlockCorrespondence_data.json"

# for testing
#CorpusFolder = "/mnt/heorot-10/Dash/Dash-Corpus/Unittests/"

# most recent build
CorpusFolder = "/mnt/heorot-10/Dash/Dash-Corpus/"
buildFolders = { "build1-30-2022_noHLconstraints" }

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
			HC = HC.union( RD.Uniquify(file, dataMap[file]) )
		elif "HotLoop" in file:
			HL = HL.union( RD.Uniquify(file, dataMap[file]) )
		else:
			PaMul = PaMul.union( RD.Uniquify(file, dataMap[file]) )
	pltv.venn3([HC, HL, PaMul], ("HC", "HL", "PaMul"))
	#pltv.legend(["HC","HL","PaMul"])
	"""
	ax.set_aspect("equal")
	ax.set_title("Block Coverage Correlation", fontsize=titleFont)
	ax.set_ylabel("PaMul Blocks", fontsize=axisLabelFont)
	ax.set_xlabel("HotCode Blocks", fontsize=axisLabelFont)
	ax.set_yscale("log")
	ax.set_xscale("log")
	#plt.xticks(ticks=[x for x in range( len(xtickLabels) )], labels=xtickLabels, fontsize=axisFont, rotation=xtickRotation)
	#ax.tick_params(axis='x', colors='white')
	VTicks = [10**0, 10**1, 10**3, 10**2, 10**4]
	plt.yticks(VTicks, fontsize=axisFont)
	HTicks = [10**0, 10**1, 10**3, 10**2, 10**4]
	plt.xticks(HTicks, fontsize=axisFont)
	#ax.set_yticks(VTicks)
	#plt.hlines(VTicks, 0, len(xtickLabels), linestyle="dashed", colors=colors[-1])
	#vLineLocs = []
	#for i in range(len(xtickLabels)):
#		if xtickLabels[i] != "":
#			vLineLocs.append(i)
#	plt.vlines(vLineLocs, VTicks[0], VTicks[-1], linestyle="dashed", colors=colors[-1])
	#ax.yaxis.label.set_color('white')
	#ax.xaxis.label.set_color('white')
	"""
	plt.savefig("BasicBlockCorrespondence.svg",format="svg")
	plt.savefig("BasicBlockCorrespondence.eps",format="eps")
	#plt.savefig("BasicBlockCorrespondence.pdf",format="pdf")
	plt.savefig("BasicBlockCorrespondence.png",format="png")
	plt.show()

dataMap = RD.retrieveKernelData(buildFolders, CorpusFolder, dataFileName, RD.readKernelFile)
refined = RD.refineBlockData(dataMap)
#matched = RD.matchData(refined)
PlotKernelCorrespondence(refined)
