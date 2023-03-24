import os

import pytest
from pytestqt import qtbot
from unittest.mock import MagicMock
from PySide2.QtWidgets import QApplication
from PySide2.QtCore import Qt

from src.gui.episode_frame import EpisodeFrame, NewSetDialog
from src.gui.mainwindow import MainWindow
from src.core import Recording
from src.constants import TEST_FILE_NAME

@pytest.fixture(scope="class")
def recording():
    path = os.path.split( os.path.dirname(os.path.abspath(__file__)) )[0]
    path = os.path.join(path, "data")
    TEST_FILE = os.path.join(path, TEST_FILE_NAME)
    return Recording.from_file(TEST_FILE, 4e4)

@pytest.fixture(scope="class")
def main(recording):
    QApplication([])
    main_window = MainWindow(screen_resolution=(1920, 1080))
    main_window.data = recording
    return main_window

class TestEpisodeFrame():
    # Note these tests alter the class scoped fixtures main and recording
    # so they must be run in order!
    # Tests that have side effects should have a docstring.
    def test_create_episode_frame(self, main):
        """Creates the EpisodeFrame object."""
        main.ep_frame = EpisodeFrame(main)
        assert isinstance(main.ep_frame, EpisodeFrame)

    def test_correct_series_name(self, main):
        assert main.ep_frame.series_selection.currentText() == 'raw_'

    def test_correct_number_of_series(self, main):
        assert main.ep_frame.series_selection.count() == 1

    def test_correct_number_of_episodes(self, main):
        assert main.ep_frame.ep_list.count() == 108

    def test_default_item_text(self, main):
        assert main.ep_frame.ep_list.item(0).text() == 'Episode 0'

    def test_default_set_name(self, main):
        assert main.ep_frame.episode_sets_frame.episode_sets[0].name == "All"

    def test_default_set_key(self, main):
        assert main.ep_frame.episode_sets_frame.episode_sets[0].key == None

    def test_default_item_selected(self, main):
        assert main.ep_frame.ep_list.currentRow() == 0

    def test_create_new_set(self, qtbot, main, monkeypatch):
        """Creates a new set with the name "SetName" and key "a"."""
        monkeypatch.setattr(
            NewSetDialog, "get_new_set",
            classmethod(lambda *args: ("SetName", "a"))
        )
        qtbot.mouseClick(main.ep_frame.episode_sets_frame.new_button, Qt.LeftButton)

        assert main.ep_frame.episode_sets_frame.episode_sets[1].name == "SetName"
        assert main.ep_frame.episode_sets_frame.episode_sets[1].key == "a"
        assert main.ep_frame.episode_sets_frame.episode_sets[1].episodes == []

    def test_set_added_to_recording(self, main):
        assert main.data.episode_sets["SetName"] == ([], "a")

    def test_add_to_set(self, main):
        """Adds the first episode to the set "SetName"."""
        main.ep_frame.episode_sets_frame.add_to_set(name="SetName", index=0)
        assert main.data.episode_sets["SetName"] == ([0], "a")
        assert main.ep_frame.episode_sets_frame.episode_sets[1].episodes == [0]

    def test_click_changes_selection(self, qtbot, main):
        """Changes the selected episode to episode 5."""
        el = main.ep_frame.ep_list
        qtbot.mouseClick(el.viewport(), Qt.LeftButton, pos=el.visualItemRect(el.item(4)).center())
        assert main.ep_frame.ep_list.currentRow() == 4

    def test_add_to_set_with_button(self, qtbot, main):
        """Adds the currently selected episode (episode at index 4) to the set "SetName"."""
        qtbot.keyClick(main.ep_frame.ep_list, "a")
        assert main.ep_frame.episode_sets_frame.episode_sets[1].episodes == [0, 4]
        # This second assertion is redundant, but you never know.
        assert main.data.episode_sets["SetName"] == ([0, 4], "a")

    def test_remove_from_set_with_button(self, qtbot, main):
        """Removes the episode at index 4 from the set "SetName"."""
        qtbot.keyClick(main.ep_frame.ep_list, "a")
        assert main.ep_frame.episode_sets_frame.episode_sets[1].episodes == [0]
        assert main.data.episode_sets["SetName"] == ([0], "a")
