#Requires AutoHotkey v2.0

; Add your own commands below. Each command needs a ;; @command annotation
; and a function prefixed with Cmd_. Optional ;; @desc, ;; @category annotations
; provide subtitle text and grouping.

;; @command Uppercase
;; @desc    Clipboard text to UPPER CASE
;; @category Text
Cmd_Uppercase(*) {
    if !ClipWait(2)
        return
    A_Clipboard := StrUpper(A_Clipboard)
}

;; @command Lowercase
;; @desc    Clipboard text to lower case
;; @category Text
Cmd_Lowercase(*) {
    if !ClipWait(2)
        return
    A_Clipboard := StrLower(A_Clipboard)
}

;; @command Title Case
;; @desc    Clipboard text to Title Case
;; @category Text
Cmd_TitleCase(*) {
    if !ClipWait(2)
        return
    A_Clipboard := StrTitle(A_Clipboard)
}

;; @command Trim Whitespace
;; @desc    Remove leading and trailing whitespace
;; @category Cleanup
Cmd_TrimWhitespace(*) {
    if !ClipWait(2)
        return
    A_Clipboard := Trim(A_Clipboard)
}

;; @command Timestamp
;; @desc    Copy current date and time to clipboard
;; @category Generate
Cmd_Timestamp(*) {
    A_Clipboard := FormatTime(, "yyyy-MM-dd HH:mm:ss")
}

;; @command UUID
;; @desc    Generate a random UUID v4
;; @category Generate
Cmd_UUID(*) {
    hex := "0123456789abcdef"
    result := ""
    loop 32 {
        i := A_Index
        if (i = 9 || i = 13 || i = 17 || i = 21)
            result .= "-"
        if (i = 13)
            result .= "4"
        else if (i = 17)
            result .= SubStr(hex, Random(9, 12), 1)
        else
            result .= SubStr(hex, Random(1, 16), 1)
    }
    A_Clipboard := result
}
