; Deluge Windows Installer Script
; Written By John Garland <johnnybg@gmail.com>
; Date: 21/02/09

; Includes

    !include "MUI2.nsh"

; Macros

    !macro get_url installer
        !define ${installer}_URL "http://download.deluge-torrent.org/windows/deps/${${installer}}"
    !macroend

    !macro download url filename
        DetailPrint "Downloading: ${url}"
        NSISdl::download ${url} ${filename}
        Pop $R0
        StrCmp $R0 "success" +2
            DetailPrint "Download failed: $R0"
    !macroend
    
    !macro install_NSIS installer_name install_dir
        ${download} "${${installer_name}_URL}" "$TEMP\${${installer_name}}"
        ExecWait '"$TEMP\${${installer_name}}" /S /D=${install_dir}\GTK'
        delete "$TEMP\${${installer_name}}"
    !macroend

    !macro install_MSI installer_name install_dir
        ${download} "${${installer_name}_URL}" "$TEMP\${${installer_name}}"
        ExecWait 'msiexec /qn /i "$TEMP\${${installer_name}}" TARGETDIR="${install_dir}'
        delete "$TEMP\${${installer_name}}"
    !macroend

    !macro install_ZIP installer_name install_dir
        ${download} "${${installer_name}_URL}" "$TEMP\${${installer_name}}"
        nsisunz::UnzipToLog "$TEMP\${${installer_name}}" "${install_dir}"
        Pop $R0
        StrCmp $R0 "success" +2
            DetailPrint "Error unzipping: $R0"
        delete "$TEMP\${${installer_name}}"
    !macroend
    
; Defines

    ; Redefine macros/functions
    !define get_url "!insertmacro get_url"
    !define download "!insertmacro download"
    !define install_NSIS "!insertmacro install_NSIS"
    !define install_MSI "!insertmacro install_MSI"
    !define install_ZIP "!insertmacro install_ZIP"

    ; Installer versions
    !define DELUGE_VERSION "1.1.3"
    !define PYTHON_VERSION "2.5"
    !define PYTHON_VERSION_FULL "${PYTHON_VERSION}.4"
    !define PYWIN32_VERSION "212"
    !define GTK_VERSION "2.12.1"
    !define PYCAIRO_VERSION "1.4.12"
    !define PYGAME_VERSION "1.8.1"
    !define PYGOBJECT_VERSION "2.14.1"
    !define PYGTK_VERSION "2.12.1"
    !define PYOPENSSL_VERSION "0.8"
    !define PYXDG_VERSION "0.17"
    !define SETUPTOOLS_VERSION "0.6c9"
    !define LIBTORRENT_VERSION "0.14.2"

    ; Installer names
    !define DELUGE_INSTALLER "deluge-${DELUGE_VERSION}.win32-py${PYTHON_VERSION}.msi"
    !define PYTHON_INSTALLER "python-${PYTHON_VERSION_FULL}.msi"
    !define PYWIN32_INSTALLER "pywin32-${PYWIN32_VERSION}.win32-py${PYTHON_VERSION}.exe"
    !define GTK_INSTALLER "gtk-${GTK_VERSION}-win32-2.exe"
    !define PYCAIRO_INSTALLER "pycairo-${PYCAIRO_VERSION}-1.win32-py${PYTHON_VERSION}.exe"
    !define PYGAME_INSTALLER "pygame-${PYGAME_VERSION}release.win32-py${PYTHON_VERSION}.msi"
    !define PYGOBJECT_INSTALLER "pygobject-${PYGOBJECT_VERSION}.win32-py${PYTHON_VERSION}.exe"
    !define PYGTK_INSTALLER "pygtk-${PYGTK_VERSION}-2.win32-py${PYTHON_VERSION}.exe"
    !define PYOPENSSL_INSTALLER "pyOpenSSL-${PYOPENSSL_VERSION}.winxp32-py${PYTHON_VERSION}.msi"
    !define PYXDG_INSTALLER "pyxdg-${PYXDG_VERSION}.win32-py${PYTHON_VERSION}.msi"
    !define SETUPTOOLS_INSTALLER "setuptools-${SETUPTOOLS_VERSION}.win32-py${PYTHON_VERSION}.exe"
    !define LIBTORRENT_INSTALLER "python-libtorrent-${LIBTORRENT_VERSION}.win32-py${PYTHON_VERSION}.msi"
    !define LIBTORRENT_DLL "MSVCP71.DLL"
    !define LIBTORRENT_DLL_ZIP "${LIBTORRENT_DLL}.zip"

    ; Installer URLs
    ${get_url} DELUGE_INSTALLER
    ${get_url} PYTHON_INSTALLER
    ${get_url} PYWIN32_INSTALLER
    ${get_url} GTK_INSTALLER
    ${get_url} PYCAIRO_INSTALLER
    ${get_url} PYGAME_INSTALLER
    ${get_url} PYGOBJECT_INSTALLER
    ${get_url} PYGTK_INSTALLER
    ${get_url} PYOPENSSL_INSTALLER
    ${get_url} PYXDG_INSTALLER
    ${get_url} SETUPTOOLS_INSTALLER
    ${get_url} LIBTORRENT_INSTALLER
    ${get_url} LIBTORRENT_DLL_ZIP

; General Settings

    ; Version
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
    
; Interface Settings

    ; Installer
    !define MUI_ICON "..\deluge\data\pixmaps\deluge.ico"
    !define MUI_HEADERIMAGE
    !define MUI_HEADERIMAGE_RIGHT
    !define MUI_HEADERIMAGE_BITMAP "installer-top.bmp"
    !define MUI_WELCOMEFINISHPAGE_BITMAP "installer-side.bmp"
    !define MUI_COMPONENTSPAGE_SMALLDESC
    !define MUI_FINISHPAGE_NOAUTOCLOSE
    !define MUI_ABORTWARNING

    ; Uninstaller
    !define MUI_UNICON "..\deluge\data\pixmaps\deluge.ico"
    !define MUI_HEADERIMAGE_UNBITMAP "installer-top.bmp"
    !define MUI_WELCOMEFINISHPAGE_UNBITMAP "installer-side.bmp"
    !define MUI_UNFINISHPAGE_NOAUTOCLOSE

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

        ${install_NSIS} GTK_INSTALLER "$INSTDIR\GTK"

    SectionEnd

    Section "PyGTK" pygtk

        SectionIn 1

        ${install_ZIP} PYGTK_INSTALLER "$INSTDIR\Python\site-packages"

    SectionEnd

    Section "PyCairo"

        SectionIn 1

        ${install_ZIP} PYCAIRO_INSTALLER "$INSTDIR\Python\site-packages"

    SectionEnd

    Section "PyGame" pygame

        SectionIn 1

        ${install_MSI} PYGAME_INSTALLER "$INSTDIR\Python\site-packages"

    SectionEnd

    Section "PyGObject" pygobject

        SectionIn 1

        ${install_ZIP} PYGOBJECT_INSTALLER "$INSTDIR\Python\site-packages"

    SectionEnd

    Section "PyOpenSSL" pyopenssl

        SectionIn 1

        ${install_MSI} PYOPENSSL_INSTALLER "$INSTDIR\Python\site-packages"

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

    SectionEnd

SubSectionEnd

SubSection /e "Core" core

    Section "Deluge" deluge

        SectionIn RO

        ${install_MSI} DELUGE_INSTALLER "$INSTDIR\Deluge"

        SetOutPath "$INSTDIR\Deluge"
        
        WriteUninstaller "$INSTDIR\Deluge\uninstall.exe"

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
    RMDir "$INSTDIR\Deluge"
    RMDir "$INSTDIR"

SectionEnd
