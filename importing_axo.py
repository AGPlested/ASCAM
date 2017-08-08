import axographio
import os
import sys

if __name__=='__main__':
	path = sys.argv[1]
	filename = sys.argv[2]
	os.chdir(path)
	file = axographio.read(filename)
	# print 'done reading files'
	
	names = file.names
	data = file.data
	
	no_measurements = len(data)
	measurement_len = len(data[0])
	## below is one possble way of gettings the data to python3,
	## it is done using the subprocess module and calling importing_axo.py
	## as a subprocess. The data is passed is aquired by collecting
	## the standardoutput (i.e. print statements)

	print(no_measurements)
	print(measurement_len)
	for i, name in enumerate(names):
		print(name)
	for i in range(no_measurements):
		for j in range(measurement_len):
			print(data[i][j])
		# print('next measurement') #this acts as a seperator when reading the data in python3
