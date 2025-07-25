# ibwpy
Read and write [Igor Pro](https://www.wavemetrics.com/) files (Igor binary wave) with Python

## Installation
### Install with pip (using Git, recommended)
1. Install ibwpy with pip
```bash
$ python -m pip install git+https://github.com/MiLL4U/ibwpy.git
```

### Install with pip (without Git)
1. download a wheel package (*.whl) from [Releases](https://github.com/MiLL4U/ibwpy/releases)

2. Install ibwpy with pip
```bash
$ python -m pip install ibwpy-x.y.z-py3-none-any.whl
```
<span style="color: #FFAAAA">(replace x.y.z with the version of ibwpy which you downloaded)</span>

### Install with git clone
1. Clone this repository

```bash
$ git clone https://github.com/MiLL4U/ibwpy.git
```

2. Go into the repository

```bash
$ cd ibwpy
```

3. Install ibwpy with setup.py

```bash
$ python setup.py install
```

## Examples
### Read
Read wave from ibw file:
```python
import ibwpy as ip
test_wave = ip.load("test_wave.ibw")
print(test_wave)
```

### Make
Make new wave from Numpy array
```python
import numpy as np

arr_1 = np.array([[1., 2., 3.],
                  [1.5, 2.5, 3.5]])
wave_1 = ip.from_nparray(arr_1, 'wave1')
# wave1 (IgorBinaryWave)
# [[1.  2.  3. ]
#  [1.5 2.5 3.5]]
```

### Calculation
Treat wave as NumPy array:
```python
arr_2 = np.ones((2, 3))
print(arr_2)
# [[1. 1. 1.]
#  [1. 1. 1.]]

wave_1 = wave_1 + arr_2
print(wave_1)
# wave1 (IgorBinaryWave)
# [[2.  3.  4. ]
#  [2.5 3.5 4.5]]
```

### Save
Save wave as ibw file
```python
wave_1.save("wave1.ibw")
```