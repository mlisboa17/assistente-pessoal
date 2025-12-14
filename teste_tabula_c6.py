import tabula
import pandas as pd
import numpy as np

def extrair_extrato_c6(caminho_pdf):
    """
    Tenta extrair dados tabulares de um PDF de extrato do C6 Bank
    usando tabula-py.
    """
    try:
        # A opção 'pages="all"' instrui o tabula a procurar tabelas
        # em todas as páginas do PDF.
        tabelas = tabula.read_pdf(
            caminho_pdf,
            pages="all",
            multiple_tables=True,  # Tentar detectar múltiplas tabelas por página
            stream=True,           # Modo 'stream' para tabelas sem bordas visíveis
            pandas_options={'header': None} # Sem cabeçalho automático
        )

        if not tabelas:
            print("❌ Tabula não encontrou nenhuma tabela.")
            return pd.DataFrame() # Retorna DataFrame vazio

        # Concatena todas as tabelas encontradas em um único DataFrame
        df_extrato = pd.concat(tabelas, ignore_index=True)

        # Retorna apenas as colunas relevantes que contêm as transações
        # (O número das colunas pode variar, requer ajuste manual após o primeiro teste)
        # Assumindo que as transações estão nas colunas 0, 1, 2, 3, 4 e 5 (data, descrição, valor...)
        # Você deve ajustar isso após inspecionar o df_extrato inicial
        df_final = df_extrato.iloc[:, 0:6].copy()

        # Limpeza inicial de linhas vazias ou de cabeçalho
        df_final.dropna(how='all', inplace=True)
        # Remove linhas onde a primeira coluna (data) não é um valor válido
        df_final = df_final[df_final.iloc[:, 0].astype(str).str.match(r'\d{2}/\d{2}/\d{4}') == True]

        return df_final.reset_index(drop=True)

    except Exception as e:
        print(f"❌ Erro durante a extração com Tabula: {e}")
        return pd.DataFrame()

# Seu arquivo PDF
arquivo = r"c:\Users\gabri\OneDrive\Área de Trabalho\Projetos\assistente-pessoal-main\test_extratos\c6_bank.pdf"

# Tentar a extração
df_dados_brutos = extrair_extrato_c6(arquivo)

if not df_dados_brutos.empty:
    print("✅ Extração bem-sucedida! Primeiras linhas do DataFrame:")
    print(df_dados_brutos.head())

    # Próximo passo: Passar este DataFrame para o seu módulo de Normalização

else:
    print("❌ Extração falhou ou retornou dados vazios. Verifique o arquivo.")