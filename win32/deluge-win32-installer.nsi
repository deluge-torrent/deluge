# Deluge Windows installer script
# Version 0.6 22-Nov-2012

# Copyright (C) 2009 by
#   Jesper Lund <mail@jesperlund.com>
#   Andrew Resch <andrewresch@gmail.com>
#   John Garland <johnnybg@gmail.com>

# Deluge is free software.
#
# You may redistribute it and/or modify it under the terms of the
# GNU General Public License, as published by the Free Software
# Foundation; either version 3 of the License, or (at your option)
# any later version.
#
# Deluge is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with deluge.    If not, write to:
# 	The Free Software Foundation, Inc.,
# 	51 Franklin Street, Fifth Floor
# 	Boston, MA    02110-1301, USA.
#

# Set default compressor
SetCompressor  /FINAL /SOLID lzma
SetCompressorDictSize 64

###
### --- The PROGRAM_VERSION !define need to be updated with new Deluge versions ---
###

# Script version; displayed when running the installer
!define DELUGE_INSTALLER_VERSION "0.6"

# Deluge program information
!define PROGRAM_NAME "Deluge"
# Deluge program information
!searchparse /file VERSION.tmp `build_version = "` PROGRAM_VERSION `"`
!ifndef PROGRAM_VERSION
   !error "Program Version Undefined"
!endif
!define PROGRAM_WEB_SITE "http://deluge-torrent.org"

# Python files generated with bbfreeze
!define DELUGE_PYTHON_BBFREEZE_OUTPUT_DIR "..\build-win32\deluge-bbfreeze-${PROGRAM_VERSION}"

# --- Interface settings ---

# Modern User Interface 2
!include MUI2.nsh

# Installer
!define MUI_ICON "deluge.ico"
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_RIGHT
!define MUI_HEADERIMAGE_BITMAP "installer-top.bmp"
!define MUI_WELCOMEFINISHPAGE_BITMAP "installer-side.bmp"
!define MUI_COMPONENTSPAGE_SMALLDESC
!define MUI_FINISHPAGE_NOAUTOCLOSE
!define MUI_ABORTWARNING

# Uninstaller
!define MUI_UNICON "${NSISDIR}\Contrib\Graphics\Icons\modern-uninstall.ico"
!define MUI_HEADERIMAGE_UNBITMAP "installer-top.bmp"
!define MUI_WELCOMEFINISHPAGE_UNBITMAP "installer-side.bmp"
!define MUI_UNFINISHPAGE_NOAUTOCLOSE

# --- Start of Modern User Interface ---

# Welcome page
!insertmacro MUI_PAGE_WELCOME

# License page
!insertmacro MUI_PAGE_LICENSE "..\LICENSE"

# Components page
!insertmacro MUI_PAGE_COMPONENTS

# Let the user select the installation directory
!insertmacro MUI_PAGE_DIRECTORY

# Run installation
!insertmacro MUI_PAGE_INSTFILES

# Display 'finished' page
!insertmacro MUI_PAGE_FINISH

# Uninstaller pages
!insertmacro MUI_UNPAGE_INSTFILES

# Language files
!insertmacro MUI_LANGUAGE "English"


# --- Functions ---

Function .onInit
	System::Call 'kernel32::OpenMutex(i 0x100000, b 0, t "deluge") i .R0'
	IntCmp $R0 0 notRunning
		System::Call 'kernel32::CloseHandle(i $R0)'
		MessageBox MB_OK|MB_ICONEXCLAMATION "Deluge is running. Please close it first" /SD IDOK
		Abort
	notRunning:
FunctionEnd

Function un.onUninstSuccess
  HideWindow
  MessageBox MB_ICONINFORMATION|MB_OK "$(^Name) was successfully removed from your computer." /SD IDOK
FunctionEnd

Function un.onInit
  MessageBox MB_ICONQUESTION|MB_YESNO|MB_DEFBUTTON2 "Do you want to completely remove $(^Name) and all of its components?" /SD IDYES IDYES +2
  Abort
FunctionEnd

# --- Installation sections ---

# Compare versions
!include "WordFunc.nsh"

!define PROGRAM_UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PROGRAM_NAME}"
!define PROGRAM_UNINST_ROOT_KEY "HKLM"

# Branding text
BrandingText "Deluge Windows Installer v${DELUGE_INSTALLER_VERSION}"

Name "${PROGRAM_NAME} ${PROGRAM_VERSION}"
OutFile "..\build-win32\deluge-${PROGRAM_VERSION}-win32-setup.exe"

InstallDir "$PROGRAMFILES\Deluge"

ShowInstDetails show
ShowUnInstDetails show

# Install main application
Section "Deluge Bittorrent Client" Section1
  SectionIn RO

  SetOutPath $INSTDIR
  File /r "${DELUGE_PYTHON_BBFREEZE_OUTPUT_DIR}\*.*"

  SetOverwrite ifnewer
  File "..\LICENSE"
SectionEnd

Section -StartMenu_Desktop_Links
  WriteIniStr "$INSTDIR\homepage.url" "InternetShortcut" "URL" "${PROGRAM_WEB_SITE}"
  # create shortcuts for all users
  SetShellVarContext all
  CreateDirectory "$SMPROGRAMS\Deluge"
  CreateShortCut "$SMPROGRAMS\Deluge\Deluge.lnk" "$INSTDIR\deluge.exe"
  CreateShortCut "$SMPROGRAMS\Deluge\Project homepage.lnk" "$INSTDIR\Homepage.url"
  CreateShortCut "$SMPROGRAMS\Deluge\Uninstall Deluge.lnk" "$INSTDIR\Deluge-uninst.exe"
  CreateShortCut "$DESKTOP\Deluge.lnk" "$INSTDIR\deluge.exe"
SectionEnd

Section -Uninstaller
  WriteUninstaller "$INSTDIR\Deluge-uninst.exe"
  WriteRegStr ${PROGRAM_UNINST_ROOT_KEY} "${PROGRAM_UNINST_KEY}" "DisplayName" "$(^Name)"
  WriteRegStr ${PROGRAM_UNINST_ROOT_KEY} "${PROGRAM_UNINST_KEY}" "UninstallString" "$INSTDIR\Deluge-uninst.exe"
SectionEnd

# Create file association for .torrent
Section "Create .torrent file association for Deluge" Section2
  # Set up file association for .torrent files
  DeleteRegKey HKCR ".torrent"
  WriteRegStr HKCR ".torrent" "" "Deluge"
  WriteRegStr HKCR ".torrent" "Content Type" "application/x-bittorrent"

  DeleteRegKey HKCR "Deluge"
  WriteRegStr HKCR "Deluge" "" "Deluge"
  WriteRegStr HKCR "Deluge\Content Type" "" "application/x-bittorrent"
  WriteRegStr HKCR "Deluge\DefaultIcon" "" "$INSTDIR\deluge.exe,0"
  WriteRegStr HKCR "Deluge\shell" "" "open"
  WriteRegStr HKCR "Deluge\shell\open\command" "" '"$INSTDIR\deluge.exe" "%1"'
SectionEnd


# Create magnet uri association
Section "Create magnet uri link association for Deluge" Section3
    DeleteRegKey HKCR "magnet"
    WriteRegStr HKCR "magnet" "" "URL:magnet protocol"
    WriteRegStr HKCR "magnet" "URL Protocol" ""

    WriteRegStr HKCR "magnet\shell\open\command" "" '"$INSTDIR\deluge.exe" "%1"'
SectionEnd


LangString DESC_Section1 ${LANG_ENGLISH} "Install Deluge Bittorrent client."
LangString DESC_Section2 ${LANG_ENGLISH} "Select this option unless you have another torrent client which you want to use for opening .torrent files."
LangString DESC_Section3 ${LANG_ENGLISH} "Select this option to have Deluge handle magnet links."

!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
  !insertmacro MUI_DESCRIPTION_TEXT ${Section1} $(DESC_Section1)
  !insertmacro MUI_DESCRIPTION_TEXT ${Section2} $(DESC_Section2)
  !insertmacro MUI_DESCRIPTION_TEXT ${Section3} $(DESC_Section3)
!insertmacro MUI_FUNCTION_DESCRIPTION_END


# --- Uninstallation section(s) ---

Section Uninstall
  RmDir /r "$INSTDIR"

  SetShellVarContext all
  Delete "$SMPROGRAMS\Deluge\Deluge.lnk"
  Delete "$SMPROGRAMS\Deluge\Uninstall Deluge.lnk"
  Delete "$SMPROGRAMS\Deluge\Project homepage.lnk"
  Delete "$DESKTOP\Deluge.lnk"

  RmDir "$SMPROGRAMS\Deluge"

  DeleteRegKey ${PROGRAM_UNINST_ROOT_KEY} "${PROGRAM_UNINST_KEY}"

  # Only delete the .torrent association if Deluge owns it
  ReadRegStr $1 HKCR ".torrent" ""
  StrCmp $1 "Deluge" 0 DELUGE_skip_delete

  # Delete the key since it is owned by Deluge; afterwards there is no .torrent association
  DeleteRegKey HKCR ".torrent"

  DELUGE_skip_delete:
  # This key is only used by Deluge, so we should always delete it
  DeleteRegKey HKCR "Deluge"
SectionEnd
