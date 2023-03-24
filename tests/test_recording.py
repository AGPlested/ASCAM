import os

import numpy as np

from src.core import Recording
from src.core.filtering import gaussian_filter, ChungKennedyFilter
from src.core.analysis import baseline_correction

class TestRecording():
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

    def test_multiple_operations_datakey(self, recording):
        # Note that the datakey is "BC_" from the previous test.
        recording.gauss_filter_series(filter_freq=1000)
        assert recording.current_datakey == "BC_GFILTER1000_"

    def test_export_idealization(self, recording, tmp_path):
        # Test exporting idealization to a CSV file
        #TODO add tempfile here to read the file and check the contents are correct
        params = {"amplitudes": np.array([0, -1, -1.4, -2])}
        for ep in recording.series:
            ep.idealize(method="TC", params=params)
        recording.export_idealization(
            filepath=os.path.join(tmp_path, "idealization.csv"),
            lists_to_save=["All"],
            time_unit='s',
            trace_unit="A",
            amplitudes=params["amplitudes"],
        )
        assert os.path.exists(os.path.join(tmp_path, "idealization.csv"))

    def test_load_header_from_csv(self, csv_data):
        header, _ = csv_data
        params, column_names, _ = header.split("\n")
        if params.startswith("# "):
            params = params[2:]
        if column_names.startswith("# "):
            column_names = column_names[2:]
        assert column_names.startswith("Time, Episode 0,")
        assert params == "amplitudes = [ 0.0e+00 -7.0e-13 -1.2e-12 -1.8e-12 -2.2e-12];" \
                         "thresholds = [-3.5e-13 -9.5e-13 -1.5e-12 -2.0e-12];" \
                         "interpolation_factor = 1;"

    def test_load_data_from_csv(self, recording, csv_data):
        _, data = csv_data
        assert data.shape == (4000, 109)
        assert np.allclose(data[:, 0], recording.episode().time)
        # The next asserting depends on the idealization from test_export_idealization
        # persisting.
        assert np.allclose(data[:, 1], recording.episode().idealization)

    def test_export_matlab_all_raw_data(self, recording, tmp_path, mat_save_file):
        # Test exporting a recording to a MATLAB file
        recording.export_matlab(
            filepath=os.path.join(tmp_path, mat_save_file),
            datakey="raw_",
            lists_to_save=["All"],
            save_piezo=True,
            save_command=True,
        )
        assert os.path.exists(os.path.join(tmp_path, mat_save_file))

    def test_load_exported_matlab_all_raw_data(self, recording, tmp_path, mat_save_file):
        # Test loading a recording from a MATLAB file
        assert os.path.exists(os.path.join(tmp_path, mat_save_file))
        loaded_recording = Recording._load_from_matlab(
                        Recording(os.path.join(tmp_path, mat_save_file)),
                                                       trace_input_unit="A",
                                                       piezo_input_unit="V",
                                                       command_input_unit="V",
                                                       time_input_unit="s")
        assert np.allclose(recording["raw_"][0].trace, loaded_recording["raw_"][0].trace)
        assert np.allclose(recording["raw_"][0].piezo, loaded_recording["raw_"][0].piezo)
        assert np.allclose(recording["raw_"][0].command, loaded_recording["raw_"][0].command)


    #TODO: Write these tests
    # def test_CK_filter_series(self, recording):
    #     recording.current_datakey = "raw_"
        # Test CK filter of a series of episodes
    # def test_detect_fa(self, recording):
    # def test_series_hist(self, recording):
    # def test_episode_hist(self, recording):
    # def test_load_from_axograph(self, recording):
    # def test_save_to_pickle(self, recording):
    # def test_save_to_axograph(self, recording):
    # def test_load_from_pickle(self, recording):

# def test_save_to_pickle():
#     # Test saving and loading a Recording object to/from a pickle file
#     recording = Recording.from_file(TEST_FILE)
#     recording.save_to_pickle("data/recording.pkl")
#     assert os.path.exists("data/recording.pkl")
#     loaded_recording = recording.from_file("data/recording.pkl")
#     assert np.allclose(recording["raw_"][0].trace, loaded_recording["raw_"][0].trace)
#     assert np.allclose(recording["raw_"][1].trace, loaded_recording["raw_"][1].trace)
#     assert np.allclose(recording["raw_"][2].trace, loaded_recording["raw_"][2].trace)

