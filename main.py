import os
import shutil
import subprocess
import sys

parent_folder_path = os.path.abspath(os.path.dirname(__file__))
sys.path.append(parent_folder_path)
sys.path.append(os.path.join(parent_folder_path, "lib"))
sys.path.append(os.path.join(parent_folder_path, "plugin"))

from pyflowlauncher import Plugin, Result, send_results

import ipc

ICON = "Images\\ahk.png"

plugin = Plugin()


@plugin.on_method
def query(query: str):
    q = query.strip()

    if not ipc.ping():
        ipc.ensure_daemon_files()
        return send_results([
            Result(
                Title="AHK Commander daemon not running",
                SubTitle="Press Enter to start the AHK v2 daemon",
                IcoPath=ICON,
                JsonRPCAction={"method": "start_daemon", "parameters": []},
            ),
            Result(
                Title="Edit commands.ahk",
                SubTitle=ipc.daemon_script_path().replace("daemon.ahk", "commands.ahk"),
                IcoPath=ICON,
                JsonRPCAction={
                    "method": "open_file",
                    "parameters": [os.path.join(ipc.DAEMON_HOME, "commands.ahk")],
                },
            ),
        ])

    if q.lower() == ":reload":
        return send_results([
            Result(
                Title="Reload commands.ahk",
                SubTitle="Re-parse the command file and refresh the list",
                IcoPath=ICON,
                JsonRPCAction={"method": "reload_commands", "parameters": []},
            )
        ])

    commands = ipc.get_commands("commands")

    results = []
    for cmd in commands:
        name = cmd.get("name", "")
        desc = cmd.get("desc", "")
        icon = cmd.get("icon") or ICON

        if q and not ipc.fuzzy_match(q, name):
            continue

        results.append(
            Result(
                Title=name,
                SubTitle=desc,
                IcoPath=icon,
                JsonRPCAction={"method": "execute_command", "parameters": [name]},
                ContextData=[name, cmd.get("file", ""), cmd.get("line", 0)],
            )
        )

    if not results and q:
        results.append(
            Result(
                Title=f"No commands matching '{q}'",
                SubTitle="Type 'ahk :reload' to refresh, or edit commands.ahk",
                IcoPath=ICON,
            )
        )

    return send_results(results)


@plugin.on_method
def context_menu(data):
    if not data or len(data) < 3:
        return send_results([])

    name, file_path, line = data[0], data[1], data[2]
    results = [
        Result(
            Title="Edit command",
            SubTitle=f"Open {os.path.basename(file_path)} at line {line}",
            IcoPath=ICON,
            JsonRPCAction={"method": "edit_command", "parameters": [file_path, line]},
        ),
        Result(
            Title="Copy command name",
            SubTitle=name,
            IcoPath=ICON,
            CopyText=name,
        ),
        Result(
            Title="Open file",
            SubTitle=file_path,
            IcoPath=ICON,
            JsonRPCAction={"method": "open_file", "parameters": [file_path]},
        ),
    ]
    return send_results(results)


@plugin.on_method
def execute_command(name: str):
    ipc.execute_command("commands", name)


@plugin.on_method
def reload_commands():
    ipc.reload_target("commands")


@plugin.on_method
def start_daemon():
    ipc.start_daemon()


@plugin.on_method
def edit_command(file_path: str, line: int):
    code = shutil.which("code") or shutil.which("code.cmd")
    if code:
        subprocess.Popen([code, "-g", f"{file_path}:{line}"], shell=False)
    else:
        os.startfile(file_path)


@plugin.on_method
def open_file(file_path: str):
    if os.path.exists(file_path):
        os.startfile(file_path)


if __name__ == "__main__":
    plugin.run()
