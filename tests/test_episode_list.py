import pytest
from pytestqt import qtbot
from PySide2.QtCore import Qt

from src.gui.episode_frame import EpisodeFrame, NewSetDialog

@pytest.fixture(scope="class")
def main(main_window):
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


# # def test_switch_series(qtbot):
# #     # Create a mock main window object
# #     class MainWindow:
# #         def __init__(self):
# #             self.data = {'key1': {}, 'key2': {}}

# #     main_window = MainWindow()
# #     episode_frame = EpisodeFrame(main_window)

# #     # Set up the necessary mocks
# #     tc_frame_mock = MagicMock()
# #     main_window.tc_frame = tc_frame_mock

# #     # Call the method with a valid series key
# #     episode_frame.switch_series('key2')

# #     # Check that the current_datakey attribute was set correctly
# #     assert main_window.data['current_datakey'] == 'key2'

# #     # Check that the tc_frame methods were called
# #     tc_frame_mock.get_params.assert_called_once()
# #     tc_frame_mock.idealize_episode.assert_called_once()

# #     # Reset the mocks
# #     tc_frame_mock.reset_mock()

# #     # Call the method with an invalid series key
# #     episode_frame.switch_series('invalid_key')

# #     # Check that the current_datakey attribute was not changed
# #     assert main_window.data['current_datakey'] == 'key2'

# #     # Check that the tc_frame methods were not called
# #     tc_frame_mock.get_params.assert_not_called()
# #     tc_frame_mock.idealize_episode.assert_not_called()
