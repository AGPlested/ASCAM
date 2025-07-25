import datetime
from typing import Tuple, Union

from typing_extensions import TypedDict

from .constants import IBWDType


class BinaryHeaderValues(TypedDict):
    formula_size: int
    note_size: int
    data_unit_size: int
    axes_unit_size: Tuple[int, int, int, int]
    axes_label_size: Tuple[int, int, int, int]


class WaveHeaderValues(TypedDict):
    creation_datetime: datetime.datetime
    mod_datetime: datetime.datetime
    dtype: IBWDType
    name: str
    shape: Tuple[int, ...]
    axes_delta: Tuple[float, float, float, float]
    axes_start: Tuple[float, float, float, float]
    data_unit: str
    axes_unit: Tuple[str, str, str, str]
    data_scale: Union[Tuple[float, float], None]


class SectionSizes(TypedDict):
    value_size: int
    formula_size: int
    note_size: int
    ex_data_unit_size: int
    ex_axes_unit_size: Tuple[int, int, int, int]
    axes_label_size: Tuple[int, int, int, int]
