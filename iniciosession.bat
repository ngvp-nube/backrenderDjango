@echo off
echo ===============================
echo  Iniciando Servidores...
echo ===============================

REM ===== Backend Django =====
start "Django Server" cmd /k "call C:\Users\ngvp\Desktop\backrenderDjango\venv\Scripts\activate.bat && cd C:\Users\ngvp\Desktop\backrenderDjango && python manage.py runserver 0.0.0.0:8000"

REM ===== Frontend Angular =====
start "Angular Server" cmd /k "cd C:\Users\ngvp\Desktop\frontrenderValdiviano && ng serve --host 0.0.0.0 --port 4200"

echo Servidores iniciados. Puedes cerrar esta ventana.
pause