@echo off

REM Run this script from the root of the repository

if "%VIRTUAL_ENV%"=="" (
    echo You need to activate your virtual env before running this script
    goto :eof
)

python src\manage.py use_external_components ./src/openapi.yaml ./src/openapi_unresolved.yaml
