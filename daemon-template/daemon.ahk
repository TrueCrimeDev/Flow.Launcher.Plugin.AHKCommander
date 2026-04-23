#Requires AutoHotkey v2.0
#SingleInstance Force
Persistent

#Include %A_ScriptDir%\lib\Socket.ahk
#Include %A_ScriptDir%\lib\JXON.ahk
#Include %A_ScriptDir%\commands.ahk

global LISTEN_PORT := 19620
global CmdRegistry := Map()
global clients := Map()

ParseAnnotatedFile(A_ScriptDir "\commands.ahk", "Cmd_", &CmdRegistry)

try {
    global server := Socket.Server(LISTEN_PORT, "127.0.0.1")
    server.OnAccept := OnAcceptClient
} catch as e {
    MsgBox("Failed to start daemon on port " LISTEN_PORT ": " e.Message, "AHK Commander Daemon", 16)
    ExitApp
}

SetupTrayMenu()
TrayTip("AHK Commander daemon listening on port " LISTEN_PORT, "AHK Commander")
SetTimer(PollClients, 50)

OnAcceptClient(this_server, err) {
    if err
        return
    client := this_server.AcceptAsClient()
    clients[ObjPtr(client)] := client
}

PollClients() {
    toRemove := []
    for ptr, client in clients {
        try {
            if client.MsgSize() > 0 {
                data := client.RecvText()
                if data {
                    data := Trim(data, "`n`r `t")
                    request := Jxon_Load(&data)
                    response := Dispatch(request)
                    responseJson := Jxon_Dump(response, 0) "`n"
                    client.SendText(responseJson)
                }
                toRemove.Push(ptr)
            }
        } catch {
            toRemove.Push(ptr)
        }
    }
    for _, ptr in toRemove
        clients.Delete(ptr)
}

ParseAnnotatedFile(filePath, prefix, &registry) {
    registry := Map()
    if !FileExist(filePath)
        return
    content := FileRead(filePath)
    lines := StrSplit(content, "`n", "`r")
    cmdName := "", cmdDesc := "", cmdIcon := "", cmdCategory := "", cmdLine := 0
    for lineNum, line in lines {
        trimmed := Trim(line)
        if RegExMatch(trimmed, "^;;\s*@command\s+(.+)$", &m) {
            cmdName := Trim(m[1])
            cmdLine := lineNum
        } else if RegExMatch(trimmed, "^;;\s*@desc\s+(.+)$", &m) {
            cmdDesc := Trim(m[1])
        } else if RegExMatch(trimmed, "^;;\s*@icon\s+(.+)$", &m) {
            cmdIcon := Trim(m[1])
        } else if RegExMatch(trimmed, "^;;\s*@category\s+(.+)$", &m) {
            cmdCategory := Trim(m[1])
        } else if RegExMatch(trimmed, "^" prefix "(\w+)\s*\(", &m) {
            funcName := prefix m[1]
            if cmdName != "" {
                entry := Map()
                entry["func"] := funcName
                entry["desc"] := cmdDesc
                entry["icon"] := cmdIcon
                entry["category"] := cmdCategory
                entry["file"] := filePath
                entry["line"] := cmdLine
                registry[cmdName] := entry
            }
            cmdName := "", cmdDesc := "", cmdIcon := "", cmdCategory := "", cmdLine := 0
        }
    }
}

Dispatch(request) {
    id := request.Has("id") ? request["id"] : ""
    action := request.Has("action") ? request["action"] : ""
    name := request.Has("name") ? request["name"] : ""

    if (action = "ping")
        return Map("id", id, "ok", true, "result", "pong")

    if (action = "list") {
        items := []
        for cmdName, entry in CmdRegistry {
            item := Map()
            item["name"] := cmdName
            item["desc"] := entry["desc"]
            item["icon"] := entry["icon"]
            item["category"] := entry["category"]
            item["file"] := entry["file"]
            item["line"] := entry["line"]
            items.Push(item)
        }
        return Map("id", id, "ok", true, "result", items)
    }

    if (action = "exec") {
        if !CmdRegistry.Has(name)
            return Map("id", id, "ok", false, "error", "Command not found: " name)
        funcName := CmdRegistry[name]["func"]
        try {
            fn := %funcName%
            fn()
            return Map("id", id, "ok", true, "result", "Executed: " name)
        } catch as e {
            return Map("id", id, "ok", false, "error", e.Message)
        }
    }

    if (action = "reload") {
        resp := Map("id", id, "ok", true, "result", "Reloading daemon...")
        SetTimer(() => Reload(), -500)
        return resp
    }

    return Map("id", id, "ok", false, "error", "Unknown action: " action)
}

SetupTrayMenu() {
    A_TrayMenu.Delete()
    A_TrayMenu.Add("Reload commands.ahk", (*) => Reload())
    A_TrayMenu.Add("Open commands.ahk", (*) => Run(A_ScriptDir "\commands.ahk"))
    A_TrayMenu.Add()
    A_TrayMenu.Add("Quit", (*) => ExitApp())

    if FileExist(A_ScriptDir "\icon.ico")
        TraySetIcon(A_ScriptDir "\icon.ico")
}
