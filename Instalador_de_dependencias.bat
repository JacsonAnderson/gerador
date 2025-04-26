@echo off
chcp 65001 > nul
title Instalador de Dependências - Gerador
color 0a

echo ================================
echo  Instalador de Dependências
echo ================================
echo.

:: Cria a pasta "data" se não existir
if not exist "data" (
    mkdir data
    echo Pasta "data" criada com sucesso.
) else (
    echo Pasta "data" já existe.
)

:: Cria a pasta "db" se não existir
if not exist "db" (
    mkdir db
    echo Pasta "db" criada com sucesso.
) else (
    echo Pasta "db" já existe.
)

:: Cria a subpasta "canais" dentro de "db" se não existir
if not exist "db\canais" (
    mkdir db\canais
    echo Pasta "db\canais" criada com sucesso.
) else (
    echo Pasta "db\canais" já existe.
)

echo.
echo Todas as dependências de diretórios foram instaladas!
echo.
pause
exit
