
import json
import RetrieveData as RD

# dataFileName defines the name of the file that will store the data specific to this script (once it is generated)
kernelDataFileName = "Kernels_"+"".join(x for x in RD.CorpusFolder.split("/"))+list(RD.buildFolders)[0]+".json"
instanceDataFileName= "Instance_"+"".join(x for x in RD.CorpusFolder.split("/"))+list(RD.buildFolders)[0]+".json"

# directory map to group like libraries together
DirectoryMap = {
    "GSL_projects_M": "GSL",
    "GSL_projects_L": "GSL",
    "GSL_examples": "GSL",
    #"MiBench": "Benchmarks",
    #"PERFECT": "Benchmarks",
    #"Dhry_and_whetstone": "Benchmarks",
    #"streamit_benchmarks": "Benchmarks",
    "Misc_Benchmarks": "Benchmarks",
    "CortexSuite_cortex": "CortexSuite",
    "CortexSuite_vision": "CortexSuite",
    "Unittests": "Artisan",
    "vdwarfs": "Artisan",
    "Dwarfs": "Artisan",
    "Raytracer": "Artisan",
    "FFTV": "Artisan",
    "MatrixOps": "Artisan",
    "Armadillo_Kernels": "Armadillo",
    "mbed_tls": "mbed_TLS",
    "opencv_projects":"OpenCV",
    "eigen_automate": "Eigen",
    "fec": "FEC",
    "ffmpeg": "FFmpeg"
}

def ParsePaMulKernels(dataMap):
	PaMulData = {}
	for path in dataMap:
		if not isinstance(dataMap[path], dict):
			continue
		if "HotCode" in path:
			continue
		elif "HotLoop" in path:
			continue
		else:
			if dataMap[path].get("Kernels") is not None:
				project = DirectoryMap.get(RD.getProjectName(path, "Dash-Corpus"), RD.getProjectName(path, "Dash-Corpus"))
				if PaMulData.get(project) is None:
					PaMulData[project] = { "Kernels": 0, "Profiles": 0 }
				PaMulData[project]["Profiles"] += 1
				PaMulData[project]["Kernels"]  += len(dataMap[path]["Kernels"])

	PaMulData["Total"] = { "Profiles": 0, "Kernels": 0 }
	for p in PaMulData:
		if p != "Total":
			PaMulData["Total"]["Profiles"] += PaMulData[p]["Profiles"]
			PaMulData["Total"]["Kernels"] += PaMulData[p]["Kernels"]
	return PaMulData

def ParseCombinedKernels(combinedMap):
	RunData = {}
	for path in combinedMap:
		project = DirectoryMap.get(RD.getProjectName(path, "Dash-Corpus"), RD.getProjectName(path, "Dash-Corpus"))
		if RunData.get(project) is None:
			RunData[project] = { "Profiles": 0, "HotCode": 0, "HotLoop": 0, "PaMul": 0, "Instance": 0 }
		RunData[project]["Profiles"] += 1
		RunData[project]["HotCode"] += len(combinedMap[path]["HotCode"])
		RunData[project]["HotLoop"] += len(combinedMap[path]["HotLoop"])
		RunData[project]["PaMul"] += len(combinedMap[path]["PaMul"])
		RunData[project]["Instance"] += len(combinedMap[path]["Instance"])

	RunData["Total"] = { "Profiles": 0, "HotCode": 0, "HotLoop": 0, "PaMul": 0, "Instance": 0 }
	for p in RunData:
		if p != "Total":
			RunData["Total"]["Profiles"] += RunData[p]["Profiles"]
			RunData["Total"]["HotCode"]  += RunData[p]["HotCode"]
			RunData["Total"]["HotLoop"]  += RunData[p]["HotLoop"]
			RunData["Total"]["PaMul"]    += RunData[p]["PaMul"]
			RunData["Total"]["Instance"] += RunData[p]["Instance"]
	return RunData

def PrintCorpusStats(data):
	infoFile = "DirectoryKernelStats_"+list(RD.buildFolders)[0]
	sortedData = {}
	for p in sorted(data):
		sortedData[p] = data[p]
	with open("Data/"+infoFile+".json","w") as f:
		json.dump(sortedData, f, indent=4)

	# print results to csv, latex
	#csvString = "Library,Profiles,Kernels\n"
	csvString = "Library,Profiles,HotCode,HotLoop,PaMul,Instance\n"
	for p in sorted(data):
		csvString  += p+","
		entry = data[p]
		#csvString += str(entry["Profiles"])+","+str(entry["Kernels"])+"\n"
		csvString += str(entry["Profiles"])+","+str(entry["HotCode"])+","+str(entry["HotLoop"])+","+str(entry["PaMul"])+","+str(entry["Instance"])+"\n"
	with open("Data/"+infoFile+".csv","w") as f:
		f.write(csvString)

	latexString = "Library & Applications & Kernels \\\\\n"
	for p in sorted(data):
		latexString += p+" & "
		#latexString += str(data[p]["Profiles"])+" & "+str(data[p]["Kernels"])+" \\\\\n"
		latexString += str(data[p]["Profiles"])+" & "+str(data[p]["PaMul"])+" \\\\\n"
	with open("Data/"+infoFile+".tex","w") as f:
		f.write(latexString)

instanceData = RD.retrieveInstanceData(RD.buildFolders, RD.CorpusFolder, instanceDataFileName, RD.readKernelFile)
kernelData   = RD.retrieveKernelData(RD.buildFolders, RD.CorpusFolder, kernelDataFileName, RD.readKernelFile)
combined     = RD.combineData(kernelData = kernelData, instanceData = instanceData)
#PaMulData = ParsePaMulKernels(kernelData)
printData    = ParseCombinedKernels(combined)
PrintCorpusStats(printData)
