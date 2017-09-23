import axographio, pickle
import numpy as np

def load_file(filename):
	file = axographio.read(filename)
	Nepisodes = len(file.data)
	episodeLength = len(file.data[0])
	return file, Nepisodes, episodeLength

def data_to_stdout(file, Nepisodes, episodeLength):
	"""
	This prints the data to `stdout` which can be read by the subprocess module in python3.
	"""
	print(Nepisodes)
	print(episodeLength)
	for i, name in enumerate(file.names):
		print(name)
	for i in range(Nepisodes):
		for j in range(episodeLength):
			print(file.data[i][j])

def write_to_file(file):
	data = np.asarray(file.data)
	with open("data.txt","wb+") as f:
		pickle.dump(file.data, f)

	# temporaryfile = open("likeDHLfordata.txt","w+")
	# temporaryfile.write(file.data[0])
	# temporaryfile.close()

if __name__=='__main__':
	import sys
	filename = sys.argv[1]
	file, Nepisodes, episodeLength = load_file(filename)
	# write_to_file(file)
	data_to_stdout(file, Nepisodes, episodeLength)