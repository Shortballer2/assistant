[Setup]
AppName=Personal Assistant
AppVersion=1.0.0
DefaultDirName={autopf}\Personal Assistant
DefaultGroupName=Personal Assistant
OutputBaseFilename=PersonalAssistantInstaller
Compression=lzma
SolidCompression=yes

[Files]
Source: "dist\PersonalAssistant.exe"; DestDir: "{app}"

[Icons]
Name: "{group}\Personal Assistant"; Filename: "{app}\PersonalAssistant.exe"
Name: "{autodesktop}\Personal Assistant"; Filename: "{app}\PersonalAssistant.exe"

[Run]
Filename: "{app}\PersonalAssistant.exe"; Description: "Launch Personal Assistant"; Flags: nowait postinstall skipifsilent
