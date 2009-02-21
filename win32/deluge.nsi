; Deluge Windows Installer Script
; Written By John Garland <johnnybg@gmail.com>
; Date: 21/02/09

; Includes

    !include "MUI2.nsh"

; General Settings

    ; Name
    Name "Deluge"
    OutFile "deluge.exe"

    ; Default install dir
    InstallDir "$PROGRAMFILES"

    ; Compress by default
    SetCompressor lzma

    ; Brand
    BrandingText "Deluge Windows Installer"

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

    ; Installer URLs
    !define DELUGE_INSTALLER_URL "${BASE}\DELUGE_INSTALLER"
    !define PYTHON_INSTALLER_URL "${BASE}\PYTHON_INSTALLER"
    !define PYWIN32_INSTALLER_URL "${BASE}\PYWIN32_INSTALLER"
    !define GTK+_INSTALLER_URL "${BASE}\GTK+_INSTALLER"
    !define PYGTK_INSTALLER_URL "${BASE}\PYGTK_INSTALLER"
    !define PYXDG_INSTALLER_URL "${BASE}\PYXDG_INSTALLER"
    !define SETUPTOOLS_INSTALLER_URL "${BASE}\SETUPTOOLS_INSTALLER"
    !define LIBTORRENT_INSTALLER_URL "${BASE}\LIBTORRENT_INSTALLER"
    !define LIBTORRENT_DLL_URL "${BASE}\LIBTORRENT_DLL"

    ; Redefine macros/functions
    !define download "NSISdl::download"
    !define install "!insertmacro install"


; Interface Settings

    ; Installer
    !define MUI_ICON "..\deluge\data\pixmaps\deluge.ico"
    !define MUI_HEADERIMAGE
    !define MUI_HEADERIMAGE_BITMAP "installer-top.bmp"
    !define MUI_WELCOMEFINISHPAGE_BITMAP "installer-side.bmp"
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

; Installer Sections

SubSection /e "Core" core

    Section "Deluge" deluge

        SectionIn RO

        ${install} DELUGE_INSTALLER

        WriteUninstaller "$INSTDIR\Deluge\uninstall.exe"

    SectionEnd

SubSectionEnd

SubSection /e "Dependencies" dependencies

    Section "Python" python

        SectionIn 1

        ${install} PYTHON_INSTALLER

    SectionEnd

    Section "Python Win32 Extensions" pywin32

        SectionIn 1

        ${install} PYWIN32_INSTALLER

    SectionEnd

    Section "GTK+ Runtime" gtk+

        SectionIn 1

        ${install} GTK+_INSTALLER

    SectionEnd

    Section "PyGTK" pygtk

        SectionIn 1

        ${install} PYGTK_INSTALLER

    SectionEnd

    Section "PyXdg" pyxdg

        SectionIn 1

        ${install} PYXDG_INSTALLER

    SectionEnd

    Section "Setuptools" setuptools

        SectionIn 1

        ${install} SETUPTOOLS_INSTALLER

    SectionEnd

    Section "libtorrent" libtorrent

        SectionIn 1

        ${install} LIBTORRENT_INSTALLER
        ${install} LIBTORRENT_DLL

    SectionEnd

SubSectionEnd

; Descriptions

    ; Language strings
    LangString DESC_deluge ${LANG_ENGLISH} "Core section."

    ; Assign language strings to sections
    !insertmacro  MUI_FUNCTION_DESCRIPTION_BEGIN
        !insertmacro MUI_DESCRIPTION_TEXT ${deluge} $(DESC_deluge)
    !insertmacro  MUI_FUNCTION_DESCRIPTION_END

; Uninstaller Section

Section "Uninstall"

    Delete "$INSTDIR\Deluge\uninstall.exe"
    RMDir "$INSTDIR"

SectionEnd

; Macros
!macro install installer_name
    ${download} "${${installer_name}_URL}" "$TEMP\${${installer_name}}"
    delete "$TEMP\${installer_name}"
!macroend
