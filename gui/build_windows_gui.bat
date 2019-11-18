rmdir /q/s __pycache__
rmdir /q/s build
rmdir /q/s dist
del install.exe

pyinstaller --add-binary hidapi.dll;. dali_gui.py
pyinstaller --add-binary hidapi.dll;. --add-binary hasseb_icon.ico;. --icon hasseb_icon.ico -F --noconsole dali_gui.py
copy hidapi.dll dist\
copy hidapi.dll dist\dali_gui
copy hasseb_icon.ico dist\
copy hasseb_icon.ico dist\dali_gui

"C:\Program Files (x86)\NSIS\makensis.exe" build_windows_install_package.nsi