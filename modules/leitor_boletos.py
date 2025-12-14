"""
📄 Módulo Leitor de Boletos
Processa e extrai dados de boletos bancários brasileiros usando python-boleto
Compatível com múltiplos bancos brasileiros

FUNÇÕES PÚBLICAS PARA REUTILIZAÇÃO:
- processar_boleto_pdf(caminho_pdf) -> DadosBoletoExtraido
- processar_boleto_imagem(caminho_imagem) -> DadosBoletoExtraido
- validar_dados_boleto(dados) -> Dict[str, Any]
- identificar_banco_por_linha(linha_digitavel) -> str
- extrair_valor_texto(texto) -> Decimal
- extrair_cpf_cnpj_texto(texto) -> List[str]
"""

import os
import re
import json
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict

# Biblioteca python-boleto
try:
    from pyboleto.bank.bradesco import BoletoBradesco
    from pyboleto.bank.itau import BoletoItau
    from pyboleto.bank.bancodobrasil import BoletoBB
    from pyboleto.bank.caixa import BoletoCaixa
    from pyboleto.bank.santander import BoletoSantander
    from pyboleto.bank.banrisul import BoletoBanrisul
    from pyboleto.bank.hsbc import BoletoHsbc
    from pyboleto.bank.sicoob import BoletoSicoob
    from pyboleto.bank.sicredi import BoletoSicredi
    from pyboleto.bank.cecred import BoletoCecred
    PYBOLETO_AVAILABLE = True
except ImportError:
    PYBOLETO_AVAILABLE = False

# OCR e processamento de imagem (fallback)
try:
    import pytesseract
    from PIL import Image
    import cv2
    import numpy as np
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

# Extração de PDF (fallback)
try:
    import pypdfium2 as pdfium
    PDFIUM_AVAILABLE = True
except ImportError:
    PDFIUM_AVAILABLE = False

# Validação brasileira
try:
    from validate_docbr import CNPJ, CPF
    VALIDATE_AVAILABLE = True
except ImportError:
    VALIDATE_AVAILABLE = False

@dataclass
class DadosBoletoExtraido:
    """Dados extraídos de um boleto"""
    banco: str = ""
    agencia: str = ""
    conta: str = ""
    numero_documento: str = ""
    valor: Optional[Decimal] = None
    vencimento: Optional[datetime] = None
    sacado_nome: str = ""
    sacado_cpf_cnpj: str = ""
    cedente_nome: str = ""
    cedente_cpf_cnpj: str = ""
    codigo_barras: str = ""
    linha_digitavel: str = ""
    nosso_numero: str = ""
    carteira: str = ""
    especie_documento: str = ""
    aceite: str = ""
    local_pagamento: str = ""
    instrucoes: List[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário"""
        data = asdict(self)
        if self.valor:
            data['valor'] = float(self.valor)
        if self.vencimento:
            data['vencimento'] = self.vencimento.strftime('%Y-%m-%d')
        if self.instrucoes is None:
            data['instrucoes'] = []
        return data

# ==========================================
# FUNÇÕES PÚBLICAS PARA REUTILIZAÇÃO
# ==========================================

def processar_boleto_pdf(caminho_pdf: str, senha: str = None) -> DadosBoletoExtraido:
    """
    Processa um boleto PDF e extrai os dados.

    Args:
        caminho_pdf: Caminho completo para o arquivo PDF
        senha: Senha do PDF (opcional)

    Returns:
        DadosBoletoExtraido com os dados extraídos

    Raises:
        FileNotFoundError: Se o arquivo não existir
        ValueError: Se não for um PDF válido
    """
    if not os.path.exists(caminho_pdf):
        raise FileNotFoundError(f"Arquivo PDF não encontrado: {caminho_pdf}")

    if not caminho_pdf.lower().endswith('.pdf'):
        raise ValueError("Arquivo deve ter extensão .pdf")

    # Extrair texto do PDF
    texto = extrair_texto_pdf(caminho_pdf, senha)
    if not texto:
        raise ValueError("Não foi possível extrair texto do PDF")

    # Processar dados
    return processar_texto_boleto(texto)

def processar_boleto_imagem(caminho_imagem: str) -> DadosBoletoExtraido:
    """
    Processa uma imagem de boleto e extrai os dados usando OCR.

    Args:
        caminho_imagem: Caminho completo para a imagem

    Returns:
        DadosBoletoExtraido com os dados extraídos

    Raises:
        FileNotFoundError: Se o arquivo não existir
        ValueError: Se não for uma imagem válida
    """
    if not os.path.exists(caminho_imagem):
        raise FileNotFoundError(f"Arquivo de imagem não encontrado: {caminho_imagem}")

    extensoes_validas = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif']
    if not any(caminho_imagem.lower().endswith(ext) for ext in extensoes_validas):
        raise ValueError(f"Formato de imagem não suportado. Use: {', '.join(extensoes_validas)}")

    # Extrair texto da imagem
    texto = extrair_texto_imagem(caminho_imagem)
    if not texto:
        raise ValueError("Não foi possível extrair texto da imagem")

    # Processar dados
    return processar_texto_boleto(texto)

def processar_texto_boleto(texto: str) -> DadosBoletoExtraido:
    """
    Processa texto extraído de boleto e retorna dados estruturados.

    Args:
        texto: Texto extraído do boleto

    Returns:
        DadosBoletoExtraido com os dados processados
    """
    dados = DadosBoletoExtraido()

    # Extrair dados usando funções específicas
    dados.banco = identificar_banco_texto(texto)
    dados.valor = extrair_valor_texto(texto)
    dados.vencimento = extrair_vencimento_texto(texto)
    dados.codigo_barras = extrair_codigo_barras_texto(texto)
    dados.linha_digitavel = extrair_linha_digitavel_texto(texto)
    dados.nosso_numero = extrair_nosso_numero_texto(texto)

    # Extrair CPFs/CNPJs
    cpfs_cnpjs = extrair_cpf_cnpj_texto(texto)
    if len(cpfs_cnpjs) >= 1:
        dados.sacado_cpf_cnpj = cpfs_cnpjs[0]
    if len(cpfs_cnpjs) >= 2:
        dados.cedente_cpf_cnpj = cpfs_cnpjs[1]

    return dados

def validar_dados_boleto(dados: DadosBoletoExtraido) -> Dict[str, Any]:
    """
    Valida os dados extraídos de um boleto.

    Args:
        dados: DadosBoletoExtraido a validar

    Returns:
        Dicionário com resultado da validação
    """
    validacoes = {
        'valido': True,
        'erros': [],
        'avisos': []
    }

    # Valida código de barras
    if dados.codigo_barras:
        if len(dados.codigo_barras) not in [44, 47, 48]:
            validacoes['erros'].append(f"Código de barras com tamanho inválido: {len(dados.codigo_barras)}")
            validacoes['valido'] = False
    else:
        validacoes['avisos'].append("Código de barras não encontrado")

    # Valida valor
    if not dados.valor or dados.valor <= 0:
        validacoes['erros'].append("Valor não encontrado ou inválido")
        validacoes['valido'] = False

    # Valida vencimento
    if not dados.vencimento:
        validacoes['avisos'].append("Data de vencimento não encontrada")

    # Valida CPF/CNPJ
    if dados.sacado_cpf_cnpj and VALIDATE_AVAILABLE:
        if not validar_cpf_cnpj_str(dados.sacado_cpf_cnpj):
            validacoes['erros'].append("CPF/CNPJ do sacado inválido")
            validacoes['valido'] = False

    return validacoes

def identificar_banco_por_linha(linha_digitavel: str) -> str:
    """
    Identifica o banco a partir da linha digitável.

    Args:
        linha_digitavel: Linha digitável do boleto

    Returns:
        Nome do banco identificado
    """
    bancos = {
        '001': 'Banco do Brasil',
        '033': 'Santander',
        '104': 'Caixa Econômica Federal',
        '237': 'Bradesco',
        '341': 'Itaú',
        '399': 'HSBC',
        '745': 'Citibank'
    }

    if len(linha_digitavel) >= 3:
        codigo_banco = linha_digitavel[:3]
        return bancos.get(codigo_banco, f"Banco {codigo_banco}")

    return "Banco não identificado"

# ==========================================
# FUNÇÕES AUXILIARES (INTERNAS)
# ==========================================

def extrair_texto_pdf(caminho_pdf: str, senha: str = None) -> str:
    """Extrai texto de PDF usando pypdfium2"""
    if not PDFIUM_AVAILABLE:
        raise ImportError("pypdfium2 não instalado")

    try:
        pdf = pdfium.PdfDocument(caminho_pdf, password=senha)
        texto = ""

        for pagina in pdf:
            texto_pagina = pagina.get_textpage()
            texto += texto_pagina.get_text_range() + "\n"

        return texto
    except Exception as e:
        print(f"❌ Erro ao extrair texto do PDF: {e}")
        return ""

def extrair_texto_imagem(caminho_imagem: str) -> str:
    """Extrai texto de imagem usando OCR"""
    if not OCR_AVAILABLE:
        raise ImportError("OCR não disponível")

    try:
        imagem = Image.open(caminho_imagem)
        if imagem.mode != 'RGB':
            imagem = imagem.convert('RGB')

        imagem_cv = cv2.cvtColor(np.array(imagem), cv2.COLOR_RGB2BGR)
        imagem_gray = cv2.cvtColor(imagem_cv, cv2.COLOR_BGR2GRAY)
        _, imagem_thresh = cv2.threshold(imagem_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        texto = pytesseract.image_to_string(imagem_thresh, lang='por')
        return texto
    except Exception as e:
        print(f"❌ Erro no OCR: {e}")
        return ""

def extrair_codigo_barras_texto(texto: str) -> str:
    """Extrai código de barras do texto (última ocorrência)"""
    padrao = re.compile(r'\d{44,48}')
    matches = padrao.findall(texto)
    return matches[-1] if matches else ""

def extrair_linha_digitavel_texto(texto: str) -> str:
    """Extrai linha digitável do texto (última ocorrência)"""
    padrao = re.compile(r'\d{5}\.\d{5}\s\d{5}\.\d{6}\s\d{5}\.\d{6}\s\d\s\d{14}')
    matches = padrao.findall(texto)
    return matches[-1] if matches else ""

def extrair_valor_texto(texto: str) -> Optional[Decimal]:
    """Extrai valor do texto (última ocorrência)"""
    padrao = re.compile(r'(?:R\$\s*|Valor:\s*|R\$\s*)(\d{1,3}(?:\.\d{3})*,\d{2})')
    matches = padrao.findall(texto)
    if matches:
        valor_str = matches[-1]
        valor_str = valor_str.replace('.', '').replace(',', '.')
        try:
            return Decimal(valor_str)
        except:
            pass
    return None

def extrair_vencimento_texto(texto: str) -> Optional[datetime]:
    """Extrai data de vencimento do texto (última ocorrência)"""
    padrao = re.compile(r'(?:Vencimento|Venc\.|Vcto\.?)\s*:\s*(\d{2}/\d{2}/\d{4})')
    matches = padrao.findall(texto)
    if matches:
        data_str = matches[-1]
        try:
            return datetime.strptime(data_str, '%d/%m/%Y')
        except:
            pass
    return None

def extrair_cpf_cnpj_texto(texto: str) -> List[str]:
    """Extrai CPFs e CNPJs do texto (últimas ocorrências)"""
    padrao = re.compile(r'(?:\d{3}\.\d{3}\.\d{3}-\d{2}|\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})')
    matches = padrao.findall(texto)
    # Retornar as últimas ocorrências únicas, mantendo ordem reversa
    seen = set()
    result = []
    for match in reversed(matches):
        if match not in seen:
            seen.add(match)
            result.append(match)
    return result[::-1]  # reverter para ordem original das últimas

def extrair_nosso_numero_texto(texto: str) -> str:
    """Extrai nosso número do texto (última ocorrência)"""
    padrao = re.compile(r'(?:Nosso\s*Número|Nº\s*Documento)\s*:\s*([A-Za-z0-9\-]+)')
    matches = padrao.findall(texto)
    return matches[-1] if matches else ""

def identificar_banco_texto(texto: str) -> str:
    """Identifica o banco no texto (última ocorrência)"""
    bancos = {
        '001': 'Banco do Brasil',
        '033': 'Santander',
        '104': 'Caixa Econômica Federal',
        '237': 'Bradesco',
        '341': 'Itaú',
        '399': 'HSBC',
        '745': 'Citibank'
    }

    # Tenta código do banco
    padrao_banco = re.compile(r'Banco\s*(\d{3})')
    matches = padrao_banco.findall(texto)
    if matches:
        codigo = matches[-1]
        return bancos.get(codigo, f"Banco {codigo}")

    # Procura nomes
    for codigo, nome in bancos.items():
        if nome.lower() in texto.lower():
            return nome

    # Tenta pela linha digitável
    linha = extrair_linha_digitavel_texto(texto)
    if linha:
        return identificar_banco_por_linha(linha)

    return "Banco não identificado"

def validar_cpf_cnpj_str(cpf_cnpj: str) -> bool:
    """Valida CPF ou CNPJ"""
    if not VALIDATE_AVAILABLE:
        return True

    cpf_cnpj = re.sub(r'\D', '', cpf_cnpj)

    if len(cpf_cnpj) == 11:
        return CPF().validate(cpf_cnpj)
    elif len(cpf_cnpj) == 14:
        return CNPJ().validate(cpf_cnpj)
    else:
        return False

# ==========================================
# CLASSE PRINCIPAL (COMPATIBILIDADE)
# ==========================================

class LeitorBoleto:
    """Classe principal para compatibilidade com código existente"""

    def __init__(self):
        self.bancos_pyboleto = {
            'bradesco': BoletoBradesco,
            'itau': BoletoItau,
            'bb': BoletoBB,
            'caixa': BoletoCaixa,
            'santander': BoletoSantander,
            'banrisul': BoletoBanrisul,
            'hsbc': BoletoHsbc,
            'sicoob': BoletoSicoob,
            'sicredi': BoletoSicredi,
            'cecred': BoletoCecred
        }

        self.bancos_codigo = {
            '001': 'Banco do Brasil',
            '033': 'Santander',
            '104': 'Caixa Econômica Federal',
            '237': 'Bradesco',
            '341': 'Itaú',
            '399': 'HSBC',
            '745': 'Citibank',
            '041': 'Banrisul',
            '756': 'Sicoob',
            '748': 'Sicredi',
            '085': 'Cecred'
        }

        self.padroes = {
            'codigo_barras': re.compile(r'\d{44,48}'),
            'linha_digitavel': re.compile(r'\d{5}\.\d{5}\s\d{5}\.\d{6}\s\d{5}\.\d{6}\s\d\s\d{14}'),
            'valor': re.compile(r'(?:R\$\s*|Valor:\s*|R\$\s*)(\d{1,3}(?:\.\d{3})*,\d{2})'),
            'vencimento': re.compile(r'(?:Vencimento|Venc\.|Vcto\.?)\s*:\s*(\d{2}/\d{2}/\d{4})'),
            'cpf_cnpj': re.compile(r'(?:\d{3}\.\d{3}\.\d{3}-\d{2}|\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})'),
            'nosso_numero': re.compile(r'(?:Nosso\s*Número|Nº\s*Documento)\s*:\s*([A-Za-z0-9\-]+)'),
            'banco': re.compile(r'Banco\s*(\d{3})')
        }

    def processar_boleto_arquivo(self, caminho_arquivo: str, senha: str = None) -> DadosBoletoExtraido:
        """Método compatibilidade - usa as funções públicas"""
        if not os.path.exists(caminho_arquivo):
            raise FileNotFoundError(f"Arquivo não encontrado: {caminho_arquivo}")

        extensao = os.path.splitext(caminho_arquivo)[1].lower()

        if extensao == '.pdf':
            return processar_boleto_pdf(caminho_arquivo, senha)
        elif extensao in ['.jpg', '.jpeg', '.png', '.bmp']:
            return processar_boleto_imagem(caminho_arquivo)
        else:
            raise ValueError(f"Formato não suportado: {extensao}")

    def validar_boleto(self, dados: DadosBoletoExtraido) -> Dict[str, Any]:
        """Método compatibilidade - usa função pública"""
        return validar_dados_boleto(dados)

    def validar_cpf_cnpj(self, cpf_cnpj: str) -> bool:
        """Método compatibilidade"""
        return validar_cpf_cnpj_str(cpf_cnpj)

    # Métodos não implementados (mantidos para compatibilidade futura)
    def _processar_com_pyboleto(self, caminho_arquivo: str) -> DadosBoletoExtraido:
        raise NotImplementedError("Processamento direto com python-boleto ainda não implementado")

    def criar_boleto_pyboleto(self, dados: DadosBoletoExtraido, banco: str = 'itau') -> Any:
        if not PYBOLETO_AVAILABLE:
            raise ImportError("python-boleto não instalado")

        if banco not in self.bancos_pyboleto:
            raise ValueError(f"Banco {banco} não suportado")

        try:
            BoletoClass = self.bancos_pyboleto[banco]
            boleto = BoletoClass()

            boleto.numero_documento = dados.numero_documento or "001"
            boleto.valor_documento = float(dados.valor) if dados.valor else 0.0
            boleto.data_vencimento = dados.vencimento or datetime.now()

            boleto.sacado_nome = dados.sacado_nome or "Sacado"
            boleto.sacado_endereco = "Endereço não informado"
            boleto.sacado_bairro = "Bairro"
            boleto.sacado_cidade = "Cidade"
            boleto.sacado_uf = "UF"
            boleto.sacado_cep = "00000-000"

            return boleto

        except Exception as e:
            print(f"❌ Erro ao criar boleto: {e}")
            return None

# ==========================================
# TESTE E DEMONSTRAÇÃO
# ==========================================

def testar_leitor_boleto():
    """Função de teste"""
    print("🧪 Testando Leitor de Boletos com python-boleto integrado...")
    print(f"📚 Python-boleto disponível: {PYBOLETO_AVAILABLE}")
    print(f"📄 PDFium disponível: {PDFIUM_AVAILABLE}")
    print(f"👁️  OCR disponível: {OCR_AVAILABLE}")
    print(f"🇧🇷 Validação disponível: {VALIDATE_AVAILABLE}")

    # Teste com arquivo real
    try:
        dados = processar_boleto_pdf(r'c:\Users\mlisb\Downloads\BOLETO_NFe002806803.PDF')
        print('✅ Dados extraídos:')
        print(json.dumps(dados.to_dict(), indent=2, ensure_ascii=False))

        validacao = validar_dados_boleto(dados)
        status = "Válido" if validacao["valido"] else "Inválido"
        print(f'\n🔍 Validação: {status}')
        if validacao['erros']:
            print('Erros:')
            for erro in validacao['erros']:
                print(f'  - {erro}')
        if validacao['avisos']:
            print('Avisos:')
            for aviso in validacao['avisos']:
                print(f'  - {aviso}')

    except Exception as e:
        print(f'❌ Erro: {e}')

    print("\n🎯 Teste concluído!")

if __name__ == "__main__":
    testar_leitor_boleto()

    def __init__(self):
        self.bancos_pyboleto = {
            'bradesco': BoletoBradesco,
            'itau': BoletoItau,
            'bb': BoletoBB,
            'caixa': BoletoCaixa,
            'santander': BoletoSantander,
            'banrisul': BoletoBanrisul,
            'hsbc': BoletoHsbc,
            'sicoob': BoletoSicoob,
            'sicredi': BoletoSicredi,
            'cecred': BoletoCecred
        }

        # Mapeamento de códigos para nomes
        self.bancos_codigo = {
            '001': 'Banco do Brasil',
            '033': 'Santander',
            '104': 'Caixa Econômica Federal',
            '237': 'Bradesco',
            '341': 'Itaú',
            '399': 'HSBC',
            '745': 'Citibank',
            '041': 'Banrisul',
            '756': 'Sicoob',
            '748': 'Sicredi',
            '085': 'Cecred'
        }

        # Padrões regex para extração
        self.padroes = {
            'codigo_barras': re.compile(r'\d{44,48}'),
            'linha_digitavel': re.compile(r'\d{5}\.\d{5}\s\d{5}\.\d{6}\s\d{5}\.\d{6}\s\d\s\d{14}'),
            'valor': re.compile(r'(?:R\$\s*|Valor:\s*|R\$\s*)(\d{1,3}(?:\.\d{3})*,\d{2})'),
            'vencimento': re.compile(r'(?:Vencimento|Venc\.|Vcto\.?)\s*:\s*(\d{2}/\d{2}/\d{4})'),
            'cpf_cnpj': re.compile(r'(?:\d{3}\.\d{3}\.\d{3}-\d{2}|\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})'),
            'nosso_numero': re.compile(r'(?:Nosso\s*Número|Nº\s*Documento)\s*:\s*([A-Za-z0-9\-]+)'),
            'banco': re.compile(r'Banco\s*(\d{3})')
        }

    def processar_boleto_arquivo(self, caminho_arquivo: str) -> DadosBoletoExtraido:
        """
        Processa um boleto a partir de arquivo usando python-boleto

        Args:
            caminho_arquivo: Caminho para o arquivo

        Returns:
            Dados extraídos do boleto
        """
        if not os.path.exists(caminho_arquivo):
            raise FileNotFoundError(f"Arquivo não encontrado: {caminho_arquivo}")

        # Primeiro tenta usar python-boleto se disponível
        if PYBOLETO_AVAILABLE:
            try:
                return self._processar_com_pyboleto(caminho_arquivo)
            except Exception as e:
                print(f"⚠️ Erro com python-boleto: {e}. Tentando método alternativo...")
                return self._processar_metodo_alternativo(caminho_arquivo)
        else:
            return self._processar_metodo_alternativo(caminho_arquivo)

    def _processar_com_pyboleto(self, caminho_arquivo: str) -> DadosBoletoExtraido:
        """
        Processa boleto usando a biblioteca python-boleto

        Args:
            caminho_arquivo: Caminho para o arquivo

        Returns:
            Dados extraídos
        """
        # Por enquanto, python-boleto é mais focado em geração
        # Vamos usar como base e extrair dados do arquivo
        raise NotImplementedError("Processamento direto com python-boleto ainda não implementado")

    def _processar_metodo_alternativo(self, caminho_arquivo: str) -> DadosBoletoExtraido:
        """
        Método alternativo usando OCR e regex

        Args:
            caminho_arquivo: Caminho para o arquivo

        Returns:
            Dados extraídos
        """
        # Determina tipo do arquivo
        extensao = os.path.splitext(caminho_arquivo)[1].lower()

        if extensao == '.pdf':
            texto = self.extrair_texto_pdf(caminho_arquivo)
        elif extensao in ['.jpg', '.jpeg', '.png', '.bmp']:
            texto = self.extrair_texto_imagem(caminho_arquivo)
        else:
            raise ValueError(f"Formato não suportado: {extensao}")

        if not texto:
            return DadosBoletoExtraido()

        # Extrai dados
        dados = DadosBoletoExtraido()

        dados.banco = self.identificar_banco(texto)
        dados.valor = self.extrair_valor(texto)
        dados.vencimento = self.extrair_vencimento(texto)
        dados.codigo_barras = self.extrair_codigo_barras(texto)
        dados.linha_digitavel = self.extrair_linha_digitavel(texto)
        dados.nosso_numero = self.extrair_nosso_numero(texto)

        # Extrai CPFs/CNPJs
        cpfs_cnpjs = self.extrair_cpf_cnpj(texto)
        if len(cpfs_cnpjs) >= 1:
            dados.sacado_cpf_cnpj = cpfs_cnpjs[0]
        if len(cpfs_cnpjs) >= 2:
            dados.cedente_cpf_cnpj = cpfs_cnpjs[1]

        return dados

    def extrair_texto_pdf(self, caminho_pdf: str) -> str:
        """Extrai texto de PDF usando pypdfium2"""
        if not PDFIUM_AVAILABLE:
            raise ImportError("pypdfium2 não instalado")

        try:
            pdf = pdfium.PdfDocument(caminho_pdf)
            texto = ""

            for pagina in pdf:
                texto_pagina = pagina.get_textpage()
                texto += texto_pagina.get_text_range() + "\n"

            return texto
        except Exception as e:
            print(f"❌ Erro ao extrair texto do PDF: {e}")
            return ""

    def extrair_texto_imagem(self, caminho_imagem: str) -> str:
        """Extrai texto de imagem usando OCR"""
        if not OCR_AVAILABLE:
            raise ImportError("OCR não disponível")

        try:
            imagem = Image.open(caminho_imagem)
            if imagem.mode != 'RGB':
                imagem = imagem.convert('RGB')

            imagem_cv = cv2.cvtColor(np.array(imagem), cv2.COLOR_RGB2BGR)
            imagem_gray = cv2.cvtColor(imagem_cv, cv2.COLOR_BGR2GRAY)
            _, imagem_thresh = cv2.threshold(imagem_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            texto = pytesseract.image_to_string(imagem_thresh, lang='por')
            return texto
        except Exception as e:
            print(f"❌ Erro no OCR: {e}")
            return ""

    def extrair_codigo_barras(self, texto: str) -> str:
        """Extrai código de barras"""
        match = self.padroes['codigo_barras'].search(texto)
        return match.group(0) if match else ""

    def extrair_linha_digitavel(self, texto: str) -> str:
        """Extrai linha digitável"""
        match = self.padroes['linha_digitavel'].search(texto)
        return match.group(0) if match else ""

    def extrair_valor(self, texto: str) -> Optional[Decimal]:
        """Extrai valor"""
        match = self.padroes['valor'].search(texto)
        if match:
            valor_str = match.group(1)
            valor_str = valor_str.replace('.', '').replace(',', '.')
            try:
                return Decimal(valor_str)
            except:
                pass
        return None

    def extrair_vencimento(self, texto: str) -> Optional[datetime]:
        """Extrai data de vencimento"""
        match = self.padroes['vencimento'].search(texto)
        if match:
            data_str = match.group(1)
            try:
                return datetime.strptime(data_str, '%d/%m/%Y')
            except:
                pass
        return None

    def extrair_cpf_cnpj(self, texto: str) -> List[str]:
        """Extrai CPFs e CNPJs"""
        matches = self.padroes['cpf_cnpj'].findall(texto)
        return list(set(matches))

    def extrair_nosso_numero(self, texto: str) -> str:
        """Extrai nosso número"""
        match = self.padroes['nosso_numero'].search(texto)
        return match.group(1) if match else ""

    def identificar_banco(self, texto: str) -> str:
        """Identifica o banco"""
        # Tenta código do banco
        match = self.padroes['banco'].search(texto)
        if match:
            codigo = match.group(1)
            return self.bancos_codigo.get(codigo, f"Banco {codigo}")

        # Procura nomes
        for codigo, nome in self.bancos_codigo.items():
            if nome.lower() in texto.lower():
                return nome

        # Tenta identificar pela linha digitável
        linha = self.extrair_linha_digitavel(texto)
        if linha:
            codigo_banco = linha[:3]
            return self.bancos_codigo.get(codigo_banco, f"Banco {codigo_banco}")

        return "Banco não identificado"

    def validar_boleto(self, dados: DadosBoletoExtraido) -> Dict[str, Any]:
        """Valida dados extraídos"""
        validacoes = {
            'valido': True,
            'erros': [],
            'avisos': []
        }

        if dados.codigo_barras:
            if len(dados.codigo_barras) not in [44, 47, 48]:
                validacoes['erros'].append(f"Código de barras com tamanho inválido: {len(dados.codigo_barras)}")
                validacoes['valido'] = False
        else:
            validacoes['avisos'].append("Código de barras não encontrado")

        if not dados.valor or dados.valor <= 0:
            validacoes['erros'].append("Valor não encontrado ou inválido")
            validacoes['valido'] = False

        if not dados.vencimento:
            validacoes['avisos'].append("Data de vencimento não encontrada")

        if dados.sacado_cpf_cnpj and VALIDATE_AVAILABLE:
            if not self.validar_cpf_cnpj(dados.sacado_cpf_cnpj):
                validacoes['erros'].append("CPF/CNPJ do sacado inválido")
                validacoes['valido'] = False

        return validacoes

    def validar_cpf_cnpj(self, cpf_cnpj: str) -> bool:
        """Valida CPF ou CNPJ"""
        if not VALIDATE_AVAILABLE:
            return True

        cpf_cnpj = re.sub(r'\D', '', cpf_cnpj)

        if len(cpf_cnpj) == 11:
            return CPF().validate(cpf_cnpj)
        elif len(cpf_cnpj) == 14:
            return CNPJ().validate(cpf_cnpj)
        else:
            return False

    def criar_boleto_pyboleto(self, dados: DadosBoletoExtraido, banco: str = 'itau') -> Any:
        """
        Cria um objeto boleto usando python-boleto para geração

        Args:
            dados: Dados do boleto
            banco: Nome do banco

        Returns:
            Objeto boleto da python-boleto
        """
        if not PYBOLETO_AVAILABLE:
            raise ImportError("python-boleto não instalado")

        if banco not in self.bancos_pyboleto:
            raise ValueError(f"Banco {banco} não suportado")

        try:
            BoletoClass = self.bancos_pyboleto[banco]
            boleto = BoletoClass()

            # Configura dados básicos
            boleto.numero_documento = dados.numero_documento or "001"
            boleto.valor_documento = float(dados.valor) if dados.valor else 0.0
            boleto.data_vencimento = dados.vencimento or datetime.now()

            # Dados do sacado
            boleto.sacado_nome = dados.sacado_nome or "Sacado"
            boleto.sacado_endereco = "Endereço não informado"
            boleto.sacado_bairro = "Bairro"
            boleto.sacado_cidade = "Cidade"
            boleto.sacado_uf = "UF"
            boleto.sacado_cep = "00000-000"

            return boleto

        except Exception as e:
            print(f"❌ Erro ao criar boleto: {e}")
            return None

# Função de teste
def testar_leitor_boleto():
    """Função de teste"""
    print("🧪 Testando Leitor de Boletos com python-boleto...")

    leitor = LeitorBoleto()

    print(f"📚 Python-boleto disponível: {PYBOLETO_AVAILABLE}")
    print(f"📄 PDFium disponível: {PDFIUM_AVAILABLE}")
    print(f"👁️  OCR disponível: {OCR_AVAILABLE}")
    print(f"🇧🇷 Validação disponível: {VALIDATE_AVAILABLE}")

    # Teste com arquivo real
    try:
        dados = leitor.processar_boleto_arquivo(r'c:\Users\mlisb\Downloads\BOLETO_NFe002806803.PDF')
        print('✅ Dados extraídos:')
        print(json.dumps(dados.to_dict(), indent=2, ensure_ascii=False))

        validacao = leitor.validar_boleto(dados)
        status = "Válido" if validacao["valido"] else "Inválido"
        print(f'\n🔍 Validação: {status}')
        if validacao['erros']:
            print('Erros:')
            for erro in validacao['erros']:
                print(f'  - {erro}')
        if validacao['avisos']:
            print('Avisos:')
            for aviso in validacao['avisos']:
                print(f'  - {aviso}')

    except Exception as e:
        print(f'❌ Erro: {e}')

    print("\n🎯 Teste concluído!")

if __name__ == "__main__":
    testar_leitor_boleto()