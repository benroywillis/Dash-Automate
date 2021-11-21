import os
import re
import json
import matplotlib
import matplotlib.pyplot as plt

# build folder name that contains traced times
buildNameTraced = "buildEntropy"
# build folder name that contains the untraced times
buildNameNative = "buildNoTracing"
# maps kernel file names (guaranteed to be unique) to ids to the number of nodes and blocks each have
kernelMap = dict()

def plotResults():
	# colors are transparent orange (r,g,b,a) and transparent blue
	colors = [ (50./255, 162./255, 81./255, 127./255), (255./255, 162./255, 0, 127./255) ]

	# sort kernelMap by block count (starting block count
	applicationMap = {}
	for project in kernelMap:
		for kernel in kernelMap[project]:
			applicationMap[kernel] = kernelMap[project][kernel]
	sortedKeys = sorted( applicationMap, key = lambda kernel: applicationMap[kernel]["Start"]["Nodes"] )
	beforeEntropyRate = []
	afterEntropyRate  = []
	beforeMaxEntropy= []
	afterMaxEntropy= []
	beforeNodes = []
	afterNodes = []
	beforeEdges = []
	afterEdges = []
	for kernel in sortedKeys:
		beforeEntropyRate.append( applicationMap[kernel]["Start"]["Entropy Rate"] )
		afterEntropyRate.append( applicationMap[kernel]["End"]["Entropy Rate"] )
		beforeMaxEntropy.append( applicationMap[kernel]["Start"]["Total Entropy"] )
		afterMaxEntropy.append( applicationMap[kernel]["End"]["Total Entropy"] )
		beforeNodes.append( applicationMap[kernel]["Start"]["Nodes"] )
		afterNodes.append( applicationMap[kernel]["End"]["Nodes"] )
		beforeEdges.append( applicationMap[kernel]["Start"]["Edges"] )
		afterEdges.append( applicationMap[kernel]["End"]["Edges"] )

	# there must be a bug in the edges because some entries before-after actually increases
	for i in range( len(beforeEdges) ):
		if beforeEdges[i] < afterEdges[i]:
			afterEdges[i] = beforeEdges[i]

	# entropy rate
	fig = plt.figure(0, tight_layout=True)
	plt.gca().patch.set_facecolor( (0,0,0) )
	fig.set_facecolor('black')

	#ax = fig.add_subplot(1, 1, 1, fc="black", aspect="equal")
	ax = fig.add_subplot(3, 1, 1, fc="black")
	ax.scatter(beforeNodes, beforeEntropyRate, marker="s", color=colors[0])
	ax.scatter(beforeNodes, afterEntropyRate, marker="^", color=colors[1])
	ax.set_title("Entropy Rate")
	ax.title.set_color('white')
	ax.set_ylabel("Rate")
	ax.yaxis.label.set_color('white')
	ax.tick_params(axis='y', colors='white')
	l = ax.legend(["Before","After"], frameon=False)
	for t in l.get_texts():
		t.set_color("white")
	ax.set_xscale("log")
	ax.set_yscale("log")
	ax.spines["bottom"].set_color("white")
	ax.spines["left"].set_color("white")

	# max entropy rate
	"""
	plt.figure(frameon=False)
	plt.scatter(beforeNodes, beforeMaxEntropy, marker=".")
	plt.scatter(beforeNodes, afterMaxEntropy, marker="x")
	plt.title("Maximum Entropy")
	plt.xlabel("Program Size")
	#plt.xticks([0, 200, 400, 600])
	#plt.xticks([0, 100, 200, 300, 400])
	plt.ylabel("Rate")
	#plt.yticks([0, 0.5, 1.0, 1.5, 2.0])
	plt.legend(["Before","After"], frameon=False)
	plt.xscale("log")
	plt.yscale("log")
	#plt.show()
	"""
	# block count
	#ax = fig.add_subplot(3, 1, 2, fc="black", aspect="equal")
	ax = fig.add_subplot(3, 1, 2, fc="black")
	ax.scatter(beforeNodes, beforeNodes, marker="s", color=colors[0])
	ax.scatter(beforeNodes, afterNodes, marker="^", color=colors[1])
	ax.set_title("States")
	ax.title.set_color('white')
	ax.set_xlabel("Program Size")
	ax.set_ylabel("Nodes")
	ax.yaxis.label.set_color('white')
	ax.tick_params(axis='y', colors='white')
	ax.set_xscale("log")
	ax.set_yscale("log")
	ax.spines["bottom"].set_color("white")
	ax.spines["left"].set_color("white")

	# edge count
	#ax = fig.add_subplot(3, 1, 3, fc="black", aspect="equal")
	ax = fig.add_subplot(3, 1, 3, fc="black")
	ax.scatter(beforeNodes, beforeEdges, marker="s", color=colors[0])
	ax.scatter(beforeNodes, afterEdges, marker="^", color=colors[1])
	ax.set_title("Transitions")
	ax.title.set_color('white')
	ax.set_xlabel("Program Size")
	ax.set_ylabel("Edges")
	plt.xticks([0, 100, 200, 300, 400])
	ax.spines["bottom"].set_color("white")
	ax.spines["left"].set_color("white")
	#ax.spines["right"].set_color("white")
	#ax.spines["top"].set_color("white")
	ax.tick_params(axis='x', colors='white')
	ax.tick_params(axis='y', colors='white')
	ax.yaxis.label.set_color('white')
	ax.xaxis.label.set_color('white')
	ax.set_xscale("log")
	ax.set_yscale("log")
	print(beforeEdges)
	print(afterEdges)
	plt.show()

def plotNodeResults():
	# sort kernelMap by block count (starting block count
	applicationMap = {}
	for project in kernelMap:
		for kernel in kernelMap[project]:
			applicationMap[kernel] = kernelMap[project][kernel]
	sortedKeys = sorted( applicationMap, key = lambda kernel: applicationMap[kernel]["Start"]["Nodes"] )
	beforeEntropyRate = []
	afterEntropyRate  = []
	beforeNodes = []
	afterNodes = []
	beforeEdges = []
	afterEdges = []
	for kernel in sortedKeys:
		beforeEntropyRate.append( applicationMap[kernel]["Start"]["Entropy Rate"] )
		afterEntropyRate.append( applicationMap[kernel]["End"]["Entropy Rate"] )
		beforeNodes.append( applicationMap[kernel]["Start"]["Nodes"] )
		afterNodes.append( applicationMap[kernel]["End"]["Nodes"] )
		beforeEdges.append( applicationMap[kernel]["Start"]["Edges"] )
		afterEdges.append( applicationMap[kernel]["End"]["Edges"] )
	plt.figure(frameon=False)
	plt.scatter([x for x in range( len(beforeEntropyRate) )], beforeEntropyRate)
	plt.scatter([x for x in range( len(afterEntropyRate) )], afterEntropyRate)
	plt.title("Graph Size")
	plt.xlabel("Application")
	plt.ylabel("Nodes")
	plt.legend(["Before","After"])
	plt.show()

def plotEdgeResults():
	# sort kernelMap by block count (starting block count
	applicationMap = {}
	for project in kernelMap:
		for kernel in kernelMap[project]:
			applicationMap[kernel] = kernelMap[project][kernel]
	sortedKeys = sorted( applicationMap, key = lambda kernel: applicationMap[kernel]["Start"]["Nodes"] )
	beforeEntropyRate = []
	afterEntropyRate  = []
	beforeNodes = []
	afterNodes = []
	beforeEdges = []
	afterEdges = []
	for kernel in sortedKeys:
		beforeEdges.append( applicationMap[kernel]["Start"]["Edges"] )
		afterEdges.append( applicationMap[kernel]["End"]["Edges"] )
	plt.figure(frameon=False)
	plt.scatter([x for x in range( len(beforeEntropyRate) )], beforeEntropyRate)
	plt.scatter([x for x in range( len(afterEntropyRate) )], afterEntropyRate)
	plt.title("Edge Change")
	plt.xlabel("Application")
	plt.ylabel("Edges")
	plt.legend(["Before","After"])
	plt.show()

def findProject(path):
	project = ""
	l = path.split("/")
	for i in range(len(l)):
		if (i+1 < len(l)) and (l[i] == "Dash-Corpus"):
			project = l[i+1]
	return project

def recurseIntoFolder(path):
	"""
	Steps:
	For the traced builds
	1.) Find each trace log in the build folder (use its name to index kernelMap
	2.) Regex the log for the trace time
	3.) Fill in the relevant category in the kernel map (either traced or untraced time) for that project/trace combo
	Then do the same thing for the untraced builds, but make sure that for each new untraced entry there is a traced entry (otherwise this trace did not work with the backend)
	"""
	currentFolder = path.split("/")[-1]
	projectName   = findProject(path)
	files = os.scandir(path)
	if currentFolder == buildName:
		if kernelMap.get(projectName) is None:
			kernelMap[projectName] = dict()
		kernelFiles = []
		for f in files:
			if f.name.startswith("kernel_"):
				kernelFiles.append(f.path)
		for kernelFile in kernelFiles:
			kernelFileName = kernelFile.split("/")[-1]
			dic = json.load( open(kernelFile) )
			if dic.get("Entropy") is not None:
				kernelMap[projectName][kernelFileName] = dict()
				for type in dic["Entropy"]:
					kernelMap[projectName][kernelFileName][type] = { "Traced Time": -1, "Untraced Time": -1 }
					if dic["Entropy"][type].get("Total Entropy") is not None:
						kernelMap[projectName][kernelFileName][type]["Total Entropy"] = dic["Entropy"][type]["Total Entropy"]
					if dic["Entropy"][type].get("Untraced Time") is not None:
						kernelMap[projectName][kernelFileName][type]["Untraced Time"] = dic["Entropy"][type]["Entropy Rate"]
		
	directories = []
	for f in files:
		if f.is_dir():
			directories.append(f)

	for d in directories:
		recurseIntoFolder(d.path)

def main():
	recurseIntoFolder(os.getcwd())
	plotResults()
	with open("KernelSizeStats.json","w") as f:
		json.dump(kernelMap, f, indent=4)

if __name__=="__main__":
    main()

