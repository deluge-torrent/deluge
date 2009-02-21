; Deluge Windows Installer Script
; Written By John Garland <johnnybg@gmail.com>
; Date: 21/02/09

; Includes

    !include "MUI2.nsh"

; General Settings

	; Version
	!define DELUGE_VERSION "1.1.3"
	!define SCRIPT_VERSION "0.2"

    ; Name
    Name "Deluge ${DELUGE_VERSION}"
    OutFile "deluge.exe"

    ; Default install dir
    InstallDir "$PROGRAMFILES"

    ; Compress by default
    SetCompressor lzma

    ; Brand
    BrandingText "Deluge Windows Installer v${SCRIPT_VERSION}"

    !ifndef NOINSTTYPES
        InstType "Full"
        InstType "Upgrade"
    !endif
	
; Defines

    ; Base URL for installers
    !define BASE "http://download.deluge-torrent.org/windows/deps/"

    ; Installer names
    !define DELUGE_INSTALLER "deluge-1.1.3.win32-py2.5.msi"
    !define PYTHON_INSTALLER "python-2.5.4.msi"
    !define PYWIN32_INSTALLER "pywin32-212.win32-py2.5.exe"
    !define GTK+_INSTALLER "gtk-2.12.9-win32-2.exe"
    !define PYGTK_INSTALLER "pygtk-2.12.1-2.win32-py2.5.exe"
    !define PYXDG_INSTALLER "pyxdg-0.17.win32-py2.5.exe"
    !define SETUPTOOLS_INSTALLER "setuptools-0.6c9.win32-py2.5.exe"
    !define LIBTORRENT_INSTALLER "python-libtorrent-0.14.2.win32-py2.5.msi"
    !define LIBTORRENT_DLL "MSVCP71.DLL"
    !define LIBTORRENT_DLL_ZIP "${LIBTORRENT_DLL}.zip"

    ; Installer URLs
    !define DELUGE_INSTALLER_URL "${BASE}\DELUGE_INSTALLER"
    !define PYTHON_INSTALLER_URL "${BASE}\PYTHON_INSTALLER"
    !define PYWIN32_INSTALLER_URL "${BASE}\PYWIN32_INSTALLER"
    !define GTK+_INSTALLER_URL "${BASE}\GTK+_INSTALLER"
    !define PYGTK_INSTALLER_URL "${BASE}\PYGTK_INSTALLER"
    !define PYXDG_INSTALLER_URL "${BASE}\PYXDG_INSTALLER"
    !define SETUPTOOLS_INSTALLER_URL "${BASE}\SETUPTOOLS_INSTALLER"
    !define LIBTORRENT_INSTALLER_URL "${BASE}\LIBTORRENT_INSTALLER"
    !define LIBTORRENT_DLL_ZIP_URL "${BASE}\LIBTORRENT_DLL_ZIP"

    ; Redefine macros/functions
    !define download "NSISdl::download"
    !define install_NSIS "!insertmacro install_NSIS"
    !define install_MSI "!insertmacro install_MSI"
    !define install_ZIP "!insertmacro install_ZIP"


; Interface Settings

    ; Installer
    !define MUI_ICON "..\deluge\data\pixmaps\deluge.ico"
    !define MUI_HEADERIMAGE
	!define MUI_HEADERIMAGE_RIGHT
    !define MUI_HEADERIMAGE_BITMAP "installer-top.bmp"
    !define MUI_WELCOMEFINISHPAGE_BITMAP "installer-side.bmp"
	!define MUI_COMPONENTSPAGE_SMALLDESC
    !define MUI_ABORTWARNING

    ; Uninstaller
    !define MUI_UNICON "..\deluge\data\pixmaps\deluge.ico"
    !define MUI_HEADERIMAGE_UNBITMAP "installer-top.bmp"
    !define MUI_WELCOMEFINISHPAGE_UNBITMAP "installer-side.bmp"

; Pages

    ; Installation

        !insertmacro MUI_PAGE_WELCOME
        !insertmacro MUI_PAGE_LICENSE "..\LICENSE"
        !insertmacro MUI_PAGE_COMPONENTS
        !insertmacro MUI_PAGE_DIRECTORY
        !insertmacro MUI_PAGE_INSTFILES
        !insertmacro MUI_PAGE_FINISH

    ; Uninstallation
    
        !insertmacro MUI_UNPAGE_CONFIRM
        !insertmacro MUI_UNPAGE_INSTFILES
        !insertmacro MUI_UNPAGE_FINISH

; Languages

    !insertmacro MUI_LANGUAGE "English"
    ; Should put all languages deluge supports here

; Macros
	
    !macro install_NSIS installer_name install_dir
		${download} "${${installer_name}_URL}" "$TEMP\${${installer_name}}"
        ExecWait '"$TEMP\${${installer_name}}" /S /D=${install_dir}\GTK+'
		delete "$TEMP\${${installer_name}}"
    !macroend

	!macro install_MSI installer_name install_dir
		${download} "${${installer_name}_URL}" "$TEMP\${${installer_name}}"
        ExecWait 'msiexec /qn /i "$TEMP\${${installer_name}}" TARGETDIR="${install_dir}'
		delete "$TEMP\${${installer_name}}"
	!macroend

    !macro install_ZIP installer_name install_dir
		${download} "${${installer_name}_URL}" "$TEMP\${${installer_name}}"
        nsisunz::Unzip "$TEMP\${${installer_name}}" "${install_dir}"
		delete "$TEMP\${${installer_name}}"
    !macroend
	
; Installer Sections

SubSection /e "Core" core

    Section "Deluge" deluge

        SectionIn RO

        ${install_MSI} DELUGE_INSTALLER "$INSTDIR\Deluge"

        WriteUninstaller "$INSTDIR\Deluge\uninstall.exe"

    SectionEnd

SubSectionEnd

SubSection /e "Dependencies" dependencies

    Section "Python" python

        SectionIn 1

        ${install_MSI} PYTHON_INSTALLER "$INSTDIR\Python"

    SectionEnd

    Section "Python Win32 Extensions" pywin32

        SectionIn 1

        ${install_ZIP} PYWIN32_INSTALLER "$INSTDIR\Python\site-packages"

    SectionEnd

    Section "GTK+ Runtime" gtk+

        SectionIn 1

        ${install_NSIS} GTK+_INSTALLER "$INSTDIR\GTK+"

    SectionEnd

    Section "PyGTK" pygtk

        SectionIn 1

        ${install_ZIP} PYGTK_INSTALLER "$INSTDIR\Python\site-packages"

    SectionEnd

    Section "PyXdg" pyxdg

        SectionIn 1

        ${install_MSI} PYXDG_INSTALLER "$INSTDIR\Python\site-packages"

    SectionEnd

    Section "Setuptools" setuptools

        SectionIn 1

        ${install_ZIP} SETUPTOOLS_INSTALLER "$INSTDIR\Python\site-packages"

    SectionEnd

    Section "libtorrent" libtorrent

        SectionIn 1

        ${install_MSI} LIBTORRENT_INSTALLER "$INSTDIR\Python\site-packages"
        ${install_ZIP} LIBTORRENT_DLL_ZIP "$SYSDIR"
        RegDLL "$SYSDIR\${LIBTORRENT_DLL}"

    SectionEnd

SubSectionEnd

; Descriptions

    ; Language strings
    LangString DESC_deluge ${LANG_ENGLISH} "Deluge 1.1.3"
    LangString DESC_python ${LANG_ENGLISH} "Python 2.5.4"

    ; Assign language strings to sections
    !insertmacro  MUI_FUNCTION_DESCRIPTION_BEGIN
        !insertmacro MUI_DESCRIPTION_TEXT ${deluge} $(DESC_deluge)
        !insertmacro MUI_DESCRIPTION_TEXT ${python} $(DESC_python)
    !insertmacro  MUI_FUNCTION_DESCRIPTION_END

; Uninstaller Section

Section "Uninstall"

    Delete "$INSTDIR\Deluge\uninstall.exe"
    RMDir "$INSTDIR"

SectionEnd
