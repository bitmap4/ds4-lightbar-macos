import sys

from . import core
from . import agent

USAGE = """ds4color - set the DS4 lightbar color

  ds4color                 show current setting and status
  ds4color list            list named colors
  ds4color blue            set a color
  ds4color blue 20         set color and brightness (percent)
  ds4color 20              set brightness only
  ds4color 255 90 0        custom rgb
  ds4color 255 90 0 40     custom rgb and brightness
  ds4color night           load the night preset
  ds4color day             load the day preset
  ds4color presets         list presets
  ds4color save night      save the current setting as a preset
  ds4color bind            lock to the controller connected right now
  ds4color unbind          allow any DualShock 4
  ds4color enable          start the background agent (sets color on connect)
  ds4color disable         stop the background agent
"""


def status():
    cfg = core.load_config()
    bound = cfg.get("controller_serial")
    print("color:", cfg["color"])
    print("brightness:", str(cfg["brightness"]) + "%")
    print("rgb:", core.resolve_rgb(cfg["color"], cfg["brightness"]))
    print("bound to:", bound if bound else "any DualShock 4")
    print("controller:", "connected" if core.find_target(bound) else "not connected")
    print("agent:", "running" if agent.is_running() else "stopped")


def is_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


def main():
    args = sys.argv[1:]
    cfg = core.load_config()

    if not args:
        status()
        return 0

    cmd = args[0].lower()
    if cmd in ("list", "colors"):
        print(", ".join(sorted(core.PALETTE)))
        return 0
    if cmd in ("status", "-s"):
        status()
        return 0
    if cmd == "enable":
        return agent.enable()
    if cmd == "disable":
        return agent.disable()
    if cmd in ("presets", "preset"):
        for name, p in cfg["presets"].items():
            print(name, p["color"], str(p["brightness"]) + "%")
        return 0
    if cmd == "bind":
        dev = core.find_target(None)
        if not dev:
            print("no controller connected")
            return 3
        cfg["controller_serial"] = dev.get("serial_number") or ""
        core.save_config(cfg)
        print("bound to", cfg["controller_serial"] or "(empty serial)")
        return 0
    if cmd == "unbind":
        cfg["controller_serial"] = None
        core.save_config(cfg)
        print("unbound")
        return 0
    if cmd == "save" and len(args) >= 2:
        name = args[1].lower()
        cfg["presets"][name] = {"color": cfg["color"], "brightness": cfg["brightness"]}
        core.save_config(cfg)
        print("saved preset", name)
        return 0
    if cmd in cfg["presets"]:
        cfg.update(cfg["presets"][cmd])
        core.save_config(cfg)
        print(cmd, "->", core.resolve_rgb(cfg["color"], cfg["brightness"]))
        print(core.apply_from_config()[1])
        return 0

    ints = [int(a) for a in args if is_int(a)]
    names = [a for a in args if not is_int(a)]

    if names and names[0].lower() in core.PALETTE:
        cfg["color"] = names[0].lower()
        if ints:
            cfg["brightness"] = ints[0]
    elif len(ints) >= 3:
        cfg["color"] = ints[:3]
        if len(ints) >= 4:
            cfg["brightness"] = ints[3]
    elif len(ints) == 1:
        cfg["brightness"] = ints[0]
    else:
        print(USAGE)
        return 2

    cfg["brightness"] = max(0, min(100, int(cfg["brightness"]))) 
    core.save_config(cfg)
    print("rgb:", core.resolve_rgb(cfg["color"], cfg["brightness"]))
    print(core.apply_from_config()[1])
    return 0


if __name__ == "__main__":
    sys.exit(main())
