#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 25 11:04:56 2017

@author: dpenguin
"""

import numpy as np
from read_data import *
fn = '170404 015.axgd'
fp = '/home/dpenguin/Documents/work/real data'
bn = 'sim1600.bin'
bp = '/home/dpenguin/Documents/work/Code/detection'
bt = np.int16
bh = 3072

n,d, p = load_axo(fp,fn)
x = load_axo(fp,fn)

y = load_binary(bp,bn,bt,bh)