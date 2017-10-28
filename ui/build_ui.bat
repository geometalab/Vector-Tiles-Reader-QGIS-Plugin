call pyuic4 -o dlg_edit_tilejson_connection.py dlg_edit_tilejson_connection.ui
call pyuic4 -o dlg_edit_postgis_connection.py dlg_edit_postgis_connection.ui
call pyuic4 -o dlg_connections.py dlg_connections.ui
call pyuic4 -o dlg_about.py dlg_about.ui
call pyuic4 -o options.py options.ui
call pyuic4 -o connections_group.py connections_group.ui
if NOT ["%errorlevel%"]==["0"] pause
exit