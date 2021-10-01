import matplotlib.pyplot as plt
import json
import statistics as st

# root path to where all the TimeMaps will be
rootPath = "/mnt/heorot-10/Dash/Dash-Corpus/"
# global data map
TimeMap = {}

def appendTimeMap(path):
	try:
		with open(rootPath+path+"/TimeMap.json", "r") as f:
			d = json.load(f)
			for key, value in d.items():
				TimeMap[path+"/"+key] = value
	except FileNotFoundError:
		print("Could not find file: "+rootPath+path+"/TimeMap.json. Skipping...")
	except json.decoder.JSONDecodeError:
		print("JSON file not valid: "+rootPath+path+"/TimeMap.json. Skipping...")

def plotDilationResults():
	colors = [ ( 50./255 , 162./255, 81./255 , 127./255 ),
               ( 255./255, 127./255, 15./255 , 127./255 ),
           	   ( 214./255, 39./255 , 40./255 , 127./255 ),
               ( 121./255, 154./255, 134./255, 127./255 ),
               ( 198./255, 195./255, 71./255 , 127./255 ),
               ( 1.      , 1.      , 1.      , 127./255 ),
               ( 0.8     , 0.8     , 0.8     , 127./255 )]
	markers = [ 'o', '^', '1', 's', '*', 'd', 'X', '>']
	# sort TimeMap by block count (starting block count
	applicationMap = {}
	sortedKeys = sorted( TimeMap, key = lambda Name: TimeMap[Name]["Natives"]["Median"] )
	# 2D list of data points, for each entry Profile, FilePrint and 
	Dilations = []
	for i in range( len(sortedKeys) ):
		Dilations.append( [] )
		Dilations[i].append( TimeMap[sortedKeys[i]]["Profiles"]["Median"] )
		Dilations[i].append( TimeMap[sortedKeys[i]]["FilePrints"]["Median"] )
		Dilations[i].append( TimeMap[sortedKeys[i]]["Segmentations"]["Median"] )

	fig = plt.figure(frameon=False)
	fig.set_facecolor("white")
	ax = fig.add_subplot(1, 1, 1, frameon=False, fc="white")
	for i in range( len(Dilations[0]) ):
		ax.scatter([x for x in range( len(Dilations) )], list(zip(*Dilations))[i], color = colors[i], marker = markers[i])
	ax.set_title("Time Dilation")
	ax.set_ylabel("Factor")
	ax.legend(["Profiles","FilePrints","Segmentations"], frameon=False)
	#ax.tick_params(axis='x', colors='white')
	#ax.yaxis.label.set_color('white')
	#ax.xaxis.label.set_color('white')
	#ax.set_xscale("log")
	ax.set_yscale("log")
	plt.savefig("ProfileTimeDilation.svg",format="svg")
	plt.show()

# import timemaps we are interested in
appendTimeMap("Unittests")
appendTimeMap("Dhry_and_whetstone")
appendTimeMap("Armadillo")
appendTimeMap("GSL")
appendTimeMap("CortexSuite")
appendTimeMap("FFmpeg")
appendTimeMap("FEC")
appendTimeMap("FFTV")
# spade 11 armadillo
# spade 10 GSL
# spade 09 artisan
# spade 07 CortexSuite
# spade 06 FFmpeg
# spade 05 FEC
# spade 04 FFTV (log integrity problems)
# spade 03 FFTW
## data processing
# get rid of outliers
for key in TimeMap:
	badIndices = []
	for i in range( len(TimeMap[key]["Natives"]) ):
		if abs(TimeMap[key]["Natives"]["Times"][i]-TimeMap[key]["Natives"]["Mean"]) > 2*TimeMap[key]["Natives"]["stdev"]:
			badIndices.append(i)
			continue
		if abs(TimeMap[key]["Profiles"]["Dilations"][i]-TimeMap[key]["Profiles"]["Mean"]) > 2*TimeMap[key]["Profiles"]["stdev"]:
			badIndices.append(i)
			continue
		if abs(TimeMap[key]["FilePrints"]["Dilations"][i]-TimeMap[key]["FilePrints"]["Mean"]) > 2*TimeMap[key]["FilePrints"]["stdev"]:
			badIndices.append(i)
			continue
		if abs(TimeMap[key]["Segmentations"]["Dilations"][i]-TimeMap[key]["Segmentations"]["Mean"]) > 2*TimeMap[key]["Segmentations"]["stdev"]:
			badIndices.append(i)
			continue
	for i in badIndices:
		del TimeMap[key]["Natives"]["Times"][i]
		TimeMap[key]["Natives"]["Mean"] = st.mean(TimeMap[key]["Natives"]["Times"])
		TimeMap[key]["Natives"]["Mean"] = st.median(TimeMap[key]["Natives"]["Times"])
		TimeMap[key]["Natives"]["Mean"] = st.pstdev(TimeMap[key]["Natives"]["Times"])
		del TimeMap[key]["Profiles"]["Dilations"][i]
		TimeMap[key]["Profiles"]["Mean"] = st.mean(TimeMap[key]["Profiles"]["Dilations"])
		TimeMap[key]["Profiles"]["Mean"] = st.median(TimeMap[key]["Profiles"]["Dilations"])
		TimeMap[key]["Profiles"]["Mean"] = st.pstdev(TimeMap[key]["Profiles"]["Dilations"])
		del TimeMap[key]["FilePrints"]["Dilations"][i]
		TimeMap[key]["FilePrints"]["Mean"] = st.mean(TimeMap[key]["FilePrints"]["Dilations"])
		TimeMap[key]["FilePrints"]["Mean"] = st.median(TimeMap[key]["FilePrints"]["Dilations"])
		TimeMap[key]["FilePrints"]["Mean"] = st.pstdev(TimeMap[key]["FilePrints"]["Dilations"])
		del TimeMap[key]["Segmentations"]["Dilations"][i]
		TimeMap[key]["Segmentations"]["Mean"] = st.mean(TimeMap[key]["Segmentations"]["Dilations"])
		TimeMap[key]["Segmentations"]["Mean"] = st.median(TimeMap[key]["Segmentations"]["Dilations"])
		TimeMap[key]["Segmentations"]["Mean"] = st.pstdev(TimeMap[key]["Segmentations"]["Dilations"])
#with open("TimeMap_Processed.json","w") as f:
#	json.dump(TimeMap, f, indent=4)

# plot
plotDilationResults()
