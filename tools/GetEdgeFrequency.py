
import RetrieveData as RD
import argparse

def parseArgs():
	arg_parser = argparse.ArgumentParser()
	arg_parser.add_argument("-p", "--profile", default="markov.bin", help="Input profile file path")
	arg_parser.add_argument("-b", "--blocks", nargs="+", default=[0], help="Input a list of blocks as a white-space-separated list. Each block frequency will be printed.")
	arg_parser.add_argument("-e", "--edges", nargs="+", default=[(0,1)], help="Input a list of edges as a white-space-separated list. Each edge should have syntax src,snk . Each edge frequency will be printed.")
	args = arg_parser.parse_args()
	blocks = []
	for block in args.blocks:
		blocks.append( int(block) )
	args.blocks = blocks
	edges = []
	for edge in args.edges:
		src = int(edge.split(",")[0])
		snk = int(edge.split(",")[1])
		edges.append( (src,snk) )
	args.edges = edges
	return args

args = parseArgs()

eF, bF = RD.readProfile(args.profile)

blockPrints = {}
for b in args.blocks:
	blockPrints[b] = bF.get(b, -1)
print("Blocks:")
print(blockPrints)
print()

edgePrints  = {}
for e in args.edges:
	edgePrints[e] = eF.get(e, -1)
print("Edges:")
print(edgePrints)

