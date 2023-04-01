import logging

import pytest
import numpy as np

from src.core.idealization import IdealizationCache
from src.core.recording import Recording

debug_logger = logging.getLogger("ascam.debug")
debug_logger.setLevel(logging.DEBUG)
# logging.basicConfig(level=logging.DEBUG)

# method_values = ["TC", "DISC"]
# param_values = [{"amplitudes": np.array([1, 2, 3]),
#                  "thresholds": np.array([1.5, 2.2]),
#                  "resolution": 5,
#                  "interpolation_factor": 2, },
#                 {"alpha": 0.5,
#                  "min_seg_entry": 2,
#                  "min_cluster_size": 2,
#                  "BIC_method": "full", }]

id_cache_params = [("TC", {"amplitudes": np.array([1, 2, 3]),
                           "thresholds": np.array([1.5, 2.2]),
                           "resolution": 5,
                           "interpolation_factor": 2, }),
                   ("DISC", {"alpha": 0.5,
                             "min_seg_length": 2,
                             "min_cluster_size": 2,
                             "BIC_method": "full", })]

@pytest.mark.parametrize("method, params", id_cache_params)
class TestIdealizationCache():
    @pytest.fixture()
    def id_cache(self, recording, method, params):
        return IdealizationCache(data=recording, method=method, **params)

    def test_initialization(self, id_cache, method, params):
        assert id_cache.method == method
        for key, value in params.items():
            if key in id_cache.params.keys():
                assert np.all(id_cache.params[key] == value)

    def test_idealize_episode(self, caplog, recording, id_cache):
        id_cache.idealize_episode(0)
        debug_log_messages = [record.message for record in caplog.records]
        assert f"idealizing episode 0 of series {recording.current_datakey}" in debug_log_messages
        id_cache.idealize_episode(0)
        debug_log_messages = [record.message for record in caplog.records]
        assert f"episode number 0 already idealized" in debug_log_messages
        # we need to clear the cache because pytest shares the recording
        # object between instances of this class
        id_cache.clear_idealization()

    def test_clear_idealization(self, id_cache, recording):
        id_cache.clear_idealization()
        for ep in recording.series:
            assert ep.idealization is None

    def test_ind_idealized(self, id_cache):
        id_cache.idealize_episode(0)
        assert id_cache.ind_idealized == {0}
        # we need to clear the cache because pytest shares the recording
        # object between instances of this class
        id_cache.clear_idealization()
