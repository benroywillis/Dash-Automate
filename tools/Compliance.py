import RetrieveData as RD
import re
import json
import matplotlib.pyplot as plt

cartographerFileName    = "Compliance_Cartographer_"+"".join(x for x in RD.CorpusFolder.split("/"))+list(RD.buildFolders)[0]+".json"
memoryPassFileName      = "Compliance_MemoryPass_"+"".join(x for x in RD.CorpusFolder.split("/"))+list(RD.buildFolders)[0]+".json"
kernelGrammarFileName   = "Compliance_KernelGrammar_"+"".join(x for x in RD.CorpusFolder.split("/"))+list(RD.buildFolders)[0]+".json"

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

# this function returns a string with information in it if information is found in the line of the log file
# this information could be confirmation of success, confirmation of error, or a specific error message
def readCartographerLog(line):
	success = re.findall("DAStepSuccess\:\scartographer\scommand\ssucceeded", line)
	if len(success):
		# this means the program went from start to finish without a fatal error
		return "success"
	errors = re.findall("DAStepError\:\scartographer\scommand\sfailed", line)
	if len(errors):
		return "errors"
	exceptions = re.findall("what\(\)\:\s+std\:\:exception", line)
	if len(exceptions):
		return "unhandled exception"
	interrupt = re.findall("Script\sinterrupted\!\sDestroying\stmp\sfolder\.", line)
	if len(interrupt):
		return "interrupt"
	reasons = re.findall("\[critical\]", line)
	if len(reasons):
		return line.split(":")[-1]
	return ""

def readMemoryPassLog(line):
	success = re.findall("DAStepSuccess\:\sMemoryRun\scommand\ssucceeded", line)
	if len(success):
		# this means the program went from start to finish without a fatal error
		return "success"
	errors = re.findall("DAStepError\:\s\w+\scommand\sfailed", line)
	if len(errors):
		return "errors"
	exceptions = re.findall("what\(\)\:\s+std\:\:exception", line)
	if len(exceptions):
		return "unhandled exception"
	interrupt = re.findall("Script\sinterrupted\!\sDestroying\stmp\sfolder\.", line)
	if len(interrupt):
		return "interrupt"
	reasons = re.findall("\[critical\]", line)
	if len(reasons):
		if "/" in line:
			return line.split(":")[-1]
		else:
			return line.split("critical]")[-1]
	return ""

# categories are:
# 1. Compliant: no errors detected
# 2. Inlining Schedule: could not insert a parent after all its inlinable dependencies were scheduled
# 3. Evaluation Time Too Long: more than 12h
# 4. Call-Return Mapping: could not identify where a function returned to in the dynamic profile
# 5. Profile Read Error: could not correctly construct a control flow graph from the input profile file
# 6. Function Subgraph: could not correctly find a function subgraph
# 7. Transform Error: problem with a transform, could be inline transform or cfg transform
# 8. Unknown: unhandled exception
def mapCartographerErrorMessage(error):
	if error.startswith("success"):
		return "Compliant"
	elif error.startswith(" Inlinable embedded function edge"):
		return "Inlining Schedule"
	elif error.startswith("interrupt"):
		return "Evaluation Time Too Long"
	elif error.startswith(" Could not find a matching next edge"):
		return "Static Information Injection"
	elif error.startswith(" Dynamic graph call edge was not confirmed"):
		return "Static Information Injection"
	elif error.startswith(" Outgoing edges do not sum to "):
		return "Static Information Injection"
	elif error.startswith(" This sink node ID is already"):
		return "Profile Read Error"
	elif error.startswith(" Function subgraph BFS exceeded"):
		return "Function Subgraph"
	elif error.startswith(" Node is unreachable"):
		return "Function Subgraph"
	elif error.startswith(" Found a shared function that exits the program"):
		return "Function Subgraph"
	elif error.startswith(" Found a midnode that is not"):
		return "Transform Error"
	elif error.startswith(" Found more than one node"):
		return "Transform Error"
	elif error.startswith("In Progress"):
		return "In Progress"
	else:
		return "Unknown"

def mapMemoryPassErrorMessage(error):
	if error.startswith("success"):
		return "Compliant"
	elif error.startswith(" Kernel entrance sink node intersected"):
		return "Kernel boundary"
	elif error.startswith(" Kernel exit source node intersected"):
		return "Kernel boundary"
	elif error.startswith(" Block was not accounted for in"):
		return "Unknown Block"
	elif error.startswith(" Found a block that has already executed"):
		return "Unknown Block"
	elif error.startswith(" Found multiple nonkernel instances that did not occur"):
		return "Unknown epoch sequence"
	elif error.startswith("In Progress"):
		return "In Progress"
	else:
		return "Unknown"

def sortAutomationLogData(dataMap, type="Cartographer"):
	"""
	"""
	results = {}
	for entry in sorted(dataMap):
		projectName = RD.getProjectName(entry, "Dash-Corpus")
		if results.get(projectName) is None:
			results[projectName] = { "success": 0 }
		if len(dataMap[entry]) == 0:
			dataMap[entry] = ["In Progress"]
		if dataMap[entry][0] == "success":
			results[projectName]["success"] += 1
		else:
			if results[projectName].get(dataMap[entry][0]) is None:
				results[projectName][dataMap[entry][0]] = 1
			else:
				results[projectName][dataMap[entry][0]] += 1

	results["Total"] = { "success": 0 }
	for entry in results:
		if entry != "Total":
			for category in results[entry]:
				if results["Total"].get(category) is None:
					results["Total"][category] = results[entry][category]
				else:
					results["Total"][category] += results[entry][category]
	results["Ignore"] = {}
	results["Ignore"]["Total"] = sum([results["Total"][x] for x in results["Total"]])
	results["Ignore"]["Errors"] = results["Ignore"]["Total"] - results["Total"]["success"] - results["Total"].get("In Progress", 0)
	results["Ignore"]["In Progress"] = results["Total"].get("In Progress", 0)
	results["Ignore"]["Compliance"] = results["Total"]["success"] / ( results["Ignore"]["Total"] - results["Ignore"].get("In Progress", 0) )
	with open("Data/Results_Compliance_"+type+"_"+"".join(x for x in RD.CorpusFolder.split("/"))+list(RD.buildFolders)[0]+".json", "w") as f:
		json.dump(results, f, indent=4)

	return results

def plotCartographerCompliance(results):
	fig = plt.figure(frameon=False)
	fig.set_facecolor("black")
	ax = fig.add_subplot(1, 1, 1, frameon=False, fc="black")

	# x axis labels
	xtickLabels = []
	for p in results:
		if p != "Ignore":
			xtickLabels.append(p)

	mappedResults = {}
	for p in results:
		if p != "Ignore":
			mappedResults[p] = { "Compliant": 0, "Inlining Schedule": 0, "Static Information Injection": 0, "Evaluation Time Too Long": 0, "Call-Return Mapping": 0, "Profile Read Error": 0, "Function Subgraph": 0, "Transform Error": 0, "In Progress": 0, "Unknown": 0 }
			for e in results[p]:
				mappedResults[p][mapCartographerErrorMessage(e)] += results[p][e]
	compliant      = [mappedResults[p]["Compliant"] for p in mappedResults]
	inlineSchedule = [mappedResults[p]["Inlining Schedule"] for p in mappedResults]
	sii            = [mappedResults[p]["Static Information Injection"] for p in mappedResults]
	ettl           = [mappedResults[p]["Evaluation Time Too Long"] for p in mappedResults]
	callReturnMap  = [mappedResults[p]["Call-Return Mapping"] for p in mappedResults]
	profile        = [mappedResults[p]["Profile Read Error"] for p in mappedResults]
	subgraph       = [mappedResults[p]["Function Subgraph"] for p in mappedResults]
	transform      = [mappedResults[p]["Transform Error"] for p in mappedResults]
	inProgress     = [mappedResults[p]["In Progress"] for p in mappedResults]
	unknown        = [mappedResults[p]["Unknown"] for p in mappedResults]

	ax.set_title("Compliance", fontsize=titleFont)
	ax.bar([x for x in range(len(compliant))], compliant, label="Compliant", color=colors[0])
	ax.bar([x for x in range(len(inlineSchedule))], inlineSchedule, bottom=compliant, label="Inlining Schedule", color=colors[1])
	ax.bar([x for x in range(len(ettl))], ettl, bottom=[compliant[i]+inlineSchedule[i] for i in range(len(compliant))], label="Evaluation Time Too Long", color=colors[2])
	ax.bar([x for x in range(len(callReturnMap))], callReturnMap, bottom=[compliant[i]+inlineSchedule[i]+ettl[i] for i in range(len(compliant))], label="Call-Return Mapping", color=colors[3])
	ax.bar([x for x in range(len(profile))], profile, bottom=[compliant[i]+inlineSchedule[i]+ettl[i]+callReturnMap[i] for i in range(len(compliant))], label="Profile Read Error", color=colors[4])
	ax.bar([x for x in range(len(subgraph))], subgraph, bottom=[compliant[i]+inlineSchedule[i]+ettl[i]+callReturnMap[i]+profile[i] for i in range(len(compliant))], label="Function Subgraph", color=colors[5])
	ax.bar([x for x in range(len(transform))], transform, bottom=[compliant[i]+inlineSchedule[i]+ettl[i]+callReturnMap[i]+profile[i]+subgraph[i] for i in range(len(compliant))], label="Transform Error", color=colors[6])
	ax.bar([x for x in range(len(sii))], sii, bottom=[compliant[i]+inlineSchedule[i]+ettl[i]+callReturnMap[i]+profile[i]+subgraph[i]+transform[i] for i in range(len(compliant))], label="Static Information Injection", color=colors[7])
	ax.bar([x for x in range(len(unknown))], inProgress, bottom=[compliant[i]+inlineSchedule[i]+ettl[i]+callReturnMap[i]+profile[i]+subgraph[i]+transform[i]+sii[i] for i in range(len(compliant))], label="InProgress", color=colors[8])
	ax.bar([x for x in range(len(unknown))], unknown, bottom=[compliant[i]+inlineSchedule[i]+ettl[i]+callReturnMap[i]+profile[i]+subgraph[i]+transform[i]+sii[i]+inProgress[i] for i in range(len(compliant))], label="Unknown", color=colors[9])
	ax.set_title("Cartographer Compliance")
	ax.set_ylabel("Count", fontsize=axisLabelFont)
	ax.set_xlabel("Application", fontsize=axisLabelFont)
	plt.xticks(ticks=[x for x in range( len(xtickLabels) )], labels=xtickLabels, fontsize=axisFont, rotation=xtickRotation)
	ax.legend(frameon=False)
	RD.PrintFigure(plt, "Compliance_Cartographer")
	plt.show()

def plotMemoryPassCompliance(results):
	"""
	"""
	fig = plt.figure(frameon=False)
	fig.set_facecolor("black")
	ax = fig.add_subplot(1, 1, 1, frameon=False, fc="black")

	# x axis labels
	xtickLabels = []
	for p in results:
		if p != "Ignore":
			xtickLabels.append(p)

	mappedResults = {}
	categories = { "Compliant": 0, "File Read Error": 0, "Kernel boundary": 0, "Unknown Block": 0, "Unknown epoch sequence": 0, "In Progress": 0, "Unknown": 0 }
	dataLabels = list(categories)
	for p in results:
		if p != "Ignore":
			mappedResults[p] = { "Compliant": 0, "File Read Error": 0, "Kernel boundary": 0, "Unknown Block": 0, "Unknown epoch sequence": 0, "In Progress": 0, "Unknown": 0 }
			for e in results[p]:
				mappedResults[p][mapMemoryPassErrorMessage(e)] += results[p][e]

	i = 0
	for i in range(len(dataLabels)):
		if i == 0:
			ax.bar([p for p in mappedResults], [mappedResults[p][dataLabels[i]] for p in mappedResults], label=dataLabels[i], color=colors[i])
		else:
			barBottom = []
			for p in mappedResults:
				sum = 0
				for k in range(i):
					sum += mappedResults[p][dataLabels[k]]
				barBottom.append( sum )
			ax.bar([p for p in mappedResults], [mappedResults[p][dataLabels[i]] for p in mappedResults], bottom=barBottom, label=dataLabels[i], color=colors[i])
		i += 1
	ax.set_title("Memory Pass Compliance")
	ax.set_ylabel("Count", fontsize=axisLabelFont)
	ax.set_xlabel("Application", fontsize=axisLabelFont)
	plt.xticks(ticks=[x for x in range( len(xtickLabels) )], labels=xtickLabels, fontsize=axisFont, rotation=xtickRotation)
	ax.legend(frameon=False)
	RD.PrintFigure(plt, "Compliance_MemoryPass")
	plt.show()

cartographerMap = RD.retrieveLogData(RD.buildFolders, RD.CorpusFolder, cartographerFileName, readCartographerLog)
memoryPassMap   = RD.retrieveLogData(RD.buildFolders, RD.CorpusFolder, memoryPassFileName, readMemoryPassLog, Prefix="MemoryPass_")
cartographerResults = sortAutomationLogData(cartographerMap)
memoryPassResults   = sortAutomationLogData(memoryPassMap, type="MemoryPass")
plotCartographerCompliance(cartographerResults)
plotMemoryPassCompliance(memoryPassResults)
