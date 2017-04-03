call pyuic4 -o dlg_edit_server_connection.py dlg_edit_server_connection.ui
call pyuic4 -o dlg_file_connection.py dlg_file_connection.ui
call pyuic4 -o dlg_server_connections.py dlg_server_connections.ui
if NOT ["%errorlevel%"]==["0"] pause