import RetrieveData as RD
import matplotlib.pyplot as plt
import re

# dataFileName defines the name of the file that will store the data specific to this script (once it is generated)
dataFileName = "Recursion_"+"".join(x for x in RD.CorpusFolder.split("/"))+list(RD.buildFolders)[0]+"_data.json"

# set of project names I'm interested in
# if this is empty we take all projects
InterestingProjects = {}

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
           ( 198./255, 195./255, 71./255 , 255./255 ) ]# mustard yellow
markers = [ 'o', '^', '1', 's', '*', 'd', 'X', '>']

def recursiveFunctionRegex(line):
	totalF     = re.findall("\sTOTAL\sFUNCTIONS:\s\d+\s", line)
	totalLiveF = re.findall("\sTOTAL\sLIVE\sFUNCTIONS:\s\d+\s", line)
	IDRF       = re.findall("\sINDIRECT\sRECURSION\sFUNCTIONS:\s\d+\s", line)
	DRF        = re.findall("\sDIRECT\sRECURSION\sFUNCTIONS:\s\d+\s", line)
	if (len(totalF) + len(totalLiveF) + len(IDRF) + len(DRF)) > 1:
		raise Exception("Got many results from a single recursive function regex! TotalF:" +str(totalF)+", totalLiveF:"+str(totalLiveF)+", IDRF: "+str(IDRF)+", DRF: "+str(DRF))
	if len(totalF):
		return totalF[0]
	elif len(totalLiveF):
		return totalLiveF[0]
	elif len(IDRF):
		return IDRF[0]
	elif len(DRF):
		return DRF[0]
	else:
		return ""

def plotRecursionData(dataMap):
	projectMap = {}
	for path in dataMap:
		if len(dataMap[path]) != 8:
			print("Entry "+path+" doesn't have all entries! - "+str(dataMap[path]))
			continue
		pName = RD.getProjectName(path, "Dash-Corpus")
		if projectMap.get(pName) is None:
			projectMap[pName] = { "Static": { "Total": 0, "Live": 0, "IDR": 0, "DR": 0 }, "Dynamic": { "Total": 0, "Live": 0, "IDR": 0, "DR": 0 } }
		# there are two entries of each category ("TOTAL FUNCTIONS", and so on) in a given dataMap[path]
		# the first entry is the static number, the second is the dynamic number
		sTotalFound = False
		sLiveFound = False
		sIDRFound = False
		sDRFound = False
		for entry in dataMap[path]:
			if "TOTAL FUNCTIONS: " in entry:
				num = re.findall("\d+", entry)
				if not len(num):
					raise Exception("Entry "+path+" did not have a number in it! - "+entry)
				if not sTotalFound:
					projectMap[pName]["Static"]["Total"] += int(num[0])
					sTotalFound = True
				else:
					projectMap[pName]["Dynamic"]["Total"] += int(num[0])
			elif "TOTAL LIVE FUNCTIONS: " in entry:
				num = re.findall("\d+", entry)
				if not len(num):
					raise Exception("Entry "+path+" did not have a number in it! - "+entry)
				if not sLiveFound:
					projectMap[pName]["Static"]["Live"] += int(num[0])
					sLiveFound = True
				else:
					projectMap[pName]["Dynamic"]["Live"] += int(num[0])
			elif "INDIRECT RECURSION FUNCTIONS: " in entry:
				num = re.findall("\d+", entry)
				if not len(num):
					raise Exception("Entry "+path+" did not have a number in it! - "+entry)
				if not sIDRFound:
					sIDRFound = True
					projectMap[pName]["Static"]["IDR"] += int(num[0])
				else:
					projectMap[pName]["Dynamic"]["IDR"] += int(num[0])
			elif "DIRECT RECURSION FUNCTIONS: " in entry:
				num = re.findall("\d+", entry)
				if not len(num):
					raise Exception("Entry "+path+" did not have a number in it! - "+entry)
				if not sDRFound:
					projectMap[pName]["Static"]["DR"] += int(num[0])
					sDRFound = True
				else:
					projectMap[pName]["Dynamic"]["DR"] += int(num[0])
			else:
				raise Exception("Found an entry that didn't match any key stats! - " + entry)
	projectMap["Total"] = { "Static": { "Total": 0, "Live": 0, "IDR": 0, "DR": 0 }, "Dynamic": { "Total": 0, "Live": 0, "IDR": 0, "DR": 0 } }
	for entry in projectMap:
		if entry == "Total":
			continue
		projectMap["Total"]["Static"]["Total"] += projectMap[entry]["Static"]["Total"]
		projectMap["Total"]["Static"]["Live"]  += projectMap[entry]["Static"]["Live"]
		projectMap["Total"]["Static"]["IDR"]   += projectMap[entry]["Static"]["IDR"]
		projectMap["Total"]["Static"]["DR"]    += projectMap[entry]["Static"]["DR"]
		projectMap["Total"]["Dynamic"]["Total"] += projectMap[entry]["Dynamic"]["Total"]
		projectMap["Total"]["Dynamic"]["Live"]  += projectMap[entry]["Dynamic"]["Live"]
		projectMap["Total"]["Dynamic"]["IDR"]   += projectMap[entry]["Dynamic"]["IDR"]
		projectMap["Total"]["Dynamic"]["DR"]    += projectMap[entry]["Dynamic"]["DR"]
	print(projectMap)

	xTickLabels = list(projectMap.keys())
	
	fig = plt.figure(frameon=False)
	fig.set_facecolor("black")
	ax = fig.add_subplot(2, 1, 1, frameon=False, fc="black")#, aspect="equal")

	ax.set_title("Recursive Functions")
	# this produces stacked bars, but in the wrong way
	ax.bar( [x for x in range(len(xTickLabels))], [projectMap[y]["Static"]["Total"] for y in projectMap], label="Static-Total", color=colors[0] )
	ax.bar( [x for x in range(len(xTickLabels))], [projectMap[y]["Static"]["Live"] for y in projectMap], label="Static-Live", color=colors[2] )
	ax.bar( [x for x in range(len(xTickLabels))], [projectMap[y]["Static"]["IDR"] for y in projectMap], label="Static-Indirect", color=colors[4] )
	ax.bar( [x for x in range(len(xTickLabels))], [projectMap[y]["Static"]["DR"] for y in projectMap], label="Static-Direct", color=colors[6] )
	ax.set_yscale("log")
	ax.legend(frameon=False)
	plt.xticks(color="white")

	ax = fig.add_subplot(2, 1, 2, frameon=False, fc="black")#, aspect="equal")
	ax.bar( [x for x in range(len(xTickLabels))], [projectMap[y]["Dynamic"]["Total"] for y in projectMap], label="Dynamic-Total", color=colors[1] )
	ax.bar( [x for x in range(len(xTickLabels))], [projectMap[y]["Dynamic"]["Live"] for y in projectMap], label="Dynamic-Live", color=colors[3] )
	ax.bar( [x for x in range(len(xTickLabels))], [projectMap[y]["Dynamic"]["IDR"] for y in projectMap], label="Dynamic-Indirect", color=colors[5] )
	ax.bar( [x for x in range(len(xTickLabels))], [projectMap[y]["Dynamic"]["DR"] for y in projectMap], label="Dynamic-Direct", color=colors[7] )

	ax.set_yscale("log")
	ax.set_ylabel("Count", fontsize=axisFont)
	ax.set_xlabel("Project", fontsize=axisFont)
	plt.xticks(ticks=[x for x in range( len(xTickLabels) )], labels=xTickLabels, fontsize=axisFont, rotation=xtickRotation)
	ax.legend(frameon=False)
	RD.PrintFigure(plt, "RecursionBars")
	plt.show()

dataMap = RD.retrieveLogData(RD.buildFolders, RD.CorpusFolder, dataFileName, recursiveFunctionRegex)
plotRecursionData(dataMap)
