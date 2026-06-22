import os
import json
import time
import zlib

import hid

VENDOR_ID = 0x054C
PRODUCT_IDS = {0x05C4, 0x09CC}  # DS4 v1 and v2

CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".config", "ds4color")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")

PALETTE = {
    "blue": (0, 0, 255),
    "red": (255, 0, 0),
    "green": (0, 255, 0),
    "cyan": (0, 255, 255),
    "magenta": (255, 0, 255),
    "pink": (255, 40, 120),
    "purple": (140, 0, 255),
    "orange": (255, 90, 0),
    "yellow": (255, 200, 0),
    "white": (255, 255, 255),
    "warm": (255, 120, 30),
}


def load_config():
    try:
        with open(CONFIG_PATH) as f:
            cfg = json.load(f)
    except Exception:
        cfg = {}
    cfg.setdefault("color", "blue")
    cfg.setdefault("brightness", 100)
    cfg.setdefault("controller_serial", None)
    presets = cfg.setdefault("presets", {})
    presets.setdefault("day", {"color": "blue", "brightness": 100})
    presets.setdefault("night", {"color": "warm", "brightness": 12})
    return cfg


def save_config(cfg):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2)
        f.write("\n")


def resolve_rgb(color, brightness):
    base = PALETTE.get(color.lower(), PALETTE["blue"]) if isinstance(color, str) else tuple(int(c) for c in color)
    scale = max(0, min(100, int(brightness))) / 100.0
    return tuple(max(0, min(255, round(c * scale))) for c in base)


def find_target(serial=None):
    want = (serial or "").upper() or None
    for d in hid.enumerate():
        if d.get("vendor_id") == VENDOR_ID and d.get("product_id") in PRODUCT_IDS:
            ser = (d.get("serial_number") or "").upper()
            if want is None or ser == want:
                return d
    return None


def _usb_report(r, g, b):
    buf = bytearray(32)
    buf[0] = 0x05
    buf[1] = 0xFF
    buf[6], buf[7], buf[8] = r, g, b
    return bytes(buf)


def _bt_report(r, g, b):
    buf = bytearray(78)
    buf[0] = 0x11
    buf[1] = 0xC0
    buf[3] = 0x07
    buf[8], buf[9], buf[10] = r, g, b
    # DS4 checks a CRC32 over a 0xA2 prefix plus the report, or it ignores us
    crc = zlib.crc32(bytes([0xA2]) + bytes(buf[0:74])) & 0xFFFFFFFF
    buf[74:78] = crc.to_bytes(4, "little")
    return bytes(buf)


def _read_input(h, attempts=12, timeout_ms=200):
    for _ in range(attempts):
        try:
            data = h.read(128, timeout_ms)
        except TypeError:
            h.set_nonblocking(False)
            data = h.read(128)
        if data and len(data) >= 10:
            return data[0], len(data)
        time.sleep(0.02)
    return None


def apply(rgb, serial=None):
    d = find_target(serial)
    if not d:
        return 3, "controller not found"

    h = hid.device()
    try:
        try:
            h.open_path(d["path"])
        except Exception:
            h.open(VENDOR_ID, d["product_id"])
    except Exception as e:
        return 5, "could not open device: %s" % e

    try:
        rid = _read_input(h)
        if rid is None:
            return 4, "connected but no input yet, leaving the light alone"
        report_id, length = rid
        over_bt = report_id == 0x11 or length >= 70
        rep = _bt_report(*rgb) if over_bt else _usb_report(*rgb)
        if h.write(rep) <= 0:
            return 6, "input works but writing the color failed"
        return 0, "%s ok, set RGB%s" % ("bluetooth" if over_bt else "usb", rgb)
    finally:
        h.close()


def apply_from_config():
    cfg = load_config()
    return apply(resolve_rgb(cfg["color"], cfg["brightness"]), cfg.get("controller_serial"))
