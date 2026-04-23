# AHK Commander

A [Flow Launcher](https://www.flowlauncher.com/) plugin that lists and runs your
AutoHotkey v2 functions from a single `commands.ahk` library.

Type `ahk` then start typing a command name. Pick one and the matching AHK
function runs instantly.

## Install

From Flow Launcher:

```
pm install AHK Commander
```

## Requirements

- Windows
- [AutoHotkey v2](https://www.autohotkey.com/) installed at the default location
  (or registered in `HKCU\Software\AutoHotkey` / `HKLM\Software\AutoHotkey`)

## First run

On first use the plugin seeds `%USERPROFILE%\.ahk-flow\` with:

```
.ahk-flow\
  daemon.ahk          The persistent listener (port 19620)
  commands.ahk        Your command library (sample provided)
  icon.ico            Tray icon
  lib\
    Socket.ahk        thqby's AHK v2 socket library
    JXON.ahk          Coco's JSON library
```

Existing files are preserved on plugin updates, so your `commands.ahk` is safe.

The first query launches `daemon.ahk` automatically. The daemon stays in the
tray and accepts JSON requests over a local TCP socket on `127.0.0.1:19620`.

## Adding commands

Edit `%USERPROFILE%\.ahk-flow\commands.ahk` and annotate each function:

```ahk
;; @command Uppercase
;; @desc    Clipboard text to UPPER CASE
;; @category Text
Cmd_Uppercase(*) {
    if !ClipWait(2)
        return
    A_Clipboard := StrUpper(A_Clipboard)
}
```

Conventions:

- The annotation block (`;; @command`, `;; @desc`, `;; @category`) must
  immediately precede the function definition.
- Function names start with `Cmd_`. The `;; @command` line is the display name
  shown in Flow.

After editing, type `ahk :reload` to re-parse the file.

## Context menu

Right-arrow on any result for:

- **Edit command** — opens `commands.ahk` at the function (uses VS Code's `code`
  command if on PATH, falls back to the default `.ahk` handler).
- **Copy command name**
- **Open file**

## Settings

| Keyword | Default | Notes |
|---------|---------|-------|
| `ahk`   | yes     | Change in Flow Launcher's plugin settings if you prefer |

## Credits

- [thqby/AHK-v2-libraries](https://github.com/thqby/ahk2_lib) — `Socket.ahk`
- [cocobelgica/AutoHotkey-JSON](https://github.com/cocobelgica/AutoHotkey-JSON) — `JXON.ahk`
- [pyflowlauncher](https://github.com/garulf/pyflowlauncher) — Python plugin runtime

## License

MIT
