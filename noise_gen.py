from __future__ import print_function

__author__="Andrew"
__date__ ="$Oct 17, 2011 3:43:48 PM$"

import numpy
import math
import binning as b         # for testing only

def pink_update (accumulator, pSUM, pA, Nstages):
    """For each new time sample, perform random update to determine 
    the pink noise generator value.
    
    Keyword Arguments:
    accumulator -- the array to update
    pSUM        -- the cumulative probability of each stage getting updated
    pA          -- the amplitudes of the contributions
    Nstages     -- the number of stages  - the length of pSUM and pA
    
    Returns:    The accumulator
    
    """
    
    #A pseudo-random number generator in the range 0.0 to 1.0, 
    #suitable for signal generation.
    ur1 = numpy.random.random()
    for stage in range (Nstages):
      if ur1 <= pSUM[stage]:
         ur2 = numpy.random.random()
         accumulator[stage]=2*(ur2-0.5)*pA[stage]
         break

    return accumulator

def pink(trace_length=10000,Verbose=False):
    """
    Generate Pink noise (1/f) array.
    From http://home.earthlink.net/%7Eltrammell/tech/newpink.htm
    
    Keyword Arguments:
    trace_length    -- the length of the array in samples
    Verbose         -- flag for debugging
    
    Returns:    The accumulator
    
    """    

    #Algorithm with coefficient set to cover 
    #approximately 9 octaves conforming to the "pink" 1/f power distribution. 
    #pP and pA are the amplitude scaling and probability of update parameters.
    #
    #pP   = numpy.array ([  0.00198, 0.01280, 0.04900, 0.17000,  0.68200 ])
    #The pSUM values are obtained by forming a running sum of the terms in the 
    #pP array. The values must sum to less than 1.0 for this algorithm to work. 
    #This is almost cumulative probability distribution.
    #
    #Accumulator array "contrib" 
    #maintains the values currently contributed by each generator stage.
    #Initialize it randomly.
    
    Nstages = 5
    pA   = numpy.array ([  3.8024,  2.9694,  2.5970,  3.0870,   3.4006  ])
    pSUM = numpy.array ([  0.00198, 0.01478, 0.06378, 0.23378,  0.91578 ])
    contrib = numpy.random.random(Nstages)
    
    if Verbose: print (contrib)
    
    pinknoise = numpy.zeros(trace_length)  
    
    for i in range(trace_length):    

        contrib = pink_update (contrib, pSUM, pA, Nstages)
        pinknoise[i] = sum(contrib)

    if Verbose: print (pinknoise)
    
    return pinknoise
    

def oneplusf_gen(spectrum_size=1e6, sample_rate=50000, type='1+f', corner=1000, Verbose=False):
    """
    Generate 1+f or 1+f2 noise spectra.
    After the method of Clements and Bekkers, Biophysical Journal 1997 Vol. 73
    
    Keyword Arguments:
    spectrum_size   -- the length of the spectrum
    type            -- the type of the spectrum to generate 
                        - default:  '1+f'  == 1 + f/f0
                        - also      '1+f2' == 1 + f**2/f0**2
                        - any other value gives white noise for debugging only                    
    sample_rate     -- the desired sample rate for the noise - default 50 kHz
    corner          -- the corner frequency (f0) - default 1kHz
    Verbose         -- flag for debugging
    
    Returns:    The complex spectrum as Numpy array
    
    """ 
    
    #if spectrum_size%2==0:
    #    spectrum_size += 1
        
    if Verbose: 
    #print inspect.getargspec(add_noise)

        print ('oneplusf_gen: arguments')
        loc = locals().keys()
        for n in loc:
            print (n, locals()[n])
    
    #random arrays for real and imaginary parts of spectrum
    real_part = numpy.random.random_sample(spectrum_size) 
    imag_part = numpy.random.random_sample(spectrum_size)
    
    spectrum =  numpy.zeros((spectrum_size), dtype=complex)
    
    #rescale 0 -> 1 into -1 to 1 and slot into spectrum
    spectrum.real = real_part * 2 - 1.
    spectrum.imag = imag_part * 2 - 1.
    
    if Verbose: print (spectrum)
    
    #the lowest representable frequency 
    freq_scale = float(sample_rate)/spectrum_size
    
    frequencies = numpy.arange(spectrum_size)
    freq_scaled = frequencies * freq_scale
    
    if Verbose: print (freq_scale, freq_scaled)
    
    # a bit longer for the sake of speed
    if type == '1+f':
        for i in range (spectrum_size):
            #work in units of Hz
            scaling = (1 + (i * freq_scale) / corner )
            spectrum[i] = spectrum[i] * scaling

    elif type == '1+f2':
        for i in range (spectrum_size):
            #work in units of Hz
            scaling = (1 + (i * freq_scale) ** 2 / corner ** 2)
            spectrum[i] = spectrum[i] * scaling
            
    else:               #return white noise for debugging only
        pass
    
    if Verbose: print ('spectrum',spectrum,'\nMag',numpy.abs(spectrum))

    return freq_scaled, spectrum
        

def norm_spec(spectrum, Verbose=False):
    """Normalize power of spectrum"""

    s = numpy.abs(spectrum)**2
    if Verbose: print (spectrum, s)
    norm_spectrum = spectrum / math.sqrt(numpy.sum(s))

    if Verbose:
        print (norm_spectrum)
        print (numpy.sum(numpy.abs(norm_spectrum)**2))

    return norm_spectrum

def calc_psd (time_series, timestep=5e-5, Normalise=True, Verbose=False):
    """
    Calculate PSD and frequencies.
    With definite hacks.

    Keyword Arguments:
    time_series    -- numpy array to calculate psd
    timestep       -- the sample interval for the array
                      default - 5e-5 or 20 kHz
    Normalise      -- Normalise the power in the spectrum
    Verbose        -- flag for debugging

    Returns:    frequencies and non-scaled power spectral density as arrays

    """
    if Verbose: 
        #print inspect.getargspec(add_noise)
        
        print ('calc_psd: arguments')
        loc = locals().keys()
        for n in loc:
            print (n, locals()[n])
    
    n = time_series.size
    noisefft = numpy.fft.rfft(time_series) / n 
    
    p_s_d = numpy.abs(noisefft) ** 2         #take magnitude

    
    frequency_full = numpy.fft.fftfreq(n, d=timestep)

    #fshifted = numpy.fft.fftshift(freq)

    if Verbose:
        print ('size of freq array', frequency_full.size, 'size of psd', p_s_d.size)
        print (frequency_full, p_s_d)
        half_n = int(n/2)
        print (frequency_full[(half_n - 1):(half_n + 1)])

    #noise is real so slice off negatives except nyquist freq
    freqs = frequency_full[:p_s_d.size]

    #even size input means includes nyquist only included in spectrum as -ve freq
    freqs[-1] = - freqs[-1]

    if Normalise:
        p_s_d = p_s_d / p_s_d.sum()

    return freqs, p_s_d

def spec_to_noise (spectrum, noise_sd=None, Verbose=False):
    """
    Make noise array from scaled complex spectra.

    Keyword Arguments:
    spectrum       -- numpy array to calculate psd
    noise_sd       -- optionally specify the noise standard deviation
    Verbose        -- flag for debugging

    Returns:
    If noise_sd is specified, scaled noise (as in Clements and Bekkers)
    If noise_sd is not specified, simple transform of array

    """
    if Verbose:
        
        print ('spec_to_noise: arguments')
        for n in locals().keys():
            print (n, locals()[n])
    
    if noise_sd != None:
        #Assume scaling wanted
        print ('Scaling....')
        ns = norm_spec(spectrum)
        print (ns, len(ns))
        norm_noise = numpy.fft.irfft(ns)
        if Verbose: print ('norm_noise:',norm_noise)
        noise_array = norm_noise * len(norm_noise)  #because of numpy fft scaling 
        
        if Verbose: print ('Scaling noise array by {} fA '.format(noise_sd))
        noise = noise_array.real * noise_sd
        if Verbose: print ('Noise:', noise)
        return noise

    else:
        
        noise_array = numpy.fft.ifft(spectrum) 
        return noise_array * len(noise_array)


if __name__ == "__main__":
    ### Testing routine

    print ('generating 1 + f spectra')
    f1, s1 = oneplusf_gen(10000, type='1+f', Verbose=True)
    #complex spectrum comes back so normalise and take magnitude
    s1n = norm_spec(s1)
    s1n = abs(s1n)

    print ('generating 1 + f**2 spectra')
    f2, s2 = oneplusf_gen(10000, type='1+f2', Verbose=True)
    s2n = norm_spec(s2)
    s2n = abs(s2n)
    
    z = numpy.column_stack((f1, s1n, f2, s2n))

    f = open('//users/andrew/oneplusf.bin','w')
    z.tofile(f)
    f.close()

    print ('generating binned 1 + f noise spectra')
    fb1,sb1 = b.log_bin_func(f1, s1n, 200)#, Vb=True)  Verbose on for debugging

    print ('generating binned 1 + f**2 noise spectra')
    fb2,sb2 = b.log_bin_func(f2, s2n, 200)#, Vb=True) # Verbose on for debugging

    z = numpy.column_stack((fb1, sb1, fb2, sb2))

    f = open('//users/andrew/oneplusf_log.bin','w')
    z.tofile(f)
    f.close()

    '''
    print ('generating stochastic pink noise')
    pn = ng.pink(10000)

    f = open('//users/andrew/pink.bin','w')
    pn.tofile(f)
    f.close()

    print ('generating pink noise psd')
    f4,s4 = nf.calc_psd(pn,timestep=5e-5,Verbose=True)
    print len(f4),len(s4)
    z = numpy.column_stack((f4,s4))

    f = open('//users/andrew/pink_spec.bin','w')
    z.tofile(f)
    f.close()

    print ('generating binned pink noise psd')
    fb4,sb4 = b.log_bin_func(f4,s4,100,Vb=True) # Verbose on for debugging
    z = numpy.column_stack((fb4,sb4))

    f = open('//users/andrew/pink_spec_log.bin','w')
    z.tofile(f)
    f.close()
    '''