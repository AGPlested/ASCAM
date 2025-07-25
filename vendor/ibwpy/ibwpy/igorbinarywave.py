from __future__ import annotations

import datetime
import re
import struct
from copy import deepcopy
from functools import reduce
from typing import List, Optional, Tuple, Union

import numpy as np

from .commonfunc import decode_unicode
from .constants import DEFAULT_EOL, TEXT_ENCODE, WAVE_HEADER_SIZE
from .waveheader import BinaryWaveHeader5, BinaryWaveHeader5Loader


class BinaryWave5:
    def __init__(self,
                 ibw_header: BinaryWaveHeader5,
                 wave_values: np.ndarray,
                 data_unit: str = '',
                 axes_unit: Optional[List[str]] = None,
                 dependency_formula: str = '',
                 note: str = '',
                 # axes_label: List[List[str]] = None,
                 ) -> None:
        self.__header = ibw_header
        if self.__header.dtype != wave_values.dtype:
            raise TypeError(
                'Data type of wave_values ({})'
                'does not match with ibw_header ({})'
                .format(wave_values.dtype, self.__header.dtype))
        self.__values = wave_values
        self.__data_unit = data_unit
        self.__axes_unit = axes_unit if axes_unit \
            else ['' for _ in range(wave_values.ndim)]

        dependency_formula = self.__convert_eol(dependency_formula)
        self.__dependency_formula = dependency_formula
        self.__header.formula_size = self.formula_size

        note = self.__convert_eol(note)
        self.__note = note
        self.__header.note_size = self.note_size

    def __update_modify_time(self):
        self.__header.update_modify_time()

    def __str__(self) -> str:
        name = '{} (IgorBinaryWave)\n'.format(self.name)
        return name + str(self.__values)

    def __add__(self, other: Union[BinaryWave5, np.ndarray, int, float,
                                   List[int], List[float]]) -> BinaryWave5:
        if isinstance(other, BinaryWave5):
            other = other.__values
        res_array = self.array + other
        res = deepcopy(self)
        res.__values = res_array

        res.__update_dtype()
        res.__update_modify_time()
        return res

    def __sub__(self, other: Union[BinaryWave5, np.ndarray, int, float,
                                   List[int], List[float]]) -> BinaryWave5:
        if isinstance(other, BinaryWave5):
            other = other.__values
        res_array = self.array - other
        res = deepcopy(self)
        res.__values = res_array

        res.__update_dtype()
        res.__update_modify_time()
        return res

    def __mul__(self, other: Union[BinaryWave5, np.ndarray, int, float,
                                   List[int], List[float]]) -> BinaryWave5:
        if isinstance(other, BinaryWave5):
            other = other.__values
        res_array = self.array * other
        res = deepcopy(self)
        res.__values = res_array

        res.__update_dtype()
        res.__update_modify_time()
        return res

    def __truediv__(self, other: Union[BinaryWave5, np.ndarray, int, float,
                                       List[int], List[float]]) -> BinaryWave5:
        if isinstance(other, BinaryWave5):
            other = other.__values
        res_array = self.array / other
        res = deepcopy(self)
        res.__values = res_array

        res.__update_dtype()
        res.__update_modify_time()
        return res

    def __len__(self) -> int:
        return len(self.__values)

    def __getitem__(self, key) -> np.ndarray:
        return self.__values[key]

    def __setitem__(self, key, value) -> BinaryWave5:
        res = self.__values.copy()
        res[key] = value
        self.__values = res

        self.__update_dtype()
        self.__update_modify_time()
        return self

    @property
    def name(self) -> str:
        return self.__header.name

    def rename(self, name: str) -> BinaryWave5:
        self.__header.rename(name)

        self.__update_modify_time()
        return self

    @property
    def shape(self) -> Tuple[int, ...]:
        return self.__header.shape

    def reshape(self, shape: Union[List[int], Tuple[int, ...]]) -> BinaryWave5:
        shape_tuple = tuple(shape)
        self.__header.reshape(shape_tuple)
        self.__values = self.__values.reshape(shape_tuple)

        # following informations will initialized
        self.__axes_unit = ['' for i in range(self.__values.ndim)]
        # TODO: support dimension label
        """
        self.__axes_label = ...
        """

        self.__update_modify_time()
        return self

    @property
    def dtype(self) -> str:
        return self.__header.dtype

    def __update_dtype(self) -> BinaryWave5:
        self.__header.set_dtype(str(self.__values.dtype))
        return self

    def change_dtype(self, dtype: str) -> BinaryWave5:
        if not self.__header.is_valid_dtype(dtype):
            raise TypeError("invalid data type")
        self.__values = self.__values.astype(dtype)

        self.__update_dtype()
        self.__update_modify_time()
        return self

    @property
    def array(self) -> np.ndarray:
        return self.__values

    def set_values(self,
                   values: Union[np.ndarray, BinaryWave5, int, float]
                   ) -> BinaryWave5:
        if isinstance(values, BinaryWave5):
            set_values = values.array
        elif isinstance(values, np.ndarray):
            set_values = values
        elif isinstance(values, (int, float)):
            set_values = np.full(self.shape, values)
        else:
            raise TypeError('IgorBinaryWave or NumPy array is required')
        if set_values.shape != tuple(self.shape):
            raise ValueError('shape of array does not match to original shape')
        self.__values = set_values

        self.__update_dtype()
        self.__update_modify_time()
        return self

    @property
    def ndim(self) -> int:
        return self.__header.ndim

    @property
    def dependency_formula(self) -> str:
        return self.__dependency_formula

    @property
    def formula_buf(self) -> bytes:
        return bytes(self.__dependency_formula, encoding=TEXT_ENCODE)

    @property
    def formula_size(self) -> int:
        return len(self.formula_buf)

    def __convert_eol(self, string, to=DEFAULT_EOL):
        return re.sub(r'\r\n|\r|\n', to, string)

    def set_dependency_formula(self, formula: str) -> BinaryWave5:
        if not isinstance(formula, str):
            raise TypeError('a string is required')
        formula = self.__convert_eol(formula)
        self.__dependency_formula = formula
        self.__header.formula_size = self.formula_size

        self.__update_modify_time()
        return self

    @property
    def data_unit(self) -> str:
        return self.__data_unit

    def set_data_unit(self, unit: str) -> BinaryWave5:
        if not isinstance(unit, str):
            raise TypeError('a string is required as unit')

        self.__header.set_data_unit(unit)
        self.__data_unit = unit

        self.__update_modify_time()
        return self

    @property
    def axes_unit(self) -> Tuple[str, ...]:
        return tuple(self.__axes_unit)

    def set_axis_unit(self, axis_index: int, unit: str) -> BinaryWave5:
        if not isinstance(unit, str):
            raise TypeError('a string is required as unit')

        self.__header.set_axis_unit(axis_index, unit)
        self.__axes_unit[axis_index] = unit

        self.__update_modify_time()
        return self

    def set_axis_scale(self, axis_index: int,
                       start: Union[float, int],
                       delta: Union[float, int]) -> BinaryWave5:
        start = float(start)
        delta = float(delta)
        self.__header.set_axis_scale(axis_index, start, delta)

        self.__update_modify_time()
        return self

    def axis_scale(self, axis_index: int) -> Tuple[float, float]:
        return self.__header.axis_scale(axis_index)

    def calculated_axis_wave(self, axis_index: int) -> np.ndarray:
        return self.__header.calculated_axis_wave(axis_index)

    @property
    def data_scale(self) -> Union[Tuple[float, float], None]:
        return self.__header.data_scale

    def set_data_scale(self,
                       max_: Union[float, int],
                       min_: Union[float, int]) -> BinaryWave5:
        max_ = float(max_)
        min_ = float(min_)
        self.__header.set_data_scale(max_, min_)

        self.__update_modify_time()
        return self

    @property
    def note(self) -> str:
        return self.__note

    @property
    def note_buf(self) -> bytes:
        return bytes(self.__note, encoding=TEXT_ENCODE)

    @property
    def note_size(self) -> int:
        return len(self.note_buf)

    def set_note(self, note: str) -> BinaryWave5:
        if not isinstance(note, str):
            raise TypeError('a string is required')
        note = self.__convert_eol(note)
        self.__note = note
        self.__header.note_size = self.note_size

        self.__update_modify_time()
        return self

    @property
    def creation_time(self) -> datetime.datetime:
        return self.__header.creation_time

    def set_creation_time(self, time: datetime.datetime) -> BinaryWave5:
        if not isinstance(time, datetime.datetime):
            raise TypeError("datetime.datetime object is required")
        self.__header.set_creation_time(time)
        return self

    def __update_creation_time(self) -> BinaryWave5:
        self.__header.update_creation_time()
        return self

    @property
    def modify_time(self) -> datetime.datetime:
        return self.__header.modify_time

    def __initialize_modify_time(self) -> BinaryWave5:
        self.__header.initialize_modify_time()
        return self

    def duplicate(self, name: str) -> BinaryWave5:
        res = deepcopy(self)
        res.rename(name)
        res.__update_creation_time()
        res.__initialize_modify_time()
        return res

    def save(self, path: Optional[str] = None) -> None:
        header_buf = self.__header.buffer
        values_buf = self.__values.tobytes(order='F')

        dependency_formula_buf = self.formula_buf
        note_buf = self.note_buf

        if not self.__header.data_unit:
            ex_data_unit_buf = bytes(self.data_unit, encoding=TEXT_ENCODE)
        else:
            ex_data_unit_buf = b''

        short_dim_units = self.__header.axes_unit
        dim_units = self.axes_unit
        ex_dim_units_bufs = [bytes(dim_unit, encoding=TEXT_ENCODE)
                             if not short_dim_unit else b''
                             for dim_unit, short_dim_unit
                             in zip(dim_units, short_dim_units)]
        ex_dim_units_buf = reduce(lambda x, y: x + y, ex_dim_units_bufs)
        # TODO: support dimension label
        # dimension_label_bufs = ...

        buffer = header_buf + values_buf \
            + dependency_formula_buf + note_buf \
            + ex_data_unit_buf + ex_dim_units_buf

        if path is None:
            path = self.name + ".ibw"
        with open(path, mode='wb') as f:
            f.write(buffer)


class BinaryWave5Loader:
    BIN_HEADER_SIZE = 64

    def __init__(self, path: str) -> None:
        self.path = path

    def __has_valid_checksum(self) -> bool:
        with open(self.path, mode='rb') as f:
            header_buf = f.read(self.BIN_HEADER_SIZE + WAVE_HEADER_SIZE)
            values = np.array(struct.unpack("192h", header_buf))
            checksum = np.sum(values, dtype=np.int16)

            return checksum == 0

    def load(self) -> BinaryWave5:
        if not self.__has_valid_checksum():
            raise ValueError('bad checksum')

        header_loader = BinaryWaveHeader5Loader()
        with open(self.path, mode='rb') as f:
            bin_header_buf = f.read(self.BIN_HEADER_SIZE)
            wave_header_buf = f.read(WAVE_HEADER_SIZE)
            header = header_loader.load_from_buffer(
                bin_header_buf, wave_header_buf)
            section_sizes = header.section_sizes

            values_buf = f.read(section_sizes['value_size'])
            values = np.frombuffer(values_buf, dtype=header.dtype)
            values_array = np.reshape(values, list(reversed(header.shape))).T

            dependency_formula_buf = f.read(section_sizes['formula_size'])
            dependency_formula = decode_unicode(dependency_formula_buf)

            note_buf = f.read(section_sizes['note_size'])
            note = decode_unicode(note_buf)

            ex_data_unit = decode_unicode(
                f.read(section_sizes['ex_data_unit_size']))
            data_unit = header.data_unit if header.data_unit else ex_data_unit

            ex_axes_unit = [decode_unicode(f.read(size))
                            for size in section_sizes['ex_axes_unit_size']]
            axes_unit = [short_unit if short_unit else ex_unit
                         for short_unit, ex_unit
                         in zip(header.axes_unit, ex_axes_unit)]

            # TODO: support dimension label
            if section_sizes['axes_label_size'] != (0, 0, 0, 0):
                print('Warning: axis labels are not supported')

                # TODO: delete when dimension labels are supported
                header.initialize_axis_label_size()

            """
            axes_label_buf = [f.read(size)
                              for size in section_sizes['axes_label_size']]
            """

        res = BinaryWave5(ibw_header=header,
                          wave_values=values_array,
                          data_unit=data_unit,
                          axes_unit=axes_unit,
                          dependency_formula=dependency_formula,
                          note=note)
        return res
