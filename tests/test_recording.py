import pytest
import os
import numpy as np

from src.core import Recording
from src.constants import TEST_FILE_NAME
from src.core.filtering import gaussian_filter, ChungKennedyFilter
from src.core.analysis import baseline_correction

class TestRecording():
    @pytest.fixture(scope="class")
    def recording(self):
        path = os.path.split( os.path.dirname(os.path.abspath(__file__)) )[0]
        path = os.path.join(path, "data")
        TEST_FILE = os.path.join(path, TEST_FILE_NAME)
        return Recording.from_file(TEST_FILE, 4e4)

    def test_load_from_matlab(self, recording):
        assert isinstance(recording, Recording)

    def test_data_key_initialization(self, recording):
        assert recording.current_datakey == "raw_"

    def test_episode_list_initialization(self, recording):
        assert len(recording["raw_"]) == 108
        assert recording.current_ep_ind == 0

    def test_sampling_rate_is_int(self, recording):
        assert isinstance(recording.sampling_rate, int)

    def test_select_episodes(self, recording):
        selected_episodes = recording.select_episodes(datakey="raw_", ep_sets=["All"])
        assert len(selected_episodes) == len(recording["raw_"])

    def test_piezo_loaded(self, recording):
        assert recording.has_piezo

    def test_command_loaded(self, recording):
        assert recording.has_command

    def test_gauss_filter_series(self, recording):
        recording.gauss_filter_series(filter_freq=1000)
        assert "GFILTER1000_" in recording.keys()
        assert np.allclose(recording["GFILTER1000_"][0].trace,
                           gaussian_filter(recording["raw_"][0].trace, 1000,
                                           recording.sampling_rate))

    def test_baseline_correction(self, recording):
        recording.current_datakey = "raw_"
        # Test baseline correction of a series of episodes
        recording.baseline_correction(active=True)
        assert "BC_" in recording.keys()
        assert np.allclose(recording["BC_"][0].trace,
                           baseline_correction(recording["raw_"][0].time,
                                               recording["raw_"][0].trace,
                                               recording.sampling_rate,
                                               piezo=recording["raw_"][0].piezo))

    #TODO: Write these tests
    # def test_CK_filter_series(self, recording):
    #     recording.current_datakey = "raw_"
        # Test CK filter of a series of episodes
    # def test_detect_fa(self, recording):
    # def test_series_hist(self, recording):
    # def test_episode_hist(self, recording):
