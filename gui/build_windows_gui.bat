pyinstaller dali_gui.py
pyinstaller --icon hasseb_icon.ico -F --noconsole dali_gui.py
copy hidapi.dll dist\
copy hidapi.dll dist\dali_gui
copy hasseb_icon.ico dist\
copy hasseb_icon.ico dist\dali_gui