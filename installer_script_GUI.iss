; MicroBridge GUI - Inno Setup Script
; Save this as "installer_script_GUI.iss"

#define MyAppName "MicroBridge"
#define MyAppVersion "0.1"
#define MyAppPublisher "Rose Scott"
#define MyAppExeName "MicroBridge.exe"
#define MyAppURL "https://yourwebsite.com"

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
// Optional: Check if app is already running during uninstall
function InitializeUninstall(): Boolean;
var
  ErrorCode: Integer;
begin
  // Try to close the app gracefully
  if CheckForMutexes('MicroBridge') then
  begin
    if MsgBox('MicroBridge is currently running. Please close it before uninstalling.' + #13#10 + 'Do you want to continue anyway?', mbConfirmation, MB_YESNO) = IDNO then
    begin
      Result := False;
      Exit;
    end;
  end;
  Result := True;
end;
