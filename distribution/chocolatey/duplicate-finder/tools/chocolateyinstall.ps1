$ErrorActionPreference = 'Stop'

$toolsDir = "$(Split-Path -Parent $MyInvocation.MyCommand.Definition)"
Install-BinFile -Path "$toolsDir\duplicate-finder.exe" -Name 'duplicate-finder'
