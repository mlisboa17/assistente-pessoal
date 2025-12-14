"""
📊 Módulo Importador de Extratos Bancários e de Cartão de Crédito
Importa e processa extratos de bancos e cartões de crédito
Suporta: CSV, PDF (com OCR), OFX e padrões comuns de bancos brasileiros
"""
import json
import os
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from abc import ABC, abstractmethod
import csv
from io import StringIO
import xml.etree.ElementTree as ET

# Para extração de PDF
PDFPLUMBER_AVAILABLE = False
try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    pass


class TipoExtrato(Enum):
    """Tipos de extrato suportados"""
    BANCO_ITAU = "itau"
    BANCO_BRADESCO = "bradesco"
    BANCO_SANTANDER = "santander"
    BANCO_CAIXA = "caixa"
    BANCO_BB = "banco_brasil"
    BANCO_NUBANK = "nubank"
    CARTAO_CREDITO = "cartao_credito"
    CARTAO_DEBITO = "cartao_debito"
    CSV_GENERICO = "csv_generico"
    OFX = "ofx"
    DESCONHECIDO = "desconhecido"


class StatusImportacao(Enum):
    """Status da importação"""
    SUCESSO = "sucesso"
    ERRO = "erro"
    PARCIAL = "parcial"
    PENDENTE_CONFIRMACAO = "pendente_confirmacao"


@dataclass
class Movimento:
    """Representa um movimento financeiro"""
    data: str  # YYYY-MM-DD
    descricao: str
    tipo: str  # "entrada" ou "saida"
    valor: float
    saldo: Optional[float] = None
    numero_documento: Optional[str] = None
    agencia: Optional[str] = None
    conta: Optional[str] = None
    banco: Optional[str] = None
    categoria_sugerida: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            'data': self.data,
            'descricao': self.descricao,
            'tipo': self.tipo,
            'valor': self.valor,
            'saldo': self.saldo,
            'numero_documento': self.numero_documento,
            'agencia': self.agencia,
            'conta': self.conta,
            'banco': self.banco,
            'categoria_sugerida': self.categoria_sugerida
        }


class ParseadorExtrato(ABC):
    """Classe base para parsers de extrato"""
    
    def __init__(self, tipo: TipoExtrato):
        self.tipo = tipo
        self.movimentos: List[Movimento] = []
        self.metadata: Dict = {}
    
    @abstractmethod
    def parse(self, conteudo: str) -> Tuple[List[Movimento], Dict]:
        """
        Parseia o conteúdo do extrato
        
        Returns:
            (lista_movimentos, metadata)
        """
        pass
    
    def _gerar_metadata(self, movimentos: List[Movimento]) -> Dict:
        """Gera metadados da importação"""
        if not movimentos:
            return {
                'total_movimentos': 0,
                'total_entradas': 0,
                'total_saidas': 0,
                'periodo_inicio': '',
                'periodo_fim': '',
            }
        
        return {
            'total_movimentos': len(movimentos),
            'total_entradas': sum(m.valor for m in movimentos if m.tipo == 'entrada'),
            'total_saidas': sum(m.valor for m in movimentos if m.tipo == 'saida'),
            'periodo_inicio': min((m.data for m in movimentos), default=''),
            'periodo_fim': max((m.data for m in movimentos), default=''),
        }
    
    def _extrair_valor(self, texto: str) -> float:
        """Extrai valor numérico do texto"""
        if not texto or not texto.strip():
            return 0.0
            
        texto = texto.strip()
        
        # Remove símbolos de moeda e espaços
        texto = re.sub(r'[R$\s]', '', texto)
        
        # Tenta formato brasileiro (1.234,56)
        if ',' in texto and '.' in texto:
            # Se tem ambos, assume formato brasileiro
            texto = texto.replace('.', '').replace(',', '.')
        elif ',' in texto:
            # Só vírgula, assume formato brasileiro
            texto = texto.replace(',', '.')
        # Se só ponto ou nenhum, assume formato americano (já está correto)
        
        # Extrai número
        match = re.search(r'-?\d+\.?\d*', texto)
        if match:
            try:
                return float(match.group())
            except ValueError:
                pass
        
        return 0.0
    
    def _parse_data(self, data_str: str) -> str:
        """Converte string de data para formato YYYY-MM-DD"""
        formatos = [
            '%d/%m/%Y', '%d/%m/%y', '%d-%m-%Y', '%d-%m-%y',
            '%Y-%m-%d', '%Y/%m/%d', '%d.%m.%Y', '%d.%m.%y'
        ]
        
        for fmt in formatos:
            try:
                data_obj = datetime.strptime(data_str.strip(), fmt)
                return data_obj.strftime('%Y-%m-%d')
            except:
                continue
        
        return datetime.now().strftime('%Y-%m-%d')
    
    def _detectar_tipo_movimento(self, descricao: str) -> str:
        """Detecta se é entrada ou saída"""
        palavras_saida = [
            'débito', 'debit', 'pagamento', 'transferência enviada',
            'compra', 'saque', 'retirada', 'tarifa', 'taxa', 'juros'
        ]
        
        descricao_lower = descricao.lower()
        
        for palavra in palavras_saida:
            if palavra in descricao_lower:
                return 'saida'
        
        return 'entrada'


class ParseadorCSVGenerico(ParseadorExtrato):
    """Parser para CSV genérico"""
    
    def __init__(self):
        super().__init__(TipoExtrato.CSV_GENERICO)
    
    def parse(self, conteudo: str) -> Tuple[List[Movimento], Dict]:
        """
        Parse CSV esperando colunas: Data, Descrição, Valor, Saldo (opcional)
        """
        movimentos = []
        
        try:
            # Tenta detectar delimitador
            delimitador = self._detectar_delimitador(conteudo)
            reader = csv.DictReader(StringIO(conteudo), delimiter=delimitador)
            
            if not reader.fieldnames:
                return [], {"erro": "CSV vazio ou inválido"}
            
            # Tenta mapear colunas automaticamente
            cols = self._mapear_colunas(reader.fieldnames)
            
            for linha in reader:
                try:
                    data = self._parse_data(linha.get(cols['data'], ''))
                    descricao = linha.get(cols['descricao'], 'Descrição não identificada')
                    valor_str = linha.get(cols['valor'], '0')
                    valor = self._extrair_valor(valor_str)
                    
                    if valor == 0:
                        continue
                    
                    # Determina tipo: primeiro da coluna Tipo, senão detecta pela descrição
                    tipo_coluna = linha.get(cols['tipo'], '').strip().lower() if cols['tipo'] else ''
                    if tipo_coluna in ['saida', 'débito', 'debito', 'saída', 'expense', 'out']:
                        tipo = 'saida'
                    elif tipo_coluna in ['entrada', 'crédito', 'credito', 'income', 'in']:
                        tipo = 'entrada'
                    else:
                        tipo = self._detectar_tipo_movimento(descricao)
                    
                    saldo = None
                    if cols['saldo']:
                        saldo_str = linha.get(cols['saldo'], '')
                        saldo = self._extrair_valor(saldo_str) if saldo_str else None
                    
                    movimento = Movimento(
                        data=data,
                        descricao=descricao.strip(),
                        tipo=tipo,
                        valor=valor,
                        saldo=saldo,
                        categoria_sugerida=self._sugerir_categoria(descricao)
                    )
                    movimentos.append(movimento)
                except Exception as e:
                    continue
            
            metadata = {
                'total_movimentos': len(movimentos),
                'total_entradas': sum(m.valor for m in movimentos if m.tipo == 'entrada'),
                'total_saidas': sum(m.valor for m in movimentos if m.tipo == 'saida'),
                'periodo_inicio': min((m.data for m in movimentos), default=''),
                'periodo_fim': max((m.data for m in movimentos), default=''),
            }
            
            return movimentos, metadata
        
        except Exception as e:
            return [], {"erro": f"Erro ao processar CSV: {str(e)}"}
    
    def _detectar_delimitador(self, conteudo: str) -> str:
        """Detecta delimitador do CSV"""
        delimitadores = [',', ';', '\t', '|']
        primeira_linha = conteudo.split('\n')[0]
        
        for delim in delimitadores:
            if delim in primeira_linha:
                return delim
        
        return ','
    
    def _mapear_colunas(self, fieldnames: List[str]) -> Dict[str, Optional[str]]:
        """Mapeia colunas encontradas para colunas esperadas"""
        fieldnames_lower = [f.lower().strip() for f in fieldnames]
        
        mapa = {
            'data': None,
            'descricao': None,
            'valor': None,
            'saldo': None,
            'tipo': None
        }
        
        # Busca data
        para_data = ['data', 'date', 'data_movimento', 'dia', 'data_transacao', 'data_operacao']
        for col in fieldnames_lower:
            if any(p in col for p in para_data):
                mapa['data'] = fieldnames[fieldnames_lower.index(col)]
                break
        
        # Busca descrição
        para_desc = ['descricao', 'description', 'operacao', 'historico', 'descricao_movimentacao']
        for col in fieldnames_lower:
            if any(p in col for p in para_desc):
                mapa['descricao'] = fieldnames[fieldnames_lower.index(col)]
                break
        
        # Busca valor
        para_valor = ['valor', 'value', 'amount', 'montante', 'valor_movimento']
        for col in fieldnames_lower:
            if any(p in col for p in para_valor):
                mapa['valor'] = fieldnames[fieldnames_lower.index(col)]
                break
        
        # Busca saldo
        para_saldo = ['saldo', 'balance', 'saldo_anterior', 'saldo_posterior']
        for col in fieldnames_lower:
            if any(p in col for p in para_saldo):
                mapa['saldo'] = fieldnames[fieldnames_lower.index(col)]
                break
        
        # Busca tipo
        para_tipo = ['tipo', 'type', 'operacao_tipo', 'tipo_movimento']
        for col in fieldnames_lower:
            if any(p in col for p in para_tipo):
                mapa['tipo'] = fieldnames[fieldnames_lower.index(col)]
                break
        
        # Se não encontrou, usa posição
        if not mapa['data']:
            mapa['data'] = fieldnames[0] if fieldnames else 'data'
        if not mapa['descricao']:
            mapa['descricao'] = fieldnames[1] if len(fieldnames) > 1 else 'descricao'
        if not mapa['valor']:
            mapa['valor'] = fieldnames[2] if len(fieldnames) > 2 else 'valor'
        
        return mapa
    
    def _sugerir_categoria(self, descricao: str) -> str:
        """Sugere categoria baseado na descrição, usando aprendizado primeiro"""
        # Primeiro tenta o sistema de aprendizado
        try:
            from modules.sistema_aprendizado import sistema_aprendizado
            aprendizado = sistema_aprendizado.sugerir_categoria_aprendida(descricao)
            if aprendizado and aprendizado['confianca'] > 0.7:  # Confiança alta
                return aprendizado['categoria']
        except ImportError:
            pass
        
        # Fallback para regras fixas
        descricao_lower = descricao.lower()
        
        categorias = {
            'alimentacao': ['mercado', 'supermercado', 'restaurante', 'padaria', 'lanchon', 'pizza'],
            'combustivel': ['gasolina', 'combustivel', 'posto', 'abastec'],
            'transporte': ['uber', 'taxi', 'onibus', 'metro', 'estacionamento'],
            'moradia': ['aluguel', 'condominio', 'agua', 'luz', 'energia', 'gas', 'internet'],
            'saude': ['farmacia', 'medicamento', 'medico', 'hospital', 'clinica'],
            'lazer': ['cinema', 'show', 'netflix', 'streaming', 'spotify'],
            'tecnologia': ['celular', 'notebook', 'computador', 'apple', 'samsung'],
            'educacao': ['curso', 'escola', 'universidade', 'livro', 'udemy'],
        }
        
        for categoria, palavras in categorias.items():
            for palavra in palavras:
                if palavra in descricao_lower:
                    return categoria
        
        return 'outros'


class ParseadorITAU(ParseadorExtrato):
    """Parser para extrato Itaú"""
    
    def __init__(self):
        super().__init__(TipoExtrato.BANCO_ITAU)
    
    def parse(self, conteudo: str) -> Tuple[List[Movimento], Dict]:
        """Parse específico para formato Itaú"""
        movimentos = []
        
        # Padrão típico Itaú:
        # DATA       HISTÓRICO                    DÉBITO        CRÉDITO       SALDO
        # 01/12/2024 SAQUE BANCO 24H           1.500,00                      5.234,56
        
        linhas = conteudo.strip().split('\n')
        
        # Extrai informações do banco
        for linha in linhas[:10]:
            if 'ITAU' in linha.upper() or 'AG' in linha.upper():
                match = re.search(r'AG[.\s]*(\d+)', linha)
                if match:
                    self.metadata['agencia'] = match.group(1)
        
        # Processa linhas de movimento
        for linha in linhas:
            # Padrão: DD/MM/YYYY TEXTO VALOR VALOR VALOR
            match = re.match(
                r'(\d{2}/\d{2}/\d{4})\s+(.+?)\s+(\d{1,3}[.,]\d{3}[.,]\d{2})?'
                r'\s+(\d{1,3}[.,]\d{3}[.,]\d{2})?\s+(\d{1,3}[.,]\d{3}[.,]\d{2})?',
                linha.strip()
            )
            
            if match:
                try:
                    data = self._parse_data(match.group(1))
                    historico = match.group(2).strip()
                    debito = match.group(3)
                    credito = match.group(4)
                    saldo = match.group(5)
                    
                    if debito and self._extrair_valor(debito) > 0:
                        valor = self._extrair_valor(debito)
                        tipo = 'saida'
                    elif credito and self._extrair_valor(credito) > 0:
                        valor = self._extrair_valor(credito)
                        tipo = 'entrada'
                    else:
                        continue
                    
                    movimento = Movimento(
                        data=data,
                        descricao=historico,
                        tipo=tipo,
                        valor=valor,
                        saldo=self._extrair_valor(saldo) if saldo else None,
                        banco='Itaú',
                        categoria_sugerida=self._sugerir_categoria_itau(historico)
                    )
                    movimentos.append(movimento)
                except:
                    continue
        
        metadata = self._gerar_metadata(movimentos)
        return movimentos, metadata
    
    def _sugerir_categoria_itau(self, historico: str) -> str:
        """Sugere categoria específica para Itaú"""
        parsador_generico = ParseadorCSVGenerico()
        return parsador_generico._sugerir_categoria(historico)


class ParseadorCartaoCredito(ParseadorExtrato):
    """Parser para extrato de cartão de crédito"""
    
    def __init__(self):
        super().__init__(TipoExtrato.CARTAO_CREDITO)
    
    def parse(self, conteudo: str) -> Tuple[List[Movimento], Dict]:
        """Parse para cartão de crédito"""
        movimentos = []
        
        # Padrão típico:
        # DATA       ESTABELECIMENTO           CATEGORIA      VALOR
        # 01/12/2024 MERCADO XYZ               SUPERMERCADO   234,56
        
        linhas = conteudo.strip().split('\n')
        
        # Extrai dados do cartão (primeiras linhas costumam ter info)
        for linha in linhas[:5]:
            if 'CARTÃO' in linha.upper() or 'CARD' in linha.upper():
                # Extrai número do cartão (últimos 4 dígitos)
                match = re.search(r'\d{4}', linha)
                if match:
                    self.metadata['numero_cartao_ultimos'] = match.group()
        
        # Processa transações
        padrao = re.compile(
            r'(\d{2}/\d{2}/\d{4})\s+(.+?)\s+(\d{1,3}[.,]\d{3}[.,]\d{2})',
            re.UNICODE
        )
        
        for linha in linhas:
            match = padrao.search(linha)
            if match:
                try:
                    data = self._parse_data(match.group(1))
                    descricao = match.group(2).strip()
                    valor = self._extrair_valor(match.group(3))
                    
                    if valor <= 0:
                        continue
                    
                    movimento = Movimento(
                        data=data,
                        descricao=descricao,
                        tipo='saida',  # Cartão de crédito são sempre saídas (no futuro)
                        valor=valor,
                        categoria_sugerida=self._sugerir_categoria_cartao(descricao)
                    )
                    movimentos.append(movimento)
                except:
                    continue
        
        metadata = self._gerar_metadata(movimentos)
        metadata['tipo_cartao'] = 'credito'
        return movimentos, metadata
    
    def _sugerir_categoria_cartao(self, estabelecimento: str) -> str:
        """Sugere categoria para transação de cartão"""
        est_lower = estabelecimento.lower()
        
        categorias = {
            'alimentacao': ['mercado', 'supermercado', 'restaurante', 'pizzaria', 'cafe', 'lanchon'],
            'combustivel': ['posto', 'gasolina', 'combustivel'],
            'transporte': ['uber', 'taxi', 'estacionamento', 'onibus'],
            'saude': ['farmacia', 'drogaria', 'medico', 'hospital'],
            'lazer': ['cinema', 'show', 'bar', 'restaurante'],
            'tecnologia': ['apple', 'samsung', 'amazon', 'playstation', 'xbox'],
            'educacao': ['livraria', 'curso', 'escola'],
            'beleza': ['salao', 'estetica', 'manicure', 'pedicure'],
            'vestuario': ['loja', 'shopping', 'renner', 'cea', 'marisa'],
        }
        
        for categoria, palavras in categorias.items():
            for palavra in palavras:
                if palavra in est_lower:
                    return categoria
        
        return 'outros'


class ParseadorOFX(ParseadorExtrato):
    """Parser para arquivos OFX (Open Financial Exchange)"""
    
    def __init__(self):
        super().__init__(TipoExtrato.OFX)
    
    def parse(self, conteudo: str) -> Tuple[List[Movimento], Dict]:
        """Parse para arquivo OFX"""
        movimentos = []
        
        try:
            # OFX é baseado em XML, mas pode ter cabeçalho SGML
            # Remove cabeçalho SGML se existir
            if conteudo.startswith('OFXHEADER'):
                # Encontra o início do XML
                xml_start = conteudo.find('<OFX>')
                if xml_start == -1:
                    xml_start = conteudo.find('<BANKMSGSRSV1>')
                if xml_start == -1:
                    xml_start = conteudo.find('<CREDITCARDMSGSRSV1>')
                
                if xml_start != -1:
                    conteudo = conteudo[xml_start:]
            
            # Parse XML
            root = ET.fromstring(conteudo)
            
            # Procura por transações bancárias
            for stmttrn in root.iter('STMTTRN'):
                movimento = self._parse_transacao(stmttrn)
                if movimento:
                    movimentos.append(movimento)
            
            # Procura por transações de cartão de crédito
            for ccstmttrn in root.iter('CCSTMTTRN'):
                movimento = self._parse_transacao_cartao(ccstmttrn)
                if movimento:
                    movimentos.append(movimento)
            
        except ET.ParseError as e:
            print(f"Erro ao parsear OFX: {e}")
            return [], {'erro': f'Erro de parsing XML: {e}'}
        except Exception as e:
            print(f"Erro geral no OFX: {e}")
            return [], {'erro': f'Erro geral: {e}'}
        
        metadata = self._gerar_metadata(movimentos)
        metadata['formato'] = 'OFX'
        return movimentos, metadata
    
    def _parse_transacao(self, stmttrn) -> Optional[Movimento]:
        """Parse uma transação bancária"""
        try:
            # Data da transação
            dtposted = stmttrn.find('DTPOSTED')
            if dtposted is None:
                return None
            
            data_str = dtposted.text[:8]  # YYYYMMDD
            data = f"{data_str[:4]}-{data_str[4:6]}-{data_str[6:8]}"
            
            # Valor
            trnamt = stmttrn.find('TRNAMT')
            if trnamt is None:
                return None
            
            valor = float(trnamt.text)
            tipo = 'entrada' if valor > 0 else 'saida'
            valor = abs(valor)
            
            # Descrição
            memo = stmttrn.find('MEMO')
            name = stmttrn.find('NAME')
            descricao = ""
            if memo is not None and memo.text:
                descricao = memo.text.strip()
            elif name is not None and name.text:
                descricao = name.text.strip()
            else:
                descricao = "Transação sem descrição"
            
            # Tipo de transação
            trntype = stmttrn.find('TRNTYPE')
            if trntype is not None:
                tipo_ofx = trntype.text.upper()
                if tipo_ofx in ['DEBIT', 'PAYMENT']:
                    tipo = 'saida'
                elif tipo_ofx in ['CREDIT', 'DEP', 'INT']:
                    tipo = 'entrada'
            
            return Movimento(
                data=data,
                descricao=descricao,
                tipo=tipo,
                valor=valor
            )
            
        except (ValueError, AttributeError) as e:
            print(f"Erro ao parsear transação: {e}")
            return None
    
    def _parse_transacao_cartao(self, ccstmttrn) -> Optional[Movimento]:
        """Parse uma transação de cartão de crédito"""
        # Similar à transação bancária, mas sempre saída
        movimento = self._parse_transacao(ccstmttrn)
        if movimento:
            movimento.tipo = 'saida'  # Cartão de crédito sempre saída
        return movimento


class ParseadorNubank(ParseadorExtrato):
    """Parser para extrato do Nubank"""
    
    def __init__(self):
        super().__init__(TipoExtrato.BANCO_NUBANK)
    
    def parse(self, conteudo: str) -> Tuple[List[Movimento], Dict]:
        """Parse para extrato Nubank"""
        movimentos = []
        
        # Divide por meses (Outubro 2025, Novembro 2025, etc.)
        meses = re.split(r'([A-Z][a-z]+ \d{4})', conteudo)
        
        for i in range(1, len(meses), 2):
            mes_ano = meses[i]
            texto_mes = meses[i+1] if i+1 < len(meses) else ""
            
            # Extrai ano do mês
            match_ano = re.search(r'\d{4}', mes_ano)
            ano = match_ano.group() if match_ano else str(datetime.now().year)
            
            # Procura por linhas de transação
            linhas = texto_mes.split('\n')
            for linha in linhas:
                linha = linha.strip()
                if not linha:
                    continue
                
                # Padrão: DD/MM DD/MM Tipo Descrição -R$ XXX,XX
                # Ou: DD/MM DD/MM Entrada/Saída Descrição R$ XXX,XX
                padrao = re.compile(
                    r'(\d{2}/\d{2})\s+(\d{2}/\d{2})\s+(Entrada|Saída|Entrada PIX|Saída PIX|PIX)\s+(.+?)\s+(-?R?\$\s*\d{1,3}(?:\.\d{3})*,\d{2})',
                    re.IGNORECASE
                )
                
                match = padrao.search(linha)
                if match:
                    data_str = match.group(1)
                    tipo_str = match.group(3).lower()
                    descricao = match.group(4).strip()
                    valor_str = match.group(5)
                    
                    # Converte data
                    try:
                        dia, mes = data_str.split('/')
                        data = f"{ano}-{mes.zfill(2)}-{dia.zfill(2)}"
                    except:
                        continue
                    
                    # Converte valor
                    valor_str = re.sub(r'[R$\s]', '', valor_str)
                    valor_str = valor_str.replace('.', '').replace(',', '.')
                    try:
                        valor = float(valor_str)
                    except:
                        continue
                    
                    # Determina tipo
                    if 'saída' in tipo_str or valor < 0:
                        tipo = 'saida'
                        valor = abs(valor)
                    else:
                        tipo = 'entrada'
                    
                    movimento = Movimento(
                        data=data,
                        descricao=descricao,
                        tipo=tipo,
                        valor=valor
                    )
                    movimentos.append(movimento)
        
        metadata = self._gerar_metadata(movimentos)
        metadata['banco'] = 'Nubank'
        return movimentos, metadata


class ImportadorExtratos:
    """Gerenciador principal de importação de extratos"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.extratos_file = os.path.join(data_dir, "extratos_importados.json")
        self.parsadores = {
            TipoExtrato.CSV_GENERICO: ParseadorCSVGenerico(),
            TipoExtrato.BANCO_ITAU: ParseadorITAU(),
            TipoExtrato.BANCO_NUBANK: ParseadorNubank(),
            TipoExtrato.CARTAO_CREDITO: ParseadorCartaoCredito(),
            TipoExtrato.OFX: ParseadorOFX(),
        }
        
        os.makedirs(data_dir, exist_ok=True)
        self.extratos_importados = self._load_extratos()
    
    def _load_extratos(self) -> List[Dict]:
        """Carrega extratos já importados"""
        if os.path.exists(self.extratos_file):
            with open(self.extratos_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    def _save_extratos(self):
        """Salva extratos no arquivo"""
        with open(self.extratos_file, 'w', encoding='utf-8') as f:
            json.dump(self.extratos_importados, f, ensure_ascii=False, indent=2)
    
    def detectar_tipo(self, conteudo: str, nome_arquivo: str = "") -> TipoExtrato:
        """Detecta automaticamente o tipo de extrato"""
        conteudo_upper = conteudo.upper()
        
        # Verifica assinatura do banco
        if 'NUBANK' in conteudo_upper or 'Cheque Especial contratado' in conteudo or 'Extrato exportado' in conteudo:
            return TipoExtrato.BANCO_NUBANK
        if 'ITAU' in conteudo_upper:
            return TipoExtrato.BANCO_ITAU
        if 'BRADESCO' in conteudo_upper:
            return TipoExtrato.BANCO_BRADESCO
        if 'SANTANDER' in conteudo_upper:
            return TipoExtrato.BANCO_SANTANDER
        if 'CAIXA' in conteudo_upper:
            return TipoExtrato.BANCO_CAIXA
        if 'BANCO DO BRASIL' in conteudo_upper or 'BANCO BRASIL' in conteudo_upper:
            return TipoExtrato.BANCO_BB
        
        # Verifica por tipo de cartão
        if 'CARTÃO' in conteudo_upper or 'CARD' in conteudo_upper:
            if 'CRÉDITO' in conteudo_upper or 'CREDIT' in conteudo_upper:
                return TipoExtrato.CARTAO_CREDITO
            if 'DÉBITO' in conteudo_upper or 'DEBIT' in conteudo_upper:
                return TipoExtrato.CARTAO_DEBITO
        
        # Verifica por formato
        if '.csv' in nome_arquivo.lower():
            return TipoExtrato.CSV_GENERICO
        if '.ofx' in nome_arquivo.lower() or conteudo.startswith('OFXHEADER') or '<OFX>' in conteudo:
            return TipoExtrato.OFX
        
        # Se tiver estrutura de CSV
        if conteudo.count('\n') > 2 and (',' in conteudo or ';' in conteudo or '\t' in conteudo):
            return TipoExtrato.CSV_GENERICO
        
        return TipoExtrato.DESCONHECIDO
    
    def importar(self, conteudo: str, tipo: TipoExtrato = None, 
                 nome_arquivo: str = "", user_id: str = "") -> Dict:
        """
        Importa um extrato
        
        Args:
            conteudo: Conteúdo do arquivo de extrato
            tipo: Tipo de extrato (detecta automaticamente se não informado)
            nome_arquivo: Nome do arquivo
            user_id: ID do usuário
        
        Returns:
            Dict com resultado da importação
        """
        
        # Detecta tipo se não informado
        if not tipo:
            tipo = self.detectar_tipo(conteudo, nome_arquivo)
        
        # Obtém parsador
        parsador = self.parsadores.get(tipo) or ParseadorCSVGenerico()
        
        # Parse do conteúdo
        movimentos, metadata = parsador.parse(conteudo)
        
        if not movimentos:
            return {
                'status': StatusImportacao.ERRO.value,
                'mensagem': '❌ Nenhum movimento encontrado no extrato',
                'movimentos': [],
                'metadata': metadata
            }
        
        # Registra importação
        registro = {
            'id': self._gerar_id(),
            'tipo': tipo.value,
            'nome_arquivo': nome_arquivo,
            'data_importacao': datetime.now().isoformat(),
            'user_id': user_id,
            'movimentos': [m.to_dict() for m in movimentos],
            'metadata': metadata,
            'status': StatusImportacao.SUCESSO.value
        }
        
        self.extratos_importados.append(registro)
        self._save_extratos()
        
        return {
            'status': StatusImportacao.SUCESSO.value,
            'mensagem': f'✅ Extrato importado com sucesso!',
            'movimentos': len(movimentos),
            'total_valor': sum(m.valor for m in movimentos),
            'metadata': metadata,
            'id_importacao': registro['id']
        }
    
    def importar_arquivo(self, caminho_arquivo: str, tipo: TipoExtrato = None,
                        senha: str = None, user_id: str = "") -> Dict:
        """
        Importa um extrato a partir de um arquivo
        
        Args:
            caminho_arquivo: Caminho completo para o arquivo
            tipo: Tipo de extrato (detecta automaticamente se não informado)
            senha: Senha do PDF (se protegido)
            user_id: ID do usuário
        
        Returns:
            Dict com resultado da importação
        """
        if not os.path.exists(caminho_arquivo):
            return {
                'status': StatusImportacao.ERRO.value,
                'mensagem': f'❌ Arquivo não encontrado: {caminho_arquivo}',
                'movimentos': 0,
                'total_valor': 0
            }
        
        nome_arquivo = os.path.basename(caminho_arquivo)
        extensao = os.path.splitext(caminho_arquivo)[1].lower()
        
        # Lê o conteúdo do arquivo
        conteudo = ""
        try:
            if extensao == '.pdf':
                # Extrai texto do PDF
                if PDFPLUMBER_AVAILABLE:
                    with pdfplumber.open(caminho_arquivo, password=senha) as pdf:
                        for page in pdf.pages:
                            texto_pagina = page.extract_text()
                            if texto_pagina:
                                conteudo += texto_pagina + '\n'
                else:
                    return {
                        'status': StatusImportacao.ERRO.value,
                        'mensagem': '❌ pdfplumber não instalado. Instale com: pip install pdfplumber',
                        'movimentos': 0,
                        'total_valor': 0
                    }
            elif extensao in ['.csv', '.txt']:
                with open(caminho_arquivo, 'r', encoding='utf-8') as f:
                    conteudo = f.read()
            elif extensao == '.ofx':
                with open(caminho_arquivo, 'r', encoding='utf-8') as f:
                    conteudo = f.read()
            else:
                return {
                    'status': StatusImportacao.ERRO.value,
                    'mensagem': f'❌ Formato não suportado: {extensao}',
                    'movimentos': 0,
                    'total_valor': 0
                }
        except Exception as e:
            return {
                'status': StatusImportacao.ERRO.value,
                'mensagem': f'❌ Erro ao ler arquivo: {e}',
                'movimentos': 0,
                'total_valor': 0
            }
        
        # Importa o conteúdo
        return self.importar(conteudo, tipo, nome_arquivo, user_id)
    
    def listar_importacoes(self, user_id: str = "", limit: int = 10) -> List[Dict]:
        """Lista importações do usuário"""
        importacoes = [e for e in self.extratos_importados if not user_id or e.get('user_id') == user_id]
        return sorted(importacoes, key=lambda x: x.get('data_importacao', ''), reverse=True)[:limit]
    
    def obter_movimentos(self, id_importacao: str) -> Dict:
        """Obtém movimentos de uma importação"""
        for e in self.extratos_importados:
            if e['id'] == id_importacao:
                return {
                    'tipo': e['tipo'],
                    'data': e['data_importacao'],
                    'total': e['metadata'].get('total_movimentos', 0),
                    'movimentos': e['movimentos']
                }
        return None
    
    def _gerar_id(self) -> str:
        """Gera ID único para importação"""
        return f"imp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    async def handle(self, command: str, args: List[str], 
                     user_id: str = "", attachments: list = None) -> str:
        """Processa comandos de importação"""
        
        if command == 'importar_extrato':
            if not attachments:
                return "📎 Por favor, anexe um arquivo (CSV ou PDF)"
            
            # Placeholder para implementação com arquivo
            return "📥 Função de upload em desenvolvimento..."
        
        elif command == 'listar_extratos':
            importacoes = self.listar_importacoes(user_id)
            
            if not importacoes:
                return "📭 Nenhum extrato importado ainda"
            
            texto = "📊 *Seus Extratos Importados*\n\n"
            for e in importacoes:
                texto += f"📅 {e['data_importacao'][:10]}\n"
                texto += f"   📄 {e['nome_arquivo']}\n"
                texto += f"   📈 {e['metadata'].get('total_movimentos', 0)} movimentos\n\n"
            
            return texto
        
        return "❓ Comando não reconhecido"


# ==========================================
# EXEMPLO DE USO
# ==========================================

if __name__ == "__main__":
    importador = ImportadorExtratos()
    
    # Exemplo 1: Importar CSV genérico
    csv_exemplo = """data,descricao,valor
    01/12/2024,Mercado Carrefour,150.50
    02/12/2024,Uber para casa,35.00
    03/12/2024,Farmácia Drogasil,85.30
    """
    
    resultado = importador.importar(
        csv_exemplo,
        tipo=TipoExtrato.CSV_GENERICO,
        nome_arquivo="extrato_dezembro.csv",
        user_id="user_123"
    )
    
    print("=" * 50)
    print("RESULTADO DA IMPORTAÇÃO")
    print("=" * 50)
    print(json.dumps(resultado, ensure_ascii=False, indent=2))
