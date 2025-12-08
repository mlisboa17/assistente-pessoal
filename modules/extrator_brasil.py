"""
🇧🇷 Módulo de Extração de Documentos Financeiros Brasileiros
Especializado em: Boletos Bancários, Comprovantes PIX, Transferências

Bibliotecas:
- validate-docbr: Validação de CPF, CNPJ
- brazilcep: Consulta de CEP
- python-barcode: Leitura de códigos de barras
- pyzbar: Decodificação de códigos de barras em imagens
- easyocr: OCR para texto em português
"""
import re
import os
import tempfile
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple, Any
from dataclasses import dataclass, asdict


# Tenta importar bibliotecas específicas
VALIDATE_DOCBR_AVAILABLE = False
BRAZILCEP_AVAILABLE = False
PYZBAR_AVAILABLE = False
EASYOCR_AVAILABLE = False
PIL_AVAILABLE = False
PDFPLUMBER_AVAILABLE = False

try:
    from validate_docbr import CPF, CNPJ
    VALIDATE_DOCBR_AVAILABLE = True
except ImportError:
    pass

try:
    import brazilcep
    BRAZILCEP_AVAILABLE = True
except (ImportError, Exception):
    pass

try:
    from pyzbar import pyzbar
    from pyzbar.pyzbar import decode as pyzbar_decode
    PYZBAR_AVAILABLE = True
except (ImportError, OSError, FileNotFoundError, Exception):
    # pyzbar pode falhar se as DLLs não estiverem instaladas
    pyzbar = None
    pyzbar_decode = None
    pass

try:
    import easyocr
    EASYOCR_AVAILABLE = True
except (ImportError, Exception):
    pass

try:
    from PIL import Image
    import io
    PIL_AVAILABLE = True
except ImportError:
    pass

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    pass


@dataclass
class DadosBoleto:
    """Dados extraídos de um boleto"""
    linha_digitavel: str = ""
    codigo_barras: str = ""
    valor: float = 0.0
    vencimento: str = ""
    beneficiario: str = ""
    beneficiario_cnpj: str = ""
    pagador: str = ""
    pagador_cpf_cnpj: str = ""
    banco: str = ""
    codigo_banco: str = ""
    nosso_numero: str = ""
    documento: str = ""
    instrucoes: str = ""
    confianca: float = 0.0  # 0-100%


@dataclass
class DadosComprovantePix:
    """Dados extraídos de um comprovante PIX"""
    tipo_transacao: str = ""  # enviado, recebido
    valor: float = 0.0
    data_hora: str = ""
    origem_nome: str = ""
    origem_documento: str = ""  # CPF/CNPJ
    origem_banco: str = ""
    destino_nome: str = ""
    destino_documento: str = ""
    destino_banco: str = ""
    chave_pix: str = ""
    tipo_chave: str = ""  # cpf, cnpj, email, telefone, aleatoria
    id_transacao: str = ""
    descricao: str = ""
    confianca: float = 0.0


@dataclass
class DadosComprovanteTransferencia:
    """Dados extraídos de comprovante TED/DOC"""
    tipo: str = ""  # TED, DOC
    valor: float = 0.0
    data_hora: str = ""
    origem_nome: str = ""
    origem_cpf_cnpj: str = ""
    origem_banco: str = ""
    origem_agencia: str = ""
    origem_conta: str = ""
    destino_nome: str = ""
    destino_cpf_cnpj: str = ""
    destino_banco: str = ""
    destino_agencia: str = ""
    destino_conta: str = ""
    id_transacao: str = ""
    confianca: float = 0.0


class ExtratorDocumentosBrasil:
    """Extrai dados de documentos financeiros brasileiros"""
    
    # Códigos dos principais bancos
    BANCOS = {
        '001': 'Banco do Brasil',
        '033': 'Santander',
        '104': 'Caixa Econômica',
        '237': 'Bradesco',
        '341': 'Itaú',
        '356': 'Banco Real',
        '389': 'Banco Mercantil',
        '399': 'HSBC',
        '422': 'Safra',
        '453': 'Banco Rural',
        '633': 'Rendimento',
        '652': 'Itaú Unibanco',
        '745': 'Citibank',
        '077': 'Banco Inter',
        '260': 'Nubank',
        '290': 'PagBank',
        '323': 'Mercado Pago',
        '336': 'C6 Bank',
        '380': 'PicPay',
        '756': 'Sicoob',
        '748': 'Sicredi',
    }
    
    def __init__(self):
        self._easyocr_reader = None
        self._cpf_validator = CPF() if VALIDATE_DOCBR_AVAILABLE else None
        self._cnpj_validator = CNPJ() if VALIDATE_DOCBR_AVAILABLE else None
    
    def _get_easyocr(self):
        """Inicializa EasyOCR sob demanda"""
        if self._easyocr_reader is None and EASYOCR_AVAILABLE:
            try:
                self._easyocr_reader = easyocr.Reader(['pt', 'en'], gpu=False)
            except:
                pass
        return self._easyocr_reader
    
    # ==================== BOLETOS ====================
    
    def extrair_boleto_imagem(self, image_data: bytes) -> DadosBoleto:
        """Extrai dados de boleto a partir de imagem"""
        dados = DadosBoleto()
        texto = ""
        codigo_barras = ""
        
        # Tenta ler código de barras primeiro
        if PYZBAR_AVAILABLE and PIL_AVAILABLE:
            try:
                img = Image.open(io.BytesIO(image_data))
                codigos = pyzbar_decode(img)
                for codigo in codigos:
                    if codigo.type in ['I25', 'CODE128', 'EAN13']:
                        codigo_barras = codigo.data.decode('utf-8')
                        break
            except:
                pass
        
        # OCR para extrair texto
        if EASYOCR_AVAILABLE:
            try:
                reader = self._get_easyocr()
                if reader:
                    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
                        tmp.write(image_data)
                        tmp_path = tmp.name
                    
                    resultados = reader.readtext(tmp_path)
                    texto = '\n'.join([r[1] for r in resultados])
                    os.unlink(tmp_path)
            except:
                pass
        
        # Processa os dados
        dados = self._processar_texto_boleto(texto, codigo_barras)
        return dados
    
    def extrair_boleto_pdf(self, pdf_path: str) -> DadosBoleto:
        """Extrai dados de boleto a partir de PDF"""
        texto = ""
        
        if PDFPLUMBER_AVAILABLE:
            try:
                with pdfplumber.open(pdf_path) as pdf:
                    for page in pdf.pages:
                        texto += page.extract_text() or ""
            except:
                pass
        
        return self._processar_texto_boleto(texto, "")
    
    def _processar_texto_boleto(self, texto: str, codigo_barras: str) -> DadosBoleto:
        """Processa texto extraído de boleto"""
        dados = DadosBoleto()
        confianca = 0
        
        # Código de barras
        if codigo_barras:
            dados.codigo_barras = codigo_barras
            dados = self._decodificar_codigo_barras(dados, codigo_barras)
            confianca += 30
        
        # Linha digitável (47 dígitos com pontos)
        linha = self._extrair_linha_digitavel(texto)
        if linha:
            dados.linha_digitavel = linha
            if not codigo_barras:
                dados = self._decodificar_linha_digitavel(dados, linha)
            confianca += 25
        
        # Valor
        valor = self._extrair_valor(texto)
        if valor > 0:
            dados.valor = valor
            confianca += 15
        
        # Vencimento
        vencimento = self._extrair_data_vencimento(texto)
        if vencimento:
            dados.vencimento = vencimento
            confianca += 10
        
        # Beneficiário
        beneficiario = self._extrair_beneficiario(texto)
        if beneficiario:
            dados.beneficiario = beneficiario
            confianca += 10
        
        # CNPJ do beneficiário
        cnpj = self._extrair_cnpj(texto)
        if cnpj:
            dados.beneficiario_cnpj = cnpj
            confianca += 5
        
        # Pagador
        pagador = self._extrair_pagador(texto)
        if pagador:
            dados.pagador = pagador
            confianca += 5
        
        dados.confianca = min(confianca, 100)
        return dados
    
    def _extrair_linha_digitavel(self, texto: str) -> str:
        """Extrai linha digitável do texto"""
        # Padrão: XXXXX.XXXXX XXXXX.XXXXXX XXXXX.XXXXXX X XXXXXXXXXXXXXXX
        # Ou sem pontos: 47 dígitos
        
        # Com formatação
        padrao1 = r'\d{5}[\.\s]?\d{5}[\s]?\d{5}[\.\s]?\d{6}[\s]?\d{5}[\.\s]?\d{6}[\s]?\d[\s]?\d{14}'
        match = re.search(padrao1, texto.replace('\n', ' '))
        if match:
            linha = re.sub(r'[\s\.]', '', match.group())
            if len(linha) == 47:
                return self._formatar_linha_digitavel(linha)
        
        # Sem formatação (47 dígitos consecutivos)
        padrao2 = r'\d{47}'
        match = re.search(padrao2, texto.replace(' ', '').replace('\n', ''))
        if match:
            return self._formatar_linha_digitavel(match.group())
        
        return ""
    
    def _formatar_linha_digitavel(self, linha: str) -> str:
        """Formata linha digitável"""
        linha = re.sub(r'\D', '', linha)
        if len(linha) != 47:
            return linha
        
        return f"{linha[0:5]}.{linha[5:10]} {linha[10:15]}.{linha[15:21]} {linha[21:26]}.{linha[26:32]} {linha[32]} {linha[33:47]}"
    
    def _decodificar_linha_digitavel(self, dados: DadosBoleto, linha: str) -> DadosBoleto:
        """Decodifica linha digitável para extrair informações"""
        linha_limpa = re.sub(r'\D', '', linha)
        
        if len(linha_limpa) != 47:
            return dados
        
        # Código do banco (primeiros 3 dígitos)
        codigo_banco = linha_limpa[0:3]
        dados.codigo_banco = codigo_banco
        dados.banco = self.BANCOS.get(codigo_banco, f"Banco {codigo_banco}")
        
        # Fator de vencimento (posições 33-36)
        fator = linha_limpa[33:37]
        try:
            fator_int = int(fator)
            if fator_int > 0:
                # Data base: 07/10/1997
                data_base = datetime(1997, 10, 7)
                data_venc = data_base + timedelta(days=fator_int)
                dados.vencimento = data_venc.strftime('%d/%m/%Y')
        except:
            pass
        
        # Valor (posições 37-47)
        valor_str = linha_limpa[37:47]
        try:
            dados.valor = int(valor_str) / 100
        except:
            pass
        
        return dados
    
    def _decodificar_codigo_barras(self, dados: DadosBoleto, codigo: str) -> DadosBoleto:
        """Decodifica código de barras de boleto"""
        codigo_limpo = re.sub(r'\D', '', codigo)
        
        if len(codigo_limpo) == 44:  # Código de barras padrão
            # Código do banco
            dados.codigo_banco = codigo_limpo[0:3]
            dados.banco = self.BANCOS.get(dados.codigo_banco, f"Banco {dados.codigo_banco}")
            
            # Fator vencimento
            fator = codigo_limpo[5:9]
            try:
                fator_int = int(fator)
                if fator_int > 0:
                    data_base = datetime(1997, 10, 7)
                    data_venc = data_base + timedelta(days=fator_int)
                    dados.vencimento = data_venc.strftime('%d/%m/%Y')
            except:
                pass
            
            # Valor
            try:
                dados.valor = int(codigo_limpo[9:19]) / 100
            except:
                pass
        
        return dados
    
    # ==================== COMPROVANTES PIX ====================
    
    def extrair_pix_imagem(self, image_data: bytes) -> DadosComprovantePix:
        """Extrai dados de comprovante PIX de imagem"""
        texto = ""
        
        if EASYOCR_AVAILABLE:
            try:
                reader = self._get_easyocr()
                if reader:
                    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
                        tmp.write(image_data)
                        tmp_path = tmp.name
                    
                    resultados = reader.readtext(tmp_path)
                    texto = '\n'.join([r[1] for r in resultados])
                    os.unlink(tmp_path)
            except:
                pass
        
        return self._processar_texto_pix(texto)
    
    def extrair_pix_pdf(self, pdf_path: str) -> DadosComprovantePix:
        """Extrai dados de comprovante PIX de PDF"""
        texto = ""
        
        if PDFPLUMBER_AVAILABLE:
            try:
                with pdfplumber.open(pdf_path) as pdf:
                    for page in pdf.pages:
                        texto += page.extract_text() or ""
            except:
                pass
        
        return self._processar_texto_pix(texto)
    
    def _processar_texto_pix(self, texto: str) -> DadosComprovantePix:
        """Processa texto de comprovante PIX"""
        dados = DadosComprovantePix()
        confianca = 0
        texto_lower = texto.lower()
        
        # Detecta tipo de transação
        if 'enviado' in texto_lower or 'transferência enviada' in texto_lower:
            dados.tipo_transacao = 'enviado'
            confianca += 10
        elif 'recebido' in texto_lower or 'transferência recebida' in texto_lower:
            dados.tipo_transacao = 'recebido'
            confianca += 10
        elif 'pix' in texto_lower:
            dados.tipo_transacao = 'pix'
            confianca += 5
        
        # Valor
        valor = self._extrair_valor(texto)
        if valor > 0:
            dados.valor = valor
            confianca += 20
        
        # Data e hora
        data_hora = self._extrair_data_hora(texto)
        if data_hora:
            dados.data_hora = data_hora
            confianca += 10
        
        # Chave PIX
        chave, tipo = self._extrair_chave_pix(texto)
        if chave:
            dados.chave_pix = chave
            dados.tipo_chave = tipo
            confianca += 15
        
        # ID da transação
        id_trans = self._extrair_id_transacao(texto)
        if id_trans:
            dados.id_transacao = id_trans
            confianca += 10
        
        # Nomes e documentos
        nomes = self._extrair_nomes_transacao(texto)
        if 'origem' in nomes:
            dados.origem_nome = nomes['origem']
            confianca += 10
        if 'destino' in nomes:
            dados.destino_nome = nomes['destino']
            confianca += 10
        
        # CPF/CNPJ
        cpf = self._extrair_cpf(texto)
        cnpj = self._extrair_cnpj(texto)
        if cpf:
            if dados.tipo_transacao == 'enviado':
                dados.destino_documento = cpf
            else:
                dados.origem_documento = cpf
            confianca += 5
        if cnpj:
            dados.destino_documento = cnpj
            confianca += 5
        
        # Bancos
        bancos = self._extrair_bancos(texto)
        if bancos:
            if len(bancos) >= 1:
                dados.origem_banco = bancos[0]
            if len(bancos) >= 2:
                dados.destino_banco = bancos[1]
            confianca += 5
        
        dados.confianca = min(confianca, 100)
        return dados
    
    # ==================== TRANSFERÊNCIAS TED/DOC ====================
    
    def extrair_transferencia_imagem(self, image_data: bytes) -> DadosComprovanteTransferencia:
        """Extrai dados de comprovante TED/DOC"""
        texto = ""
        
        if EASYOCR_AVAILABLE:
            try:
                reader = self._get_easyocr()
                if reader:
                    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
                        tmp.write(image_data)
                        tmp_path = tmp.name
                    
                    resultados = reader.readtext(tmp_path)
                    texto = '\n'.join([r[1] for r in resultados])
                    os.unlink(tmp_path)
            except:
                pass
        
        return self._processar_texto_transferencia(texto)
    
    def _processar_texto_transferencia(self, texto: str) -> DadosComprovanteTransferencia:
        """Processa texto de comprovante TED/DOC"""
        dados = DadosComprovanteTransferencia()
        confianca = 0
        texto_lower = texto.lower()
        
        # Tipo
        if 'ted' in texto_lower:
            dados.tipo = 'TED'
            confianca += 15
        elif 'doc' in texto_lower:
            dados.tipo = 'DOC'
            confianca += 15
        
        # Valor
        valor = self._extrair_valor(texto)
        if valor > 0:
            dados.valor = valor
            confianca += 20
        
        # Data/hora
        data_hora = self._extrair_data_hora(texto)
        if data_hora:
            dados.data_hora = data_hora
            confianca += 10
        
        # Agência e conta
        agencia_conta = self._extrair_agencia_conta(texto)
        if agencia_conta:
            dados.destino_agencia = agencia_conta.get('agencia', '')
            dados.destino_conta = agencia_conta.get('conta', '')
            confianca += 15
        
        # Nomes
        nomes = self._extrair_nomes_transacao(texto)
        if 'origem' in nomes:
            dados.origem_nome = nomes['origem']
            confianca += 10
        if 'destino' in nomes:
            dados.destino_nome = nomes['destino']
            confianca += 10
        
        # Bancos
        bancos = self._extrair_bancos(texto)
        if bancos:
            if len(bancos) >= 1:
                dados.origem_banco = bancos[0]
            if len(bancos) >= 2:
                dados.destino_banco = bancos[1]
            confianca += 10
        
        dados.confianca = min(confianca, 100)
        return dados
    
    # ==================== FUNÇÕES AUXILIARES ====================
    
    def _extrair_valor(self, texto: str) -> float:
        """Extrai valor monetário do texto"""
        # Padrões: R$ 1.234,56 ou R$1234.56 ou 1.234,56
        padroes = [
            r'R\$\s*(\d{1,3}(?:\.\d{3})*,\d{2})',  # R$ 1.234,56
            r'R\$\s*(\d+,\d{2})',                    # R$ 123,45
            r'valor[:\s]+R?\$?\s*(\d{1,3}(?:\.\d{3})*,\d{2})',
            r'total[:\s]+R?\$?\s*(\d{1,3}(?:\.\d{3})*,\d{2})',
        ]
        
        for padrao in padroes:
            match = re.search(padrao, texto, re.IGNORECASE)
            if match:
                valor_str = match.group(1)
                valor_str = valor_str.replace('.', '').replace(',', '.')
                try:
                    return float(valor_str)
                except:
                    pass
        
        return 0.0
    
    def _extrair_data_vencimento(self, texto: str) -> str:
        """Extrai data de vencimento"""
        padroes = [
            r'vencimento[:\s]+(\d{2}/\d{2}/\d{4})',
            r'venc[:\s]+(\d{2}/\d{2}/\d{4})',
            r'data\s+venc[:\s]+(\d{2}/\d{2}/\d{4})',
        ]
        
        for padrao in padroes:
            match = re.search(padrao, texto, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return ""
    
    def _extrair_data_hora(self, texto: str) -> str:
        """Extrai data e hora"""
        padroes = [
            r'(\d{2}/\d{2}/\d{4})\s+[àa]?s?\s*(\d{2}:\d{2}(?::\d{2})?)',
            r'(\d{2}/\d{2}/\d{4})\s*-?\s*(\d{2}:\d{2})',
            r'data[:\s]+(\d{2}/\d{2}/\d{4})',
        ]
        
        for padrao in padroes:
            match = re.search(padrao, texto, re.IGNORECASE)
            if match:
                if len(match.groups()) >= 2:
                    return f"{match.group(1)} {match.group(2)}"
                return match.group(1)
        
        return ""
    
    def _extrair_beneficiario(self, texto: str) -> str:
        """Extrai nome do beneficiário"""
        padroes = [
            r'benefici[aá]rio[:\s]+([A-Za-zÀ-ÿ\s]+)',
            r'favorecido[:\s]+([A-Za-zÀ-ÿ\s]+)',
            r'cedente[:\s]+([A-Za-zÀ-ÿ\s]+)',
        ]
        
        for padrao in padroes:
            match = re.search(padrao, texto, re.IGNORECASE)
            if match:
                nome = match.group(1).strip()
                # Limita a 50 caracteres e remove lixo
                nome = nome[:50].split('\n')[0]
                return nome
        
        return ""
    
    def _extrair_pagador(self, texto: str) -> str:
        """Extrai nome do pagador"""
        padroes = [
            r'pagador[:\s]+([A-Za-zÀ-ÿ\s]+)',
            r'sacado[:\s]+([A-Za-zÀ-ÿ\s]+)',
        ]
        
        for padrao in padroes:
            match = re.search(padrao, texto, re.IGNORECASE)
            if match:
                nome = match.group(1).strip()[:50].split('\n')[0]
                return nome
        
        return ""
    
    def _extrair_cpf(self, texto: str) -> str:
        """Extrai e valida CPF"""
        padrao = r'\d{3}[\.\s]?\d{3}[\.\s]?\d{3}[\-\s]?\d{2}'
        matches = re.findall(padrao, texto)
        
        for match in matches:
            cpf = re.sub(r'\D', '', match)
            if len(cpf) == 11:
                if self._cpf_validator:
                    if self._cpf_validator.validate(cpf):
                        return self._cpf_validator.mask(cpf)
                else:
                    return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:11]}"
        
        return ""
    
    def _extrair_cnpj(self, texto: str) -> str:
        """Extrai e valida CNPJ"""
        padrao = r'\d{2}[\.\s]?\d{3}[\.\s]?\d{3}[/\s]?\d{4}[\-\s]?\d{2}'
        matches = re.findall(padrao, texto)
        
        for match in matches:
            cnpj = re.sub(r'\D', '', match)
            if len(cnpj) == 14:
                if self._cnpj_validator:
                    if self._cnpj_validator.validate(cnpj):
                        return self._cnpj_validator.mask(cnpj)
                else:
                    return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:14]}"
        
        return ""
    
    def _extrair_chave_pix(self, texto: str) -> Tuple[str, str]:
        """Extrai chave PIX e identifica tipo"""
        texto_clean = texto.replace('\n', ' ')
        
        # Email
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', texto_clean)
        if email_match:
            return email_match.group(), 'email'
        
        # Telefone
        tel_match = re.search(r'\+?55?\s*\(?\d{2}\)?\s*9?\d{4}[\-\s]?\d{4}', texto_clean)
        if tel_match:
            return tel_match.group(), 'telefone'
        
        # Chave aleatória (32 caracteres)
        chave_match = re.search(r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}', texto_clean, re.IGNORECASE)
        if chave_match:
            return chave_match.group(), 'aleatoria'
        
        # CPF como chave
        cpf = self._extrair_cpf(texto)
        if cpf:
            return cpf, 'cpf'
        
        # CNPJ como chave
        cnpj = self._extrair_cnpj(texto)
        if cnpj:
            return cnpj, 'cnpj'
        
        return "", ""
    
    def _extrair_id_transacao(self, texto: str) -> str:
        """Extrai ID da transação"""
        padroes = [
            r'id[:\s]+([A-Za-z0-9]+)',
            r'c[óo]digo[:\s]+([A-Za-z0-9]+)',
            r'end\s*to\s*end[:\s]+([A-Za-z0-9]+)',
            r'e2eid[:\s]+([A-Za-z0-9]+)',
        ]
        
        for padrao in padroes:
            match = re.search(padrao, texto, re.IGNORECASE)
            if match:
                id_trans = match.group(1)
                if len(id_trans) >= 10:
                    return id_trans
        
        return ""
    
    def _extrair_nomes_transacao(self, texto: str) -> Dict[str, str]:
        """Extrai nomes de origem e destino"""
        nomes = {}
        
        # Origem
        padroes_origem = [
            r'de[:\s]+([A-Za-zÀ-ÿ\s]+)',
            r'origem[:\s]+([A-Za-zÀ-ÿ\s]+)',
            r'remetente[:\s]+([A-Za-zÀ-ÿ\s]+)',
        ]
        
        for padrao in padroes_origem:
            match = re.search(padrao, texto, re.IGNORECASE)
            if match:
                nome = match.group(1).strip()[:40].split('\n')[0]
                if len(nome) > 3:
                    nomes['origem'] = nome
                    break
        
        # Destino
        padroes_destino = [
            r'para[:\s]+([A-Za-zÀ-ÿ\s]+)',
            r'destino[:\s]+([A-Za-zÀ-ÿ\s]+)',
            r'destinat[áa]rio[:\s]+([A-Za-zÀ-ÿ\s]+)',
            r'favorecido[:\s]+([A-Za-zÀ-ÿ\s]+)',
        ]
        
        for padrao in padroes_destino:
            match = re.search(padrao, texto, re.IGNORECASE)
            if match:
                nome = match.group(1).strip()[:40].split('\n')[0]
                if len(nome) > 3:
                    nomes['destino'] = nome
                    break
        
        return nomes
    
    def _extrair_bancos(self, texto: str) -> List[str]:
        """Extrai nomes de bancos mencionados"""
        bancos_encontrados = []
        texto_lower = texto.lower()
        
        for codigo, nome in self.BANCOS.items():
            if nome.lower() in texto_lower:
                bancos_encontrados.append(nome)
        
        # Busca por código
        for match in re.finditer(r'banco[:\s]+(\d{3})', texto_lower):
            codigo = match.group(1)
            if codigo in self.BANCOS:
                banco = self.BANCOS[codigo]
                if banco not in bancos_encontrados:
                    bancos_encontrados.append(banco)
        
        return bancos_encontrados
    
    def _extrair_agencia_conta(self, texto: str) -> Dict[str, str]:
        """Extrai agência e conta"""
        resultado = {}
        
        # Agência
        ag_match = re.search(r'ag[êe]?ncia[:\s]+(\d{4})', texto, re.IGNORECASE)
        if ag_match:
            resultado['agencia'] = ag_match.group(1)
        
        # Conta
        conta_match = re.search(r'conta[:\s]+(\d{5,12}[\-]?\d?)', texto, re.IGNORECASE)
        if conta_match:
            resultado['conta'] = conta_match.group(1)
        
        return resultado
    
    # ==================== DETECÇÃO AUTOMÁTICA ====================
    
    def detectar_tipo_documento(self, texto: str) -> str:
        """Detecta o tipo de documento financeiro"""
        texto_lower = texto.lower()
        
        # Boleto
        if any(palavra in texto_lower for palavra in ['boleto', 'linha digitável', 'código de barras', 'vencimento', 'cedente', 'sacado']):
            return 'boleto'
        
        # PIX
        if any(palavra in texto_lower for palavra in ['pix', 'chave pix', 'end to end', 'e2eid']):
            return 'pix'
        
        # TED/DOC
        if any(palavra in texto_lower for palavra in ['ted', 'doc', 'transferência bancária']):
            return 'transferencia'
        
        # Comprovante genérico
        if any(palavra in texto_lower for palavra in ['comprovante', 'recibo', 'pagamento']):
            return 'comprovante'
        
        return 'desconhecido'
    
    def extrair_automatico(self, image_data: bytes = None, pdf_path: str = None) -> Dict[str, Any]:
        """Extrai dados automaticamente detectando o tipo"""
        texto = ""
        
        # Extrai texto
        if image_data and EASYOCR_AVAILABLE:
            try:
                reader = self._get_easyocr()
                if reader:
                    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
                        tmp.write(image_data)
                        tmp_path = tmp.name
                    resultados = reader.readtext(tmp_path)
                    texto = '\n'.join([r[1] for r in resultados])
                    os.unlink(tmp_path)
            except:
                pass
        
        if pdf_path and PDFPLUMBER_AVAILABLE:
            try:
                with pdfplumber.open(pdf_path) as pdf:
                    for page in pdf.pages:
                        texto += page.extract_text() or ""
            except:
                pass
        
        # Detecta tipo
        tipo = self.detectar_tipo_documento(texto)
        
        # Extrai conforme tipo
        if tipo == 'boleto':
            if image_data:
                dados = self.extrair_boleto_imagem(image_data)
            else:
                dados = self._processar_texto_boleto(texto, "")
            return {'tipo': 'boleto', 'dados': asdict(dados)}
        
        elif tipo == 'pix':
            dados = self._processar_texto_pix(texto)
            return {'tipo': 'pix', 'dados': asdict(dados)}
        
        elif tipo == 'transferencia':
            dados = self._processar_texto_transferencia(texto)
            return {'tipo': 'transferencia', 'dados': asdict(dados)}
        
        else:
            # Tenta extrair o máximo possível
            return {
                'tipo': 'desconhecido',
                'texto_extraido': texto[:500],
                'valor': self._extrair_valor(texto),
                'data': self._extrair_data_hora(texto),
                'cpf': self._extrair_cpf(texto),
                'cnpj': self._extrair_cnpj(texto)
            }


# Singleton
_extrator: Optional[ExtratorDocumentosBrasil] = None

def get_extrator() -> ExtratorDocumentosBrasil:
    """Retorna instância singleton"""
    global _extrator
    if _extrator is None:
        _extrator = ExtratorDocumentosBrasil()
    return _extrator
