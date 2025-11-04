function Parse-CodexDsl {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string[]] $Lines
    )
    $steps = @()
    for ($i = 0; $i -lt $Lines.Count; $i++) {
        $text = $Lines[$i].Trim()
        if ($text -eq "" -or $text.StartsWith("#")) { continue }

        if ($text -match '^CleanLedger\s+"([^"]+)"$') {
            $steps += @{ Type = "CleanLedger"; Path = $Matches[1] }
        }
        elseif ($text -match '^Snapshot\s+"([^"]+)"\s*,\s*"([^"]+)"$') {
            $steps += @{ Type = "Snapshot"; Src = $Matches[1]; Dest = $Matches[2] }
        }
        elseif ($text -match '^Validate\s+"([^"]+)"$') {
            $steps += @{ Type = "Validate"; Script = $Matches[1] }
        }
        elseif ($text -match '^Handshake\s*\{$') {
            $body = ""
            while ($true) {
                $i++
                if ($i -ge $Lines.Count) { throw "Handshake block not closed at line $i" }
                $ln = $Lines[$i].Trim()
                if ($ln -eq "}") { break }
                $body += $ln + ";"
            }
            $pairs = $body.Split(";") | Where-Object { $_ -ne "" }
            $h = @{}
            foreach ($p in $pairs) {
                if ($p -match '^(script|ledger|output)\s*=\s*"([^"]+)"$') {
                    $h[$Matches[1]] = $Matches[2]
                } else {
                    throw "Invalid Handshake entry '$p' at line $i"
                }
            }
            foreach ($k in 'script','ledger','output') {
                if (-not $h.ContainsKey($k)) { throw "Missing Handshake key '$k' at line $i" }
            }
            $steps += @{ Type = "Handshake"; Params = $h }
        }
        else {
            throw "Unrecognized DSL line '$text' at line $i"
        }
    }
    return $steps
}

Export-ModuleMember -Function Parse-CodexDsl
