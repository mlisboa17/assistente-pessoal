"""
Módulo de Normalização de Extratos Bancários
Segundo estágio do processamento: padronização, validação e enriquecimento dos dados
"""

import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict

@dataclass
class TransacaoNormalizada:
    """Transação bancária normalizada e enriquecida"""
    id: str
    data: str
    descricao: str
    valor: float
    tipo: str  # 'credito' ou 'debito'
    categoria: str
    subcategoria: str
    banco: str
    conta: str
    agencia: str
    documento: str
    lote: str
    historico_completo: str
    valor_absoluto: float
    data_formatada: str
    mes_ano: str
    dia_semana: str
    tags: List[str]
    confianca_categorizacao: float
    fonte: str  # 'pdf', 'csv', 'ofx', etc.
    data_processamento: str
    valido: bool
    erros_validacao: List[str]

@dataclass
class TransacaoNormalizadaFinal:
    """Transação normalizada no formato final para entrega conforme especificações ETL"""
    # Campos obrigatórios padronizados
    ID_Transacao_Unico: str  # UUID ou Hash único
    Conta_ID: str  # Identificador da conta (Agencia + Conta)
    Data_Hora_Transacao: str  # ISO 8601
    Valor_Numerico: float  # Com sinal correto (+ crédito, - débito)
    Tipo_Movimento: str  # 'CREDITO' ou 'DEBITO'
    Descricao_Normalizada: str  # Descrição limpa e normalizada
    ID_Contraparte: str  # CPF/CNPJ se identificado, senão vazio
    Agencia_Banco_Origem: str  # Código do banco + agencia
    Origem_Dado: str  # Fonte do dado (PDF, API, OFX, etc.)

    # Campos adicionais para enriquecimento (opcionais)
    Categoria_Sugerida: str
    Subcategoria_Sugerida: str
    Confianca_Categorizacao: float
    Nome_Contraparte: str
    Saldo_Apos_Transacao: float
    Tags_Identificadas: List[str]
    Validado: bool
    Data_Processamento: str

class NormalizadorExtratos:
    """Normaliza e enriquece dados de extratos bancários"""

    def __init__(self):
        self.categorias_padrao = self._carregar_categorias_padrao()
        self.regras_normalizacao = self._carregar_regras_normalizacao()

    def _carregar_categorias_padrao(self) -> Dict[str, List[str]]:
        """Carrega categorias padrão para classificação automática"""
        return {
            'receitas': {
                'vendas': ['VENDA', 'RECEITA', 'FATURAMENTO', 'COMISSAO'],
                'servicos': ['SERVICO', 'CONSULTORIA', 'ASSESSORIA', 'MANUTENCAO'],
                'investimentos': ['DIVIDENDO', 'JUROS', 'RENDIMENTO', 'APLICACAO'],
                'transferencias_entrada': ['TRANSFERENCIA RECEBIDA', 'PIX RECEBIDO', 'DOC RECEBIDO', 'TED RECEBIDO'],
                'devolucoes': ['DEVOLUCAO', 'ESTORNO', 'CREDITO'],
                'outros_creditos': ['OUTROS CREDITOS', 'CREDITO DIVERSO']
            },
            'despesas': {
                'combustivel': ['COMBUSTIVEL', 'GASOLINA', 'ETANOL', 'DIESEL', 'POSTO', 'ABASTECIMENTO'],
                'alimentacao': ['RESTAURANTE', 'LANCHONETE', 'SUPERMERCADO', 'PADARIA', 'MERCADO'],
                'transporte': ['UBER', 'TAXI', 'METRO', 'ONIBUS', 'ESTACIONAMENTO', 'PEDAGIO'],
                'saude': ['FARMACIA', 'MEDICO', 'HOSPITAL', 'PLANO SAUDE', 'CONSULTA'],
                'educacao': ['ESCOLA', 'CURSO', 'LIVRARIA', 'MATERIAL ESCOLAR'],
                'lazer': ['CINEMA', 'TEATRO', 'SHOW', 'INGRESSO', 'ENTRETENIMENTO'],
                'vestuario': ['ROUPA', 'CALÇADO', 'ACESSORIO'],
                'casa': ['ALUGUEL', 'CONDOMINIO', 'LUZ', 'AGUA', 'GAS', 'INTERNET', 'TELEFONE'],
                'impostos': ['IMPOSTO', 'TAXA', 'MULTA', 'JUROS', 'ENCARGOS'],
                'transferencias_saida': ['TRANSFERENCIA ENVIADA', 'PIX ENVIADO', 'DOC ENVIADO', 'TED ENVIADO'],
                'tarifas': ['TARIFA', 'TAXA SERVICO', 'MANUTENCAO CONTA'],
                'seguros': ['SEGURO', 'PREVIDENCIA'],
                'outros_debitos': ['OUTROS DEBITOS', 'DEBITO DIVERSO']
            }
        }

    def _carregar_regras_normalizacao(self) -> Dict[str, Any]:
        """Carrega regras de normalização específicas por banco seguindo padrão ETL"""
        return {
            'c6': {
                'prefixos_remover': ['PIX REC', 'PIX ENV', 'TED REC', 'TED ENV', 'DOC REC', 'DOC ENV'],
                'padroes_data': [r'\d{2}/\d{2}/\d{4}', r'\d{2}/\d{2}'],
                'padroes_valor': [r'R\$\s*[\d.,]+', r'[\d.,]+'],
                'padroes_contraparte': {
                    'cpf': r'\d{3}\.\d{3}\.\d{3}-\d{2}',
                    'cnpj': r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}',
                    'nome': r'(?:PARA|DE)\s+([A-Z\s]+?)(?:\s+\d|\s+R\$|\s*$)'
                },
                'normalizar_descricao': self._normalizar_descricao_c6,
                'mapear_tipo_movimento': self._mapear_tipo_c6
            },
            'banco_do_brasil': {
                'prefixos_remover': ['DEP DIN BCO24H', 'BOLETO', 'PIX', 'TED', 'DOC'],
                'padroes_data': [r'\d{2}/\d{2}/\d{4}'],
                'padroes_valor': [r'R\$\s*[\d.,]+', r'[\d.,]+'],
                'padroes_contraparte': {
                    'cpf': r'\d{3}\.\d{3}\.\d{3}-\d{2}',
                    'cnpj': r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}',
                    'nome': r'(?:PARA|DE)\s+([A-Z\s]+?)(?:\s+\d|\s+R\$|\s*$)'
                },
                'normalizar_descricao': self._normalizar_descricao_bb,
                'mapear_tipo_movimento': self._mapear_tipo_bb
            },
            'itau': {
                'prefixos_remover': ['PIX', 'TED', 'DOC', 'BOLETO'],
                'padroes_data': [r'\d{2}/\d{2}'],
                'padroes_valor': [r'[\d.,]+'],
                'padroes_contraparte': {
                    'cpf': r'\d{3}\.\d{3}\.\d{3}-\d{2}',
                    'cnpj': r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}',
                    'nome': r'(?:PARA|DE)\s+([A-Z\s]+?)(?:\s+\d|\s+R\$|\s*$)'
                },
                'normalizar_descricao': self._normalizar_descricao_itau,
                'mapear_tipo_movimento': self._mapear_tipo_itau
            },
            'santander': {
                'prefixos_remover': ['PIX', 'TED', 'DOC', 'BOLETO', 'TRANSF'],
                'padroes_data': [r'\d{2}/\d{2}'],
                'padroes_valor': [r'R\$\s*[\d.,]+', r'[\d.,]+'],
                'padroes_contraparte': {
                    'cpf': r'\d{3}\.\d{3}\.\d{3}-\d{2}',
                    'cnpj': r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}',
                    'nome': r'(?:PARA|DE)\s+([A-Z\s]+?)(?:\s+\d|\s+R\$|\s*$)'
                },
                'normalizar_descricao': self._normalizar_descricao_santander,
                'mapear_tipo_movimento': self._mapear_tipo_santander
            },
            'pagseguro': {
                'prefixos_remover': ['PIX', 'TED', 'DOC', 'BOLETO', 'PAGBANK'],
                'padroes_data': [r'\d{2}/\d{2}/\d{4}', r'\d{2}/\d{2}'],
                'padroes_valor': [r'R\$\s*[\d.,]+', r'[\d.,]+'],
                'padroes_contraparte': {
                    'cpf': r'\d{3}\.\d{3}\.\d{3}-\d{2}',
                    'cnpj': r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}',
                    'nome': r'(?:PARA|DE)\s+([A-Z\s]+?)(?:\s+\d|\s+R\$|\s*$)'
                },
                'normalizar_descricao': self._normalizar_descricao_pagseguro,
                'mapear_tipo_movimento': self._mapear_tipo_pagseguro
            },
            'geral': {
                'prefixos_remover': ['PAGAMENTO', 'PAGTO', 'RECEBIMENTO', 'REC'],
                'padroes_data': [r'\d{2}/\d{2}/?\d{4}?'],
                'padroes_valor': [r'R\$\s*[\d.,]+', r'[\d.,]+'],
                'padroes_contraparte': {
                    'cpf': r'\d{3}\.\d{3}\.\d{3}-\d{2}',
                    'cnpj': r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}',
                    'nome': r'(?:PARA|DE)\s+([A-Z\s]+?)(?:\s+\d|\s+R\$|\s*$)'
                },
                'normalizar_descricao': self._normalizar_descricao_geral,
                'mapear_tipo_movimento': self._mapear_tipo_geral
            }
        }

    def normalizar_extrato(self, dados_extrato: Dict[str, Any], banco: str) -> Dict[str, Any]:
        """
        Normaliza um extrato completo
        Retorna dados normalizados e estatísticas
        """
        print(f"🔄 Normalizando extrato do {banco}...")

        # Normalizar informações básicas
        extrato_normalizado = {
            'banco': banco.upper(),
            'agencia': dados_extrato.get('agencia', ''),
            'conta': dados_extrato.get('conta', ''),
            'nome_empresa': dados_extrato.get('nome_empresa', ''),
            'titular': self._normalizar_titular(dados_extrato.get('titular', '')),
            'cpf_cnpj_titular': dados_extrato.get('cpf_cnpj_titular', ''),
            'periodo': dados_extrato.get('periodo', ''),
            'saldo_anterior': dados_extrato.get('saldo_anterior', 0.0),
            'saldo_atual': dados_extrato.get('saldo_atual', 0.0),
            'data_processamento': datetime.now().isoformat(),
            'fonte': 'pdf',  # TODO: detectar automaticamente
            'transacoes': []
        }

        # Normalizar transações
        transacoes_normalizadas = []
        for transacao in dados_extrato.get('transacoes', []):
            transacao_norm = self._normalizar_transacao(transacao, banco)
            if transacao_norm:
                transacoes_normalizadas.append(transacao_norm)

        extrato_normalizado['transacoes'] = transacoes_normalizadas

        # Calcular estatísticas
        estatisticas = self._calcular_estatisticas(transacoes_normalizadas)
        extrato_normalizado['estatisticas'] = estatisticas

        # Validar dados
        validacao = self._validar_extrato_normalizado(extrato_normalizado)
        extrato_normalizado['validacao'] = validacao

        # Criar preview para confirmação
        extrato_normalizado['preview_categorias'] = self._criar_preview_categorias(transacoes_normalizadas, estatisticas)

        # CONVERTER PARA FORMATO FINAL PADRONIZADO
        print("🔄 Convertendo para formato final padronizado...")
        transacoes_finais = []
        for transacao in transacoes_normalizadas:
            transacao_final = self._converter_para_formato_final(
                transacao,
                extrato_normalizado.get('agencia', ''),
                extrato_normalizado.get('conta', '')
            )
            transacoes_finais.append(transacao_final)

        # Adicionar dados no formato final
        extrato_normalizado['transacoes_finais'] = [asdict(t) for t in transacoes_finais]

        print(f"✅ Normalização concluída: {len(transacoes_normalizadas)} transações")
        print(f"📋 Formato final gerado com {len(transacoes_finais)} transações padronizadas")

        return extrato_normalizado

    def _normalizar_transacao(self, transacao, banco: str) -> Optional[TransacaoNormalizada]:
        """Normaliza uma transação individual seguindo padrão ETL"""
        try:
            # Extrair dados básicos
            data = getattr(transacao, 'data', '')
            descricao_original = getattr(transacao, 'descricao', '')
            valor_bruto = getattr(transacao, 'valor', 0.0)
            tipo_bruto = getattr(transacao, 'tipo', 'credito')
            categoria_sugerida = getattr(transacao, 'categoria_sugerida', 'sem_categoria')

            # Aplicar regras específicas do banco
            regras = self.regras_normalizacao.get(banco.lower(), self.regras_normalizacao['geral'])

            # Mapear tipo de movimento padronizado
            tipo_movimento = regras['mapear_tipo_movimento'](tipo_bruto, descricao_original)

            # Normalizar valor com sinal correto
            valor = self._normalizar_valor(valor_bruto, tipo_movimento)

            # Normalizar data para ISO 8601
            data_hora_iso, data_formatada, mes_ano, dia_semana = self._normalizar_data(data)

            # Gerar ID único da transação
            id_transacao = self._gerar_id_transacao(banco, data_hora_iso, descricao_original, valor)

            # Normalizar descrição e extrair contraparte
            descricao_normalizada, contraparte_info = self._normalizar_descricao_completa(
                descricao_original, banco
            )

            # Categorizar transação
            categoria, subcategoria, confianca = self._recategorizar_transacao(
                descricao_normalizada, valor, tipo_movimento
            )

            # Usar categoria sugerida se confiança for baixa
            if confianca < 0.7 and categoria_sugerida != 'sem_categoria':
                categoria = categoria_sugerida
                confianca = 0.8

            # Extrair tags
            tags = self._extrair_tags(descricao_normalizada)

            # Validar transação
            valido, erros_validacao = self._validar_transacao(
                id_transacao, data_hora_iso, valor, tipo_movimento
            )

            # Criar objeto normalizado
            transacao_norm = TransacaoNormalizada(
                id=id_transacao,
                data=data_hora_iso,
                descricao=descricao_normalizada,
                valor=valor,
                tipo=tipo_movimento,  # Usando o tipo_movimento padronizado
                categoria=categoria,
                subcategoria=subcategoria,
                banco=banco,
                conta='',  # TODO: preencher do extrato
                agencia='',  # TODO: preencher do extrato
                documento='',  # TODO: extrair se disponível
                lote='',  # TODO: extrair se disponível
                historico_completo=descricao_original,
                valor_absoluto=abs(valor),
                data_formatada=data_formatada,
                mes_ano=mes_ano,
                dia_semana=dia_semana,
                tags=tags,
                confianca_categorizacao=confianca,
                fonte='pdf',
                data_processamento=datetime.now().isoformat(),
                valido=valido,
                erros_validacao=erros_validacao
            )

            return transacao_norm

        except Exception as e:
            print(f"❌ Erro ao normalizar transação: {e}")
            return None

    def _normalizar_data(self, data_str: str) -> tuple:
        """Normaliza data para formato ISO e extrai informações"""
        try:
            # Tentar diferentes formatos
            formatos = ['%d/%m/%Y', '%d/%m/%y', '%d/%m']

            for formato in formatos:
                try:
                    if formato == '%d/%m':
                        # Data sem ano, assumir ano atual
                        dt = datetime.strptime(f"{data_str}/{datetime.now().year}", '%d/%m/%Y')
                    else:
                        dt = datetime.strptime(data_str, formato)

                    data_iso = dt.date().isoformat()
                    data_formatada = dt.strftime('%d/%m/%Y')
                    mes_ano = dt.strftime('%m/%Y')
                    dia_semana = dt.strftime('%A')  # Nome do dia da semana

                    return data_iso, data_formatada, mes_ano, dia_semana

                except ValueError:
                    continue

            # Fallback
            return data_str, data_str, '', ''

        except Exception:
            return data_str, data_str, '', ''

    def _gerar_id_transacao(self, banco: str, data: str, descricao: str, valor: float) -> str:
        """Gera ID único para a transação"""
        import hashlib
        # Criar hash único baseado nos dados da transação
        dados_para_hash = f"{banco}{data}{descricao}{valor}".encode('utf-8')
        hash_obj = hashlib.md5(dados_para_hash)
        return f"{banco.upper()}_{hash_obj.hexdigest()[:12]}"

    def _normalizar_valor(self, valor_bruto: float, tipo_movimento: str) -> float:
        """Normaliza valor aplicando sinal correto"""
        valor_abs = abs(float(valor_bruto))

        # Aplicar sinal correto: negativo para SAÍDAS, positivo para ENTRADAS
        if tipo_movimento == 'SAIDA':
            return -valor_abs
        else:
            return valor_abs

    def _mapear_tipo_c6(self, tipo_bruto: str, descricao: str) -> str:
        """Mapeia tipo de movimento específico do C6"""
        descricao_upper = descricao.upper()

        # Verificar palavras-chave que indicam saída
        saidas = ['PIX ENVIADO', 'TED ENVIADO', 'DOC ENVIADO', 'PAGAMENTO', 'SAQUE', 'COMPRA']
        if any(saida in descricao_upper for saida in saidas) or tipo_bruto.lower() == 'debito':
            return 'SAIDA'

        # Verificar palavras-chave que indicam entrada
        entradas = ['PIX RECEBIDO', 'TED RECEBIDO', 'DOC RECEBIDO', 'DEPOSITO', 'RECEBIMENTO']
        if any(entrada in descricao_upper for entrada in entradas) or tipo_bruto.lower() == 'credito':
            return 'ENTRADA'

        # Default baseado no tipo bruto
        return 'ENTRADA' if tipo_bruto.lower() == 'credito' else 'SAIDA'

    def _mapear_tipo_bb(self, tipo_bruto: str, descricao: str) -> str:
        """Mapeia tipo de movimento específico do Banco do Brasil"""
        return self._mapear_tipo_geral(tipo_bruto, descricao)

    def _mapear_tipo_itau(self, tipo_bruto: str, descricao: str) -> str:
        """Mapeia tipo de movimento específico do Itaú"""
        return self._mapear_tipo_geral(tipo_bruto, descricao)

    def _mapear_tipo_santander(self, tipo_bruto: str, descricao: str) -> str:
        """Mapeia tipo de movimento específico do Santander"""
        return self._mapear_tipo_geral(tipo_bruto, descricao)

    def _mapear_tipo_pagseguro(self, tipo_bruto: str, descricao: str) -> str:
        """Mapeia tipo de movimento específico do PagSeguro"""
        return self._mapear_tipo_geral(tipo_bruto, descricao)

    def _mapear_tipo_geral(self, tipo_bruto: str, descricao: str) -> str:
        """Mapeia tipo de movimento genérico"""
        if tipo_bruto.lower() in ['debito', 'saida', 'pagamento']:
            return 'SAIDA'
        elif tipo_bruto.lower() in ['credito', 'entrada', 'recebimento']:
            return 'ENTRADA'

        # Fallback baseado na descrição
        descricao_upper = descricao.upper()
        if any(word in descricao_upper for word in ['PAGAMENTO', 'SAQUE', 'ENVIADO', 'COMPRA']):
            return 'SAIDA'
        elif any(word in descricao_upper for word in ['RECEBIMENTO', 'DEPOSITO', 'RECEBIDO']):
            return 'ENTRADA'

        return 'ENTRADA'  # Default

    def _normalizar_descricao_completa(self, descricao: str, banco: str) -> tuple:
        """Normaliza descrição e extrai informações da contraparte"""
        regras = self.regras_normalizacao.get(banco.lower(), self.regras_normalizacao['geral'])

        # Aplicar normalização específica do banco
        descricao_normalizada = regras['normalizar_descricao'](descricao.upper().strip())

        # Extrair contraparte
        contraparte_info = self._extrair_contraparte(descricao_normalizada, regras)

        return descricao_normalizada, contraparte_info

    def _extrair_contraparte(self, descricao: str, regras: Dict[str, Any]) -> Dict[str, str]:
        """Extrai informações da contraparte da descrição"""
        padroes = regras.get('padroes_contraparte', {})

        # Tentar extrair CNPJ
        match_cnpj = re.search(padroes.get('cnpj', ''), descricao)
        if match_cnpj:
            return {
                'tipo': 'CNPJ',
                'identificacao': match_cnpj.group(0),
                'nome': self._extrair_nome_empresa(descricao, match_cnpj.end())
            }

        # Tentar extrair CPF
        match_cpf = re.search(padroes.get('cpf', ''), descricao)
        if match_cpf:
            return {
                'tipo': 'CPF',
                'identificacao': match_cpf.group(0),
                'nome': self._extrair_nome_pessoa(descricao, match_cpf.end())
            }

        # Tentar extrair nome
        match_nome = re.search(padroes.get('nome', ''), descricao)
        if match_nome:
            nome = match_nome.group(1).strip()
            if len(nome) > 3:  # Nome deve ter pelo menos 4 caracteres
                return {
                    'tipo': 'NOME_EMPRESA',
                    'identificacao': '',
                    'nome': nome
                }

        # Não conseguiu identificar contraparte
        return {
            'tipo': 'DESCONHECIDA',
            'identificacao': '',
            'nome': ''
        }

    def _extrair_nome_empresa(self, descricao: str, posicao_inicio: int) -> str:
        """Extrai nome da empresa após CNPJ"""
        parte_direita = descricao[posicao_inicio:].strip()
        # Pegar primeiras palavras até encontrar números ou caracteres especiais
        palavras = re.split(r'[^\w\s]', parte_direita)[0].strip()
        return palavras[:50] if palavras else ''

    def _extrair_nome_pessoa(self, descricao: str, posicao_inicio: int) -> str:
        """Extrai nome da pessoa após CPF"""
        parte_direita = descricao[posicao_inicio:].strip()
        # Pegar primeiras palavras
        palavras = parte_direita.split()[:3]  # Máximo 3 palavras
        return ' '.join(palavras) if palavras else ''

    def _mapear_tipo_movimento_final(self, tipo_movimento: str) -> str:
        """Mapeia tipo de movimento para formato final (CREDITO/DEBITO)"""
        if tipo_movimento == 'ENTRADA':
            return 'CREDITO'
        elif tipo_movimento == 'SAIDA':
            return 'DEBITO'
        else:
            # Fallback baseado no sinal do valor (se disponível)
            return 'CREDITO' if tipo_movimento == 'credito' else 'DEBITO'

    def _validar_transacao(self, id_transacao: str, data_hora: str, valor: float, tipo_movimento: str) -> tuple:
        """Valida uma transação e retorna se é válida e lista de erros"""
        erros = []

        # Validar ID
        if not id_transacao or len(id_transacao) < 10:
            erros.append("ID da transação inválido")

        # Validar data
        try:
            datetime.fromisoformat(data_hora.replace('Z', '+00:00'))
        except:
            erros.append("Data/hora inválida")

        # Validar valor
        if valor == 0:
            erros.append("Valor da transação não pode ser zero")

        # Validar tipo de movimento
        if tipo_movimento not in ['ENTRADA', 'SAIDA']:
            erros.append("Tipo de movimento deve ser ENTRADA ou SAIDA")

        # Validar sinal do valor
        if tipo_movimento == 'SAIDA' and valor > 0:
            erros.append("Transações de saída devem ter valor negativo")
        elif tipo_movimento == 'ENTRADA' and valor < 0:
            erros.append("Transações de entrada devem ter valor positivo")

        return len(erros) == 0, erros

    def _converter_para_formato_final(self, transacao, agencia: str, conta: str) -> TransacaoNormalizadaFinal:
        """Converte TransacaoNormalizada para o formato final padronizado"""
        # Monta Conta_ID (Agencia + Conta)
        conta_id = f"{agencia}-{conta}" if agencia and conta else f"{agencia or ''}{conta or ''}"

        # Monta Agencia_Banco_Origem (Código do banco + agencia)
        agencia_banco_origem = f"{transacao.banco}_{agencia}" if agencia else transacao.banco

        # Mapeia tipo de movimento para formato final
        tipo_movimento_final = self._mapear_tipo_movimento_final(transacao.tipo)

        # ID_Contraparte: apenas CPF/CNPJ, não nome
        id_contraparte = ""
        if hasattr(transacao, 'contraparte_tipo') and hasattr(transacao, 'contraparte_identificacao'):
            if getattr(transacao, 'contraparte_tipo', '') in ['CPF', 'CNPJ']:
                id_contraparte = getattr(transacao, 'contraparte_identificacao', '')

        # Saldo após transação (não temos essa informação ainda)
        saldo_apos = 0.0

        # Tags identificadas
        tags = getattr(transacao, 'tags', [])

        return TransacaoNormalizadaFinal(
            ID_Transacao_Unico=getattr(transacao, 'id', ''),
            Conta_ID=conta_id,
            Data_Hora_Transacao=getattr(transacao, 'data', ''),
            Valor_Numerico=getattr(transacao, 'valor', 0.0),
            Tipo_Movimento=tipo_movimento_final,
            Descricao_Normalizada=getattr(transacao, 'descricao', ''),
            ID_Contraparte=id_contraparte,
            Agencia_Banco_Origem=agencia_banco_origem,
            Origem_Dado=getattr(transacao, 'fonte', 'PDF').upper(),
            Categoria_Sugerida=getattr(transacao, 'categoria', ''),
            Subcategoria_Sugerida=getattr(transacao, 'subcategoria', ''),
            Confianca_Categorizacao=getattr(transacao, 'confianca_categorizacao', 0.0),
            Nome_Contraparte=getattr(transacao, 'contraparte_nome', ''),
            Saldo_Apos_Transacao=saldo_apos,
            Tags_Identificadas=tags,
            Validado=getattr(transacao, 'valido', True),
            Data_Processamento=getattr(transacao, 'data_processamento', '')
        )

    def _normalizar_descricao_c6(self, descricao: str) -> str:
        """Normaliza descrição específica do C6 Bank"""
        # Remover códigos e números desnecessários
        descricao = re.sub(r'\d{15,}', '', descricao)  # Remove números muito longos
        descricao = re.sub(r'\s+', ' ', descricao)  # Remove espaços extras

        # Padronizar termos comuns do C6
        substituicoes = {
            'PIX REC': 'PIX RECEBIDO',
            'PIX ENV': 'PIX ENVIADO',
            'TED REC': 'TED RECEBIDO',
            'TED ENV': 'TED ENVIADO',
            'DOC REC': 'DOC RECEBIDO',
            'DOC ENV': 'DOC ENVIADO',
            'PAGTO': 'PAGAMENTO',
            'REC': 'RECEBIMENTO'
        }

        for antigo, novo in substituicoes.items():
            descricao = descricao.replace(antigo, novo)

        return descricao.strip()

    def _normalizar_descricao_bb(self, descricao: str) -> str:
        """Normaliza descrição específica do Banco do Brasil"""
        # Remover códigos e números desnecessários
        descricao = re.sub(r'\d{15,}', '', descricao)  # Remove números muito longos
        descricao = re.sub(r'\s+', ' ', descricao)  # Remove espaços extras

        # Padronizar termos
        substituicoes = {
            'DEP DIN BCO24H': 'DEPOSITO',
            'BOLETO': 'PAGAMENTO BOLETO',
            'PIX': 'PIX',
            'TED': 'TED',
            'DOC': 'DOC'
        }

        for antigo, novo in substituicoes.items():
            descricao = descricao.replace(antigo, novo)

        return descricao.strip()

    def _normalizar_descricao_itau(self, descricao: str) -> str:
        """Normaliza descrição específica do Itaú"""
        # Remover códigos específicos do Itaú
        descricao = re.sub(r'ITAÚ\s+', '', descricao)
        descricao = re.sub(r'\s+', ' ', descricao)

        # Padronizar termos
        substituicoes = {
            'PIX': 'PIX',
            'TED': 'TED',
            'DOC': 'DOC',
            'BOLETO': 'PAGAMENTO BOLETO'
        }

        for antigo, novo in substituicoes.items():
            descricao = descricao.replace(antigo, novo)

        return descricao.strip()

    def _normalizar_descricao_santander(self, descricao: str) -> str:
        """Normaliza descrição específica do Santander"""
        # Remover códigos específicos do Santander
        descricao = re.sub(r'SANTANDER\s+', '', descricao)
        descricao = re.sub(r'\s+', ' ', descricao)

        # Padronizar termos
        substituicoes = {
            'PIX': 'PIX',
            'TED': 'TED',
            'DOC': 'DOC',
            'TRANSF': 'TRANSFERENCIA',
            'BOLETO': 'PAGAMENTO BOLETO'
        }

        for antigo, novo in substituicoes.items():
            descricao = descricao.replace(antigo, novo)

        return descricao.strip()

    def _normalizar_descricao_pagseguro(self, descricao: str) -> str:
        """Normaliza descrição específica do PagSeguro"""
        # Remover códigos específicos do PagSeguro
        descricao = re.sub(r'PAGBANK\s+', '', descricao)
        descricao = re.sub(r'PAGSEGURO\s+', '', descricao)
        descricao = re.sub(r'\s+', ' ', descricao)

        # Padronizar termos
        substituicoes = {
            'PIX': 'PIX',
            'TED': 'TED',
            'DOC': 'DOC',
            'TRANSF': 'TRANSFERENCIA',
            'BOLETO': 'PAGAMENTO BOLETO',
            'PAGAMENTO': 'PAGAMENTO',
            'RECEBIMENTO': 'RECEBIMENTO'
        }

        for antigo, novo in substituicoes.items():
            descricao = descricao.replace(antigo, novo)

        return descricao.strip()

    def _normalizar_descricao_geral(self, descricao: str) -> str:
        """Normaliza descrição genérica"""
        # Remover caracteres especiais e normalizar espaços
        descricao = re.sub(r'[^\w\s]', ' ', descricao)
        descricao = re.sub(r'\s+', ' ', descricao)

        # Padronizar termos comuns
        substituicoes = {
            'PAGAMENTO': 'PAGAMENTO',
            'PAGTO': 'PAGAMENTO',
            'RECEBIMENTO': 'RECEBIMENTO',
            'REC': 'RECEBIMENTO',
            'DEP': 'DEPOSITO',
            'SAQ': 'SAQUE'
        }

        for antigo, novo in substituicoes.items():
            descricao = descricao.replace(antigo, novo)

        return descricao.strip()
        descricao = re.sub(r'\d{10,}', '', descricao)  # Remove números longos
        return descricao.strip()

    def _normalizar_descricao_geral(self, descricao: str) -> str:
        """Normaliza descrição genérica"""
        # Remover caracteres especiais e números desnecessários
        descricao = re.sub(r'[^\w\s]', ' ', descricao)
        descricao = re.sub(r'\s+', ' ', descricao)
        return descricao.strip()

    def _extrair_tags(self, descricao: str) -> List[str]:
        """Extrai tags relevantes da descrição"""
        tags = []
        palavras = descricao.split()

        # Tags de estabelecimentos comuns
        estabelecimentos = ['POSTO', 'RESTAURANTE', 'FARMACIA', 'SUPERMERCADO', 'PADARIA']
        for estabelecimento in estabelecimentos:
            if estabelecimento in descricao:
                tags.append(estabelecimento.lower())

        # Tags de tipos de transação
        tipos = ['PIX', 'TED', 'DOC', 'BOLETO', 'DEPOSITO', 'SAQUE']
        for tipo in tipos:
            if tipo in descricao:
                tags.append(tipo.lower())

        return tags

    def _recategorizar_transacao(self, descricao: str, valor: float, tipo_movimento: str) -> tuple:
        """Recategoriza transação com regras aprimoradas seguindo padrão ETL"""
        melhor_categoria = 'sem_categoria'
        melhor_subcategoria = ''
        maior_confianca = 0.0

        # Determinar se é receita ou despesa baseado no tipo de movimento e valor
        if tipo_movimento == 'ENTRADA' or valor > 0:
            categorias_busca = self.categorias_padrao['receitas']
        else:
            categorias_busca = self.categorias_padrao['despesas']

        # Buscar em todas as subcategorias
        for subcat, padroes in categorias_busca.items():
            for padrao in padroes:
                if padrao.upper() in descricao:
                    confianca = 0.9  # Alta confiança para match exato

                    # Ajustar confiança baseada em contexto
                    if abs(valor) > 1000 and tipo_movimento == 'SAIDA':
                        confianca *= 0.8  # Valores altos em despesas podem ser suspeitos

                    if len(descricao.split()) < 3:
                        confianca *= 0.7  # Descrições muito curtas têm menos confiança

                    # Bonus para múltiplas correspondências
                    matches = sum(1 for p in padroes if p.upper() in descricao)
                    if matches > 1:
                        confianca = min(confianca * 1.2, 1.0)

                    if confianca > maior_confianca:
                        maior_confianca = confianca
                        melhor_categoria = 'receitas' if tipo_movimento == 'ENTRADA' else 'despesas'
                        melhor_subcategoria = subcat

        return melhor_categoria, melhor_subcategoria, maior_confianca

    def _normalizar_titular(self, titular: str) -> str:
        """Normaliza nome do titular"""
        if not titular:
            return ''

        # Remover caracteres especiais e números
        titular = re.sub(r'[^\w\s]', '', titular)
        titular = re.sub(r'\s+', ' ', titular)

        # Capitalizar palavras
        return titular.title().strip()

    def _calcular_estatisticas(self, transacoes: List[TransacaoNormalizada]) -> Dict[str, Any]:
        """Calcula estatísticas do extrato seguindo padrão ETL"""
        stats = {
            'total_transacoes': len(transacoes),
            'total_entradas': 0,
            'total_saidas': 0,
            'valor_total_entradas': 0.0,
            'valor_total_saidas': 0.0,
            'saldo_calculado': 0.0,
            'categorias': defaultdict(int),
            'subcategorias': defaultdict(int),
            'dias_com_movimento': set(),
            'transacoes_por_dia': defaultdict(int),
            'transacoes_validas': 0,
            'transacoes_invalidas': 0,
            'contrapartes_identificadas': 0
        }

        for transacao in transacoes:
            # Contar entradas e saídas
            if transacao.tipo == 'ENTRADA':
                stats['total_entradas'] += 1
                stats['valor_total_entradas'] += transacao.valor_absoluto
            else:
                stats['total_saidas'] += 1
                stats['valor_total_saidas'] += transacao.valor_absoluto

            # Contar por categoria e subcategoria
            stats['categorias'][transacao.categoria] += 1
            if transacao.subcategoria:
                stats['subcategorias'][transacao.subcategoria] += 1

            # Estatísticas de data
            data_date = transacao.data.split('T')[0] if 'T' in transacao.data else transacao.data
            stats['dias_com_movimento'].add(data_date)
            stats['transacoes_por_dia'][data_date] += 1

            # Validação
            if transacao.valido:
                stats['transacoes_validas'] += 1
            else:
                stats['transacoes_invalidas'] += 1

            # Contrapartes
            if getattr(transacao, 'contraparte_tipo', 'DESCONHECIDA') != 'DESCONHECIDA':
                stats['contrapartes_identificadas'] += 1

        stats['saldo_calculado'] = stats['valor_total_entradas'] - stats['valor_total_saidas']
        stats['dias_com_movimento'] = len(stats['dias_com_movimento'])

        return stats

    def _criar_preview_categorias(self, transacoes: List[TransacaoNormalizada], estatisticas: Dict[str, Any]) -> Dict[str, Any]:
        """Cria estrutura de preview agrupada por categorias"""
        from collections import defaultdict

        # Agrupar transações por categoria
        receitas = defaultdict(lambda: {'total': 0.0, 'transacoes': []})
        despesas = defaultdict(lambda: {'total': 0.0, 'transacoes': []})
        sem_categoria = []

        for transacao in transacoes:
            if transacao.categoria == 'sem_categoria':
                sem_categoria.append(transacao)
            elif transacao.tipo == 'credito':
                receitas[transacao.categoria]['total'] += abs(transacao.valor)
                receitas[transacao.categoria]['transacoes'].append(transacao)
            else:  # debito
                despesas[transacao.categoria]['total'] += abs(transacao.valor)
                despesas[transacao.categoria]['transacoes'].append(transacao)

        return {
            'totais': {
                'entradas': estatisticas['valor_total_entradas'],
                'saidas': estatisticas['valor_total_saidas'],
                'saldo': estatisticas['saldo_calculado']
            },
            'receitas': dict(receitas),
            'despesas': dict(despesas),
            'sem_categoria': sem_categoria
        }

    def _validar_extrato_normalizado(self, extrato: Dict[str, Any]) -> Dict[str, Any]:
        """Valida dados do extrato normalizado seguindo padrão ETL"""
        validacao = {
            'valido': True,
            'erros': [],
            'avisos': [],
            'estatisticas': {}
        }

        # Verificações básicas
        if not extrato.get('banco'):
            validacao['erros'].append('Banco não identificado')

        if not extrato.get('transacoes'):
            validacao['erros'].append('Nenhuma transação encontrada')

        if len(extrato.get('transacoes', [])) == 0:
            validacao['erros'].append('Extrato vazio')

        # Verificações de consistência
        stats = extrato.get('estatisticas', {})

        # Verificar se saldo calculado bate com saldo informado
        saldo_calculado = stats.get('saldo_calculado', 0)
        saldo_atual = extrato.get('saldo_atual', 0)
        diferenca_saldo = abs(saldo_calculado - saldo_atual)

        if diferenca_saldo > 0.01:  # Tolerância de 1 centavo
            validacao['avisos'].append(f"Diferença de saldo: R$ {diferenca_saldo:.2f}")

        # Verificar transações sem categoria
        sem_categoria = stats.get('categorias', {}).get('sem_categoria', 0)
        total_transacoes = stats.get('total_transacoes', 0)

        if sem_categoria > total_transacoes * 0.5:  # Mais de 50% sem categoria
            validacao['avisos'].append(f'Alta porcentagem de transações sem categoria: {sem_categoria}/{total_transacoes}')

        # Verificar transações inválidas
        invalidas = stats.get('transacoes_invalidas', 0)
        if invalidas > 0:
            validacao['avisos'].append(f'Transações com erros de validação: {invalidas}')

        # Verificar contrapartes identificadas
        contrapartes = stats.get('contrapartes_identificadas', 0)
        if contrapartes < total_transacoes * 0.3:  # Menos de 30% com contraparte identificada
            validacao['avisos'].append(f'Baixa identificação de contrapartes: {contrapartes}/{total_transacoes}')

        # Verificar se há erros
        if validacao['erros']:
            validacao['valido'] = False

        return validacao

# Instância global para uso
normalizador = NormalizadorExtratos()

def normalizar_extrato_completo(dados_extrato: Dict[str, Any], banco: str) -> Dict[str, Any]:
    """Função principal para normalizar extrato"""
    return normalizador.normalizar_extrato(dados_extrato, banco)

if __name__ == "__main__":
    print("🧹 Módulo de Normalização de Extratos Carregado")
    print("📊 Pronto para normalizar dados de extratos bancários")