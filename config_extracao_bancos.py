"""
CONFIGURAÇÃO DE EXTRAÇÃO DE EXTRATOS BANCÁRIOS - PRODUÇÃO
Documentação das funções de extração que funcionam para cada banco
"""

# Mapeamento de bancos para suas funções de extração que funcionam
BANCOS_EXTRACAO_CONFIG = {
    'itau': {
        'funcao_extracao': '_extrair_itau',
        'formatos_suportados': ['PDF'],
        'metodos_avancados': ['Camelot', 'PyMuPDF'],
        'fallback_tradicional': True,
        'status': 'FUNCIONANDO',
        'notas': 'Suporta extratos PJ com PIX, boletos e depósitos 24h. Sistema de normalização ativo.'
    },

    'banco_do_brasil': {
        'funcao_extracao': '_extrair_bb',
        'formatos_suportados': ['PDF'],
        'metodos_avancados': ['Camelot', 'PyMuPDF'],
        'fallback_tradicional': True,
        'status': 'FUNCIONANDO',
        'notas': 'Suporta formato tabular com colunas: Dia, Lote, Documento, Histórico, Valor. Processa 548+ transações automaticamente.'
    },

    'bradesco': {
        'funcao_extracao': '_extrair_bradesco',
        'formatos_suportados': ['PDF'],
        'metodos_avancados': ['Camelot', 'PyMuPDF'],
        'fallback_tradicional': True,
        'status': 'IMPLEMENTADO',
        'notas': 'Aguardando testes com arquivos reais'
    },

    'santander': {
        'funcao_extracao': '_extrair_santander',
        'formatos_suportados': ['PDF'],
        'metodos_avancados': ['Camelot', 'PyMuPDF'],
        'fallback_tradicional': True,
        'status': 'IMPLEMENTADO',
        'notas': 'Aguardando testes com arquivos reais'
    },

    'nubank': {
        'funcao_extracao': '_extrair_nubank',
        'formatos_suportados': ['PDF', 'CSV'],
        'metodos_avancados': ['Camelot', 'PyMuPDF'],
        'fallback_tradicional': True,
        'status': 'IMPLEMENTADO',
        'notas': 'Suporte para extratos Nubank'
    },

    'caixa': {
        'funcao_extracao': '_extrair_caixa',
        'formatos_suportados': ['PDF'],
        'metodos_avancados': ['Camelot', 'PyMuPDF'],
        'fallback_tradicional': True,
        'status': 'IMPLEMENTADO',
        'notas': 'Usa extração genérica'
    },

    'inter': {
        'funcao_extracao': '_extrair_inter',
        'formatos_suportados': ['PDF'],
        'metodos_avancados': ['Camelot', 'PyMuPDF'],
        'fallback_tradicional': True,
        'status': 'IMPLEMENTADO',
        'notas': 'Usa extração genérica'
    },

    'c6': {
        'funcao_extracao': '_extrair_c6',
        'formatos_suportados': ['PDF'],
        'metodos_avancados': ['PyMuPDF'],
        'fallback_tradicional': False,
        'status': 'FUNCIONANDO',
        'notas': 'Extração específica funcionando perfeitamente. Processa 25+ transações com categorização automática, valores corretos e detecção de senha.'
    },

    'next': {
        'funcao_extracao': '_extrair_padrao_generico',
        'formatos_suportados': ['PDF'],
        'metodos_avancados': ['Camelot', 'PyMuPDF'],
        'fallback_tradicional': True,
        'status': 'IMPLEMENTADO',
        'notas': 'Extração genérica para Next'
    },

    'original': {
        'funcao_extracao': '_extrair_padrao_generico',
        'formatos_suportados': ['PDF'],
        'metodos_avancados': ['Camelot', 'PyMuPDF'],
        'fallback_tradicional': True,
        'status': 'IMPLEMENTADO',
        'notas': 'Extração genérica para Banco Original'
    },

    'pagbank': {
        'funcao_extracao': '_extrair_padrao_generico',
        'formatos_suportados': ['PDF', 'CSV'],
        'metodos_avancados': ['Camelot', 'PyMuPDF'],
        'fallback_tradicional': True,
        'status': 'IMPLEMENTADO',
        'notas': 'Extração genérica para PagBank'
    },

    'mercadopago': {
        'funcao_extracao': '_extrair_padrao_generico',
        'formatos_suportados': ['PDF', 'CSV'],
        'metodos_avancados': ['Camelot', 'PyMuPDF'],
        'fallback_tradicional': True,
        'status': 'IMPLEMENTADO',
        'notas': 'Extração genérica para Mercado Pago'
    }
}

# Padrões de identificação de bancos (usados na produção)
BANCOS_PATTERNS = {
    'itau': [
        r'ITAÚ', r'Itaú', r'ITAÚ UNIBANCO', r'Banco Itaú',
        r'www\.itau\.com\.br', r'4004', r'341'
    ],
    'bradesco': [
        r'BRADESCO', r'Bradesco', r'Banco Bradesco',
        r'www\.bradesco\.com\.br', r'237'
    ],
    'santander': [
        r'SANTANDER', r'Santander', r'Banco Santander',
        r'www\.santander\.com\.br', r'033'
    ],
    'nubank': [
        r'NUBANK', r'Nubank', r'Nu Bank',
        r'www\.nubank\.com\.br', r'260'
    ],
    'banco_do_brasil': [
        r'BANCO DO BRASIL', r'Banco do Brasil', r'BB',
        r'www\.bb\.com\.br', r'001'
    ],
    'caixa': [
        r'CAIXA ECONÔMICA', r'Caixa Econômica', r'CEF',
        r'www\.caixa\.gov\.br', r'104'
    ],
    'inter': [
        r'BANCO INTER', r'Banco Inter', r'Inter',
        r'www\.bancointer\.com\.br', r'077'
    ],
    'c6': [
        r'C6 BANK', r'C6', r'Banco C6',
        r'www\.c6bank\.com\.br', r'336'
    ],
    'next': [
        r'NEXT', r'Banco Next', r'Next',
        r'www\.banco next\.com\.br', r'237'  # Mesmo código do Bradesco
    ],
    'original': [
        r'BANCO ORIGINAL', r'Banco Original', r'Original',
        r'www\.bancooriginal\.com\.br', r'212'
    ],
    'pagbank': [
        r'PAGBANK', r'PagBank', r'PagSeguro',
        r'www\.pagbank\.com\.br'
    ],
    'mercadopago': [
        r'MERCADO PAGO', r'Mercado Pago', r'MercadoPago',
        r'www\.mercadopago\.com\.br'
    ]
}

# Configurações de bibliotecas avançadas
BIBLIOTECAS_AVANCADAS = {
    'camelot': {
        'status': 'ATIVO',
        'usos': ['Extração de tabelas estruturadas', 'PDFs com layout tabular'],
        'dependencias': ['camelot-py[cv]', 'ghostscript'],
        'notas': 'Melhor para tabelas bem formatadas'
    },
    'pymupdf': {
        'status': 'ATIVO',
        'usos': ['Extração de texto puro', 'PDFs com texto selecionável'],
        'dependencias': ['PyMuPDF'],
        'notas': 'Rápido e confiável para texto'
    },
    'tabula': {
        'status': 'DESABILITADO',
        'usos': ['Extração de tabelas Java-based'],
        'dependencias': ['tabula-py', 'jpype1', 'Java'],
        'notas': 'Problemas de compatibilidade com jpype'
    },
    'pdfplumber': {
        'status': 'ATIVO',
        'usos': ['Extração tradicional de texto'],
        'dependencias': ['pdfplumber'],
        'notas': 'Fallback confiável'
    }
}

# Função para obter configuração de um banco
def get_config_banco(banco: str) -> dict:
    """Retorna a configuração de extração para um banco específico"""
    return BANCOS_EXTRACAO_CONFIG.get(banco.lower(), {})

# Função para verificar se um banco é suportado
def banco_suportado(banco: str) -> bool:
    """Verifica se um banco tem suporte de extração"""
    return banco.lower() in BANCOS_EXTRACAO_CONFIG

# Função para listar bancos funcionais
def bancos_funcionais() -> list:
    """Retorna lista de bancos com status 'FUNCIONANDO'"""
    return [banco for banco, config in BANCOS_EXTRACAO_CONFIG.items()
            if config.get('status') == 'FUNCIONANDO']

if __name__ == "__main__":
    print("CONFIGURAÇÃO DE EXTRAÇÃO DE EXTRATOS BANCÁRIOS")
    print("=" * 60)
    print(f"Total de bancos configurados: {len(BANCOS_EXTRACAO_CONFIG)}")
    print(f"Bancos funcionais: {len(bancos_funcionais())}")
    print()
    print("BANCOS FUNCIONAIS:")
    for banco in bancos_funcionais():
        config = get_config_banco(banco)
        print(f"  • {banco.upper()}: {config.get('notas', '')}")