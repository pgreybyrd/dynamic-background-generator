#pytest tests/test_state.py -v
from wallpaper.state import load_state, save_state


# ~~~~~ LOAD STATE ~~~~~

def test_load_state_returns_empty_dict_when_file_is_missing(tmp_path):
    state_path = tmp_path / "state.json"

    assert load_state(state_path) == {}


def test_load_state_reads_saved_json(tmp_path):
    state_path = tmp_path / "state.json"

    state_path.write_text(
        """
        {
            "season": "late_autumn",
            "_output_slot": "a"
        }
        """,
        encoding="utf-8",
    )

    assert load_state(state_path) == {
        "season": "late_autumn",
        "_output_slot": "a",
    }


# ~~~~~ SAVE STATE ~~~~~

def test_save_state_creates_file(tmp_path):
    state_path = tmp_path / "state.json"

    save_state(
        {
            "weather": "rain",
        },
        state_path,
    )

    assert state_path.exists()


def test_save_state_round_trips_through_load_state(tmp_path):
    state_path = tmp_path / "state.json"

    original = {
        "_bottom_visual_state": {
            "layers": [
                "sky/noon.png",
                "landscape/base.png",
            ],
            "banner": None,
            "mode": "panorama",
            "monitor_indices": [0, 1, 2],
            "monitor_widths": [1920, 1920, 1920],
        },
        "_top_visual_state": {
            "layers": [
                "sky/noon.png",
                "landscape/base.png",
            ],
            "banner": None,
        },
        "_bottom_output_slot": "a",
        "_top_output_slot": "b",
    }

    save_state(original, state_path)

    assert load_state(state_path) == original


def test_save_state_overwrites_existing_state(tmp_path):
    state_path = tmp_path / "state.json"

    save_state(
        {
            "season": "summer",
        },
        state_path,
    )

    save_state(
        {
            "season": "winter",
        },
        state_path,
    )

    assert load_state(state_path) == {
        "season": "winter",
    }


def test_save_state_preserves_nested_data_types(tmp_path):
    state_path = tmp_path / "state.json"

    original = {
        "string": "hello",
        "number": 42,
        "boolean": True,
        "nothing": None,
        "list": [1, 2, 3],
        "nested": {
            "slot": "a",
        },
    }

    save_state(original, state_path)

    assert load_state(state_path) == original