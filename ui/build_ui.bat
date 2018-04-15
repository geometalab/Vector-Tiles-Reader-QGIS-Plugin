call pyuic4 -o qt/dlg_edit_tilejson_connection_qt4.py qt/dlg_edit_tilejson_connection.ui
call pyuic5 -o qt/dlg_edit_tilejson_connection_qt5.py qt/dlg_edit_tilejson_connection.ui

call pyuic4 -o qt/dlg_edit_postgis_connection_qt4.py qt/dlg_edit_postgis_connection.ui
call pyuic5 -o qt/dlg_edit_postgis_connection_qt5.py qt/dlg_edit_postgis_connection.ui

call pyuic4 -o qt/dlg_connections_qt4.py qt/dlg_connections.ui
call pyuic5 -o qt/dlg_connections_qt5.py qt/dlg_connections.ui

call pyuic4 -o qt/dlg_about_qt4.py qt/dlg_about.ui
call pyuic5 -o qt/dlg_about_qt5.py qt/dlg_about.ui

call pyuic4 -o qt/options_qt4.py qt/options.ui
call pyuic5 -o qt/options_qt5.py qt/options.ui

call pyuic4 -o qt/connections_group_qt4.py qt/connections_group.ui
call pyuic5 -o qt/connections_group_qt5.py qt/connections_group.ui

if NOT ["%errorlevel%"]==["0"] pause

exit