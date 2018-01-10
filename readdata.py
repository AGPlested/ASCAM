import numpy as np
import subprocess
from scipy.io import loadmat as scipy_loadmat
from scipy.io.matlab.mio5 import varmats_from_mat

def load_matlab(filename):
    """
    Uses `scipy.io.loadmat` to load data from a `.mat` file.
    Input:
        filename [string] - name (including location) of the file to be loaded
    Output:
        names [list of strings] - names of the different variables
        time [1D array] - times of measurement
        current [list of 1D arrays] - the current recorded from the patch
        piezo [list of 1D arrays] - voltage of the piezo pipette
        commandVoltage [list of 1D arrays] - command voltage applied to the patch
    Because the data we have comes with strange dictionary keys (i.e. including column numbers
    and hex values) the function loops over the keys to extract current, command voltatge, 
    piezo voltage and time.
    """
    current = []
    commandVoltage = []
    piezo = []
    names = ['Time [ms]']
    
    # we use varmats to split up the file into seperate mat files, one for each variable
    # this is necessary for files containing a lot of data (i.e. more that 1000 episode)
    # because the variable names contain 3-digit column numbers
    varmats = varmats_from_mat(open(filename, 'rb'))
    
    for variable in varmats:
        value = scipy_loadmat(variable[1])[variable[0]]
        if 'Ipatch' in variable[0]:
            current.append(value.flatten())
        elif '10Vm' in variable[0]:
            commandVoltage.append(value.flatten())
        elif 'Piezo' in variable[0]:
            piezo.append(value.flatten())
        elif 'Time' in variable[0]:
            time = value.flatten()
    if current:
        names.append('Current [A]')
    if piezo:
        names.append('Piezo [V]')
    if commandVoltage:
        names.append('Command Voltage [V]')
    return names, time, current, piezo, commandVoltage

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
    names = ["Time [ms]", "Current [A]"]
    current = current[np.newaxis]
    return names, time, current

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
    names_to_output = []
    if 'Time (s)' in names:
        names_to_output.append('Time [s]')
    if 'Ipatch (A)' in names:
        names_to_output.append('Current [A]')
    if 'Piezo Com (V)' in names:
        names_to_output.append('Piezo [V]')
    if '10Vm (V)' in names:
        names_to_output.append('Command Voltage [V]')

    data = np.zeros((Nepisodes,measurement_len))
    for i in range(Nepisodes):
        for j in range(measurement_len):
            data[i,j] = float(output[outputindex])
            outputindex+=1
    time = data[0]
    current = data[1::3]
    piezo = data[2::3]
    commandVoltage = data[3::3]

    return names_to_output, time, current, piezo, commandVoltage

def load(filetype, filename, dtype=None, headerlength=None, fs=None):
    if filetype == 'axo':
        return load_axo(filename)
    elif filetype == 'mat':
        return load_matlab(filename)
    elif filetype == 'bin':
        return load_binary(filename,dtype,headerlength,fs)
    else:
        print("Filetype not supported.")
        pass
