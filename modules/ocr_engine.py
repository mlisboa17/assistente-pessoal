"""
🔍 Módulo de OCR e Extração de Texto
Processa imagens e PDFs usando bibliotecas gratuitas
Alternativas ao Tesseract e Gemini
"""
import os
import re
import base64
import tempfile
from typing import Optional, Dict, List, Tuple
from datetime import datetime


# Tenta importar bibliotecas de OCR (ordem de preferência)
EASYOCR_AVAILABLE = False
PYTESSERACT_AVAILABLE = False
PIL_AVAILABLE = False
PDF2IMAGE_AVAILABLE = False
PDFPLUMBER_AVAILABLE = False
PYPDF2_AVAILABLE = False

try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    pass

try:
    import pytesseract
    PYTESSERACT_AVAILABLE = True
except ImportError:
    pass

try:
    from PIL import Image
    import io
    PIL_AVAILABLE = True
except ImportError:
    pass

try:
    import pdf2image
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    pass

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    pass

try:
    from PyPDF2 import PdfReader
    PYPDF2_AVAILABLE = True
except ImportError:
    pass


class OCREngine:
    """Motor de OCR com múltiplas opções gratuitas"""
    
    def __init__(self):
        self._easyocr_reader = None
        
        # Status de disponibilidade
        self.status = {
            'easyocr': EASYOCR_AVAILABLE,
            'pytesseract': PYTESSERACT_AVAILABLE,
            'pdfplumber': PDFPLUMBER_AVAILABLE,
            'pypdf2': PYPDF2_AVAILABLE,
            'pdf2image': PDF2IMAGE_AVAILABLE,
            'pil': PIL_AVAILABLE
        }
    
    def _get_easyocr_reader(self):
        """Carrega EasyOCR sob demanda (economiza memória)"""
        if self._easyocr_reader is None and EASYOCR_AVAILABLE:
            try:
                self._easyocr_reader = easyocr.Reader(['pt', 'en'], gpu=False)
            except Exception as e:
                print(f"Erro ao inicializar EasyOCR: {e}")
        return self._easyocr_reader
    
    def extrair_texto_imagem(self, image_data: bytes) -> str:
        """
        Extrai texto de uma imagem usando OCR
        Tenta EasyOCR primeiro, depois Tesseract
        """
        texto = ""
        
        # Método 1: EasyOCR (melhor para português)
        if EASYOCR_AVAILABLE:
            try:
                reader = self._get_easyocr_reader()
                if reader:
                    # Salva temporariamente
                    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
                        tmp.write(image_data)
                        tmp_path = tmp.name
                    
                    resultados = reader.readtext(tmp_path)
                    texto = ' '.join([r[1] for r in resultados])
                    
                    os.unlink(tmp_path)
                    
                    if texto.strip():
                        return texto
            except Exception as e:
                print(f"EasyOCR falhou: {e}")
        
        # Método 2: Tesseract
        if PYTESSERACT_AVAILABLE and PIL_AVAILABLE:
            try:
                image = Image.open(io.BytesIO(image_data))
                texto = pytesseract.image_to_string(image, lang='por')
                
                if texto.strip():
                    return texto
            except Exception as e:
                print(f"Tesseract falhou: {e}")
        
        return texto
    
    def extrair_texto_pdf(self, pdf_data: bytes) -> str:
        """
        Extrai texto de um PDF
        Tenta pdfplumber primeiro, depois PyPDF2, depois OCR em imagens
        """
        texto = ""
        
        # Salva PDF temporariamente
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp.write(pdf_data)
            tmp_path = tmp.name
        
        try:
            # Método 1: pdfplumber (melhor para tabelas)
            if PDFPLUMBER_AVAILABLE:
                try:
                    with pdfplumber.open(tmp_path) as pdf:
                        for page in pdf.pages:
                            page_text = page.extract_text() or ""
                            texto += page_text + "\n"
                    
                    if texto.strip():
                        return texto.strip()
                except Exception as e:
                    print(f"pdfplumber falhou: {e}")
            
            # Método 2: PyPDF2
            if PYPDF2_AVAILABLE:
                try:
                    reader = PdfReader(tmp_path)
                    for page in reader.pages:
                        page_text = page.extract_text() or ""
                        texto += page_text + "\n"
                    
                    if texto.strip():
                        return texto.strip()
                except Exception as e:
                    print(f"PyPDF2 falhou: {e}")
            
            # Método 3: Converte PDF para imagem e usa OCR
            if PDF2IMAGE_AVAILABLE:
                try:
                    images = pdf2image.convert_from_path(tmp_path)
                    for img in images:
                        # Converte para bytes
                        img_bytes = io.BytesIO()
                        img.save(img_bytes, format='JPEG')
                        img_bytes.seek(0)
                        
                        page_text = self.extrair_texto_imagem(img_bytes.read())
                        texto += page_text + "\n"
                    
                    if texto.strip():
                        return texto.strip()
                except Exception as e:
                    print(f"pdf2image OCR falhou: {e}")
        
        finally:
            try:
                os.unlink(tmp_path)
            except:
                pass
        
        return texto
    
    def extrair_dados_comprovante(self, texto: str) -> Dict:
        """
        Extrai dados estruturados de um comprovante a partir do texto OCR
        """
        dados = {
            'valor': None,
            'data': None,
            'tipo': None,
            'destinatario': None,
            'descricao': None
        }
        
        texto_lower = texto.lower()
        
        # Extrai valor
        padroes_valor = [
            r'R\$\s*([\d.,]+)',
            r'Valor:?\s*R?\$?\s*([\d.,]+)',
            r'VALOR:?\s*R?\$?\s*([\d.,]+)',
            r'Total:?\s*R?\$?\s*([\d.,]+)',
            r'(\d{1,3}(?:\.\d{3})*,\d{2})',
        ]
        for padrao in padroes_valor:
            match = re.search(padrao, texto, re.IGNORECASE)
            if match:
                valor_str = match.group(1)
                valor_str = valor_str.replace('.', '').replace(',', '.')
                try:
                    dados['valor'] = float(valor_str)
                    break
                except:
                    pass
        
        # Extrai data
        padroes_data = [
            r'(\d{2}/\d{2}/\d{4})',
            r'(\d{2}/\d{2}/\d{2})',
            r'(\d{2}-\d{2}-\d{4})',
            r'Data:?\s*(\d{2}/\d{2}/\d{4})',
        ]
        for padrao in padroes_data:
            match = re.search(padrao, texto)
            if match:
                dados['data'] = match.group(1)
                break
        
        # Detecta tipo
        if 'pix' in texto_lower:
            dados['tipo'] = 'pix'
        elif 'boleto' in texto_lower:
            dados['tipo'] = 'boleto'
        elif 'transfer' in texto_lower:
            dados['tipo'] = 'transferencia'
        elif 'cartão' in texto_lower or 'cartao' in texto_lower:
            dados['tipo'] = 'cartao'
        elif 'recibo' in texto_lower:
            dados['tipo'] = 'recibo'
        
        # Extrai destinatário
        padroes_dest = [
            r'Para:?\s*([^\n]+)',
            r'Destinat[aá]rio:?\s*([^\n]+)',
            r'Favorecido:?\s*([^\n]+)',
            r'Nome:?\s*([^\n]+)',
            r'Recebedor:?\s*([^\n]+)',
        ]
        for padrao in padroes_dest:
            match = re.search(padrao, texto, re.IGNORECASE)
            if match:
                dados['destinatario'] = match.group(1).strip()[:100]
                break
        
        return dados
    
    def extrair_dados_boleto(self, texto: str) -> Dict:
        """
        Extrai dados de um boleto a partir do texto OCR
        """
        dados = {
            'valor': None,
            'vencimento': None,
            'codigo_barras': None,
            'linha_digitavel': None,
            'beneficiario': None,
            'pagador': None,
            'tipo': 'boleto'
        }
        
        # Extrai valor
        padroes_valor = [
            r'Valor\s*(?:do\s*)?(?:documento|boleto)?:?\s*R?\$?\s*([\d.,]+)',
            r'R\$\s*([\d.,]+)',
            r'(\d{1,3}(?:\.\d{3})*,\d{2})',
        ]
        for padrao in padroes_valor:
            match = re.search(padrao, texto, re.IGNORECASE)
            if match:
                valor_str = match.group(1)
                valor_str = valor_str.replace('.', '').replace(',', '.')
                try:
                    dados['valor'] = float(valor_str)
                    break
                except:
                    pass
        
        # Extrai vencimento
        padroes_venc = [
            r'Vencimento:?\s*(\d{2}/\d{2}/\d{4})',
            r'Data\s*(?:de\s*)?vencimento:?\s*(\d{2}/\d{2}/\d{4})',
            r'Venc(?:to)?\.?:?\s*(\d{2}/\d{2}/\d{4})',
        ]
        for padrao in padroes_venc:
            match = re.search(padrao, texto, re.IGNORECASE)
            if match:
                dados['vencimento'] = match.group(1)
                break
        
        # Extrai código de barras (47-48 dígitos)
        match = re.search(r'(\d{5}\.\d{5}\s*\d{5}\.\d{6}\s*\d{5}\.\d{6}\s*\d\s*\d{14})', texto)
        if match:
            dados['linha_digitavel'] = match.group(1).replace(' ', '')
        else:
            # Tenta formato sem pontos
            match = re.search(r'(\d{47,48})', texto.replace(' ', ''))
            if match:
                dados['codigo_barras'] = match.group(1)
        
        # Extrai beneficiário
        padroes_benef = [
            r'Benefici[aá]rio:?\s*([^\n]+)',
            r'Cedente:?\s*([^\n]+)',
            r'Favorecido:?\s*([^\n]+)',
        ]
        for padrao in padroes_benef:
            match = re.search(padrao, texto, re.IGNORECASE)
            if match:
                dados['beneficiario'] = match.group(1).strip()[:100]
                break
        
        # Detecta tipo específico de boleto
        texto_lower = texto.lower()
        if 'darf' in texto_lower:
            dados['tipo'] = 'darf'
        elif 'gps' in texto_lower:
            dados['tipo'] = 'gps'
        elif 'das' in texto_lower:
            dados['tipo'] = 'das'
        elif 'iptu' in texto_lower:
            dados['tipo'] = 'iptu'
        elif 'ipva' in texto_lower:
            dados['tipo'] = 'ipva'
        
        return dados
    
    def get_status(self) -> str:
        """Retorna status das bibliotecas disponíveis"""
        status_lines = ["🔍 *Status das Bibliotecas de OCR:*\n"]
        
        libs = [
            ('EasyOCR', EASYOCR_AVAILABLE, 'OCR para imagens (português)'),
            ('Tesseract', PYTESSERACT_AVAILABLE, 'OCR alternativo'),
            ('pdfplumber', PDFPLUMBER_AVAILABLE, 'Extração de texto de PDF'),
            ('PyPDF2', PYPDF2_AVAILABLE, 'Leitura de PDF'),
            ('pdf2image', PDF2IMAGE_AVAILABLE, 'Converte PDF para imagem'),
            ('Pillow', PIL_AVAILABLE, 'Processamento de imagem'),
        ]
        
        for nome, disponivel, desc in libs:
            icone = "✅" if disponivel else "❌"
            status_lines.append(f"{icone} *{nome}* - {desc}")
        
        status_lines.append("\n💡 Instale bibliotecas faltantes com:")
        status_lines.append("`pip install easyocr pdfplumber PyPDF2 pillow`")
        
        return '\n'.join(status_lines)


# Singleton
_ocr_engine: Optional[OCREngine] = None

def get_ocr_engine() -> OCREngine:
    """Retorna instância singleton do OCR Engine"""
    global _ocr_engine
    if _ocr_engine is None:
        _ocr_engine = OCREngine()
    return _ocr_engine
