"""Shared IPC helper for communicating with the AHK daemon."""
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import uuid
import winreg

DAEMON_HOST = "127.0.0.1"
DAEMON_PORT = 19620
CONNECT_TIMEOUT = 2.0
READ_TIMEOUT = 5.0


def _find_ahk_exe():
    """Detect AHK v2 executable from registry or common paths."""
    for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
        try:
            with winreg.OpenKey(hive, r"Software\AutoHotkey") as key:
                install_dir = winreg.QueryValueEx(key, "InstallDir")[0]
                exe = os.path.join(install_dir, "v2", "AutoHotkey64.exe")
                if os.path.isfile(exe):
                    return exe
                exe = os.path.join(install_dir, "v2", "AutoHotkey32.exe")
                if os.path.isfile(exe):
                    return exe
        except OSError:
            continue
    for path in [
        r"C:\Program Files\AutoHotkey\v2\AutoHotkey64.exe",
        r"C:\Program Files\AutoHotkey\v2\AutoHotkey32.exe",
    ]:
        if os.path.isfile(path):
            return path
    return None


def _daemon_script_path():
    return os.path.join(os.path.expanduser("~"), ".ahk-flow", "daemon.ahk")


def _send_request(payload, timeout=READ_TIMEOUT):
    payload.setdefault("id", str(uuid.uuid4()))
    raw = json.dumps(payload) + "\n"
    with socket.create_connection(
        (DAEMON_HOST, DAEMON_PORT), timeout=CONNECT_TIMEOUT
    ) as s:
        s.settimeout(timeout)
        s.sendall(raw.encode("utf-8"))
        buf = b""
        while b"\n" not in buf:
            chunk = s.recv(4096)
            if not chunk:
                break
            buf += chunk
    return json.loads(buf.decode("utf-8"))


def ping():
    try:
        resp = _send_request({"action": "ping"}, timeout=2.0)
        return resp.get("ok", False)
    except Exception:
        return False


def start_daemon():
    if ping():
        return True
    ahk_exe = _find_ahk_exe()
    daemon_path = _daemon_script_path()
    if not ahk_exe or not os.path.isfile(daemon_path):
        return False
    subprocess.Popen(
        [ahk_exe, daemon_path],
        creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NO_WINDOW,
    )
    for _ in range(10):
        time.sleep(0.3)
        if ping():
            return True
    return False


def ensure_daemon():
    if ping():
        return True
    return start_daemon()


def ipc(payload, timeout=READ_TIMEOUT):
    try:
        return _send_request(payload, timeout)
    except (ConnectionRefusedError, OSError):
        if start_daemon():
            try:
                return _send_request(payload, timeout)
            except Exception:
                return None
        return None


def _cache_path(target):
    return os.path.join(tempfile.gettempdir(), f"ahk_flow_{target}_cache.json")


def get_commands(target, max_age=60):
    cache_file = _cache_path(target)
    if os.path.isfile(cache_file):
        age = time.time() - os.path.getmtime(cache_file)
        if age < max_age:
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
    resp = ipc({"action": "list", "target": target})
    if resp and resp.get("ok"):
        commands = resp["result"]
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(commands, f)
        except IOError:
            pass
        return commands
    return []


def invalidate_cache(target):
    cache_file = _cache_path(target)
    if os.path.isfile(cache_file):
        os.remove(cache_file)


def execute_command(target, name):
    return ipc({"action": "exec", "target": target, "name": name})


def reload_target(target):
    invalidate_cache(target)
    return ipc({"action": "reload", "target": target})


def fuzzy_match(query, target):
    qi = 0
    q_lower = query.lower()
    t_lower = target.lower()
    for ch in t_lower:
        if qi < len(q_lower) and ch == q_lower[qi]:
            qi += 1
    return qi == len(q_lower)
