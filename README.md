# ds4-lightbar-macos

A DualShock 4 connected to a Mac over Bluetooth never gets told what colour to
make its lightbar, so it just pulses white forever even though it works fine.
On a PS4 the console sends that command; macOS doesn't. This is a tiny tool
that sends it, so the light goes solid instead.

It also sets the colour automatically every time the controller connects, over
USB or Bluetooth, and only after it has read a real input report from the pad.
That last part matters: if the light goes solid, the controller is genuinely
connected and sending input. If it stays blinking white, something is wrong
with the connection and you know not to trust it.

## Install

Homebrew:

```bash
brew install bitmap4/tap/ds4color
ds4color enable
```

Or with pipx:

```bash
pipx install ds4color
ds4color enable
```

`ds4color enable` starts a small background agent that runs at login and sets
the colour whenever the controller connects. `ds4color disable` stops it.

## Usage

```bash
ds4color              # current setting and whether the pad is connected
ds4color blue         # pick a colour
ds4color blue 20      # colour at 20% brightness
ds4color 20           # just the brightness
ds4color 255 90 0     # custom rgb
ds4color night        # dim warm preset
ds4color day          # bright blue preset
ds4color list         # named colours
ds4color presets      # saved presets
ds4color save night   # save the current setting as a preset
```

Changes apply right away if the pad is connected, and the agent reuses them on
every reconnect.

If you own more than one DS4 and want this to touch only one of them, connect
that one and run `ds4color bind`. `ds4color unbind` goes back to matching any
DualShock 4.

## Config

`~/.config/ds4color/config.json`:

```json
{
  "color": "blue",
  "brightness": 100,
  "controller_serial": null,
  "presets": {
    "day":   { "color": "blue", "brightness": 100 },
    "night": { "color": "warm", "brightness": 12 }
  }
}
```

`controller_serial` is the controller's Bluetooth MAC (the DS4 reports the same
value over USB). Leave it `null` to match any DS4.

## How it works

Setting the lightbar is a HID output report. Over USB it's report `0x05`; over
Bluetooth it's report `0x11` with a CRC32 the controller checks before it
listens. The tool figures out which transport you're on by looking at the input
report the pad sends back, then writes the matching one. That's the whole trick.

## Uninstall

```bash
ds4color disable
brew uninstall ds4color   # or: pipx uninstall ds4color
```

## License

MIT
