import numpy as np
import subprocess

def load_binary(
    path,
	filename,
	dtype,
	header_length,
    fs
	):
    """Loads data from binary file using the numpy function fromfile,
    it assumes that the words in the header are of the
    same bit-length as the numbers in the file and removes 
    the header
    Input:
        path - string
        filename - string
        dtype - should be a numpy dtype duch as 'np.int16' but without(!) quotes
        header_length - number of words in header (same bitlength as data)
    Output:
        data - 1 x #(samples) numpy array containing the data
        """

    current = np.fromfile(filename, dtype=dtype)
    current = current[header_length:]
    tend = len(current)/fs*1000
    time = np.linspace(0,tend,len(current))
    # current = np.vstack([time,current])
    return ["Current (A)"], time, current

def load_axo(path, filename):
    """
    Read axograph data by calling a python2 subprocess that uses the 
    axopgraphio module to read it.
    For now path should be the full path of the directory containinig the
    file.
    Returns data as an array and labels as names and the number of measurements
    and their length.
    """
    module_name = 'importing_axo.py'
    cmd = 'python2 '+module_name+' '+'"'+path+'"'+' '+'"'+filename+'"'
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    out, err = p.communicate()
    
    if err is not None:
        print("Something went wrong while tyring to read the data!")
        print(err)
        #--raise exception here

    result = out.split(b'\n')

    output = []
    i = 0
    while i < len(result):
        output.append(result[i].decode("utf-8"))
        i+=1

    ind = 0 #this should keep track of where in the output list we are
    no_measurements = int(output[ind])
    ind += 1
    measurement_len = int(output[ind])
    ind += 1
    
    names = []
    for i in np.arange(ind,ind+no_measurements):
        names.append(output[i])
        ind += 1

    data = np.zeros((no_measurements,measurement_len))
    for i in range(no_measurements):
        for j in range(measurement_len):
            data[i,j] = float(output[ind])
            ind+=1
    time = data[0]
    current = data[1::3]
    piezo = data[2::3]
    voltage = data[3::3]
    return names, time, current, piezo, voltage