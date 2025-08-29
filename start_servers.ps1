# Iniciar el servidor Django
Start-Process "cmd.exe" "/K cd C:\backrenderDjango\venv\Scripts\activate.bat && cd C:\backrenderDjango && python manage.py runserver 0.0.0.0:8000"

# Iniciar el servidor Angular
Start-Process "cmd.exe" "/K cd C:\frontrenderValdiviano && ng serve --host 0.0.0.0 --port 4200"
