#! /usr/bin/python

# To change this template, choose Tools | Templates
# and open the template in the editor.

__author__="Andrew"
__date__ ="$Jan 13, 2012 2:15:32 PM$"
import numpy
import simulator as s
import filter
import scanhistIO

if __name__ == "__main__":
    ints, amps = scanhistIO.load_ints_amps("//users/andrew/ideal.txt", unpack=True)
    
    #convert to ms
    ints = ints/1e3
    #amps are in femtoAmps
    print ints, amps

    cu = s.digitise_sequence(ints, amps, 40000) #sample rate 40kHz
    noisy_cu = s.add_noise(cu, sample_rate, noise_SD, noise_type='1+f2', f0=1000, Verbose=True)
    #add noise here
    filtered_ncu = filter.gaussian_filter_one(noisy_cu, sample_rate, filter_bw=20000)
    print cu

    f=open("//users/andrew/ncint_"+str(g)+".bin", 'w')
    nc_int.tofile(f)
    f.close()
    