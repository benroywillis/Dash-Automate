import RetrieveData as RD
import re
import json
import matplotlib.pyplot as plt

kernelGrammarFileName   = "KernelGrammar_"+"".join(x for x in RD.CorpusFolder.split("/"))+list(RD.buildFolders)[0]+".json"

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
           ( 198./255, 195./255, 71./255 , 255./255 ), # mustard yellow
           ( 204./255, 153./255, 255./255, 255./255 ), # light violet
           ( 255./255, 178./255, 100./255, 255./255 ) ]# tan
markers = [ 'o', '^', '1', 's', '*', 'd', 'X', '>']

def KGProjectData(dataMap, Dead=True):
	# create stats by project
	projects = {}
	for p in sorted(dataMap):
		projectName = RD.getProjectName(p, "Dash-Corpus")
		if projects.get(projectName) is None:
			projects[projectName] = { "Dead": 0.0, "Live": 0.0, "Kernel": 0.0, "Categorized": 0.0, "Stats": { "StaticInstCount": 0, "DynamicInstCount": 0, "KernelInstCount": 0, "LabeledInstCount": 0 }, "Histogram": {}}
		stats = dataMap[p]
		projects[projectName]["Stats"]["StaticInstCount"]  += stats["StaticInstCount"]
		projects[projectName]["Stats"]["DynamicInstCount"] += stats["DynamicInstCount"]
		projects[projectName]["Stats"]["KernelInstCount"]  += stats["KernelInstCount"]
		projects[projectName]["Stats"]["LabeledInstCount"] += stats["LabeledInstCount"]
		for entry in stats["FunctionHistogram"]:
			if stats["FunctionHistogram"][entry] > 0:
				if projects[projectName]["Histogram"].get(entry) is None:
					projects[projectName]["Histogram"][entry] = 0
			else:
				continue
			projects[projectName]["Histogram"][entry] += stats["FunctionHistogram"][entry]
	for p in projects:
		stats = projects[p]["Stats"]
		if Dead:
			projects[p]["Categorized"] = (float(stats["LabeledInstCount"]) / float(stats["StaticInstCount"])) if stats["StaticInstCount"] > 0.0 else 0.0
			projects[p]["Kernel"]      = ( (float(stats["KernelInstCount"]) / float(stats["StaticInstCount"])) if stats["StaticInstCount"] > 0.0 else 0.0 ) - projects[p]["Categorized"]
			projects[p]["Live"]        = ( (float(stats["DynamicInstCount"]) / float(stats["StaticInstCount"])) if stats["StaticInstCount"] > 0.0 else 0.0 ) - projects[p]["Categorized"] - projects[p]["Kernel"]
			projects[p]["Dead"]        = 1.0 - projects[p]["Live"] - projects[p]["Kernel"] - projects[p]["Categorized"]

		else:
			projects[p]["Categorized"] = (float(stats["LabeledInstCount"]) / float(stats["DynamicInstCount"])) if stats["DynamicInstCount"] > 0.0 else 0.0
			projects[p]["Kernel"]      = ( (float(stats["KernelInstCount"]) / float(stats["DynamicInstCount"])) if stats["DynamicInstCount"] > 0.0 else 0.0 ) - projects[p]["Categorized"]
			projects[p]["Live"]        = (1.0 - projects[p]["Kernel"] - projects[p]["Categorized"]) if stats["DynamicInstCount"] > 0.0 else 0.0

	# output project stats
	with open("Figures/Results_KernelGrammar_"+list(RD.buildFolders)[0]+".json", "w") as f:
		json.dump(projects, f, indent=4)

	return projects

def plotKGCompliance(refined, Dead=True):
	"""
	"""
	fig = plt.figure(frameon=False)
	fig.set_facecolor("black")
	ax = fig.add_subplot(1, 1, 1, frameon=False, fc="black")

	# x axis labels
	xtickLabels = []
	for p in refined:
		xtickLabels.append(p)
	
	if Dead:	
		categories = [ "Categorized", "Kernel", "Live", "Dead" ]
	else:
		categories = [ "Categorized", "Kernel", "Live" ]
		
	i = 0
	for i in range(len(categories)):
		if i == 0:
			ax.bar([p for p in refined], [refined[p][categories[i]] for p in refined], label=categories[i], color=colors[i])
		else:
			barBottom = []
			for p in refined:
				sum = 0
				for k in range(i):
					sum += refined[p][categories[k]]
				barBottom.append( sum )
			ax.bar([p for p in refined], [refined[p][categories[i]] for p in refined], bottom=barBottom, label=categories[i], color=colors[i])
		i += 1
	ax.set_title("Kernel Grammar Compliance")
	ax.set_ylabel("%", fontsize=axisLabelFont)
	ax.set_xlabel("Library", fontsize=axisLabelFont)
	plt.xticks(ticks=[x for x in range( len(xtickLabels) )], labels=xtickLabels, fontsize=axisFont, rotation=xtickRotation)
	ax.legend(frameon=False)
	RD.PrintFigure(plt, "Compliance_KernelGrammar")
	plt.show()

def plotKGHistogram(refined):
	"""
	"""
	fig = plt.figure(frameon=False)
	fig.set_facecolor("black")
	ax = fig.add_subplot(1, 1, 1, frameon=False, fc="black")

	# x axis labels
	xtickLabels = []
	for p in refined:
		xtickLabels.append(p)

	# distill the histogram data by 
	# first collecting all non-zero function op types then 
	# applying that set to all projects and their numbers
	categories = set()
	for p in refined:
		for op in refined[p]["Histogram"]:
			categories.add(op)
	histogram = {}
	for p in refined:
		histogram[p] = {}
		for op in categories:
			histogram[p][op] = 0
			if refined[p]["Histogram"].get(op) is not None:
				histogram[p][op] = refined[p]["Histogram"][op]
	categories = list(categories)
	i = 0
	for i in range(len(categories)):
		i_c = i % len(colors)
		if i == 0:
			ax.bar([p for p in histogram], [histogram[p][categories[i]] for p in histogram], label=categories[i], color=colors[i_c])
		else:
			barBottom = []
			for p in histogram:
				sum = 0
				for k in range(i):
					sum += histogram[p][categories[k]]
				barBottom.append( sum )
			ax.bar([p for p in histogram], [histogram[p][categories[i]] for p in histogram], bottom=barBottom, label=categories[i], color=colors[i_c])
		i += 1
	ax.set_title("Kernel Grammar Functions")
	ax.set_ylabel("Count", fontsize=axisLabelFont)
	ax.set_xlabel("Library", fontsize=axisLabelFont)
	plt.xticks(ticks=[x for x in range( len(xtickLabels) )], labels=xtickLabels, fontsize=axisFont, rotation=xtickRotation)
	ax.legend(frameon=False)
	RD.PrintFigure(plt, "Histogram_KernelGrammar")
	plt.show()

dataMap = RD.retrieveKernelGrammarData(RD.buildFolders, RD.CorpusFolder, kernelGrammarFileName, RD.readKernelGrammarFile)
projects_dead = KGProjectData(dataMap)
projects_live = KGProjectData(dataMap, Dead=False)
plotKGCompliance(projects_dead)
plotKGCompliance(projects_live, Dead=False)
plotKGHistogram(projects_dead)
