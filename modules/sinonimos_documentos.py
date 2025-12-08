"""
📖 Dicionário de Sinônimos para Documentos Financeiros
Identifica beneficiário, pagador, valor e outros campos em documentos
"""

# Sinônimos para identificar o BENEFICIÁRIO (quem recebe o pagamento)
SINONIMOS_BENEFICIARIO = {
    'beneficiário',
    'beneficiario',
    'credor',
    'empresa',
    'instituição',
    'instituicao',
    'banco',
    'caixa',
    'bradesco',
    'itaú',
    'itau',
    'santander',
    'recebedor',
    'receptor',
    'prestador de serviço',
    'prestador de servico',
    'fornecedor',
    'favorecido',
    'empresa credora',
    'empresa desenvolvedora',
    'empresa gestora',
    'prefeitura',
    'município',
    'municipio',
    'governo',
    'estado',
    'companhia',
    'concessionária',
    'concessionaria',
    'distribuidora',
    'provedora',
    'provedora de serviço',
    'provedora de servico',
    'operadora',
    'transportadora',
    'armazém',
    'armazem',
    'órgão',
    'orgao',
    'agência',
    'agencia',
    'associação',
    'associacao',
    'sindicato',
    'cooperativa',
    'fundo',
    'fundo de garantia',
    'inss',
    'receita federal',
    'receita estadual',
    'câmara',
    'camara',
    'condomínio',
    'condominio',
    'síndico',
    'sindico',
    'administradora',
    'universidade',
    'escola',
    'hospital',
    'clínica',
    'clinica',
    'consultório',
    'consultorio',
}

# Sinônimos para identificar o PAGADOR (quem paga)
SINONIMOS_PAGADOR = {
    'pagador',
    'devedor',
    'depositante',
    'ordenante',
    'ordenador',
    'emitente',
    'sacado',
    'pessoa física',
    'pessoa fisica',
    'cpf',
    'pf',
    'pessoa jurídica',
    'pessoa juridica',
    'cnpj',
    'pj',
    'cliente',
    'contratante',
    'mutuário',
    'mutuario',
    'credor',
    'tomador',
    'locatário',
    'locatario',
    'inquilino',
    'consumidor',
    'autorizado a debitar',
    'débito automático',
    'debito automatico',
    'conta débito',
    'conta debito',
    'correntista',
    'titular',
    'poupador',
    'investidor',
    'beneficiário da folha',
    'beneficiario da folha',
    'autônomo',
    'autonomo',
    'proprietário',
    'proprietario',
    'responsável',
    'responsavel',
    'assinante',
}

# Sinônimos para identificar o VALOR
SINONIMOS_VALOR = {
    'valor',
    'valor total',
    'valor a pagar',
    'valor a descontar',
    'valor do boleto',
    'valor do documento',
    'total',
    'total a pagar',
    'montante',
    'quantia',
    'principal',
    'débito',
    'debito',
    'crédito',
    'credito',
    'importância',
    'importancia',
    'preço',
    'preco',
    'tarifa',
    'taxa',
    'juros',
    'multa',
    'correção',
    'correcao',
    'reajuste',
    'acréscimo',
    'acrescimo',
    'desconto',
    'abatimento',
    'valor líquido',
    'valor liquido',
    'valor bruto',
    'valor base',
    'valor à vista',
    'valor a vista',
    'valor a prazo',
    'valor parcelado',
    'valor cobrado',
    'cobrado',
    'a receber',
    'a pagar',
    'due date amount',
    'invoice amount',
    'bill amount',
    'payment amount',
    'r$',
}

# Sinônimos para DOCUMENTOS
SINONIMOS_DOCUMENTO_BOLETO = {
    'boleto',
    'boleto bancário',
    'boleto bancario',
    'documento de cobrança',
    'documento de cobranca',
    'bloqueto',
    'título',
    'titulo',
    'nota promissória',
    'nota promissoria',
    'letra de câmbio',
    'letra de cambio',
}

SINONIMOS_DOCUMENTO_FATURA = {
    'fatura',
    'conta',
    'conta a pagar',
    'nota de débito',
    'nota de debito',
    'recibo',
    'invoice',
    'bill',
    'billing',
    'extrato',
    'extrato de conta',
    'comprovante',
    'cupom',
    'recebimento',
    'nota fiscal',
    'nf',
    'nfe',
}

SINONIMOS_DOCUMENTO_TRANSFERENCIA = {
    'transferência',
    'transferencia',
    'transfer',
    'ted',
    'tef',
    'transf',
    'envio de recursos',
    'envio de dinheiro',
    'ordem de pagamento',
    'ordem de crédito',
    'ordem de credito',
    'comprovante de transferência',
    'comprovante de transferencia',
    'comprovante de ted',
    'comprovante de tef',
    'recebimento de transferência',
    'recebimento de transferencia',
}

SINONIMOS_DOCUMENTO_IMPOSTO = {
    'darf',
    'gps',
    'das',
    'iptu',
    'ipva',
    'itbi',
    'fgts',
    'inss',
    'pis',
    'cofins',
    'icms',
    'ipi',
    'ir',
    'irpf',
    'imposto de renda',
    'imposto sobre serviço',
    'iss',
    'guia',
    'guia de imposto',
    'guia de pagamento',
    'guia de recolhimento',
    'declaração de imposto',
    'declaracao de imposto',
}

SINONIMOS_DOCUMENTO_CONDOMINIO = {
    'condomínio',
    'condominio',
    'taxa de condomínio',
    'taxa de condominio',
    'boleto de condomínio',
    'boleto de condominio',
    'cobrança condominial',
    'cobranca condominial',
    'despesa de condomínio',
    'despesa de condominio',
}

SINONIMOS_DOCUMENTO_UTILIDADE = {
    'conta de luz',
    'energia',
    'eletricidade',
    'conta de água',
    'conta de agua',
    'água',
    'agua',
    'saneamento',
    'conta de telefone',
    'telefone',
    'conta de internet',
    'internet',
    'telefonia',
    'conta de gás',
    'conta de gas',
    'gás',
    'gas',
    'multiservços',
    'multiservicos',
    'conta de consumo',
}

SINONIMOS_DOCUMENTO_ALUGUEL = {
    'aluguel',
    'alugel',
    'alugol',
    'aluguel de imóvel',
    'aluguel de imovel',
    'aluguel de casa',
    'aluguel de apartamento',
    'aluguel comercial',
    'locação',
    'locacao',
    'arrendamento',
    'contrato de aluguel',
}

# Dicionário com INFORMAÇÕES ADICIONAIS
SINONIMOS_DATA = {
    'vencimento',
    'data de vencimento',
    'prazo',
    'data de pagamento',
    'data limite',
    'data final',
    'data de exigibilidade',
    'vence em',
    'deadline',
    'due date',
    'data de competência',
    'competência',
    'competencia',
    'período',
    'periodo',
    'referência',
    'referencia',
}

SINONIMOS_CODIGO = {
    'código',
    'codigo',
    'código de barras',
    'codigo de barras',
    'barras',
    'barcode',
    'linha digitável',
    'linha digitavel',
    'digitable line',
    'número de documento',
    'numero de documento',
    'número de referência',
    'numero de referencia',
    'nosso número',
    'nosso numero',
    'sequencial',
}

SINONIMOS_IDENTIFICACAO = {
    'cpf',
    'cnpj',
    'identidade',
    'rg',
    'documento',
    'documento de identidade',
    'inscrição estadual',
    'inscricao estadual',
    'ie',
    'inscrição municipal',
    'inscricao municipal',
    'im',
    'nih',
    'nire',
    'codigo sifi',
    'codigo sicaf',
}

# Função para extrair contexto
def identificar_tipo_documento(texto: str) -> str:
    """Identifica o tipo de documento baseado no texto"""
    texto_lower = texto.lower()
    
    if any(sin in texto_lower for sin in SINONIMOS_DOCUMENTO_BOLETO):
        return 'boleto'
    elif any(sin in texto_lower for sin in SINONIMOS_DOCUMENTO_IMPOSTO):
        return 'imposto'
    elif any(sin in texto_lower for sin in SINONIMOS_DOCUMENTO_CONDOMINIO):
        return 'condominio'
    elif any(sin in texto_lower for sin in SINONIMOS_DOCUMENTO_UTILIDADE):
        return 'utilidade'
    elif any(sin in texto_lower for sin in SINONIMOS_DOCUMENTO_ALUGUEL):
        return 'aluguel'
    elif any(sin in texto_lower for sin in SINONIMOS_DOCUMENTO_TRANSFERENCIA):
        return 'transferencia'
    elif any(sin in texto_lower for sin in SINONIMOS_DOCUMENTO_FATURA):
        return 'fatura'
    else:
        return 'documento'


def extrair_com_sinonimos(texto: str, tipo_campo: str) -> List[str]:
    """
    Extrai valores do texto usando sinônimos
    
    Args:
        texto: Texto do documento
        tipo_campo: 'beneficiario', 'pagador', 'valor', 'data', 'codigo' ou 'tipo'
    
    Returns:
        Lista de possibilidades encontradas
    """
    from typing import List
    
    texto_lower = texto.lower()
    encontrados = []
    
    mapa_sinonimos = {
        'beneficiario': SINONIMOS_BENEFICIARIO,
        'pagador': SINONIMOS_PAGADOR,
        'valor': SINONIMOS_VALOR,
        'data': SINONIMOS_DATA,
        'codigo': SINONIMOS_CODIGO,
        'identificacao': SINONIMOS_IDENTIFICACAO,
    }
    
    sinonimos = mapa_sinonimos.get(tipo_campo, set())
    
    if not sinonimos:
        return encontrados
    
    # Procura por sinônimos no texto
    for sinonimo in sinonimos:
        if sinonimo in texto_lower:
            encontrados.append(sinonimo)
    
    return encontrados


# Função para criar prompt melhorado para Gemini
def criar_prompt_extracao_melhorado(tipo_documento: str = None) -> str:
    """Cria um prompt otimizado para extração de dados com sinônimos"""
    
    prompt = """Analise este documento financeiro (boleto, fatura, transferência, imposto) e extraia as informações em formato JSON.

INSTRUÇÕES ESPECÍFICAS PARA EXTRAÇÃO:

1. **BENEFICIÁRIO** (quem recebe o pagamento):
   - Procure por: beneficiário, credor, empresa, instituição, banco, empresa credora, fornecedor, prestador de serviço
   - Pode estar nos campos: "Cedente", "Favorecido", "Empresa", "Instituição", "Empresa Gestora", "Concessionária"
   - Para CONDOMÍNIO: procure pelo nome do condomínio ou síndico
   - Para UTILIDADES (luz, água): procure pelo nome da distribuidora/concessionária

2. **PAGADOR** (quem paga):
   - Procure por: pagador, devedor, depositante, cliente, titular, cpf/cnpj, pessoa física/jurídica
   - Pode estar nos campos: "Sacado", "Devedor", "Contratante", "Conta Débito", "Débito Automático"
   - Para TRANSFERÊNCIA: procure pelo "Ordenante" ou "Remetente"
   - Para ALUGUEL: procure pelo "Locatário" ou "Inquilino"

3. **VALOR** (quanto é cobrado):
   - Procure por: valor, valor total, total a pagar, montante, quantia, principal, tarifa, taxa
   - Pode estar destacado, em negrito, em campos específicos como "Valor Cobrado", "Total Devido"
   - Pode conter: juros, multa, correção, acréscimo, desconto
   - IMPORTANTE: extraia APENAS o número (ex: 150.00 ou 150,00)

4. **DATAS IMPORTANTES**:
   - Vencimento: procure por "vencimento", "data de vencimento", "prazo", "data limite"
   - Competência/Referência: para impostos, procure por "período", "competência", "referência"

5. **TIPO DE DOCUMENTO**:
   - Boleto: tem linha digitável (47-48 dígitos), código de barras (44 dígitos), vencimento
   - DARF/GPS/DAS: imposto específico, tem código de receita, período de apuração
   - CONDOMÍNIO: menciona condomínio, síndico, despesa condominial
   - UTILIDADE: luz, água, gás, telefone, internet
   - ALUGUEL: menciona aluguel, locação, imóvel
   - TRANSFERÊNCIA: tem dados de transferência, TED, TEF, ordem de crédito
   - FATURA: conta, nota de débito, recibo, invoice

Retorne APENAS um JSON válido (sem markdown, sem ```json) com os seguintes campos:

{
    "tipo": "boleto | darf | gps | das | iptu | ipva | fgts | condominio | aluguel | luz | agua | gas | telefone | internet | transferencia | fatura | outro",
    "valor": número decimal APENAS (ex: 150.00 ou 150,00 → retorne 150.00),
    "linha_digitavel": "linha digitável completa (47-48 dígitos, apenas números)",
    "codigo_barras": "código de barras (44 dígitos, apenas números)",
    "vencimento": "data no formato DD/MM/YYYY",
    "beneficiario": "nome completo de quem recebe o pagamento",
    "pagador": "nome completo de quem paga",
    "descricao": "descrição do que está sendo cobrado",
    "cnpj_cpf": "CNPJ ou CPF do beneficiário (com ou sem formatação)",
    "banco": "nome do banco (se for boleto bancário)",
    "agencia": "número da agência (se houver)",
    "conta": "número da conta (se houver)",
    "periodo_apuracao": "período de referência para impostos (ex: 01/2024)",
    "codigo_receita": "código de receita para DARF/GPS/DAS"
}

REGRAS IMPORTANTES:
- Se algum campo não estiver visível, retorne null
- Retorne APENAS o JSON, sem explicações ou markdown
- O valor DEVE ser apenas números com ponto decimal (150.00, não 150,00 ou R$ 150,00)
- A linha digitável deve ter TODOS os dígitos, sem espaços
- Não adicione campos extras"""
    
    return prompt


if __name__ == "__main__":
    # Testes
    print("Sinônimos de Beneficiário:", len(SINONIMOS_BENEFICIARIO))
    print("Sinônimos de Pagador:", len(SINONIMOS_PAGADOR))
    print("Sinônimos de Valor:", len(SINONIMOS_VALOR))
    print("\nTipo identificado: 'luz e água':", identificar_tipo_documento("Sua conta de luz e água"))
    print("Tipo identificado: 'IPTU':", identificar_tipo_documento("Guia de IPTU 2024"))
