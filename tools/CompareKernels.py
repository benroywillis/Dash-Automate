
import json
import argparse

def argumentParse():
	arg_parser = argparse.ArgumentParser()

	arg_parser.add_argument("i", "--input-file", default="kernel.json", help="Input main kernel file path and name")
	arg_parser.add_argument("k", "--kernel-file", default="kernel_.json", help="Kernel file to compare to main kernel file")
	
	args = arg_parser.parse_args()
	return args

args = argumentParse()

kernels_0 = {}
with open(args.input_file, "r") as f:
	j = json.load(f)
	kernels_0 = j["Kernels"]

kernels_1 = {}
with open(args.kernel_file, "r") as f:
	j = json.load(f)
	kernels_1 = j["Kernels"]


