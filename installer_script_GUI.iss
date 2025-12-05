; MicroBridge GUI - Inno Setup Script
; Save this as "installer_gui.iss"

#define MyAppName "MicroBridge GUI"
#define MyAppVersion "0.1"
#define MyAppPublisher "Rose Scott"
#define MyAppExeName "MicroBridge_GUI.exe"

[Setup]
; Basic app info
AppId={{3a2234f0-7e80-4e72-8e69-6cef270fd9c5}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppPublisher}\MicroBridge
DefaultGroupName=MicroBridge
; No admin rights needed
PrivilegesRequired=lowest
; Output configuration
OutputDir=installer_output
OutputBaseFilename=MicroBridge_GUI_Setup_v{#MyAppVersion}
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
; Main executable
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Start Menu shortcuts
Name: "{group}\MicroBridge GUI"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,MicroBridge}"; Filename: "{uninstallexe}"
; Desktop shortcut (if user selected it)
Name: "{autodesktop}\MicroBridge GUI"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
; Quick Launch (if user selected it)
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\MicroBridge GUI"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

[Run]
; Option to run after install
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
