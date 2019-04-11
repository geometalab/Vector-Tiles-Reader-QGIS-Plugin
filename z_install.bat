set PATH_TO_VTR=%~dp0
mklink /D "%appdata%\QGIS\QGIS3\profiles\default\python\plugins\vector_tiles_reader" %PATH_TO_VTR%

:: Make sure the IDE knows about the qgis package (run in admin console)
mklink /D "%programfiles%\QGIS 3.6\apps\Python37\Lib\site-packages\qgis" "%programfiles%\QGIS 3.6\apps\qgis\python\qgis"