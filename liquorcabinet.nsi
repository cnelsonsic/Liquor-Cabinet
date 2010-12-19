!include "MUI.nsh"

name "Liquor Cabinet"
outFile "Installer.exe"

InstallDir "$PROGRAMFILES\Liquor Cabinet"

LicenseText "GPLv3"
LicenseData "LICENSE"

InstallDirRegKey HKCU "Software\Liquor Cabinet" ""
RequestExecutionLevel user

#Get Python:
Var PythonDirectory
!define PythonExecutable "$PythonDirectory\pythonw.exe"

Function findPython
    ReadRegStr $9 HKLM "SOFTWARE\Python\PythonCore\2.7\InstallPath" ""
    StrCmp $9 "" tryPython26 ok
tryPython26:
    ReadRegStr $9 HKLM "SOFTWARE\Python\PythonCore\2.6\InstallPath" ""
    StrCmp $9 "" oops ok
oops:
	MessageBox MB_YESNO "Download and Install Python?" /SD IDYES IDNO done
    NSISdl::download "http://python.org/ftp/python/2.7.1/python-2.7.1.msi" "$INSTDIR\python.msi"
    ExecWait '"msiexec" /i "$INSTDIR\python.msi"'
    ReadRegStr $9 HKLM "SOFTWARE\Python\PythonCore\2.7\InstallPath" ""
    StrCmp $9 "" done ok
ok:
    StrCpy $PythonDirectory $9
done:

FunctionEnd

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "LICENSE"
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_DIRECTORY

Var StartMenuFolder
!insertmacro MUI_PAGE_STARTMENU "Application" $StartMenuFolder

!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "English"

#Page license
#Page components
#Page directory
#Page instfiles

#UninstPage uninstConfirm
#UninstPage uninstfiles

Section "Liquor Cabinet"
  SectionIn RO

  SetOutPath $INSTDIR
  File *.py
  File CREDITS
  File LICENSE
  File README.md
  File liquor_cabinet.bat

  SetOutPath "$INSTDIR\resources\"
  File "resources\*"

  SetOutPath "$INSTDIR\Cheetah\"
  File "Cheetah\*"

  SetOutPath "$INSTDIR\sqlalchemy\"
  File "sqlalchemy\*"
  
  WriteRegStr HKCU "Software\Liquor Cabinet" "" $INSTDIR
  
  WriteUninstaller "$INSTDIR\Uninstall.exe"

SectionEnd

Section "Python"
	Call findPython
SectionEnd

Section "PyQt"
	ExecWait '"${PythonExecutable}" -c "import PyQt4"' $0
	StrCmp $0 "0" done installPyQt4
	 
	installPyQt4:
		NSISdl::download "http://www.riverbankcomputing.co.uk/static/Downloads/PyQt4/PyQt-Py2.7-gpl-4.8.1-1.exe" "$INSTDIR\pyqt4.exe"
		ExecWait '"$INSTDIR\pyqt4.exe"'
	done:
		
SectionEnd

Section "StartMenu Shortcuts"
	createShortCut "$SMPROGRAMS\Liquor Cabinet\Liquor Cabinet.lnk" "${PythonExecutable} $INSTDIR\guiclient.py"
	createShortCut "$SMPROGRAMS\Liquor Cabinet\Uninstall.lnk" "$INSTDIR\Uninstall.exe"
	
SectionEnd

Section "Uninstall"

  Delete "$INSTDIR\*.py"
  Delete "$INSTDIR\CREDITS"
  Delete "$INSTDIR\LICENSE"
  Delete "$INSTDIR\README.md"
  Delete "$INSTDIR\liquor_cabinet.bat"

  Delete "$INSTDIR\resources\*"
  RMDir "$INSTDIR\resources\"

  Delete "$INSTDIR\Cheetah\*"
  RMDir "$INSTDIR\Cheetah\"

  Delete "$INSTDIR\sqlalchemy\*"
  RMDir "$INSTDIR\sqlalchemy\"

  Delete "$INSTDIR\Uninstall.exe"

  RMDir "$INSTDIR"
  
  Delete "$SMPROGRAMS\Liquor Cabinet\Liquor Cabinet.lnk"
  Delete "$SMPROGRAMS\Liquor Cabinet\Uninstall.lnk"
  RMDir "$SMPROGRAMS\Liquor Cabinet\"
  
  DeleteRegKey /ifempty HKCU "Software\Liquor Cabinet"

SectionEnd

