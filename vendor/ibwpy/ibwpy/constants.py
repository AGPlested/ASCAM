import datetime

from typing_extensions import Literal

IBWPY_VERSION = "1.0.4"

IBWDType = Literal['float32', 'float64', 'int8', 'int16', 'int32']
DEFAULT_DTYPE: IBWDType = 'float32'

WAVE_HEADER_SIZE = 320

DATETIME_OFFSET = datetime.datetime(1904, 1, 1, 0, 0, 0)
MAX_WAVE_NAME_LENGTH = 31

TEXT_ENCODE = 'utf-8'
TEXT_ENCODE_2ND = 'shift_jis'
DEFAULT_EOL = '\r'
