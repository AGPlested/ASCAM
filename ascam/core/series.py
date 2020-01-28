import copy
import logging

import numpy as np

from ascam.core.episode import Episode
from ascam.utils.tools import piezo_selection, interval_selection


class Series(list):
    def __init__(self, data=[], idealized=False):
        """`Series` are lists of episodes which also store relevant parameters
        about the recording and operations that have been performed on the
        data.
        """

        list.__init__(self, data)


