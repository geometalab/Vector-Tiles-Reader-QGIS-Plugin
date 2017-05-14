call pyuic4 -o dlg_edit_connection.py dlg_edit_connection.ui
call pyuic4 -o dlg_connections.py dlg_connections.ui
call pyuic4 -o dlg_about.py dlg_about.ui
call pyuic4 -o dlg_progress.py dlg_progress.ui
call pyuic4 -o options.py options.ui
if NOT ["%errorlevel%"]==["0"] pause