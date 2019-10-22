REM in case of "RuntimeError: Could not find the hidapi shared library." add path of hidapi.dll to the PATH environment variable

pyinstaller --add-binary hidapi.dll;. dali_gui.py
pyinstaller --add-binary hidapi.dll;. --add-binary hasseb_icon.ico;. --icon hasseb_icon.ico -F --noconsole dali_gui.py
copy hidapi.dll dist\
copy hidapi.dll dist\dali_gui
copy hasseb_icon.ico dist\
copy hasseb_icon.ico dist\dali_gui