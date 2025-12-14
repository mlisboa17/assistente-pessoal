"""
🔍 DEBUG - Análise do conteúdo do PDF Itaú PJ
Verifica exatamente o que está sendo extraído
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    import pdfplumber
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    print("❌ pdfplumber não instalado")
    sys.exit(1)

def analisar_pdf_itau():
    """Analisa o conteúdo do PDF Itaú PJ"""

    arquivo_path = r"c:\Users\gabri\Downloads\Extratos\Itau_Pj.pdf"

    if not os.path.exists(arquivo_path):
        print(f"❌ Arquivo não encontrado: {arquivo_path}")
        return

    print("🔍 ANALISANDO CONTEÚDO DO PDF ITAÚ PJ")
    print("=" * 60)

    try:
        pdf = pdfplumber.open(arquivo_path)
        print(f"📄 Páginas encontradas: {len(pdf.pages)}")

        for i, page in enumerate(pdf.pages):
            print(f"\n📄 PÁGINA {i+1}")
            print("-" * 40)

            texto = page.extract_text()
            if texto:
                print("TEXTO EXTRAÍDO:")
                print("-" * 30)
                print(texto)
                print()

                # Analisa linhas
                linhas = texto.split('\n')
                print(f"LINHAS ENCONTRADAS: {len(linhas)}")
                print("-" * 30)

                import re

                for j, linha in enumerate(linhas[:20]):  # Mostra primeiras 20 linhas
                    linha = linha.strip()
                    if linha:
                        print(f"Linha {j+1:2d}: {linha}")

                        # Testa a regex atual
                        match = re.search(r'(\d{2}/\d{2}/?\d{4}?)\s+(.+?)\s+([\d.,]+-?)\s+([\d.,]+)', linha)
                        if match:
                            data, desc, valor_str, saldo_str = match.groups()
                            print(f"         → MATCH: Data={data}, Desc='{desc}', Valor={valor_str}, Saldo={saldo_str}")

                print("\n" + "="*60)

        pdf.close()

    except Exception as e:
        print(f"❌ Erro ao analisar PDF: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analisar_pdf_itau()