; MicroBridge CLI - Inno Setup Script
; Save this as "installer_cli.iss"

#define MyAppName "MicroBridge CLI"
#define MyAppVersion "0.1.1"
#define MyAppPublisher "Rose Scott"
#define MyAppExeName "MicroBridge.exe"

[Setup]
; Basic app info (DIFFERENT GUID from GUI version!)
AppId={{7d4f8e2a-9b3c-4a1e-8f6d-2c5b9a7e4f3d}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppPublisher}\MicroBridge
DefaultGroupName=MicroBridge
; No admin rights needed
PrivilegesRequired=lowest
; Output configuration
OutputDir=installer_output
OutputBaseFilename=MicroBridge_CLI_Setup_v{#MyAppVersion}
Compression=lzma
SolidCompression=yes
; Modern UI
WizardStyle=modern
; Uninstall
UninstallDisplayIcon={app}\{#MyAppExeName}
; Add to PATH option
ChangesEnvironment=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "addtopath"; Description: "Add MicroBridge to system PATH (allows running from any command prompt)"; GroupDescription: "Additional options:"; Flags: unchecked

[Files]
; Main executable
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Start Menu shortcuts
Name: "{group}\MicroBridge CLI"; Filename: "cmd.exe"; Parameters: "/k cd /d ""{app}"" && echo MicroBridge CLI Ready. Type 'MicroBridge --help' for usage."; Comment: "Open command prompt in MicroBridge directory"
Name: "{group}\{cm:UninstallProgram,MicroBridge CLI}"; Filename: "{uninstallexe}"

[Registry]
; Add to PATH if user selected the option
Root: HKCU; Subkey: "Environment"; ValueType: expandsz; ValueName: "Path"; ValueData: "{olddata};{app}"; Tasks: addtopath; Check: NeedsAddPath('{app}')

[Code]
// Function to check if path already exists
function NeedsAddPath(Param: string): boolean;
var
  OrigPath: string;
begin
  if not RegQueryStringValue(HKEY_CURRENT_USER, 'Environment', 'Path', OrigPath) then
  begin
    Result := True;
    exit;
  end;
  Result := Pos(';' + Param + ';', ';' + OrigPath + ';') = 0;
end;

[Run]
; Don't auto-launch CLI (it's command-line only)
; Instead, show a message or open command prompt
Filename: "{app}\{#MyAppExeName}"; Parameters: "--help"; Flags: postinstall skipifsilent shellexec; Description: "View MicroBridge CLI help"
