import pytest
from pytestqt import qtbot  # pyright: reportMissingImports=false
from PySide2.QtCore import Qt

from src.core import IdealizationCache
from src.gui.idealization_frame import (IdealizationFrame,
                                        IdealizationTabFrame)
from src.gui.threshold_crossing_frame import ThresholdCrossingFrame
from unittest.mock import MagicMock, patch

@pytest.fixture(scope="module", autouse=True)
def mock_other_idealization_cache():
    with patch.object(IdealizationCache,
                      "idealize_episode",
                      new=MagicMock(return_value="IdealizationCache.idealize_episode called")
                      ):
        yield

@pytest.fixture(scope="class")
def mock_plot_frame():
    plot_frame = MagicMock()
    plot_frame.tc_tracking = False
    plot_frame.update_episode = MagicMock(return_value="PlotFrame.update_episode called")
    return plot_frame

@pytest.fixture(scope="class")
def main(main_window, mock_plot_frame):
    main_window.plot_frame = mock_plot_frame
    main_window.plot_frame.tc_tracking = False
    return main_window

class TestThresholdCrossingFrame():
    # Note these tests alter the class scoped fixtures main and recording
    # so they must be run in order!
    # Tests that have side effects should have a docstring.
    def test_create_idealization_frame(self, main):
        """Creates the IdealizationFrame object."""
        main.id_frame = IdealizationFrame(main, idealization_method="TC")
        assert isinstance(main.id_frame, IdealizationFrame)

    def test_tab_frame_created(self, main):
        assert isinstance(main.id_frame.tab_frame, IdealizationTabFrame)

    def test_tc_frame_created(self, main):
        assert len(main.id_frame.tab_frame.tabs) == 1
        assert isinstance(main.id_frame.tab_frame.tabs[0],
                          ThresholdCrossingFrame)

    @pytest.fixture
    def tc_frame(self, main):
        return main.id_frame.tab_frame.tabs[0]

    def test_neg_check(self, tc_frame, qtbot):
        """Toggle on the negative amplitude checkbox."""
        assert not tc_frame.neg_check.isChecked()  # Initially unchecked
        qtbot.mouseClick(tc_frame.neg_check, Qt.LeftButton)
        assert tc_frame.neg_check.isChecked()  # Checked after click

    def test_drag_amp_toggle(self, tc_frame, qtbot):
        assert not tc_frame.drag_amp_toggle.isChecked()  # Initially checked
        assert not tc_frame.main.plot_frame.tc_tracking
        qtbot.mouseClick(tc_frame.drag_amp_toggle, Qt.LeftButton)
        assert tc_frame.drag_amp_toggle.isChecked()  # Unchecked after click
        assert tc_frame.main.plot_frame.tc_tracking
        qtbot.mouseClick(tc_frame.drag_amp_toggle, Qt.LeftButton)
        assert not tc_frame.drag_amp_toggle.isChecked()
        assert not tc_frame.main.plot_frame.tc_tracking

    def test_calculate_click(self, tc_frame, qtbot):
        tc_frame.main.plot_frame.update_episode.reset_mock()
        with qtbot.waitSignal(tc_frame.calc_button.clicked):
            qtbot.mouseClick(tc_frame.calc_button, Qt.LeftButton)
        tc_frame.main.plot_frame.update_episode.assert_called_once()
        tc_frame.idealization_cache.idealize_episode.assert_called_once()

    def test_amp_unit_change(self, tc_frame):
        assert tc_frame.trace_unit_entry.currentText() == "pA"
        assert tc_frame.trace_unit == "pA"
        tc_frame.trace_unit_entry.setCurrentText("mA")
        assert tc_frame.trace_unit_entry.currentText() == "mA"
        assert tc_frame.trace_unit == "mA"
        tc_frame.trace_unit_entry.setCurrentText("pA")  # Reset for other tests
        assert tc_frame.trace_unit == "pA"


    #TODO:
    # test entering amplitude values, using int and float and separated by
    #   commas and spaces
    # test thresholds are updated when amplitude values are changed and
    #   when auto threshold is checked
    # test entering resolution values
    # test entering threshold values
    # test entering interpolation values
    # test get_params
    # test params_changed function
    # test showing table of events
    # test showing dwell time histogram
    # test exporting events
    # test exporting idealization
    # test close tab button

    # # # For some reason clicking the checkbox doesn't work in tests
    # def test_show_amp_check(self, tc_frame, qtbot):
    #     assert tc_frame.show_amp_check.isChecked()  # Initially checked
    #     print(type(tc_frame.show_amp_check))
    #     # isVisible probably doesn't mean anything because that's
    #     # also false in tests that work
    #     print("Is visible= ", tc_frame.show_amp_check.isVisible())
    #     # isEnabled probably doesn't mean anything because that's
    #     # also true in tests that work
    #     print("Is enabled= ", tc_frame.show_amp_check.isEnabled())
    #     with qtbot.waitSignal(tc_frame.show_amp_check.clicked):
    #         qtbot.mouseClick(tc_frame.show_amp_check, Qt.LeftButton)
    #     # under mouse probably doesn't mean anything because that's
    #     # also false in tests that work
    #     print("Under mouse= ", tc_frame.show_amp_check.underMouse())
    #     print("After click: isChecked =", tc_frame.show_amp_check.isChecked())
    #     assert not tc_frame.show_amp_check.isChecked()  # Unchecked after click

    # this test also doesn't work because clicking the checkbox doesn't work
    # def test_show_threshold_check(self, tc_frame, qtbot):
    #     assert not tc_frame.show_threshold_check.isChecked()  # Initially unchecked
    #     qtbot.mouseClick(tc_frame.show_threshold_check, Qt.LeftButton)
    #     assert tc_frame.show_threshold_check.isChecked()  # Checked after click

    # same as above
    # def test_auto_thresholds(self, tc_frame, qtbot):
    #     assert not tc_frame.auto_thresholds.isChecked()  # Initially unchecked
    #     qtbot.mouseClick(tc_frame.auto_thresholds, Qt.LeftButton)
    #     assert tc_frame.auto_thresholds.isChecked()  # Checked after click

    # def test_use_resolution(self, tc_frame, qtbot):
    #     assert not tc_frame.use_resolution.isChecked()  # Initially unchecked
    #     qtbot.mouseClick(tc_frame.use_resolution, Qt.LeftButton)
    #     assert tc_frame.use_resolution.isChecked()  # Checked after click

    # def test_interpolate(self, tc_frame, qtbot):
    #     assert not tc_frame.interpolate.isChecked()
    #     qtbot.mouseClick(tc_frame.interpolate, Qt.LeftButton)
    #     assert tc_frame.interpolate.isChecked()
