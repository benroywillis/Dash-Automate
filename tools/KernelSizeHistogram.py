import os
import re
import json
import matplotlib.pyplot as plt

# build folder name that will be targeted in this run
buildName = "build3-04-2021"
# maps kernel file names (guaranteed to be unique) to ids to the number of nodes and blocks each have
kernelMap = dict()

def plotResults():
	# results for all
	l = []
	for size in kernelMap["Histogram"]["All"]["Nodes"]:
		for i in range( kernelMap["Histogram"]["All"]["Nodes"][size] ):
			l.append(size)
	plt.figure(frameon=False)
	plt.hist(l, bins=len(kernelMap["Histogram"]["All"]["Nodes"]))
	plt.title("Kernel Size")
	plt.xlabel("Nodes")
	plt.ylabel("Count")
	plt.yscale("log")
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
			if dic.get("Kernels") is not None:
				kernelMap[projectName][kernelFileName] = dict()
				for id in dic["Kernels"]:
					kernelMap[projectName][kernelFileName][id] = { "Blocks": -1, "Nodes": -1 }
					if dic["Kernels"][id].get("Blocks") is not None:
						kernelMap[projectName][kernelFileName][id]["Blocks"] = len(dic["Kernels"][id]["Blocks"])
					if dic["Kernels"][id].get("Nodes") is not None:
						kernelMap[projectName][kernelFileName][id]["Nodes"]  = len(dic["Kernels"][id]["Nodes"])
		
	directories = []
	for f in files:
		if f.is_dir():
			directories.append(f)

	for d in directories:
		recurseIntoFolder(d.path)

def collectHistogram():
	# calculate histogram stats
	kernelMap["Histogram"] = { "All": { "Blocks": {}, "Nodes": {} } }
	for p in kernelMap:
		if p == "Histogram":
			continue
		if kernelMap["Histogram"].get(p) is None:
			kernelMap["Histogram"][p] = { "Blocks": {}, "Nodes": {} }
		for kf in kernelMap[p]:
			for id in kernelMap[p][kf]:
				blocks= kernelMap[p][kf][id]["Blocks"]
				nodes = kernelMap[p][kf][id]["Nodes"]
				if (blocks != -1) and (nodes != -1):
					# add to All key first
					if kernelMap["Histogram"]["All"]["Blocks"].get(blocks) is None:
						kernelMap["Histogram"]["All"]["Blocks"][blocks] = 0
					kernelMap["Histogram"]["All"]["Blocks"][blocks] += 1
					if kernelMap["Histogram"]["All"]["Nodes"].get(nodes) is None:
						kernelMap["Histogram"]["All"]["Nodes"][nodes] = 0
					kernelMap["Histogram"]["All"]["Nodes"][nodes] += 1
					# next the specific project key
					if kernelMap["Histogram"][p]["Blocks"].get(blocks) is None:
						kernelMap["Histogram"][p]["Blocks"][blocks] = 0
					kernelMap["Histogram"][p]["Blocks"][blocks] += 1
					if kernelMap["Histogram"][p]["Nodes"].get(nodes) is None:
						kernelMap["Histogram"][p]["Nodes"][nodes] = 0
					kernelMap["Histogram"][p]["Nodes"][nodes] += 1

def main():
	recurseIntoFolder(os.getcwd())
	collectHistogram()
	plotResults()
	with open("KernelSizeStats.json","w") as f:
		json.dump(kernelMap, f, indent=4)

if __name__=="__main__":
    main()

