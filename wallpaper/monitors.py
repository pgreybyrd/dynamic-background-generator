import ctypes

from wallpaper.logging import debug_log

try:
    import comtypes
    import comtypes.client
    from comtypes import GUID, COMMETHOD, HRESULT
    from ctypes import POINTER, c_uint
    from ctypes.wintypes import LPWSTR, RECT
except ImportError:
    comtypes = None

class IDesktopWallpaper(comtypes.IUnknown if comtypes is not None else object):
    if comtypes is not None:
        _iid_ = GUID("{B92B56A9-8B55-4E14-9A89-0199BBB6F93B}")
        _methods_ = [
            COMMETHOD([], HRESULT, "SetWallpaper",
                      (["in"], LPWSTR, "monitorID"),
                      (["in"], LPWSTR, "wallpaper")),
            COMMETHOD([], HRESULT, "GetWallpaper",
                      (["in"], LPWSTR, "monitorID"),
                      (["out"], POINTER(LPWSTR), "wallpaper")),
            COMMETHOD([], HRESULT, "GetMonitorDevicePathAt",
                      (["in"], c_uint, "monitorIndex"),
                      (["out"], POINTER(LPWSTR), "monitorID")),
            COMMETHOD([], HRESULT, "GetMonitorDevicePathCount",
                      (["out"], POINTER(c_uint), "count")),
            COMMETHOD([], HRESULT, "GetMonitorRECT",
                      (["in"], LPWSTR, "monitorID"),
                      (["out"], POINTER(RECT), "displayRect")),
        ]


def get_desktop_wallpaper_object():
    if comtypes is None:
        raise RuntimeError("Missing dependency: pip install comtypes")

    return comtypes.client.CreateObject(
        GUID("{C2CF3110-460E-4FC1-B9D0-8A1C0C9CC4BD}"),
        interface=IDesktopWallpaper,
    )


def debug_monitor_ids():
    wallpaper = get_desktop_wallpaper_object()
    count = wallpaper.GetMonitorDevicePathCount()
    debug_log(f"Detected {count} monitor(s).")

    for i in range(count):
        monitor_id = wallpaper.GetMonitorDevicePathAt(i)
        rect = wallpaper.GetMonitorRECT(monitor_id)
        debug_log(f"Monitor {i}: {monitor_id} rect={rect}")


def set_wallpapers_per_monitor(
    bottom_path,
    top_path,
    top_monitor_index,
    update_bottom=True,
    update_top=True,
):
    wallpaper = get_desktop_wallpaper_object()
    count = wallpaper.GetMonitorDevicePathCount()

    if top_monitor_index is None or top_monitor_index < 0 or top_monitor_index >= count:
        debug_log(
            f"Invalid top_monitor.monitor_index={top_monitor_index}; "
            f"expected 0 through {count - 1}."
        )

        if update_bottom and bottom_path:
            debug_log("Falling back to single wallpaper for horizontal update.")
            set_wallpaper(bottom_path)
            return

        raise RuntimeError(
            "Cannot safely apply a vertical-only wallpaper update because "
            "top_monitor.monitor_index is invalid."
        )

    top_monitor_id = wallpaper.GetMonitorDevicePathAt(top_monitor_index)

    if update_bottom and update_top:
        if not bottom_path or not top_path:
            raise ValueError("Both wallpaper paths are required when both groups update.")

        # Fast path from Pass 1: one shared refresh, then restore the vertical monitor.
        wallpaper.SetWallpaper(None, bottom_path)
        wallpaper.SetWallpaper(top_monitor_id, top_path)
        return

    if update_bottom:
        if not bottom_path:
            raise ValueError("bottom_path is required for a horizontal wallpaper update.")

        # Do NOT use SetWallpaper(None, ...) here: that would also refresh the
        # vertical monitor and defeat independent group updates.
        for i in range(count):
            if i == top_monitor_index:
                continue

            monitor_id = wallpaper.GetMonitorDevicePathAt(i)
            wallpaper.SetWallpaper(monitor_id, bottom_path)

    if update_top:
        if not top_path:
            raise ValueError("top_path is required for a vertical wallpaper update.")

        wallpaper.SetWallpaper(top_monitor_id, top_path)


def set_wallpaper(path):
    SPI_SETDESKWALLPAPER = 20
    ctypes.windll.user32.SystemParametersInfoW(SPI_SETDESKWALLPAPER, 0, path, 3)
