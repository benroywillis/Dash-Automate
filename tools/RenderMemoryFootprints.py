import argparse
import matplotlib.pyplot as plt
import RetrieveData as RD

# plot parameters
axisFont  = 10
axisLabelFont  = 10
titleFont = 16
xtickRotation = 90
barWidth = 0.3
colors = [ ( 50./255 , 162./255, 81./255 , 255./255 ), # leaf green
           ( 255./255, 127./255, 15./255 , 255./255 ), # crimson red
           ( 214./255, 39./255 , 40./255 , 255./255 ), # orange
           ( 121./255, 154./255, 134./255, 255./255 ), # olive green
           ( 190./255, 10./255 , 255./255, 255./255 ), # violet
           ( 180./255, 90./255 , 0.0     , 255./255 ), # brown
           ( 255./255, 10./255 , 140./255, 255./255 ), # hot pink
           ( 198./255, 195./255, 71./255 , 255./255 ), # mustard yellow
           ( 204./255, 153./255, 255./255, 255./255 ) ]# light violet
markers = [ 'o', '^', '1', 's', '*', 'd', 'X', '>']

def readArgs():
	arg_parser = argparse.ArgumentParser()
	arg_parser.add_argument("-i", "--input-csv", default="MemoryFootprints_Hierarchies.csv", help="Input csv file defining memory footprints")
	args = arg_parser.parse_args()
	return args

def PlotMemoryFootprints(input):
	fig = plt.figure(frameon=False)
	ax  = fig.add_subplot(1, 1, 1, frameon=False)

	plotKeys = list(input.keys())
	labelHandles = [] # this contains the first reader and first writer, to render each category exactly once in the legend 
	maxAddr = 0 # used to set the y axis boundaries
	for entry in input:
		for region in input[entry]:
			labelHandles.append
			barHeights = [0] * len(plotKeys)
			barHeights[int(entry)] = region[2]
			barColor = colors[0] if region[0] == "READ" else colors[1]
			width = barWidth if region[0] == "READ" else (-1)*barWidth
			bar = ax.bar(plotKeys, barHeights, bottom=region[1], color=barColor, width=width, align='edge', label=region[0])
			if (len(labelHandles) == 0) and (region[0] == "READ"):
				labelHandles.append( bar )
			elif (len(labelHandles) == 1) and (region[0] == "WRITE"):
				labelHandles.append(bar)
			if region[2] > maxAddr:
				maxAddr = region[2]
	ax.set_title("Code Section Memory Footprints")
	ax.legend(labelHandles, ["READ","WRITE"], frameon=False)
	ax.set_yscale('log')
	ax.set_ylabel("Address")
	#ax.set_ylim([1, maxAddr*100])
	ax.set_xlabel("Code Section Time Slot")
	ax.set_aspect('equal')
	RD.PrintFigure(plt, "MemoryFootprints")
	plt.show()

def ReadCSV(args):
	inputCSV = {}
	with open(args.input_csv, "r") as f:
		for line in f:
			if line.startswith("Hierarchy"):
				# column name line, skip it
				continue
			entries = line.split(",")
			hierarchy = entries[0]
			type      = entries[1]
			start     = int(entries[2])
			end       = int(entries[3])
			if inputCSV.get(hierarchy) is None:
				inputCSV[hierarchy] = []
			inputCSV[hierarchy].append( (type, start, end) )
	return inputCSV

args = readArgs()
input = ReadCSV(args)
PlotMemoryFootprints(input)
