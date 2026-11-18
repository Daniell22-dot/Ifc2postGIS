; Inno Setup Installer Script for ifc2postgis Tool
; -------------------------------------------------

[Setup]
; Basic information about the installer
AppName=ifc2postgis Tool
AppVersion=0.1.0
AppPublisher=Daniell22-dot
AppSupportURL=https://github.com/Daniell22-dot/Ifc2postGIS
Unicode=true
DefaultLanguage english

[Languages]
Name: english; MessagesFile: compiler:inglish.isl

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut to ifc2postgis CLI"; Flags: skipifdisabled

[Files]
; Copy ifc2postgis module files
Source: "D:\Ifc2postGIS\ifc2postgis\__init__.py"; DestDir: "{app}"; Flags: ignoreknownfiles
Source: "D:\Ifc2postGIS\ifc2postgis\cli.py"; DestDir: "{app}"; Flags: ignoreknownfiles
Source: "D:\Ifc2postGIS\ifc2postgis\database.py"; DestDir: "{app}"; Flags: ignoreknownfiles
Source: "D:\Ifc2postGIS\ifc2postgis\parser.py"; DestDir: "{app}"; Flags: ignoreknownfiles
Source: "D:\Ifc2postGIS\SOE.ifc"; DestDir: "{app}"; Flags: ignoreknownfiles
Source: "D:\Ifc2postGIS\pyproject.toml"; DestDir: "{app}"; Flags: ignoreknownfiles
Source: "D:\Ifc2postGIS\README.md"; DestDir: "{app}"; Flags: ignoreknownfiles

; Create desktop shortcut
Source: "{cmddesktop}\ifc2postgis CLI.lnk"; DestDir: "{desk}"; Tasks: desktopicon

[Icons]
Name: "{usersappdata}\Microsoft\Windows\Start Menu\Programs\ifc2postgis Tool"; Filename: "{app}\cli.py"
Name: "{desktop}\ifc2postgis CLI"; Filename: "{app}\cli.py"; Tasks: desktopicon

[Run]
Filename: "{code}"; Status: skip
; After installation, user can run:
; python "{app}\cli.py" --help
; python "{app}\cli.py" --input model.ifc --db-url "postgresql://..." --srid 4326