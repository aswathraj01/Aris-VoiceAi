param(
    [Parameter(Mandatory = $true)][string]$WavPath,
    [Parameter(Mandatory = $true, ValueFromRemainingArguments = $true)][string[]]$SpeechText
)
$ErrorActionPreference = 'Stop'
$text = ($SpeechText -join ' ').Trim()
if (-not $text) { throw 'Speech text is empty.' }
Add-Type -AssemblyName System.Speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
try {
    $synth.SetOutputToWaveFile($WavPath)
    $synth.Speak($text)
    $synth.SetOutputToNull()
} finally {
    $synth.Dispose()
}
if (-not (Test-Path -LiteralPath $WavPath) -or (Get-Item -LiteralPath $WavPath).Length -lt 44) {
    throw 'Windows speech synthesis did not create a valid WAV file.'
}
