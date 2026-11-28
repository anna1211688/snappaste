; KIVO 安装脚本 (Inno Setup 6) —— 2026-11-27 品牌全量定名 KIVO (用户明确决定): 显示名/图标/安装包名/AppId/安装目录/数据目录全部换 KIVO, 不再保留旧品牌兼容标识; 旧版数据由应用自身的老数据搬移逻辑在首次运行时接管, [InstallDelete] 里的旧名是清理旧快捷方式的历史引用, 故意保留。
; 构建: iscc /DAppVersion=x.y.z KIVO.iss (GitHub Actions 自动执行, 本地也可跑)
; 设计要点: 按用户安装 (不弹管理员)、固定 AppId 实现原地升级覆盖、用户数据 %APPDATA%\KIVO 永不触碰。
#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif
#ifndef ExePath
  #define ExePath "dist\KIVO.exe"
#endif

[Setup]
AppId={{50750BB8-B534-4BAB-8D6F-E315C139C640}
AppName=KIVO
AppVersion={#AppVersion}
AppVerName=KIVO v{#AppVersion}
AppPublisher=KIVO
DefaultDirName={autopf}\KIVO
DefaultGroupName=KIVO
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=installer
OutputBaseFilename=KIVO-Setup-{#AppVersion}
SetupIconFile=KIVO.ico
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
AppMutex=KIVO_SingleInstance_Mutex
CloseApplications=yes
UninstallDisplayName=KIVO 启沃智能工作台
UninstallDisplayIcon={app}\KIVO.exe
VersionInfoVersion={#AppVersion}

[Languages]
Name: "chinesesimplified"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce

[InstallDelete]
; 清理旧版 SPST 的快捷方式与旧 exe (历史引用, 故意保留旧名; 改成 KIVO 会误删新装的快捷方式与主程序)
Type: files; Name: "{autodesktop}\SPST.lnk"
Type: files; Name: "{group}\SPST.lnk"
Type: files; Name: "{app}\SPST.exe"

[Files]
Source: "{#ExePath}"; DestDir: "{app}"; DestName: "KIVO.exe"; Flags: ignoreversion

[Icons]
Name: "{group}\KIVO"; Filename: "{app}\KIVO.exe"
Name: "{autodesktop}\KIVO"; Filename: "{app}\KIVO.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\KIVO.exe"; Description: "{cm:LaunchProgram,KIVO}"; Flags: nowait postinstall skipifsilent
