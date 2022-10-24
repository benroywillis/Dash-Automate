import json
import matplotlib.pyplot as plt
import matplotlib_venn   as pltv
import venn
import RetrieveData as RD

# dataFileName defines the name of the file that will store the data specific to this script (once it is generated)
dataFileName = "Instance_"+"".join(x for x in RD.CorpusFolder.split("/"))+list(RD.buildFolders)[0]+".json"
loopFileName = "Loops_"+"".join(x for x in RD.CorpusFolder.split("/"))+list(RD.buildFolders)[0]+".json"

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

dataMap = RD.retrieveInstanceData(RD.buildFolders, RD.CorpusFolder, dataFileName, RD.readKernelFile)
exit(dataMap)
#loopMap = RD.retrieveStaticLoopData(RD.buildFolders, RD.CorpusFolder, loopFileName, RD.readLoopFile)
refined = RD.refineBlockData(dataMap)
matched = RD.matchData(refined)
PlotKernelCorrespondence(matched)
