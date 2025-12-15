@echo off
REM Script de Setup - Assistente Pessoal (Windows)
REM Instala dependências e configura o ambiente

echo 🤖 ASSISTENTE PESSOAL - SCRIPT DE SETUP
echo ======================================

REM Verificar se Python está instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python não encontrado. Instale Python 3.8+ primeiro.
    echo Baixe em: https://python.org
    pause
    exit /b 1
)

echo ✅ Python encontrado
python --version

REM Verificar se pip está instalado
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Pip não encontrado. Instale pip primeiro.
    pause
    exit /b 1
)

echo ✅ Pip encontrado

REM Instalar dependências Python
echo.
echo 📦 Instalando dependências Python...
pip install -r requirements.txt

if %errorlevel% equ 0 (
    echo ✅ Dependências Python instaladas com sucesso
) else (
    echo ❌ Erro ao instalar dependências Python
    pause
    exit /b 1
)

REM Instalar bibliotecas de processamento de PDF (opcionais mas recomendadas)
echo.
echo 🔧 Instalando bibliotecas de processamento de PDF...

REM PyMuPDF (Fitz)
echo   - Instalando PyMuPDF...
pip install PyMuPDF
if %errorlevel% equ 0 (
    echo     ✅ PyMuPDF instalado
) else (
    echo     ⚠️  PyMuPDF falhou (continuando sem ele)
)

REM Camelot
echo   - Instalando Camelot...
pip install "camelot-py[cv]"
if %errorlevel% equ 0 (
    echo     ✅ Camelot instalado
) else (
    echo     ⚠️  Camelot falhou (continuando sem ele)
)

REM Tabula-py
echo   - Instalando Tabula-py...
pip install tabula-py
if %errorlevel% equ 0 (
    echo     ✅ Tabula-py instalado
) else (
    echo     ⚠️  Tabula-py falhou (continuando sem ele)
)

REM Ofxparse
echo   - Instalando Ofxparse...
pip install ofxparse
if %errorlevel% equ 0 (
    echo     ✅ Ofxparse instalado
) else (
    echo     ⚠️  Ofxparse falhou (continuando sem ele)
)

REM Criar diretórios necessários
echo.
echo 📁 Criando diretórios necessários...
if not exist "data" mkdir data
if not exist "uploads" mkdir uploads
if not exist "static" mkdir static
if not exist "templates" mkdir templates

echo ✅ Diretórios criados

REM Verificar instalação
echo.
echo 🧪 Testando instalação...
python -c "
try:
    import flask
    print('✅ Flask: OK')
except ImportError:
    print('❌ Flask: FALHA')

try:
    import sqlite3
    print('✅ SQLite3: OK')
except ImportError:
    print('❌ SQLite3: FALHA')

try:
    import fitz
    print('✅ PyMuPDF: OK')
except ImportError:
    print('⚠️  PyMuPDF: Não disponível')

try:
    import camelot
    print('✅ Camelot: OK')
except ImportError:
    print('⚠️  Camelot: Não disponível')

try:
    import tabula
    print('✅ Tabula-py: OK')
except ImportError:
    print('⚠️  Tabula-py: Não disponível')

try:
    import ofxparse
    print('✅ Ofxparse: OK')
except ImportError:
    print('⚠️  Ofxparse: Não disponível')
"

echo.
echo 🎉 SETUP CONCLUÍDO!
echo.
echo Para iniciar o servidor:
echo   python api_server.py
echo.
echo Acesse: http://localhost:5501
echo.
echo Para testar as bibliotecas:
echo   python teste_bibliotecas.py
echo.
pause