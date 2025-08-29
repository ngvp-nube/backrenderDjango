@echo off
echo ===============================
echo  Iniciando Servidores...
echo ===============================
REM ===== Frontend Angular =====
start "Angular Server" cmd /k "cd C:\frontrenderValdiviano && ng serve --host 0.0.0.0 --port 4200"

REM ===== Backend Django =====
start "Django Server" cmd /k "call C:\backrenderDjango\venv\Scripts\activate.bat && cd C:\backrenderDjango && python manage.py runserver 0.0.0.0:8000"

echo Servidores iniciados. Puedes cerrar esta ventana.
pause