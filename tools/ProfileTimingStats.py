# Captures the profile times of various builds a different markov_order levels
# Resulting figure is used in the higherordermarkov experiment

import os
import re
import json
import matplotlib
import matplotlib.pyplot as plt

# build folder name that contains profiled times
#BuildNames = [ "buildNativeTiming", "buildMarkovOrder_1", "buildMarkovOrder_2", "buildMarkovOrder_3", "buildMarkovOrder_4", "buildMarkovOrder_5" ] 
BuildNames = [ "buildNativeTiming", "buildMarkovOrder_1", "buildMarkovOrder_2", "buildMarkovOrder_3", "buildMarkvOrder_4" ] 
# maps trace filenames (guaranteed to be unique) to a time they took to execute the profile stage
profileMap = dict()

def plotResults():
	# colors are transparent orange (r,g,b,a) and transparent blue
	colors = [ (50./255, 162./255, 81./255, 127./255), (255./255, 162./255, 0, 127./255) ]

	# sort profileMap by block count (starting block count
	applicationMap = {}
	for project in profileMap:
		for kernel in profileMap[project]:
			applicationMap[kernel] = profileMap[project][kernel]
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

def plotDilationResults():
	colors = [ ( 50./255 , 162./255, 81./255 , 127./255 ),
               ( 255./255, 127./255, 15./255 , 127./255 ),
           	   ( 214./255, 39./255 , 40./255 , 127./255 ),
               ( 121./255, 154./255, 134./255, 127./255 ),
               ( 198./255, 195./255, 71./255 , 127./255 ),
               ( 1.      , 1.      , 1.      , 127./255 ),
               ( 0.8     , 0.8     , 0.8     , 127./255 )]
	markers = [ 'o', '^', '1', 's', '*', 'd', 'X', '>']
	# sort profileMap by block count (starting block count
	applicationMap = {}
	for project in profileMap:
		for log in profileMap[project]:
			applicationMap[log] = profileMap[project][log]
	sortedKeys = sorted( applicationMap, key = lambda log: applicationMap[log][BuildNames[-1]]/applicationMap[log][BuildNames[0]] if applicationMap[log][BuildNames[0]] > 0 else 0 )
	Dilations = []
	for i in range( 1, len(BuildNames) ):
		Dilations.append( [] )
		for log in sortedKeys:
			Dilations[i-1].append( applicationMap[log][BuildNames[i]]/applicationMap[log][BuildNames[0]] if applicationMap[log][BuildNames[0]] > 0 else 0 )

	fig = plt.figure(frameon=False)
	fig.set_facecolor("white")
	ax = fig.add_subplot(1, 1, 1, frameon=False, fc="white")
	for i in range( len(Dilations) ):
		ax.scatter([x for x in range( len(Dilations[i]) )], Dilations[i], color = colors[i], marker = markers[i])
	ax.set_title("Time Dilation")
	ax.set_ylabel("Factor")
	ax.legend(BuildNames[1:], frameon=False)
	ax.tick_params(axis='x', colors='white')
	#ax.yaxis.label.set_color('white')
	ax.xaxis.label.set_color('white')
	#ax.set_xscale("log")
	#ax.set_yscale("log")
	plt.savefig("ProfileTimeDilation.svg",format="svg")
	plt.show()

def findProject(path):
	project = ""
	l = path.split("/")
	for i in range(len(l)):
		if (i+1 < len(l)) and (l[i] == "Dash-Corpus"):
			project = l[i+1]
	return project

def getExecutionTime(log):
	"""
	@param[in] log 		Absolute path to the logfile to be read
	@retval    time		Time of the execution as a float in seconds
	"""
	time  = -1
	error = []
	with open(log,"r") as f:
		try:
			for line in f:
				stuff = re.findall("real\s\d+\.\d+",line)
				error += re.findall("DAStepERROR", line)
				if (len(stuff) == 1) and (time < 0):
					numberString = stuff[0].replace("real ","")
					time = float(numberString)
			if len(error) > 0:
				return -1
			return time
		except:
			return -1

def recurseIntoFolder(path):
	"""
	Steps:
	For the profiled builds
	1.) Find each profile log in the build folder (use its name to index profileMap
	2.) Regex the log for the profile time
	3.) Fill in the relevant category in the kernel map (either profiled or unprofiled time) for that project/profile combo
	Then do the same thing for the unprofiled builds, but make sure that for each new unprofiled entry there is a profiled entry (otherwise this profile did not work with the backend)
	"""
	currentFolder = path.split("/")[-1]
	projectName   = findProject(path)
	if currentFolder in set(BuildNames):
		if profileMap.get(projectName) is None:
			profileMap[projectName] = dict()
		logFiles = []
		logs = path+"/logs/"
		files = os.scandir(logs)
		for f in files:
			if f.name.startswith("makeTrace"):
				logFiles.append(f.path)
		for log in logFiles:
			logFileName = log.split("/")[-1]
			if profileMap[projectName].get(logFileName) is None:
				profileMap[projectName][logFileName] = dict()
			profileMap[projectName][logFileName][currentFolder] = getExecutionTime(log)
		
	directories = []
	for f in os.scandir(path):
		if f.is_dir():
			directories.append(f)

	for d in directories:
		recurseIntoFolder(d.path)

def main():
	recurseIntoFolder(os.getcwd())
	# post processing 
	for project in profileMap:
		toRemove = []
		for file in profileMap[project]:
			if len(profileMap[project][file].keys()) != len(BuildNames):
				toRemove.append(file)
		for item in toRemove:
			profileMap[project].pop(item)
	plotDilationResults()
	with open("ProfileDilationStats.json","w") as f:
		json.dump(profileMap, f, indent=4)

if __name__=="__main__":
    main()

