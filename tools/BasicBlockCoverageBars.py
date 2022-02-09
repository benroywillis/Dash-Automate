import RetrieveData as RD
import matplotlib.pyplot as plt

# for testing
#CorpusFolder = "/mnt/heorot-10/Dash/Dash-Corpus/Unittests/"
#buildFolders = {"build1-30-2022_noHLconstraints"}

# most recent build
CorpusFolder = "/mnt/heorot-10/Dash/Dash-Corpus/"
#buildFolders = {"build1-30-2022_noHLconstraints"}
buildFolders = {"build2-8-2022_hc95"}

# dataFileName defines the name of the file that will store the data specific to this script (once it is generated)
dataFileName = "Coverage_"+"".join(x for x in CorpusFolder.split("/"))+list(buildFolders)[0]+"_data.json"
loopFileName = "Coverage_"+"".join(x for x in CorpusFolder.split("/"))+list(buildFolders)[0]+"_loop.json"

# set of project names I'm interested in
#InterestingProjects = { "Armadillo","PERFECT","Unittests","FFTV","Artisan","OpenCV" }
InterestingProjects = { "OpenCV" }

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
	projectNames = set()
	appNames = dict()
	for kfPath in sortedKeys:
		project = RD.getProjectName(kfPath, "Dash-Corpus")
		if project not in InterestingProjects:
			continue
		appName = "/".join(x for x in kfPath.split("/")[:-1])+RD.getTraceName(kfPath)
		# if we haven't seen this app before, add a tick
		if appName not in appNames:
			appNames[appName] = { "HC": -1, "HL": -1, "PaMul": -1 }#.add(appName)
			# if the project doesn't yet exist make the tick the project name if project not in projectNames:
			xtickLabels.append(project)
			projectNames.add(project)
			# else make it a blank tick
		else:
			xtickLabels.append("")
		if "HotCode" in kfPath:
			HC.append( dataMap[kfPath]*100 )
			if appNames[appName]["HC"] != -1:
				print("Warning:Already have a hotcode file for {}!".format(kfPath))
				xtickLabels.append("")
			appNames[appName]["HC"] = kfPath
		elif "HotLoop" in kfPath:
			HL.append( dataMap[kfPath]*100 )
			if appNames[appName]["HL"] != -1:
				print("Warning:Already have a hotloop file for {}!".format(kfPath))
				xtickLabels.append("")
			appNames[appName]["HL"] = kfPath
		else:
			PaMul.append( dataMap[kfPath]*100 )
			if appNames[appName]["PaMul"] != -1:
				print("Warning:Already have a pamul file for {}!".format(kfPath))
				xtickLabels.append("")
			appNames[appName]["PaMul"] = kfPath
	
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

def PlotCoverageBarsWithLoops(dataMap, loopMap):
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
	Loops = list()
	xtickLabels = list()
	projectNames = set()
	appNames = dict()
	for kfPath in sortedKeys:
		project = RD.getProjectName(kfPath, "Dash-Corpus")
		if project not in InterestingProjects:
			continue
		# appname is the tracename with its absolute path
		appName = "/".join(x for x in kfPath.split("/")[:-1])+RD.getTraceName(kfPath)
		# ntvName is the backprojected native name of the appName, useful for matching loopfiles to kernel files
#		ntvName = "/".join(x for x in kfPath.split("/")[:-1])+RD.getNativeName(kfPath, kernel=True)
		ntvName = "/".join( x for x in RD.getNativeName(kfPath, kernel=True).split("/")[:-1] )+"/Loops_"+RD.getNativeName(kfPath, kernel=True).split("/")[-1]+".json"
		# if we haven't seen this app before, add a tick
		if appName not in appNames:
			appNames[appName] = { "HC": -1, "HL": -1, "PaMul": -1, "Loop": -1 }#.add(appName)
			# if the project doesn't yet exist make the tick the project name
			if project not in projectNames:
				xtickLabels.append(project)
				projectNames.add(project)
			# else make it a blank tick
			else:
				xtickLabels.append("")
		if "HotCode" in kfPath:
			HC.append( dataMap[kfPath]*100 )
			if appNames[appName]["HC"] != -1:
				print("Warning:Already have a hotcode file for {}!".format(kfPath))
				xtickLabels.append("")
			appNames[appName]["HC"] = kfPath
		elif "HotLoop" in kfPath:
			HL.append( dataMap[kfPath]*100 )
			if appNames[appName]["HL"] != -1:
				print("Warning:Already have a hotloop file for {}!".format(kfPath))
				xtickLabels.append("")
			appNames[appName]["HL"] = kfPath
		else:
			PaMul.append( dataMap[kfPath]*100 )
			if appNames[appName]["PaMul"] != -1:
				print("Warning:Already have a pamul file for {}!".format(kfPath))
				xtickLabels.append("")
			appNames[appName]["PaMul"] = kfPath
		if appNames[appName]["Loop"] == -1:
			Loops.append( loopMap[ntvName]*100 )
			appNames[appName]["Loop"] = ntvName
	sortedLoopKeys = sorted(loopMap)
	
	ax.set_aspect("equal")
	ax.set_title("Per Application Block Coverage", fontsize=titleFont)
	ax.bar([x for x in range(len(xtickLabels))], Loops, label="Loops", color=colors[1])
	ax.bar([x for x in range(len(xtickLabels))], PaMul, label="PaMul", color=colors[3])
	ax.bar([x for x in range(len(xtickLabels))], HL, label="Hotloop", color=colors[0])
	ax.bar([x for x in range(len(xtickLabels))], HC, label="Hotcode", color=colors[2])
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
loopMap = RD.retrieveStaticLoopData(buildFolders, CorpusFolder, loopFileName, RD.readLoopFile_Coverage)
refined = RD.refineBlockData(dataMap)
matched = RD.matchData(refined)
#dataMap = RD.retrieveKernelData(buildFolders, CorpusFolder, dataFileName, RD.readKernelFile_Coverage)
#matched = RD.matchData(dataMap)
#PlotCoverageBars(matched)
PlotCoverageBarsWithLoops(matched, loopMap)
