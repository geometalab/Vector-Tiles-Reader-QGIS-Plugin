call pyuic4 -o dlg_edit_tilejson_connection_qt4.py dlg_edit_tilejson_connection.ui
call C:\Python36\Scripts\pyuic5 -o dlg_edit_tilejson_connection_qt5.py dlg_edit_tilejson_connection.ui

call pyuic4 -o dlg_edit_postgis_connection_qt4.py dlg_edit_postgis_connection.ui
call C:\Python36\Scripts\pyuic5 -o dlg_edit_postgis_connection_qt5.py dlg_edit_postgis_connection.ui

call pyuic4 -o dlg_connections_qt4.py dlg_connections.ui
call C:\Python36\Scripts\pyuic5 -o dlg_connections_qt5.py dlg_connections.ui

call pyuic4 -o dlg_about_qt4.py dlg_about.ui
call C:\Python36\Scripts\pyuic5 -o dlg_about_qt5.py dlg_about.ui

call pyuic4 -o options_qt4.py options.ui
call C:\Python36\Scripts\pyuic5 -o options_qt5.py options.ui

call pyuic4 -o connections_group_qt4.py connections_group.ui
call C:\Python36\Scripts\pyuic5 -o connections_group_qt5.py connections_group.ui

if NOT ["%errorlevel%"]==["0"] pause

exit