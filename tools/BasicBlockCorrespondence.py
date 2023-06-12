import json
import matplotlib.pyplot as plt
import matplotlib_venn   as pltv
import venn
import RetrieveData as RD

# set that selects projects we want to be included in the input data
# if this set is empty we select all available projects
InterestingProjects = {}

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

def PlotKernelCorrespondence(dataMap):
	fig = plt.figure(frameon=False)
	fig.set_facecolor("white")
	ax = fig.add_subplot(1, 1, 1, frameon=False, fc="white")

	# we need to go through each application and find the overlap of the blocks from the application
	# 1. uniquify the BBIDs across all project,application,blocks sets
	# 2. categorize the hotcode blocks, hot loop blocks and pamul blocks
	# 3. throw these sets into the venn3 call and see what happens

	HC = set()
	HL = set()
	PaMul = set()
	for file in dataMap:
		HC = HC.union( RD.Uniquify(file, dataMap[file]["hotcode"], tn=False) )
		HL = HL.union( RD.Uniquify(file, dataMap[file]["hotloop"], tn=False) )
		PaMul = PaMul.union( RD.Uniquify(file, dataMap[file]["instance"], tn=False) )
	print(" HC: {}, HL: {}, PaMul: {} ".format(len(HC), len(HL), len(PaMul)))
	v = pltv.venn3([HC, HL, PaMul], ("HC", "HL", "PaMul"))
	RD.PrintFigure(plt, "BasicBlockCorrespondence")
	plt.show()

def PlotKernelCorrespondence_Manual(dataMap):
	zoneMags = { "HC": 0, "HL": 0, "PaMul": 0, "HCHL": 0, "HCPaMul": 0, "HLPaMul": 0, "HCHLPaMul": 0 }
	exclusionRegions = { "HC": [], "HCHL": [] }
	for path in dataMap:
		HC, HL, PaMul, HCHL, HCPaMul, HLPaMul, HCHLPaMul = RD.OverlapRegions(dataMap[path]["HC"], dataMap[path]["HL"], dataMap[path]["PaMul"])
		zoneMags["HC"] += len(HC)
		if len(HC):
			exclusionRegions["HC"].append( [path, list(HC)] )
		zoneMags["HL"] += len(HL)
		zoneMags["PaMul"] += len(PaMul)
		zoneMags["HCHL"] += len(HCHL)
		if len(HCHL):
			exclusionRegions["HCHL"].append( [path, list(HCHL)] )
		zoneMags["HCPaMul"] += len(HCPaMul)
		zoneMags["HLPaMul"] += len(HLPaMul)
		zoneMags["HCHLPaMul"] += len(HCHLPaMul)
	print("Manual correspondence region magnitudes:")
	print(zoneMags)
	with open("Data/ExclusionRegions_"+list(RD.buildFolders)[0]+".json", "w") as f:
		json.dump(exclusionRegions, f, indent=4)

def PlotKernelCorrespondence_static(dataMap, loopMap):
	fig = plt.figure(frameon=False)
	fig.set_facecolor("white")
	ax = fig.add_subplot(1, 1, 1, frameon=False, fc="white")

	# we need to go through each application and find the overlap of the blocks from the application
	# 1. uniquify the BBIDs across all project,application,blocks sets
	# 2. categorize the hotcode blocks, hot loop blocks and pamul blocks
	# 3. throw these sets into the venn3 call and see what happens

	HC = set()
	HL = set()
	PaMul = set()
	Loops = set()
	for file in dataMap:
		if dataMap[file].get("Kernels"):
			if "HotCode" in file:
				HC = HC.union( RD.Uniquify_static(file, dataMap[file]["Kernels"], trc=True) )
			elif "HotLoop" in file:
				HL = HL.union( RD.Uniquify_static(file, dataMap[file]["Kernels"], trc=True) )
			else:
				PaMul = PaMul.union( RD.Uniquify_static(file, dataMap[file]["Kernels"], trc=True) )
	for file in loopMap:
		Loops = Loops.union( RD.Uniquify_static(file, loopMap[file]) )
	print(" HC: {}, HL: {}, PaMul: {}, Loops: {} ".format(len(HC), len(HL), len(PaMul), len(Loops)))
	types = { "HotCode": HC, "HotLoop": HL, "PaMul": PaMul, "Loop": Loops }
	venn.venn(types)
	RD.PrintFigure(plt, "BasicBlockCorrespondence")
	plt.show()

def ExclusionZones(dataMap):
	# observe the unique blocks of each data file and create the sets for each segmentation method
	exclusions = {}
	HC = set()
	HL = set()
	Cyclebite = set()
	Loops = set()
	for file in dataMap:
		HC = HC.union( RD.Uniquify(file, dataMap[file]["hotcode"], tn=False) )
		HL = HL.union( RD.Uniquify(file, dataMap[file]["hotloop"], tn=False) )
		Cyclebite = Cyclebite.union( RD.Uniquify(file, dataMap[file]["pamul"], tn=False) )
	
		exclusions[file] = { "HC": 0, "HL": 0, "Cyclebite": 0, "HCHL": 0, "HCCyclebite": 0, "HLCyclebite": 0, "HCHLCyclebite": 0, "Total": 0 }
		exclusions[file]["HC"] = len( HC - HL - Cyclebite )
		exclusions[file]["HL"] = len( HL - HC - Cyclebite )
		exclusions[file]["Cyclebite"] = len( Cyclebite - HC - HL )
		exclusions[file]["HCHL"] = len( HC.intersection(HL) - Cyclebite )
		exclusions[file]["HCCyclebite"] = len( HC.intersection(Cyclebite) - HL )
		exclusions[file]["HLCyclebite"] = len( HL.intersection(Cyclebite) - HC )
		exclusions[file]["HCHLCyclebite"] = len( HC.intersection(HL).intersection(Cyclebite) )
		exclusions[file]["Total"] = len( HC.union(HL).union(Cyclebite) )

	RD.DumpData(exclusions, "ExclusiveRegions")		

combined = RD.RetrieveData(loop=True, hotcode=True, hotloop=True, pamul=True, instance=True)
#PlotKernelCorrespondence_Manual(combined)
ExclusionZones(combined)
PlotKernelCorrespondence(combined)
