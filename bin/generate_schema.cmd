@echo off

REM Run this script from the root of the repository

if "%VIRTUAL_ENV%"=="" (
    echo You need to activate your virtual env before running this script
    goto :eof
)

echo Generating Swagger schema
python src\manage.py generate_swagger^
    --output-file ./src/openapi.yaml^
    --overwrite^
    --format=openapi^
    --mock-request^
    --url https://example.com/api/v1

call patch_content_types

echo Generating unresolved OpenAPI 3.0 schema
call use_external_components

echo Prettifying OpenAPI schema
call npx prettier --write --single-quote ./src/openapi.yaml

echo Generating resources document
python src\manage.py generate_swagger^
    --output-file ./src/resources.md^
    --overwrite^
    --mock-request^
    --url https://example.com/api/v1^
    --to-markdown-table

echo "Generating autorisaties.md"
src\manage.py generate_autorisaties --output-file ./src/autorisaties.md

echo "Generating notificaties.md"
src\manage.py generate_notificaties --output-file ./src/notificaties.md
