import os
import sys
import subprocess

LABEL = "com.ds4color.agent"
PLIST = os.path.join(os.path.expanduser("~"), "Library", "LaunchAgents", LABEL + ".plist")
LOG = os.path.join(os.path.expanduser("~"), ".config", "ds4color", "watch.log")

PLIST_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{label}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{python}</string>
        <string>-m</string>
        <string>ds4color.watch</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>ThrottleInterval</key>
    <integer>5</integer>
    <key>StandardOutPath</key>
    <string>{log}</string>
    <key>StandardErrorPath</key>
    <string>{log}</string>
</dict>
</plist>
"""


def _domain():
    return "gui/%d" % os.getuid()


def is_running():
    r = subprocess.run(["launchctl", "print", "%s/%s" % (_domain(), LABEL)],
                       capture_output=True)
    return r.returncode == 0


def enable():
    os.makedirs(os.path.dirname(PLIST), exist_ok=True)
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(PLIST, "w") as f:
        f.write(PLIST_TEMPLATE.format(label=LABEL, python=sys.executable, log=LOG))
    subprocess.run(["launchctl", "bootout", "%s/%s" % (_domain(), LABEL)], capture_output=True)
    r = subprocess.run(["launchctl", "bootstrap", _domain(), PLIST], capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr.strip() or "failed to start the agent")
        return 1
    print("agent enabled, runs at login")
    return 0


def disable():
    subprocess.run(["launchctl", "bootout", "%s/%s" % (_domain(), LABEL)], capture_output=True)
    try:
        os.remove(PLIST)
    except FileNotFoundError:
        pass
    print("agent disabled")
    return 0
