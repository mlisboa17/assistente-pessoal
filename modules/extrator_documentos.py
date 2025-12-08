"""
Módulo de Extração de Documentos Financeiros Brasileiros
=========================================================
Suporta:
- Extratos bancários (PDF e OFX de todos os bancos)
- Comprovantes de pagamento de boletos
- Comprovantes de transferência TED/DOC
- Guias de impostos: DAS, FGTS, INSS/GPS, DARF, GRU
- Notas fiscais eletrônicas
"""

import re
import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from decimal import Decimal
import io

# ========== DATACLASSES ==========

@dataclass
class TransacaoExtrato:
    """Representa uma transação de extrato bancário"""
    data: str
    descricao: str
    valor: float
    tipo: str  # credito, debito
    saldo: Optional[float] = None
    documento: Optional[str] = None
    categoria: Optional[str] = None

@dataclass
class ExtratoBancario:
    """Extrato bancário completo"""
    banco: str
    agencia: str
    conta: str
    titular: str
    periodo_inicio: str
    periodo_fim: str
    saldo_inicial: float
    saldo_final: float
    transacoes: List[TransacaoExtrato]
    total_creditos: float = 0
    total_debitos: float = 0

@dataclass
class GuiaDAS:
    """Documento de Arrecadação do Simples (DAS/MEI)"""
    periodo_apuracao: str  # MM/YYYY
    cnpj: str
    razao_social: str
    valor_principal: float
    valor_total: float
    data_vencimento: str
    codigo_barras: str
    linha_digitavel: str
    numero_documento: str
    receita_bruta: Optional[float] = None
    
@dataclass
class GuiaFGTS:
    """Guia de Recolhimento do FGTS (GRF/GRRF)"""
    competencia: str  # MM/YYYY
    cnpj: str
    razao_social: str
    codigo_recolhimento: str
    valor_fgts: float
    valor_total: float
    data_vencimento: str
    codigo_barras: str
    linha_digitavel: str
    numero_funcionarios: Optional[int] = None
    
@dataclass
class GuiaINSS:
    """Guia da Previdência Social (GPS)"""
    competencia: str  # MM/YYYY
    identificador: str  # CNPJ/CPF/CEI
    tipo_identificador: str  # empresa, contribuinte_individual, domestico
    codigo_pagamento: str
    valor_inss: float
    valor_outras_entidades: float
    valor_atualizacao: float
    valor_total: float
    data_vencimento: str
    codigo_barras: str
    linha_digitavel: str

@dataclass
class GuiaDARF:
    """Documento de Arrecadação de Receitas Federais"""
    periodo_apuracao: str
    cnpj_cpf: str
    codigo_receita: str
    nome_receita: str
    valor_principal: float
    valor_multa: float
    valor_juros: float
    valor_total: float
    data_vencimento: str
    codigo_barras: str
    linha_digitavel: str
    numero_referencia: Optional[str] = None

@dataclass
class ComprovanteBoletoPago:
    """Comprovante de pagamento de boleto"""
    banco_pagador: str
    agencia_conta: str
    data_pagamento: str
    valor_pago: float
    valor_documento: float
    desconto: float
    juros: float
    multa: float
    beneficiario: str
    beneficiario_doc: str
    linha_digitavel: str
    autenticacao: str
    forma_pagamento: str  # app, internet_banking, caixa, etc

# ========== MAPEAMENTOS ==========

BANCOS_BRASIL = {
    '001': 'Banco do Brasil',
    '033': 'Santander',
    '104': 'Caixa Econômica Federal',
    '237': 'Bradesco',
    '341': 'Itaú',
    '260': 'Nubank',
    '077': 'Inter',
    '212': 'Banco Original',
    '336': 'C6 Bank',
    '290': 'PagSeguro',
    '380': 'PicPay',
    '323': 'Mercado Pago',
    '756': 'Sicoob',
    '748': 'Sicredi',
    '422': 'Safra',
    '745': 'Citibank',
    '399': 'HSBC',
    '389': 'Mercantil do Brasil',
    '246': 'ABC Brasil',
    '025': 'Alfa',
    '069': 'Crefisa',
    '655': 'Neon/Votorantim',
    '633': 'Rendimento',
    '739': 'BGN',
    '743': 'Semear',
    '121': 'Agibank',
    '654': 'Digimais',
    '070': 'BRB',
    '047': 'Banese',
    '021': 'Banestes',
    '037': 'Banpará',
    '041': 'Banrisul',
    '004': 'BNB',
    '003': 'Basa',
    '707': 'Daycoval',
    '136': 'Unicred',
    '084': 'Uniprime',
    '097': 'CrediSIS',
}

CODIGOS_RECEITA_DARF = {
    '0190': 'IRPJ - Lucro Real Mensal',
    '0220': 'IRPJ - Lucro Real Trimestral',
    '0561': 'IRRF - Rendimentos do Trabalho',
    '0588': 'IRRF - Aluguéis',
    '1708': 'IRRF - Serviços Profissionais',
    '2372': 'CSLL - Lucro Real Mensal',
    '6012': 'PIS - Faturamento',
    '5856': 'COFINS - Faturamento',
    '5952': 'PIS/COFINS - Importação',
    '4600': 'IRPF - Carnê-Leão',
    '0211': 'IRPF - Ganho de Capital',
    '6015': 'IRPF - Renda Variável',
    '8053': 'IOF',
    '2985': 'FGTS - Contribuinte Individual',
    '5123': 'IPI',
    '1599': 'INSS Patronal',
}

CODIGOS_GPS = {
    '2003': 'Simples - CNPJ',
    '2100': 'Empresa em Geral - CNPJ',
    '2208': 'Cooperativa de Trabalho',
    '2402': 'Órgão Público - CNPJ',
    '1007': 'Contribuinte Individual',
    '1104': 'Contribuinte Individual Trimestral',
    '1120': 'Contribuinte Individual - Complementação',
    '1163': 'Contribuinte Individual - Rural',
    '1406': 'Empregado Doméstico',
    '1457': 'Empregado Doméstico Trimestral',
    '1600': 'Empregador Doméstico',
    '1651': 'Empregador Doméstico - 13º Salário',
    '2909': 'Reclamatória Trabalhista',
}

CATEGORIAS_TRANSACAO = {
    'pix': ['PIX', 'TRANSF PIX'],
    'transferencia': ['TED', 'DOC', 'TRANSF'],
    'pagamento': ['PAG', 'PAGTO', 'PGTO'],
    'saque': ['SAQUE', 'SAQ'],
    'deposito': ['DEP', 'DEPOSITO'],
    'tarifa': ['TAR', 'TARIFA', 'ANUIDADE'],
    'salario': ['SALARIO', 'SAL', 'FOLHA'],
    'cartao': ['CARTAO', 'CARD'],
    'boleto': ['BOLETO', 'BOL'],
    'emprestimo': ['EMPREST', 'PARCELA'],
    'investimento': ['INVEST', 'APLIC', 'REND'],
    'imposto': ['DARF', 'GPS', 'DAS', 'FGTS', 'ISS', 'IPTU', 'IPVA'],
}


class ExtratorDocumentos:
    """Extrator universal de documentos financeiros brasileiros"""
    
    def __init__(self):
        self._easyocr_reader = None
        self._ofxparse = None
        self._pdfplumber = None
        
    def _get_ocr_reader(self):
        """Carrega EasyOCR sob demanda"""
        if self._easyocr_reader is None:
            try:
                import easyocr
                self._easyocr_reader = easyocr.Reader(['pt', 'en'], gpu=False)
            except ImportError:
                print("[EXTRATOR] EasyOCR não instalado")
        return self._easyocr_reader
    
    def _get_ofxparse(self):
        """Carrega ofxparse sob demanda"""
        if self._ofxparse is None:
            try:
                import ofxparse
                self._ofxparse = ofxparse
            except ImportError:
                print("[EXTRATOR] ofxparse não instalado")
        return self._ofxparse
    
    def _get_pdfplumber(self):
        """Carrega pdfplumber sob demanda"""
        if self._pdfplumber is None:
            try:
                import pdfplumber
                self._pdfplumber = pdfplumber
            except ImportError:
                print("[EXTRATOR] pdfplumber não instalado")
        return self._pdfplumber
    
    # ========== EXTRATO BANCÁRIO - OFX ==========
    
    def extrair_extrato_ofx(self, arquivo_path: str) -> Optional[ExtratoBancario]:
        """Extrai extrato de arquivo OFX (formato universal de bancos)"""
        ofxparse = self._get_ofxparse()
        if not ofxparse:
            return None
            
        try:
            with open(arquivo_path, 'rb') as f:
                ofx = ofxparse.OfxParser.parse(f)
            
            account = ofx.account
            statement = account.statement
            
            transacoes = []
            for trans in statement.transactions:
                transacoes.append(TransacaoExtrato(
                    data=trans.date.strftime('%d/%m/%Y') if trans.date else '',
                    descricao=trans.memo or trans.payee or '',
                    valor=float(trans.amount),
                    tipo='credito' if float(trans.amount) >= 0 else 'debito',
                    documento=trans.id,
                    categoria=self._categorizar_transacao(trans.memo or trans.payee or '')
                ))
            
            # Calcula totais
            total_creditos = sum(t.valor for t in transacoes if t.tipo == 'credito')
            total_debitos = sum(abs(t.valor) for t in transacoes if t.tipo == 'debito')
            
            # Identifica banco pelo routing number ou institution
            banco_codigo = account.routing_number or ''
            banco_nome = BANCOS_BRASIL.get(banco_codigo[:3], 'Banco não identificado')
            if hasattr(account, 'institution') and account.institution:
                banco_nome = account.institution.organization or banco_nome
            
            return ExtratoBancario(
                banco=banco_nome,
                agencia=account.branch_id or '',
                conta=account.account_id,
                titular='',  # OFX geralmente não tem nome do titular
                periodo_inicio=statement.start_date.strftime('%d/%m/%Y') if statement.start_date else '',
                periodo_fim=statement.end_date.strftime('%d/%m/%Y') if statement.end_date else '',
                saldo_inicial=float(statement.balance) - total_creditos + total_debitos,
                saldo_final=float(statement.balance),
                transacoes=transacoes,
                total_creditos=total_creditos,
                total_debitos=total_debitos
            )
            
        except Exception as e:
            print(f"[EXTRATOR OFX] Erro: {e}")
            return None
    
    # ========== EXTRATO BANCÁRIO - PDF ==========
    
    def extrair_extrato_pdf(self, arquivo_path: str) -> Optional[ExtratoBancario]:
        """Extrai extrato de PDF bancário"""
        pdfplumber = self._get_pdfplumber()
        if not pdfplumber:
            return None
            
        try:
            texto_completo = ""
            tabelas = []
            
            with pdfplumber.open(arquivo_path) as pdf:
                for page in pdf.pages:
                    texto_completo += page.extract_text() or ""
                    page_tables = page.extract_tables()
                    if page_tables:
                        tabelas.extend(page_tables)
            
            # Identifica banco
            banco = self._identificar_banco(texto_completo)
            
            # Extrai dados básicos
            agencia, conta = self._extrair_agencia_conta(texto_completo)
            titular = self._extrair_titular(texto_completo)
            periodo_inicio, periodo_fim = self._extrair_periodo(texto_completo)
            saldo_inicial, saldo_final = self._extrair_saldos(texto_completo)
            
            # Extrai transações
            transacoes = self._extrair_transacoes_pdf(tabelas, texto_completo)
            
            # Calcula totais
            total_creditos = sum(t.valor for t in transacoes if t.tipo == 'credito')
            total_debitos = sum(abs(t.valor) for t in transacoes if t.tipo == 'debito')
            
            return ExtratoBancario(
                banco=banco,
                agencia=agencia,
                conta=conta,
                titular=titular,
                periodo_inicio=periodo_inicio,
                periodo_fim=periodo_fim,
                saldo_inicial=saldo_inicial,
                saldo_final=saldo_final,
                transacoes=transacoes,
                total_creditos=total_creditos,
                total_debitos=total_debitos
            )
            
        except Exception as e:
            print(f"[EXTRATOR PDF] Erro: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _identificar_banco(self, texto: str) -> str:
        """Identifica banco pelo texto"""
        texto_upper = texto.upper()
        
        # Padrões específicos de cada banco
        padroes_bancos = {
            'BANCO DO BRASIL': ['BANCO DO BRASIL', 'BB S.A'],
            'Itaú': ['ITAÚ', 'ITAU UNIBANCO'],
            'Bradesco': ['BRADESCO', 'BRADESCARD'],
            'Santander': ['SANTANDER'],
            'Caixa Econômica Federal': ['CAIXA ECONOMICA', 'CAIXA FEDERAL', 'CEF'],
            'Nubank': ['NUBANK', 'NU PAGAMENTOS'],
            'Inter': ['BANCO INTER', 'INTER S.A'],
            'C6 Bank': ['C6 BANK', 'C6 S.A'],
            'Original': ['BANCO ORIGINAL'],
            'PagSeguro': ['PAGSEGURO', 'PAGBANK'],
            'Mercado Pago': ['MERCADO PAGO', 'MERCADOPAGO'],
            'Sicoob': ['SICOOB'],
            'Sicredi': ['SICREDI'],
            'Banrisul': ['BANRISUL'],
            'BRB': ['BRB', 'BANCO DE BRASÍLIA'],
        }
        
        for banco, padroes in padroes_bancos.items():
            for padrao in padroes:
                if padrao in texto_upper:
                    return banco
        
        return 'Banco não identificado'
    
    def _extrair_agencia_conta(self, texto: str) -> Tuple[str, str]:
        """Extrai agência e conta do texto"""
        # Padrões comuns
        padroes = [
            r'AG[ÊE]NCIA[:\s]*(\d{4}[-\s]?\d?)\s*(?:CONTA|C/C)[:\s]*(\d{5,12}[-\s]?\d?)',
            r'AG[:\s]*(\d{4})\s*C/C[:\s]*(\d{5,12})',
            r'AGÊNCIA[:\s]*(\d+)[^\d]*CONTA[:\s]*(\d+)',
        ]
        
        for padrao in padroes:
            match = re.search(padrao, texto, re.IGNORECASE)
            if match:
                return match.group(1).strip(), match.group(2).strip()
        
        return '', ''
    
    def _extrair_titular(self, texto: str) -> str:
        """Extrai nome do titular"""
        padroes = [
            r'CLIENTE[:\s]*([A-ZÁÉÍÓÚÂÊÎÔÛÃÕÇ\s]+)',
            r'TITULAR[:\s]*([A-ZÁÉÍÓÚÂÊÎÔÛÃÕÇ\s]+)',
            r'NOME[:\s]*([A-ZÁÉÍÓÚÂÊÎÔÛÃÕÇ\s]+)',
        ]
        
        for padrao in padroes:
            match = re.search(padrao, texto, re.IGNORECASE)
            if match:
                nome = match.group(1).strip()
                # Limita a 50 caracteres e remove linhas extras
                return nome.split('\n')[0][:50]
        
        return ''
    
    def _extrair_periodo(self, texto: str) -> Tuple[str, str]:
        """Extrai período do extrato"""
        padroes = [
            r'PER[ÍI]ODO[:\s]*(\d{2}/\d{2}/\d{4})\s*[aA]\s*(\d{2}/\d{2}/\d{4})',
            r'DE[:\s]*(\d{2}/\d{2}/\d{4})\s*AT[ÉE][:\s]*(\d{2}/\d{2}/\d{4})',
            r'(\d{2}/\d{2}/\d{4})\s*[-–]\s*(\d{2}/\d{2}/\d{4})',
        ]
        
        for padrao in padroes:
            match = re.search(padrao, texto, re.IGNORECASE)
            if match:
                return match.group(1), match.group(2)
        
        return '', ''
    
    def _extrair_saldos(self, texto: str) -> Tuple[float, float]:
        """Extrai saldo inicial e final"""
        saldo_inicial = 0.0
        saldo_final = 0.0
        
        # Saldo anterior/inicial
        match_ini = re.search(
            r'SALDO\s*(?:ANTERIOR|INICIAL)[:\s]*R?\$?\s*([\d.,]+)',
            texto, re.IGNORECASE
        )
        if match_ini:
            saldo_inicial = self._parse_valor(match_ini.group(1))
        
        # Saldo final/atual
        match_fim = re.search(
            r'SALDO\s*(?:FINAL|ATUAL|DISPONÍVEL)[:\s]*R?\$?\s*([\d.,]+)',
            texto, re.IGNORECASE
        )
        if match_fim:
            saldo_final = self._parse_valor(match_fim.group(1))
        
        return saldo_inicial, saldo_final
    
    def _extrair_transacoes_pdf(self, tabelas: List, texto: str) -> List[TransacaoExtrato]:
        """Extrai transações das tabelas do PDF"""
        transacoes = []
        
        for tabela in tabelas:
            if not tabela or len(tabela) < 2:
                continue
                
            # Tenta identificar colunas
            header = tabela[0] if tabela else []
            
            for linha in tabela[1:]:
                if not linha or len(linha) < 3:
                    continue
                
                try:
                    # Tenta extrair data, descrição e valor
                    data = None
                    descricao = None
                    valor = None
                    
                    for cell in linha:
                        if not cell:
                            continue
                        cell_str = str(cell).strip()
                        
                        # Detecta data
                        if re.match(r'\d{2}/\d{2}(/\d{2,4})?', cell_str) and not data:
                            data = cell_str
                        # Detecta valor
                        elif re.match(r'^-?[\d.,]+$', cell_str.replace(' ', '')) and not valor:
                            valor = self._parse_valor(cell_str)
                        # Detecta descrição
                        elif len(cell_str) > 3 and not descricao:
                            descricao = cell_str
                    
                    if data and descricao and valor is not None:
                        transacoes.append(TransacaoExtrato(
                            data=data,
                            descricao=descricao,
                            valor=abs(valor),
                            tipo='debito' if valor < 0 or 'D' in str(linha[-1] or '') else 'credito',
                            categoria=self._categorizar_transacao(descricao)
                        ))
                except Exception:
                    continue
        
        return transacoes
    
    def _categorizar_transacao(self, descricao: str) -> str:
        """Categoriza uma transação baseado na descrição"""
        desc_upper = descricao.upper()
        
        for categoria, palavras in CATEGORIAS_TRANSACAO.items():
            for palavra in palavras:
                if palavra in desc_upper:
                    return categoria
        
        return 'outros'
    
    # ========== GUIAS DE IMPOSTOS ==========
    
    def extrair_das(self, arquivo_path: str = None, imagem_bytes: bytes = None) -> Optional[GuiaDAS]:
        """Extrai dados de DAS (Documento de Arrecadação do Simples/MEI)"""
        texto = self._extrair_texto(arquivo_path, imagem_bytes)
        if not texto:
            return None
        
        texto_upper = texto.upper()
        
        # Verifica se é DAS
        if 'SIMPLES NACIONAL' not in texto_upper and 'DAS' not in texto_upper:
            return None
        
        try:
            # Período de apuração
            periodo = ''
            match = re.search(r'(?:PER[ÍI]ODO|COMPET[ÊE]NCIA|PA)[:\s]*(\d{2}/\d{4})', texto)
            if match:
                periodo = match.group(1)
            
            # CNPJ
            cnpj = ''
            match = re.search(r'CNPJ[:\s]*([\d./-]+)', texto)
            if match:
                cnpj = match.group(1)
            
            # Razão Social
            razao = ''
            match = re.search(r'(?:RAZ[ÃA]O\s*SOCIAL|NOME)[:\s]*([^\n]+)', texto, re.IGNORECASE)
            if match:
                razao = match.group(1).strip()
            
            # Valores
            valor_principal = 0.0
            match = re.search(r'(?:VALOR\s*PRINCIPAL|VALOR\s*ORIGINAL)[:\s]*R?\$?\s*([\d.,]+)', texto, re.IGNORECASE)
            if match:
                valor_principal = self._parse_valor(match.group(1))
            
            valor_total = 0.0
            match = re.search(r'(?:VALOR\s*TOTAL|TOTAL\s*A\s*RECOLHER)[:\s]*R?\$?\s*([\d.,]+)', texto, re.IGNORECASE)
            if match:
                valor_total = self._parse_valor(match.group(1))
            else:
                valor_total = valor_principal
            
            # Data de vencimento
            vencimento = ''
            match = re.search(r'(?:VENCIMENTO|DATA\s*VENC)[:\s]*(\d{2}/\d{2}/\d{4})', texto)
            if match:
                vencimento = match.group(1)
            
            # Código de barras e linha digitável
            codigo_barras, linha_digitavel = self._extrair_codigo_barras(texto)
            
            # Número do documento
            num_doc = ''
            match = re.search(r'(?:N[ÚU]MERO|DOC)[:\s]*(\d{10,20})', texto)
            if match:
                num_doc = match.group(1)
            
            # Receita bruta (se disponível)
            receita = None
            match = re.search(r'RECEITA\s*BRUTA[:\s]*R?\$?\s*([\d.,]+)', texto, re.IGNORECASE)
            if match:
                receita = self._parse_valor(match.group(1))
            
            return GuiaDAS(
                periodo_apuracao=periodo,
                cnpj=cnpj,
                razao_social=razao,
                valor_principal=valor_principal,
                valor_total=valor_total,
                data_vencimento=vencimento,
                codigo_barras=codigo_barras,
                linha_digitavel=linha_digitavel,
                numero_documento=num_doc,
                receita_bruta=receita
            )
            
        except Exception as e:
            print(f"[EXTRATOR DAS] Erro: {e}")
            return None
    
    def extrair_fgts(self, arquivo_path: str = None, imagem_bytes: bytes = None) -> Optional[GuiaFGTS]:
        """Extrai dados de guia FGTS (GRF/GRRF)"""
        texto = self._extrair_texto(arquivo_path, imagem_bytes)
        if not texto:
            return None
        
        texto_upper = texto.upper()
        
        # Verifica se é FGTS
        if 'FGTS' not in texto_upper and 'GRF' not in texto_upper:
            return None
        
        try:
            # Competência
            competencia = ''
            match = re.search(r'COMPET[ÊE]NCIA[:\s]*(\d{2}/\d{4})', texto)
            if match:
                competencia = match.group(1)
            
            # CNPJ
            cnpj = ''
            match = re.search(r'CNPJ[:\s]*([\d./-]+)', texto)
            if match:
                cnpj = match.group(1)
            
            # Razão Social
            razao = ''
            match = re.search(r'(?:RAZ[ÃA]O\s*SOCIAL|EMPREGADOR)[:\s]*([^\n]+)', texto, re.IGNORECASE)
            if match:
                razao = match.group(1).strip()
            
            # Código de recolhimento
            codigo_rec = ''
            match = re.search(r'C[ÓO]DIGO\s*(?:RECOLHIMENTO|REC)[:\s]*(\d+)', texto, re.IGNORECASE)
            if match:
                codigo_rec = match.group(1)
            
            # Valores
            valor_fgts = 0.0
            match = re.search(r'(?:VALOR\s*FGTS|DEP[ÓO]SITO)[:\s]*R?\$?\s*([\d.,]+)', texto, re.IGNORECASE)
            if match:
                valor_fgts = self._parse_valor(match.group(1))
            
            valor_total = 0.0
            match = re.search(r'(?:TOTAL\s*A\s*RECOLHER|VALOR\s*TOTAL)[:\s]*R?\$?\s*([\d.,]+)', texto, re.IGNORECASE)
            if match:
                valor_total = self._parse_valor(match.group(1))
            else:
                valor_total = valor_fgts
            
            # Data de vencimento
            vencimento = ''
            match = re.search(r'(?:VENCIMENTO|DATA\s*VENC)[:\s]*(\d{2}/\d{2}/\d{4})', texto)
            if match:
                vencimento = match.group(1)
            
            # Código de barras e linha digitável
            codigo_barras, linha_digitavel = self._extrair_codigo_barras(texto)
            
            # Número de funcionários
            num_func = None
            match = re.search(r'(?:FUNCION[ÁA]RIOS|EMPREGADOS)[:\s]*(\d+)', texto, re.IGNORECASE)
            if match:
                num_func = int(match.group(1))
            
            return GuiaFGTS(
                competencia=competencia,
                cnpj=cnpj,
                razao_social=razao,
                codigo_recolhimento=codigo_rec,
                valor_fgts=valor_fgts,
                valor_total=valor_total,
                data_vencimento=vencimento,
                codigo_barras=codigo_barras,
                linha_digitavel=linha_digitavel,
                numero_funcionarios=num_func
            )
            
        except Exception as e:
            print(f"[EXTRATOR FGTS] Erro: {e}")
            return None
    
    def extrair_gps(self, arquivo_path: str = None, imagem_bytes: bytes = None) -> Optional[GuiaINSS]:
        """Extrai dados de GPS (Guia da Previdência Social)"""
        texto = self._extrair_texto(arquivo_path, imagem_bytes)
        if not texto:
            return None
        
        texto_upper = texto.upper()
        
        # Verifica se é GPS/INSS
        if 'GPS' not in texto_upper and 'PREVIDÊNCIA' not in texto_upper and 'INSS' not in texto_upper:
            return None
        
        try:
            # Competência
            competencia = ''
            match = re.search(r'COMPET[ÊE]NCIA[:\s]*(\d{2}/\d{4})', texto)
            if match:
                competencia = match.group(1)
            
            # Identificador (CNPJ/CPF/CEI)
            identificador = ''
            tipo_id = 'empresa'
            
            match = re.search(r'CNPJ[:\s]*([\d./-]+)', texto)
            if match:
                identificador = match.group(1)
                tipo_id = 'empresa'
            else:
                match = re.search(r'CPF[:\s]*([\d./-]+)', texto)
                if match:
                    identificador = match.group(1)
                    tipo_id = 'contribuinte_individual'
                else:
                    match = re.search(r'CEI[:\s]*([\d./-]+)', texto)
                    if match:
                        identificador = match.group(1)
                        tipo_id = 'domestico'
            
            # Código de pagamento
            codigo_pag = ''
            match = re.search(r'C[ÓO]DIGO\s*(?:PAGAMENTO|PAG)[:\s]*(\d{4})', texto, re.IGNORECASE)
            if match:
                codigo_pag = match.group(1)
            
            # Valores
            valor_inss = 0.0
            match = re.search(r'(?:VALOR\s*INSS|CONTRIBUI[ÇC][ÃA]O)[:\s]*R?\$?\s*([\d.,]+)', texto, re.IGNORECASE)
            if match:
                valor_inss = self._parse_valor(match.group(1))
            
            valor_outras = 0.0
            match = re.search(r'OUTRAS\s*ENTIDADES[:\s]*R?\$?\s*([\d.,]+)', texto, re.IGNORECASE)
            if match:
                valor_outras = self._parse_valor(match.group(1))
            
            valor_atualizacao = 0.0
            match = re.search(r'(?:ATUALIZA[ÇC][ÃA]O|JUROS|MULTA)[:\s]*R?\$?\s*([\d.,]+)', texto, re.IGNORECASE)
            if match:
                valor_atualizacao = self._parse_valor(match.group(1))
            
            valor_total = 0.0
            match = re.search(r'(?:TOTAL\s*A\s*RECOLHER|VALOR\s*TOTAL)[:\s]*R?\$?\s*([\d.,]+)', texto, re.IGNORECASE)
            if match:
                valor_total = self._parse_valor(match.group(1))
            else:
                valor_total = valor_inss + valor_outras + valor_atualizacao
            
            # Data de vencimento
            vencimento = ''
            match = re.search(r'(?:VENCIMENTO|DATA\s*VENC)[:\s]*(\d{2}/\d{2}/\d{4})', texto)
            if match:
                vencimento = match.group(1)
            
            # Código de barras e linha digitável
            codigo_barras, linha_digitavel = self._extrair_codigo_barras(texto)
            
            return GuiaINSS(
                competencia=competencia,
                identificador=identificador,
                tipo_identificador=tipo_id,
                codigo_pagamento=codigo_pag,
                valor_inss=valor_inss,
                valor_outras_entidades=valor_outras,
                valor_atualizacao=valor_atualizacao,
                valor_total=valor_total,
                data_vencimento=vencimento,
                codigo_barras=codigo_barras,
                linha_digitavel=linha_digitavel
            )
            
        except Exception as e:
            print(f"[EXTRATOR GPS] Erro: {e}")
            return None
    
    def extrair_darf(self, arquivo_path: str = None, imagem_bytes: bytes = None) -> Optional[GuiaDARF]:
        """Extrai dados de DARF"""
        texto = self._extrair_texto(arquivo_path, imagem_bytes)
        if not texto:
            return None
        
        texto_upper = texto.upper()
        
        # Verifica se é DARF
        if 'DARF' not in texto_upper and 'RECEITA FEDERAL' not in texto_upper:
            return None
        
        try:
            # Período de apuração
            periodo = ''
            match = re.search(r'PER[ÍI]ODO\s*(?:DE\s*)?APURA[ÇC][ÃA]O[:\s]*(\d{2}/\d{2}/\d{4}|\d{2}/\d{4})', texto)
            if match:
                periodo = match.group(1)
            
            # CNPJ/CPF
            cnpj_cpf = ''
            match = re.search(r'(?:CNPJ|CPF)[:\s]*([\d./-]+)', texto)
            if match:
                cnpj_cpf = match.group(1)
            
            # Código da receita
            codigo_receita = ''
            match = re.search(r'C[ÓO]DIGO\s*(?:DA\s*)?RECEITA[:\s]*(\d{4})', texto, re.IGNORECASE)
            if match:
                codigo_receita = match.group(1)
            
            # Nome da receita
            nome_receita = CODIGOS_RECEITA_DARF.get(codigo_receita, '')
            
            # Valores
            valor_principal = 0.0
            match = re.search(r'(?:VALOR\s*PRINCIPAL|VALOR\s*ORIGINAL)[:\s]*R?\$?\s*([\d.,]+)', texto, re.IGNORECASE)
            if match:
                valor_principal = self._parse_valor(match.group(1))
            
            valor_multa = 0.0
            match = re.search(r'MULTA[:\s]*R?\$?\s*([\d.,]+)', texto, re.IGNORECASE)
            if match:
                valor_multa = self._parse_valor(match.group(1))
            
            valor_juros = 0.0
            match = re.search(r'JUROS[:\s]*R?\$?\s*([\d.,]+)', texto, re.IGNORECASE)
            if match:
                valor_juros = self._parse_valor(match.group(1))
            
            valor_total = 0.0
            match = re.search(r'(?:TOTAL\s*A\s*PAGAR|VALOR\s*TOTAL)[:\s]*R?\$?\s*([\d.,]+)', texto, re.IGNORECASE)
            if match:
                valor_total = self._parse_valor(match.group(1))
            else:
                valor_total = valor_principal + valor_multa + valor_juros
            
            # Data de vencimento
            vencimento = ''
            match = re.search(r'(?:VENCIMENTO|DATA\s*VENC)[:\s]*(\d{2}/\d{2}/\d{4})', texto)
            if match:
                vencimento = match.group(1)
            
            # Código de barras e linha digitável
            codigo_barras, linha_digitavel = self._extrair_codigo_barras(texto)
            
            # Número de referência
            num_ref = None
            match = re.search(r'REFER[ÊE]NCIA[:\s]*(\d+)', texto, re.IGNORECASE)
            if match:
                num_ref = match.group(1)
            
            return GuiaDARF(
                periodo_apuracao=periodo,
                cnpj_cpf=cnpj_cpf,
                codigo_receita=codigo_receita,
                nome_receita=nome_receita,
                valor_principal=valor_principal,
                valor_multa=valor_multa,
                valor_juros=valor_juros,
                valor_total=valor_total,
                data_vencimento=vencimento,
                codigo_barras=codigo_barras,
                linha_digitavel=linha_digitavel,
                numero_referencia=num_ref
            )
            
        except Exception as e:
            print(f"[EXTRATOR DARF] Erro: {e}")
            return None
    
    # ========== COMPROVANTE DE BOLETO PAGO ==========
    
    def extrair_comprovante_boleto(self, arquivo_path: str = None, imagem_bytes: bytes = None) -> Optional[ComprovanteBoletoPago]:
        """Extrai dados de comprovante de pagamento de boleto"""
        texto = self._extrair_texto(arquivo_path, imagem_bytes)
        if not texto:
            return None
        
        texto_upper = texto.upper()
        
        # Verifica se é comprovante de pagamento
        if not any(kw in texto_upper for kw in ['COMPROVANTE', 'PAGAMENTO', 'BOLETO', 'QUITAÇÃO']):
            return None
        
        try:
            # Banco pagador
            banco_pagador = self._identificar_banco(texto)
            
            # Agência e conta
            agencia, conta = self._extrair_agencia_conta(texto)
            agencia_conta = f"{agencia}/{conta}" if agencia and conta else ""
            
            # Data de pagamento
            data_pag = ''
            match = re.search(r'(?:DATA\s*(?:DO\s*)?PAGAMENTO|PAGO\s*EM)[:\s]*(\d{2}/\d{2}/\d{4})', texto, re.IGNORECASE)
            if match:
                data_pag = match.group(1)
            
            # Valor pago
            valor_pago = 0.0
            match = re.search(r'(?:VALOR\s*PAGO|TOTAL\s*PAGO|VALOR\s*DEBITADO)[:\s]*R?\$?\s*([\d.,]+)', texto, re.IGNORECASE)
            if match:
                valor_pago = self._parse_valor(match.group(1))
            
            # Valor documento
            valor_doc = 0.0
            match = re.search(r'(?:VALOR\s*(?:DO\s*)?(?:DOCUMENTO|NOMINAL))[:\s]*R?\$?\s*([\d.,]+)', texto, re.IGNORECASE)
            if match:
                valor_doc = self._parse_valor(match.group(1))
            
            # Desconto
            desconto = 0.0
            match = re.search(r'DESCONTO[:\s]*R?\$?\s*([\d.,]+)', texto, re.IGNORECASE)
            if match:
                desconto = self._parse_valor(match.group(1))
            
            # Juros
            juros = 0.0
            match = re.search(r'JUROS[:\s]*R?\$?\s*([\d.,]+)', texto, re.IGNORECASE)
            if match:
                juros = self._parse_valor(match.group(1))
            
            # Multa
            multa = 0.0
            match = re.search(r'MULTA[:\s]*R?\$?\s*([\d.,]+)', texto, re.IGNORECASE)
            if match:
                multa = self._parse_valor(match.group(1))
            
            # Beneficiário
            beneficiario = ''
            match = re.search(r'(?:BENEFICI[ÁA]RIO|FAVORECIDO|CEDENTE)[:\s]*([^\n]+)', texto, re.IGNORECASE)
            if match:
                beneficiario = match.group(1).strip()[:60]
            
            # Doc beneficiário
            benef_doc = ''
            match = re.search(r'(?:CNPJ|CPF)\s*(?:BENEFICI[ÁA]RIO|FAVORECIDO)?[:\s]*([\d./-]+)', texto, re.IGNORECASE)
            if match:
                benef_doc = match.group(1)
            
            # Linha digitável
            _, linha_digitavel = self._extrair_codigo_barras(texto)
            
            # Autenticação
            autenticacao = ''
            match = re.search(r'AUTENTICA[ÇC][ÃA]O[:\s]*([A-Z0-9\-]+)', texto, re.IGNORECASE)
            if match:
                autenticacao = match.group(1)
            
            # Forma de pagamento
            forma_pag = 'internet_banking'
            if 'APP' in texto_upper or 'APLICATIVO' in texto_upper:
                forma_pag = 'app'
            elif 'CAIXA' in texto_upper and 'ELETRÔNICO' in texto_upper:
                forma_pag = 'caixa_eletronico'
            elif 'AGÊNCIA' in texto_upper or 'AGENCIA' in texto_upper:
                forma_pag = 'agencia'
            
            return ComprovanteBoletoPago(
                banco_pagador=banco_pagador,
                agencia_conta=agencia_conta,
                data_pagamento=data_pag,
                valor_pago=valor_pago,
                valor_documento=valor_doc,
                desconto=desconto,
                juros=juros,
                multa=multa,
                beneficiario=beneficiario,
                beneficiario_doc=benef_doc,
                linha_digitavel=linha_digitavel,
                autenticacao=autenticacao,
                forma_pagamento=forma_pag
            )
            
        except Exception as e:
            print(f"[EXTRATOR COMPROVANTE] Erro: {e}")
            return None
    
    # ========== DETECÇÃO AUTOMÁTICA ==========
    
    def extrair_automatico(self, arquivo_path: str = None, imagem_bytes: bytes = None) -> Dict:
        """Detecta automaticamente o tipo de documento e extrai os dados"""
        texto = self._extrair_texto(arquivo_path, imagem_bytes)
        if not texto:
            return {'tipo': 'desconhecido', 'erro': 'Não foi possível extrair texto'}
        
        texto_upper = texto.upper()
        
        resultado = {
            'tipo': 'desconhecido',
            'dados': None,
            'confianca': 0.0
        }
        
        # Tenta identificar tipo
        # Extrato bancário
        if arquivo_path and arquivo_path.lower().endswith('.ofx'):
            extrato = self.extrair_extrato_ofx(arquivo_path)
            if extrato:
                return {'tipo': 'extrato_bancario', 'dados': asdict(extrato), 'confianca': 0.95}
        
        # DAS/MEI
        if 'SIMPLES NACIONAL' in texto_upper or 'DAS' in texto_upper:
            das = self.extrair_das(arquivo_path, imagem_bytes)
            if das:
                return {'tipo': 'das', 'dados': asdict(das), 'confianca': 0.9}
        
        # FGTS
        if 'FGTS' in texto_upper or 'GRF' in texto_upper:
            fgts = self.extrair_fgts(arquivo_path, imagem_bytes)
            if fgts:
                return {'tipo': 'fgts', 'dados': asdict(fgts), 'confianca': 0.9}
        
        # GPS/INSS
        if 'GPS' in texto_upper or 'PREVIDÊNCIA' in texto_upper or 'INSS' in texto_upper:
            gps = self.extrair_gps(arquivo_path, imagem_bytes)
            if gps:
                return {'tipo': 'gps', 'dados': asdict(gps), 'confianca': 0.9}
        
        # DARF
        if 'DARF' in texto_upper or ('RECEITA FEDERAL' in texto_upper and 'CÓDIGO' in texto_upper):
            darf = self.extrair_darf(arquivo_path, imagem_bytes)
            if darf:
                return {'tipo': 'darf', 'dados': asdict(darf), 'confianca': 0.9}
        
        # Comprovante de boleto
        if 'COMPROVANTE' in texto_upper and 'PAGAMENTO' in texto_upper:
            comp = self.extrair_comprovante_boleto(arquivo_path, imagem_bytes)
            if comp:
                return {'tipo': 'comprovante_boleto', 'dados': asdict(comp), 'confianca': 0.85}
        
        # Extrato PDF
        if 'EXTRATO' in texto_upper or ('SALDO' in texto_upper and 'TRANSAÇÃO' in texto_upper):
            if arquivo_path and arquivo_path.lower().endswith('.pdf'):
                extrato = self.extrair_extrato_pdf(arquivo_path)
                if extrato:
                    return {'tipo': 'extrato_bancario', 'dados': asdict(extrato), 'confianca': 0.8}
        
        return resultado
    
    # ========== MÉTODOS AUXILIARES ==========
    
    def _extrair_texto(self, arquivo_path: str = None, imagem_bytes: bytes = None) -> str:
        """Extrai texto de arquivo ou imagem"""
        texto = ""
        
        if arquivo_path:
            # PDF
            if arquivo_path.lower().endswith('.pdf'):
                pdfplumber = self._get_pdfplumber()
                if pdfplumber:
                    try:
                        with pdfplumber.open(arquivo_path) as pdf:
                            for page in pdf.pages:
                                texto += page.extract_text() or ""
                    except:
                        pass
            # Imagem
            elif arquivo_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
                reader = self._get_ocr_reader()
                if reader:
                    try:
                        result = reader.readtext(arquivo_path)
                        texto = ' '.join([r[1] for r in result])
                    except:
                        pass
        
        elif imagem_bytes:
            reader = self._get_ocr_reader()
            if reader:
                try:
                    import numpy as np
                    from PIL import Image
                    
                    image = Image.open(io.BytesIO(imagem_bytes))
                    image_np = np.array(image)
                    result = reader.readtext(image_np)
                    texto = ' '.join([r[1] for r in result])
                except Exception as e:
                    print(f"[OCR] Erro: {e}")
        
        return texto
    
    def _extrair_codigo_barras(self, texto: str) -> Tuple[str, str]:
        """Extrai código de barras e linha digitável do texto"""
        codigo_barras = ''
        linha_digitavel = ''
        
        # Linha digitável (47 ou 48 dígitos com pontos/espaços)
        match = re.search(r'(\d{5}[.\s]?\d{5}[.\s]?\d{5}[.\s]?\d{6}[.\s]?\d{5}[.\s]?\d{6}[.\s]?\d[.\s]?\d{14})', texto.replace(' ', ''))
        if match:
            linha_digitavel = match.group(1).replace('.', '').replace(' ', '')
        else:
            # Formato alternativo
            match = re.search(r'(\d{47,48})', texto.replace(' ', '').replace('.', ''))
            if match:
                linha_digitavel = match.group(1)
        
        # Código de barras (44 dígitos)
        match = re.search(r'(\d{44})', texto.replace(' ', ''))
        if match:
            codigo_barras = match.group(1)
        
        return codigo_barras, linha_digitavel
    
    def _parse_valor(self, valor_str: str) -> float:
        """Converte string de valor para float"""
        try:
            # Remove espaços e caracteres não numéricos exceto vírgula e ponto
            valor_str = valor_str.strip()
            valor_str = re.sub(r'[^\d.,\-]', '', valor_str)
            
            # Detecta formato brasileiro (1.234,56) ou americano (1,234.56)
            if ',' in valor_str and '.' in valor_str:
                if valor_str.rfind(',') > valor_str.rfind('.'):
                    # Formato brasileiro: 1.234,56
                    valor_str = valor_str.replace('.', '').replace(',', '.')
                else:
                    # Formato americano: 1,234.56
                    valor_str = valor_str.replace(',', '')
            elif ',' in valor_str:
                # Assume brasileiro: 1234,56
                valor_str = valor_str.replace(',', '.')
            
            return float(valor_str)
        except:
            return 0.0


# ========== INSTÂNCIA GLOBAL ==========
extrator_documentos = ExtratorDocumentos()
