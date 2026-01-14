; MicroBridge GUI - Inno Setup Script
; Save this as "installer_script_GUI.iss"

#define MyAppName "MicroBridge"
#define MyAppVersion "0.1.1"
#define MyAppPublisher "Rose Scott"
#define MyAppExeName "MicroBridge.exe"
#define MyAppURL "https://github.com/Snowman-scott/MicroBridge"

[Setup]
; Basic app info
AppId={{3a2234f0-7e80-4e72-8e69-6cef270fd9c5}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppPublisher}\MicroBridge
DefaultGroupName=MicroBridge
; Allow non-admin installation (user can override)
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
; Output configuration
OutputDir=installer_output
OutputBaseFilename=MicroBridge_Setup_v{#MyAppVersion}
Compression=lzma2/max
SolidCompression=yes
; Modern UI
WizardStyle=modern
; Uninstall
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}
; Optional: Add setup icon (if you have one)
; SetupIconFile=MicroBridge_Icon.ico

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Main executable
Source: "MicroBridge_\MicroBridge\MicroBridge.exe"; DestDir: "{app}"; Flags: ignoreversion
; Include ALL files from _internal folder (all dependencies)
Source: "MicroBridge_\MicroBridge\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs
; Optional: Include icon file if you want it accessible
; Source: "MicroBridge_Icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Start Menu shortcuts
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
; Desktop shortcut (if user selected it)
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
; Option to run after install
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
// Check if app is already running during uninstall
function InitializeUninstall(): Boolean;
begin
  // Note: The Python GUI doesn't create a named mutex, so we can't reliably detect if it's running.
  // Instead, we warn the user to close it manually.
  if MsgBox('Please ensure MicroBridge is closed before continuing with uninstall.' + #13#10 + 'Do you want to proceed with uninstall?', mbConfirmation, MB_YESNO) = IDYES then
  begin
    Result := True;
  end
  else
  begin
    Result := False;
  end;
end;
