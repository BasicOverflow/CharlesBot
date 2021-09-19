@echo off


@REM start api\frontend\build & serve -p 8005
start python api/backend/main.py
start python TaskQueue/__init__.py


