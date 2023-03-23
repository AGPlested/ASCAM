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

# create a fixture if the previous test passed
@pytest.fixture(scope="session")
def recording():
    path = os.path.split( os.path.dirname(os.path.abspath(__file__)) )[0]
    path = os.path.join(path, "data")
    TEST_FILE = os.path.join(path, TEST_FILE_NAME)
    return Recording.from_file(TEST_FILE, 4e4)

@pytest.fixture(scope="session")
def main(recording):
    QApplication([])
    main_window = MainWindow(screen_resolution=(1920, 1080))
    main_window.data = recording
    return main_window

def test_create_episode_frame(main):
    main.ep_frame = EpisodeFrame(main)
    assert isinstance(main.ep_frame, EpisodeFrame)
    assert main.ep_frame.series_selection.currentText() == 'raw_'
    assert main.ep_frame.series_selection.count() == 1
    assert main.ep_frame.ep_list.count() == 108
    assert main.ep_frame.ep_list.item(0).text() == 'Episode 0'
    assert main.ep_frame.episode_sets_frame.episode_sets[0].name == "All"
    assert main.ep_frame.episode_sets_frame.episode_sets[0].key == None

def test_create_new_set(qtbot, main, monkeypatch):
    # ep_frame = EpisodeFrame(main)
    # qtbot.addWidget(ep_frame)
    # qtbot.mouseClick(episode_frame.new_button, Qt.LeftButton)

    monkeypatch.setattr(
        NewSetDialog, "get_new_set",
        classmethod(lambda *args: ("SetName", "a"))
    )
    qtbot.mouseClick(main.ep_frame.episode_sets_frame.new_button, Qt.LeftButton)

    assert main.ep_frame.episode_sets_frame.episode_sets[1].name == "SetName"
    assert main.ep_frame.episode_sets_frame.episode_sets[1].key == "a"
    assert main.ep_frame.episode_sets_frame.episode_sets[1].episodes == []
    assert main.data.episode_sets["SetName"] == ([], "a")

def test_add_to_set(qtbot, main):
    main.ep_frame.episode_sets_frame.add_to_set(name="SetName", index=0)
    assert main.data.episode_sets["SetName"] == ([0], "a")
    assert main.ep_frame.episode_sets_frame.episode_sets[0].episodes == [0]
