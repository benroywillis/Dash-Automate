
import json
import RetrieveData as RD

# dataFileName defines the name of the file that will store the data specific to this script (once it is generated)
dataFileName = "Kernels_"+"".join(x for x in RD.CorpusFolder.split("/"))+list(RD.buildFolders)[0]+".json"

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

def PrintCorpusStats(data):
	sortedData = {}
	for p in sorted(data):
		sortedData[p] = data[p]
	with open("Data/DirectoryKernelStats.json","w") as f:
		json.dump(sortedData, f, indent=4)

	# print results to csv, latex
	csvString = "Library,Profiles,Kernels\n"
	for p in sorted(data):
		csvString  += p+","
		entry = data[p]
		csvString += str(entry["Profiles"])+","+str(entry["Kernels"])+"\n"
	with open("Data/DirectoryKernelStats.csv","w") as f:
		f.write(csvString)

	latexString = "Library & Applications & Kernels \\\\\n"
	for p in sorted(data):
		latexString += p+" & "
		latexString += str(data[p]["Profiles"])+" & "+str(data[p]["Kernels"])+" \\\\\n"
	with open("Data/DirectoryKernelStats.tex","w") as f:
		f.write(latexString)

dataMap = RD.retrieveKernelData(RD.buildFolders, RD.CorpusFolder, dataFileName, RD.readKernelFile)
PaMulData = ParsePaMulKernels(dataMap)
PrintCorpusStats(PaMulData)
