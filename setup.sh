#!/bin/bash
# Script de Setup - Assistente Pessoal
# Instala dependências e configura o ambiente

echo "🤖 ASSISTENTE PESSOAL - SCRIPT DE SETUP"
echo "======================================"

# Verificar se Python está instalado
if ! command -v python &> /dev/null; then
    echo "❌ Python não encontrado. Instale Python 3.8+ primeiro."
    exit 1
fi

echo "✅ Python encontrado: $(python --version)"

# Verificar se pip está instalado
if ! command -v pip &> /dev/null; then
    echo "❌ Pip não encontrado. Instale pip primeiro."
    exit 1
fi

echo "✅ Pip encontrado"

# Instalar dependências Python
echo ""
echo "📦 Instalando dependências Python..."
pip install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✅ Dependências Python instaladas com sucesso"
else
    echo "❌ Erro ao instalar dependências Python"
    exit 1
fi

# Instalar bibliotecas de processamento de PDF (opcionais mas recomendadas)
echo ""
echo "🔧 Instalando bibliotecas de processamento de PDF..."

# PyMuPDF (Fitz)
echo "  - Instalando PyMuPDF..."
pip install PyMuPDF
if [ $? -eq 0 ]; then
    echo "    ✅ PyMuPDF instalado"
else
    echo "    ⚠️  PyMuPDF falhou (continuando sem ele)"
fi

# Camelot
echo "  - Instalando Camelot..."
pip install "camelot-py[cv]"
if [ $? -eq 0 ]; then
    echo "    ✅ Camelot instalado"
else
    echo "    ⚠️  Camelot falhou (continuando sem ele)"
fi

# Tabula-py
echo "  - Instalando Tabula-py..."
pip install tabula-py
if [ $? -eq 0 ]; then
    echo "    ✅ Tabula-py instalado"
else
    echo "    ⚠️  Tabula-py falhou (continuando sem ele)"
fi

# Ofxparse
echo "  - Instalando Ofxparse..."
pip install ofxparse
if [ $? -eq 0 ]; then
    echo "    ✅ Ofxparse instalado"
else
    echo "    ⚠️  Ofxparse falhou (continuando sem ele)"
fi

# Criar diretório data se não existir
echo ""
echo "📁 Criando diretórios necessários..."
mkdir -p data
mkdir -p uploads
mkdir -p static
mkdir -p templates

echo "✅ Diretórios criados"

# Verificar instalação
echo ""
echo "🧪 Testando instalação..."
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

echo ""
echo "🎉 SETUP CONCLUÍDO!"
echo ""
echo "Para iniciar o servidor:"
echo "  python api_server.py"
echo ""
echo "Acesse: http://localhost:5001"
echo ""
echo "Para testar as bibliotecas:"
echo "  python teste_bibliotecas.py"