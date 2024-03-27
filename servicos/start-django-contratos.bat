@echo off

cd c:\
cd "projetos"
cd "ekoos_contratos_api"

python manage.py runserver 192.168.0.7:8001

pause
exit;