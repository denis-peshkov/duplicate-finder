$ErrorActionPreference = 'Stop'

$toolsDir = "$(Split-Path -Parent $MyInvocation.MyCommand.Definition)"
Install-BinFile -Path "$toolsDir\DuplicateFinder.exe" -Name 'duplicate-finder'
