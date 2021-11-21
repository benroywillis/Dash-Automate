
import dashAutomate as dA
import dashDatabase as dDb
import argparse 
import os

def argumentParse():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("-t", "--table", default="Root", help="Specifies the table in the database to be searched. Root by default.")
    arg_parser.add_argument("-c", "--column", default="UID", help="Specifies the column in the table specified by -t to be searched in. If unspecified, this option defaults to the UID column (which is present in all three tables.")
    arg_parser.add_argument("-f", "--find", default="0", help="Specific trait to be searched for. The value of this argument will be looked for in the column from -c in the table from -t.")
    arg_parser.add_argument("-rc", "--return_column", default="UID", help="The query will return this specified column. Default value is UID.")
    arg_parser.add_argument("-r", "--recurse", default="store_true", help="Recurses through tables in the database. If the criteria from the values of -t, -c and -f successfully find matches in the database, the tool will then recurse to the table containing child entries (unless -t is SPADE_x86) and return their results.")
    arg_parser.add_argument("-o", "--output_file", default=None, help="Specifies output file name. If the results of the query are to be stored in a file, this option will enable that feature and name the output file.")
    return arg_parser.parse_args()

def recurseThroughArgs(argsDict):
    if(argsDict['table']=='Root'):
        if(argsDict['find'] is not 0):
            dataList = dash.db.searchDatabase(argsDict['column'], argsDict['table'], argsDict['search_column'], specify=argsDict['find'])
        else:
            dataList = dash.db.searchDatabase(argsDict['column'], argsDict['table'])
        argsDict['table'] = 'Kernel'
    elif(argsDict['table']=='RunIds'):
        dataList = dash.db.searchDatabase(argsDict['column'], argsDict['table'])
        print(dataList)
    elif(argsDict['table']=='Kernel'):
        if(argsDict['find'] is not 0):
            dataList = dash.db.searchDatabase(argsDict['column'], argsDict['table'], argsDict['search_column'], specify=argsDict['find'])
        else:
            dataList = dash.db.searchDatabase(argsDict['column'], argsDict['table'])
        argsDict['table'] = 'SPADE_x86'
    else: 
        return

def main():
    args = argumentParse()
    argsDict = vars(args)
    dash = dA("READ_DATABASE", author="", db = dDb())
    dash.db.databaseInit()

    if(argsDict['find'] is not 0):
        dataList = dash.db.searchDatabase(argsDict['column'], argsDict['table'], argsDict['search_column'], specify=argsDict['find'])
    else:
        dataList = dash.db.searchDatabase(argsDict['column'], argsDict['table'])

    print(dataList)
    if(argsDict['output_file']):
        donothing = True
        # output dataList to a .csv
    
    if(argsDict['recurse']):
        recurseThroughArgs(argsDict)

    return
           
if __name__=='__main__':
    main()





'''
    dataList = dash.db.searchDatabase(argsDict['column'],argsDict['table'])
    print(dataList)
    findData = ""
    for entry in dataList:
        if(entry == int(vars(args)['find'])):
            findData = str(entry)
    print("\nResults for kernel table.")
    dataList = dash.db.searchDatabase('UID', "Kernels", "Parent", specify=findData)
    print(dataList)
    for entry in dataList:
        csvrows = []
        csvrows = dash.db.searchDatabase('*', 'SPADE_x86', 'Parent', specify=str(entry))
        
    print(csvrows)
''' 



