call pyuic4 -o dlg_edit_tilejson_connection_qt4.py dlg_edit_tilejson_connection.ui 2>NUL
call C:\Python36\Scripts\pyuic5 -o dlg_edit_tilejson_connection_qt5.py dlg_edit_tilejson_connection.ui 2>NUL

call pyuic4 -o dlg_edit_postgis_connection_qt4.py dlg_edit_postgis_connection.ui 2>NUL
call C:\Python36\Scripts\pyuic5 -o dlg_edit_postgis_connection_qt5.py dlg_edit_postgis_connection.ui 2>NUL

call pyuic4 -o dlg_connections_qt4.py dlg_connections.ui 2>NUL
call C:\Python36\Scripts\pyuic5 -o dlg_connections_qt5.py dlg_connections.ui 2>NUL

call pyuic4 -o dlg_about_qt4.py dlg_about.ui 2>NUL
call C:\Python36\Scripts\pyuic5 -o dlg_about_qt5.py dlg_about.ui 2>NUL

call pyuic4 -o options_qt4.py options.ui 2>NUL
call C:\Python36\Scripts\pyuic5 -o options_qt5.py options.ui 2>NUL

call pyuic4 -o connections_group_qt4.py connections_group.ui 2>NUL
call C:\Python36\Scripts\pyuic5 -o connections_group_qt5.py connections_group.ui 2>NUL

if NOT ["%errorlevel%"]==["0"] pause

exit