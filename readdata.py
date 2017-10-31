import numpy as np
import subprocess

def load_binary(filename, dtype, headerlength, fs):
    """Loads data from binary file using the numpy function fromfile,
    it assumes that the words in the header are of the
    same bit-length as the numbers in the file and removes 
    the header
    Input:
        filename - string
        dtype - should be a numpy dtype duch as 'np.int16' but 
                without(!) quotes
        header_length - number of words in header (same bitlength as 
                        data)
    Output:
        data - 1 x #(samples) numpy array containing the data
        """
    headerlength = int(headerlength)
    current = np.fromfile(filename, dtype=dtype)
    current = current[headerlength:]
    tend = len(current)/fs*1000
    time = np.linspace(0,tend,len(current))
    return ["Current (A)"], time, current[np.newaxis]

def load_axo(filename):
    """
    Read axograph data by calling a python2 subprocess that uses the 
    axopgraphio module to read it.
    For now path should be the full path of the directory containinig 
    the file.
    Returns data as an array and labels as names and the number of 
    measurements and their length.
    """
    moduleName = 'importing_axo.py'
    command = 'python2 '+moduleName+' '+'"'+filename+'"'
    python2output = subprocess.Popen(command, shell=True, 
                                     stdout=subprocess.PIPE)
    out, error = python2output.communicate()
    
    if error:
        print("Something went wrong while tyring to read the data!")
        print(err)

    results = out.split(b'\n')
    output = []
    for result in results:
        output.append(result.decode("utf-8"))

    outputindex = 0
    Nepisodes = int(output[outputindex])
    outputindex += 1
    measurement_len = int(output[outputindex])
    outputindex += 1
    
    names = []
    for i in np.arange(outputindex,outputindex+Nepisodes):
        names.append(output[i])
        outputindex += 1

    data = np.zeros((Nepisodes,measurement_len))
    for i in range(Nepisodes):
        for j in range(measurement_len):
            data[i,j] = float(output[outputindex])
            outputindex+=1
    time = data[0]
    current = data[1::3]
    piezo = data[2::3]
    voltage = data[3::3]
    return names, time, current, piezo, voltage

def load(filetype, filename, dtype=None, headerlength=None, fs=None):
    if filetype == 'axo':
         return load_axo(filename)
    elif filetype == 'bin':
        return load_binary(filename,dtype,headerlength,fs)
    else:
        print("Filetype not supported.")
        pass