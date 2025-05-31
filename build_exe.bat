@echo off
echo Installing requirements...
pip install -r requirements.txt

echo Building EXE...
python -m nuitka ^
    --standalone ^
    --enable-plugin=pyside6 ^
    --windows-disable-console ^
    --include-package=requests ^
    --include-package=certifi ^
    --include-package=idna ^
    --include-package=urllib3 ^
    --include-package=charset_normalizer ^
    --output-dir=build ^
    client/main.py

echo Done!
pause 