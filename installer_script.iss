; NDP to LMD Converter - Inno Setup Script
; Save this as "installer_script.iss"

#define MyAppName "NDP to LMD Converter"
#define MyAppVersion "1.0"
#define MyAppPublisher "Your Name/Organization"
#define MyAppExeName "NDP_to_LMD_Converter.exe"

[Setup]
; Basic app info
AppId={{YOUR-UNIQUE-GUID-HERE}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
; No admin rights needed
PrivilegesRequired=lowest
; Output configuration
OutputDir=installer_output
OutputBaseFilename=NDP_to_LMD_Converter_Setup
Compression=lzma
SolidCompression=yes
; Modern UI
WizardStyle=modern
; Uninstall
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Files]
; Main executable (update the Source path to where your .exe is located)
Source: "dist\NDP_to_LMD_Converter.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Start Menu shortcuts
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
; Desktop shortcut (if user selected it)
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
; Quick Launch (if user selected it)
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

[Run]
; Option to run after install
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
