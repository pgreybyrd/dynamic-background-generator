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
    bottom_mode="shared",
    bottom_monitor_indices=None,
    panorama_paths=None,
    update_bottom=True,
    update_top=True,
):
    wallpaper = get_desktop_wallpaper_object()
    count = wallpaper.GetMonitorDevicePathCount()

    if bottom_monitor_indices is None:
        bottom_monitor_indices = [
            index
            for index in range(count)
            if index != top_monitor_index
        ]

    # Make sure every configured monitor actually exists.
    for index in bottom_monitor_indices:
        if index < 0 or index >= count:
            raise ValueError(
                f"Invalid bottom monitor index {index}; "
                f"expected 0 through {count - 1}."
            )
        
    if (
        top_monitor_index is not None
        and top_monitor_index in bottom_monitor_indices
    ):
        raise ValueError(
            "top_monitor.monitor_index cannot also be in bottom_monitors.monitor_indices."
        )

    if top_monitor_index is not None:
        if top_monitor_index < 0 or top_monitor_index >= count:
            raise ValueError(
                f"Invalid top_monitor.monitor_index={top_monitor_index}; "
                f"expected 0 through {count - 1}."
            )

    top_monitor_id = (
        wallpaper.GetMonitorDevicePathAt(top_monitor_index)
        if top_monitor_index is not None
        else None
    )

    # ----- Bottom monitor group -----

    if update_bottom:
        if bottom_mode == "panorama":
            if not panorama_paths:
                raise ValueError(
                    "panorama_paths are required when bottom_mode='panorama'."
                )

            if len(panorama_paths) != len(bottom_monitor_indices):
                raise ValueError(
                    "The number of panorama slices must match the number "
                    "of configured bottom monitors."
                )

            # Panorama monitor indices are configured in physical left-to-right order.
            for index, wallpaper_path in zip(
                bottom_monitor_indices,
                panorama_paths,
            ):
                monitor_id = wallpaper.GetMonitorDevicePathAt(index)
                wallpaper.SetWallpaper(
                    monitor_id,
                    str(wallpaper_path),
                )

        elif bottom_mode == "shared":
            if not bottom_path:
                raise ValueError(
                    "bottom_path is required when bottom_mode='shared'."
                )

            # The fast shared-wallpaper shortcut is safe only when the bottom
            # group contains every monitor except the configured top monitor.
            non_top_indices = {
                index
                for index in range(count)
                if index != top_monitor_index
            }

            configured_bottom_indices = set(bottom_monitor_indices)

            if (
                update_top
                and top_monitor_id is not None
                and configured_bottom_indices == non_top_indices
            ):
                wallpaper.SetWallpaper(None, bottom_path)

            else:
                for index in bottom_monitor_indices:
                    monitor_id = wallpaper.GetMonitorDevicePathAt(index)
                    wallpaper.SetWallpaper(monitor_id, bottom_path)

        else:
            raise ValueError(
                f"Unknown bottom monitor mode: {bottom_mode}"
            )

    # ----- Top monitor -----

    if update_top:
        if top_monitor_id is None:
            raise ValueError(
                "A top monitor index is required for a vertical wallpaper update."
            )

        if not top_path:
            raise ValueError(
                "top_path is required for a vertical wallpaper update."
            )

        wallpaper.SetWallpaper(top_monitor_id, top_path)


def set_wallpaper(path):
    SPI_SETDESKWALLPAPER = 20
    ctypes.windll.user32.SystemParametersInfoW(SPI_SETDESKWALLPAPER, 0, path, 3)
