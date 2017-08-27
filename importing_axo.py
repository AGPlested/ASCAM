### This is a python2.x module that allows axograph data (e.g. .axgd format)
### to be imported into python3.x. This model is used together with 
### `read_data.load_axo`

import axographio, os, sys

if __name__=='__main__':
	filename = sys.argv[1]
	file = axographio.read(filename)
	
	names = file.names
	data = file.data
	
	no_measurements = len(data)
	measurement_length = len(data[0])
	## below is one possble way of gettings the data to python3,
	## it is done using the subprocess module and calling importing_axo.py
	## as a subprocess. The data is passed is aquired by collecting
	## the standardoutput (i.e. print statements)

	print(no_measurements)
	print(measurement_length)
	for i, name in enumerate(names):
		print(name)
	for i in range(no_measurements):
		for j in range(measurement_length):
			print(data[i][j])
		# print('next measurement') #this acts as a seperator when reading the 
		# data in python3
