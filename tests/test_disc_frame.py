import pytest
from pytestqt import qtbot  # pyright: reportMissingImports=false
from PySide2.QtCore import Qt
from unittest.mock import MagicMock, patch

from .conftest import clear_text_edit
from src.constants import DEFAULT_DISC_ALPHA
from src.core import IdealizationCache
from src.gui.DISC_frame import DISCFrame
from src.gui.idealization_frame import (IdealizationFrame,
                                        IdealizationTabFrame)

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
    plot_frame.update_episode = MagicMock(return_value="PlotFrame.update_episode called")
    return plot_frame

@pytest.fixture(scope="class")
def main(main_window, mock_plot_frame):
    main_window.plot_frame = mock_plot_frame
    return main_window

class TestDISCFrame():
    # Note these tests alter the class scoped fixtures main and recording
    # so they must be run in order!
    # Tests that have side effects should have a docstring.
    def test_create_idealization_frame(self, main):
        """Creates the IdealizationFrame object."""
        main.id_frame = IdealizationFrame(main, idealization_method="DISC")
        assert isinstance(main.id_frame, IdealizationFrame)

    def test_tab_frame_created(self, main):
        assert isinstance(main.id_frame.tab_frame, IdealizationTabFrame)

    def test_tc_frame_created(self, main):
        assert len(main.id_frame.tab_frame.tabs) == 1
        assert isinstance(main.id_frame.tab_frame.tabs[0], DISCFrame)

    @pytest.fixture
    def disc_frame(self, main):
        return main.id_frame.tab_frame.tabs[0]

    def test_BIC_method_buttons(self, disc_frame, qtbot):
        """Toggle on the negative amplitude checkbox."""
        assert disc_frame.approx_BIC_button.isChecked()
        assert not disc_frame.full_BIC_button.isChecked()
        qtbot.mouseClick(disc_frame.full_BIC_button, Qt.LeftButton)
        assert not disc_frame.approx_BIC_button.isChecked()
        assert disc_frame.full_BIC_button.isChecked()
        qtbot.mouseClick(disc_frame.full_BIC_button, Qt.LeftButton)
        assert disc_frame.approx_BIC_button.isChecked()
        assert not disc_frame.full_BIC_button.isChecked()

    def test_enter_alpha_value(self, disc_frame, qtbot):
        """Enter a value in the alpha text box."""
        assert disc_frame.divseg_frame.alpha_entry.text() == str(DEFAULT_DISC_ALPHA)
        clear_text_edit(qtbot, disc_frame.divseg_frame.alpha_entry)
        qtbot.keyClicks(disc_frame.divseg_frame.alpha_entry, "0.01")
        assert disc_frame.divseg_frame.alpha_entry.text() == "0.01"
        clear_text_edit(qtbot, disc_frame.divseg_frame.alpha_entry)
        qtbot.keyClicks(disc_frame.divseg_frame.alpha_entry, str(DEFAULT_DISC_ALPHA))
        assert disc_frame.divseg_frame.alpha_entry.text() == str(DEFAULT_DISC_ALPHA)

#     def test_drag_amp_toggle(self, tc_frame, qtbot):
#         assert not tc_frame.drag_amp_toggle.isChecked()  # Initially checked
#         assert not tc_frame.main.plot_frame.tc_tracking
#         qtbot.mouseClick(tc_frame.drag_amp_toggle, Qt.LeftButton)
#         assert tc_frame.drag_amp_toggle.isChecked()  # Unchecked after click
#         assert tc_frame.main.plot_frame.tc_tracking
#         tc_frame.drag_amp_toggle.setChecked(False)  # Reset for other tests
#         assert not tc_frame.drag_amp_toggle.isChecked()
#         assert not tc_frame.main.plot_frame.tc_tracking

#     def test_calculate_click(self, tc_frame, qtbot):
#         tc_frame.main.plot_frame.update_episode.reset_mock()
#         with qtbot.waitSignal(tc_frame.calc_button.clicked):
#             qtbot.mouseClick(tc_frame.calc_button, Qt.LeftButton)
#         tc_frame.main.plot_frame.update_episode.assert_called_once()
#         tc_frame.idealization_cache.idealize_episode.assert_called_once()

