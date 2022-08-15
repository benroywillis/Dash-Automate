
import re
import json
import argparse

def ArgumentParse():
	arg_parser = argparse.ArgumentParser()

	arg_parser.add_argument("-l", "--log", default="Cartographer.log", help="Cartographer log file with dead code warnings in it")
	arg_parser.add_argument("-e", "--exclusive-regions", default="ExclusiveRegions.json", help="Exclusive regions json file with HL category in it")
	args = arg_parser.parse_args()
	return args

args = ArgumentParse()

# first, dead blocks from the cartographer
deadBlocks = set()
with open(args.log, "r") as f:
	for line in f:
		deadBlock = re.findall("BB\d+\sis\sdead\.", line)
		if len(deadBlock):
			number = re.findall("\d+", deadBlock[0])
			deadBlocks.add( int(number[0]) )

# second, blocks from hotloop exclusive region
HLdeadBlocks = set()
HLregion = {}
with open(args.exclusive_regions,"r") as f:
	j = json.load(f)
	HLregion = set(j["HL"][0][1])

# third, intersect the sets
deadHL = deadBlocks.intersection(HLregion)
deadHL = HLregion.intersection(deadBlocks)
exit(deadHL)

