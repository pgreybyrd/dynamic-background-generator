#pytest tests/test_monitors.py -v
import pytest

import wallpaper.monitors as monitors


class FakeWallpaper:
    def __init__(self, count=4):
        self.count = count
        self.set_calls = []

    def GetMonitorDevicePathCount(self):
        return self.count

    def GetMonitorDevicePathAt(self, index):
        return f"monitor-{index}"

    def SetWallpaper(self, monitor_id, path):
        self.set_calls.append((monitor_id, path))


def install_fake(monkeypatch, count=4):
    fake = FakeWallpaper(count=count)

    monkeypatch.setattr(
        monitors,
        "get_desktop_wallpaper_object",
        lambda: fake,
    )

    return fake


# ~~~~~ DEFAULT BOTTOM MONITOR SELECTION ~~~~~

def test_default_bottom_monitors_are_everything_except_top(monkeypatch):
    fake = install_fake(monkeypatch, count=4)

    monitors.set_wallpapers_per_monitor(
        bottom_path="bottom.png",
        top_path="top.png",
        top_monitor_index=3,
    )

    # Shared optimization applies bottom globally first,
    # then restores the special top monitor.
    assert fake.set_calls == [
        (None, "bottom.png"),
        ("monitor-3", "top.png"),
    ]


def test_no_top_monitor_defaults_all_monitors_to_bottom(monkeypatch):
    fake = install_fake(monkeypatch, count=3)

    monitors.set_wallpapers_per_monitor(
        bottom_path="bottom.png",
        top_path=None,
        top_monitor_index=None,
        update_top=False,
    )

    assert fake.set_calls == [
        ("monitor-0", "bottom.png"),
        ("monitor-1", "bottom.png"),
        ("monitor-2", "bottom.png"),
    ]


# ~~~~~ SHARED MODE ~~~~~

def test_shared_mode_sets_each_configured_bottom_monitor(monkeypatch):
    fake = install_fake(monkeypatch, count=4)

    monitors.set_wallpapers_per_monitor(
        bottom_path="bottom.png",
        top_path=None,
        top_monitor_index=3,
        bottom_mode="shared",
        bottom_monitor_indices=[0, 2],
        update_top=False,
    )

    assert fake.set_calls == [
        ("monitor-0", "bottom.png"),
        ("monitor-2", "bottom.png"),
    ]


def test_shared_mode_uses_global_shortcut_when_safe(monkeypatch):
    fake = install_fake(monkeypatch, count=4)

    monitors.set_wallpapers_per_monitor(
        bottom_path="bottom.png",
        top_path="top.png",
        top_monitor_index=3,
        bottom_mode="shared",
        bottom_monitor_indices=[0, 1, 2],
        update_bottom=True,
        update_top=True,
    )

    assert fake.set_calls == [
        (None, "bottom.png"),
        ("monitor-3", "top.png"),
    ]


def test_shared_mode_does_not_use_global_shortcut_when_top_not_updated(
    monkeypatch,
):
    fake = install_fake(monkeypatch, count=4)

    monitors.set_wallpapers_per_monitor(
        bottom_path="bottom.png",
        top_path=None,
        top_monitor_index=3,
        bottom_mode="shared",
        bottom_monitor_indices=[0, 1, 2],
        update_bottom=True,
        update_top=False,
    )

    assert fake.set_calls == [
        ("monitor-0", "bottom.png"),
        ("monitor-1", "bottom.png"),
        ("monitor-2", "bottom.png"),
    ]


def test_shared_mode_requires_bottom_path(monkeypatch):
    install_fake(monkeypatch)

    with pytest.raises(
        ValueError,
        match="bottom_path is required",
    ):
        monitors.set_wallpapers_per_monitor(
            bottom_path=None,
            top_path="top.png",
            top_monitor_index=3,
            bottom_mode="shared",
        )


# ~~~~~ PANORAMA MODE ~~~~~

def test_panorama_assigns_slices_left_to_right(monkeypatch):
    fake = install_fake(monkeypatch, count=4)

    monitors.set_wallpapers_per_monitor(
        bottom_path=None,
        top_path="top.png",
        top_monitor_index=3,
        bottom_mode="panorama",
        bottom_monitor_indices=[2, 0, 1],
        panorama_paths=[
            "left.png",
            "middle.png",
            "right.png",
        ],
    )

    assert fake.set_calls == [
        ("monitor-2", "left.png"),
        ("monitor-0", "middle.png"),
        ("monitor-1", "right.png"),
        ("monitor-3", "top.png"),
    ]


def test_panorama_requires_paths(monkeypatch):
    install_fake(monkeypatch)

    with pytest.raises(
        ValueError,
        match="panorama_paths are required",
    ):
        monitors.set_wallpapers_per_monitor(
            bottom_path=None,
            top_path="top.png",
            top_monitor_index=3,
            bottom_mode="panorama",
            bottom_monitor_indices=[0, 1, 2],
            panorama_paths=None,
        )


def test_panorama_slice_count_must_match_monitor_count(monkeypatch):
    install_fake(monkeypatch)

    with pytest.raises(
        ValueError,
        match="number of panorama slices",
    ):
        monitors.set_wallpapers_per_monitor(
            bottom_path=None,
            top_path="top.png",
            top_monitor_index=3,
            bottom_mode="panorama",
            bottom_monitor_indices=[0, 1, 2],
            panorama_paths=[
                "left.png",
                "middle.png",
            ],
        )


def test_panorama_paths_are_converted_to_strings(monkeypatch, tmp_path):
    fake = install_fake(monkeypatch, count=2)

    path = tmp_path / "slice.png"

    monitors.set_wallpapers_per_monitor(
        bottom_path=None,
        top_path=None,
        top_monitor_index=None,
        bottom_mode="panorama",
        bottom_monitor_indices=[0],
        panorama_paths=[path],
        update_top=False,
    )

    assert fake.set_calls == [
        ("monitor-0", str(path)),
    ]


# ~~~~~ MONITOR INDEX VALIDATION ~~~~~

@pytest.mark.parametrize(
    "bad_index",
    [
        -1,
        4,
        999,
    ],
)
def test_invalid_bottom_monitor_index_raises(monkeypatch, bad_index):
    install_fake(monkeypatch, count=4)

    with pytest.raises(
        ValueError,
        match="Invalid bottom monitor index",
    ):
        monitors.set_wallpapers_per_monitor(
            bottom_path="bottom.png",
            top_path="top.png",
            top_monitor_index=3,
            bottom_monitor_indices=[0, bad_index],
        )


@pytest.mark.parametrize(
    "bad_index",
    [
        -1,
        4,
        999,
    ],
)
def test_invalid_top_monitor_index_raises(monkeypatch, bad_index):
    install_fake(monkeypatch, count=4)

    with pytest.raises(
        ValueError,
        match="Invalid top_monitor.monitor_index",
    ):
        monitors.set_wallpapers_per_monitor(
            bottom_path="bottom.png",
            top_path="top.png",
            top_monitor_index=bad_index,
            bottom_monitor_indices=[0, 1, 2],
        )


def test_top_monitor_cannot_also_be_bottom_monitor(monkeypatch):
    install_fake(monkeypatch, count=4)

    with pytest.raises(
        ValueError,
        match="cannot also be in bottom_monitors",
    ):
        monitors.set_wallpapers_per_monitor(
            bottom_path="bottom.png",
            top_path="top.png",
            top_monitor_index=3,
            bottom_monitor_indices=[0, 1, 3],
        )


# ~~~~~ SELECTIVE UPDATES ~~~~~

def test_update_bottom_false_does_not_touch_bottom_monitors(monkeypatch):
    fake = install_fake(monkeypatch, count=4)

    monitors.set_wallpapers_per_monitor(
        bottom_path="bottom.png",
        top_path="top.png",
        top_monitor_index=3,
        bottom_monitor_indices=[0, 1, 2],
        update_bottom=False,
        update_top=True,
    )

    assert fake.set_calls == [
        ("monitor-3", "top.png"),
    ]


def test_update_top_false_does_not_touch_top_monitor(monkeypatch):
    fake = install_fake(monkeypatch, count=4)

    monitors.set_wallpapers_per_monitor(
        bottom_path="bottom.png",
        top_path="top.png",
        top_monitor_index=3,
        bottom_monitor_indices=[0, 1, 2],
        update_bottom=True,
        update_top=False,
    )

    assert ("monitor-3", "top.png") not in fake.set_calls


def test_both_updates_false_changes_nothing(monkeypatch):
    fake = install_fake(monkeypatch, count=4)

    monitors.set_wallpapers_per_monitor(
        bottom_path="bottom.png",
        top_path="top.png",
        top_monitor_index=3,
        bottom_monitor_indices=[0, 1, 2],
        update_bottom=False,
        update_top=False,
    )

    assert fake.set_calls == []


# ~~~~~ TOP MONITOR REQUIREMENTS ~~~~~

def test_top_update_requires_top_monitor_index(monkeypatch):
    install_fake(monkeypatch, count=4)

    with pytest.raises(
        ValueError,
        match="top monitor index is required",
    ):
        monitors.set_wallpapers_per_monitor(
            bottom_path="bottom.png",
            top_path="top.png",
            top_monitor_index=None,
            update_bottom=False,
            update_top=True,
        )


def test_top_update_requires_top_path(monkeypatch):
    install_fake(monkeypatch, count=4)

    with pytest.raises(
        ValueError,
        match="top_path is required",
    ):
        monitors.set_wallpapers_per_monitor(
            bottom_path="bottom.png",
            top_path=None,
            top_monitor_index=3,
            update_bottom=False,
            update_top=True,
        )


# ~~~~~ BAD MODE ~~~~~

def test_unknown_bottom_mode_raises(monkeypatch):
    install_fake(monkeypatch)

    with pytest.raises(
        ValueError,
        match="Unknown bottom monitor mode",
    ):
        monitors.set_wallpapers_per_monitor(
            bottom_path="bottom.png",
            top_path="top.png",
            top_monitor_index=3,
            bottom_mode="absolute_nonsense",
        )