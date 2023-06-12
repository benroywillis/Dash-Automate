import RetrieveData as RD
import matplotlib.pyplot as plt
import argparse

# parameter reads the maximum exponent recorded in the input histogram

def parse_args():
	arg_parser = argparse.ArgumentParser()
	arg_parser.add_argument("-i", "--input-file", default="hist.csv", help="Specify input csv histogram file")
	args = arg_parser.parse_args()
	return args

def readCSV(args):
	global maxExp
	maxExp = 0
	input = {}
	with open(args.input_file, "r") as f:
		for row in f:
			rowList = row.split(",")
			if rowList[0] == "TaskID":
				# find out how high the exponents go
				maxExp = int(rowList[-1])
				continue
			taskID  = int(rowList[0])
			entries = []
			for i in range(1, len(rowList)):
				entries.append( int(rowList[i]) )
			input[taskID] = entries
	return input

def plotHistogram(input, args):
	for task in input:
		fig = plt.figure(frameon=False)
		ax = fig.add_subplot(1, 1, 1, frameon=False)
		ax.bar([x for x in range(maxExp+1)], input[task])
		ax.set_title("Dynamic Range For Task {}".format(task))
		ax.set_ylabel("Frequency")
		ax.set_xlabel("Magnitude (base 2)")
		appName = args.input_file
		while "/" in appName:
			appName = appName.replace("/","")
		RD.PrintFigure(plt, "DynamicRangeHistogram_Task{}_{}".format(task, appName))
	plt.show()

args = parse_args()
input = readCSV(args)
plotHistogram(input, args)
