import json
import os
import re
import statistics as st
import matplotlib.pyplot as plt
import matplotlib_venn   as pltv
import RetrieveData as RD

# dataFileName defines the name of the file that will store the data specific to this script (once it is generated)
dataFileName = "BasicBlockCoverage.json"

# for testing
#CorpusFolder = "/home/bwilli46/Dash/Dash-Automate/testing/"
#buildFolders = {"build"}
# for more extensive testing
CorpusFolder = "/mnt/heorot-10/Dash/Dash-Corpus/Unittests/"
buildFolders = {"build1-30-2022_noHLconstraints"}
# most recent build
#CorpusFolder = "/mnt/heorot-10/Dash/Dash-Corpus/"
#buildFolders = {"build1-30-2022_noHLconstraints"}

# maps build folder names to hotcode, hotloop, pamul
NameMap = { "build2DMarkov": "PaMul", "build2DMarkov11-21-21": "PaMul", "buildHC": "HC", "buildHC11-21-21": "HC" }

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

UniqueIDMap = {}
UniqueID = 0

def PlotCoverageBars(dataMap):
	fig = plt.figure(frameon=False)
	fig.set_facecolor("white")
	ax = fig.add_subplot(1, 1, 1, frameon=False, fc="white")

	# we need to go through each application and find the overlap of the blocks from the application
	# 1. uniquify the BBIDs across all project,application,blocks sets
	# 2. categorize the hotcode blocks, hot loop blocks and pamul blocks
	# 3. throw these sets into the venn3 call and see what happens
	sortedKeys = sorted(dataMap)
	HC = list()
	HL = list()
	PaMul = list()
	xtickLabels = list()
	appended = False
	projectNames = set()
	appNames = set()
	for kfPath in sortedKeys:
		appName = RD.getTraceName(kfPath)
		if appName not in appNames:
			appNames.add(appName)
			project = RD.getProjectName(kfPath, "Dash-Corpus")
			if project not in projectNames:
				xtickLabels.append(project)
				projectNames.add(project)
			else:
				xtickLabels.append("")
		if "HotCode" in kfPath:
			HC.append( dataMap[kfPath]*100 )
		elif "HotLoop" in kfPath:
			HL.append( dataMap[kfPath]*100 )
		else:
			PaMul.append( dataMap[kfPath]*100 )
	
	ax.set_aspect("equal")
	ax.set_title("Per Application Block Coverage", fontsize=titleFont)
	ax.bar([x for x in range(len(xtickLabels))], PaMul, label="PaMul")
	ax.bar([x for x in range(len(xtickLabels))], HL, label="Hotloop")
	ax.bar([x for x in range(len(xtickLabels))], HC, label="Hotcode")
	ax.set_ylabel("%", fontsize=axisLabelFont)
	ax.set_xlabel("Application", fontsize=axisLabelFont)
	plt.xticks(ticks=[x for x in range( len(xtickLabels) )], labels=xtickLabels, fontsize=axisFont, rotation=xtickRotation)
	ax.legend()
	#for i in range(len(xtickLabels)):
#		if xtickLabels[i] != "":
#			vLineLocs.append(i)
#	plt.vlines(vLineLocs, VTicks[0], VTicks[-1], linestyle="dashed", colors=colors[-1])
	#ax.yaxis.label.set_color('white')
	#ax.xaxis.label.set_color('white')
	plt.savefig("BasicBlockCoverageBars.svg",format="svg")
	plt.savefig("BasicBlockCoverageBars.eps",format="eps")
	#plt.savefig("BasicBlockCoverageBars.pdf",format="pdf")
	plt.savefig("BasicBlockCoverageBars.png",format="png")
	plt.show()

dataMap = RD.retrieveKernelData(buildFolders, CorpusFolder, dataFileName, RD.readKernelFile_Coverage)
matched = RD.matchData(dataMap)
PlotCoverageBars(matched)
