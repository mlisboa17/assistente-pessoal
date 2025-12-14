"""
🛠️ MÓDULO 3: LÓGICA DE DECISÃO E NORMALIZAÇÃO AVANÇADA
Implementa a automação inteligente para transformação de dados bancários

Características principais:
1. ROTA DE AUTOMAÇÃO: Aplica regras salvas automaticamente
2. ROTA DE INTERVENÇÃO: Interface para novos layouts
3. UNIFICAÇÃO CRÉDITO/DÉBITO: Lógica robusta para diferentes formatos
4. VALIDAÇÃO DE DADOS: Garante qualidade da normalização
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple, Optional, Union
from dataclasses import dataclass
import re
from datetime import datetime
import json


# ==========================================
# ESTRUTURAS DE MAPEAMENTO
# ==========================================

@dataclass
class RegrasNormalizacao:
    """Define regras específicas para normalização de dados"""
    
    # Mapeamento de colunas
    mapeamento_colunas: Dict[str, str]
    
    # Regras para unificação de Crédito/Débito
    estrategia_credito_debito: str = "coluna_unica"  # "coluna_unica", "colunas_separadas", "sinal_valor"
    coluna_credito: Optional[str] = None
    coluna_debito: Optional[str] = None
    coluna_tipo: Optional[str] = None
    valores_credito: List[str] = None
    valores_debito: List[str] = None
    
    # Regras de formatação
    formato_data: str = "dd/mm/yyyy"
    separador_decimal: str = ","
    simbolo_moeda: str = "R$"
    
    # Validações específicas
    validar_saldo: bool = True
    aceitar_valores_zero: bool = False


class ProcessadorAvancado:
    """Processador inteligente para normalização de extratos bancários"""
    
    def __init__(self):
        self.debug_mode = True
    
    def aplicar_mapeamento_completo(self, df_bruto: pd.DataFrame, 
                                  regras: RegrasNormalizacao) -> pd.DataFrame:
        """
        🎯 FUNÇÃO PRINCIPAL: Aplica mapeamento completo seguindo o contrato
        
        Esta é a função que unifica todo o processo de normalização
        """
        if self.debug_mode:
            print(f"📊 Iniciando normalização de {len(df_bruto)} registros...")
        
        # 1. Renomear colunas básicas
        df_mapeado = self._renomear_colunas(df_bruto, regras.mapeamento_colunas)
        
        # 2. Unificar Crédito/Débito (LÓGICA CRÍTICA)
        df_unificado = self._unificar_credito_debito(df_mapeado, regras)
        
        # 3. Normalizar tipos de dados
        df_normalizado = self._normalizar_tipos_dados(df_unificado, regras)
        
        # 4. Validar dados finais
        df_validado = self._validar_dados_finais(df_normalizado, regras)
        
        if self.debug_mode:
            print(f"✅ Normalização concluída: {len(df_validado)} registros válidos")
        
        return df_validado
    
    def _renomear_colunas(self, df: pd.DataFrame, mapeamento: Dict[str, str]) -> pd.DataFrame:
        """Renomeia colunas conforme mapeamento definido"""
        df_resultado = df.copy()
        
        # Aplica mapeamento direto
        colunas_renomeadas = {}
        for col_original, col_destino in mapeamento.items():
            if col_original in df_resultado.columns:
                colunas_renomeadas[col_original] = col_destino
        
        df_resultado = df_resultado.rename(columns=colunas_renomeadas)
        
        if self.debug_mode:
            print(f"📋 Colunas renomeadas: {list(colunas_renomeadas.keys())} → {list(colunas_renomeadas.values())}")
        
        return df_resultado
    
    def _unificar_credito_debito(self, df: pd.DataFrame, regras: RegrasNormalizacao) -> pd.DataFrame:
        """
        🎯 LÓGICA CRÍTICA: Unificação de Crédito/Débito
        
        Implementa as 4 estratégias mais comuns de extratos bancários brasileiros:
        1. COLUNA_UNICA: Valor positivo/negativo em uma coluna + tipo em outra
        2. COLUNAS_SEPARADAS: Uma coluna para crédito, outra para débito
        3. SINAL_VALOR: Apenas o sinal do valor indica crédito/débito
        4. TEXTO_DESCRITIVO: Inferência por palavras-chave na descrição
        """
        
        df_resultado = df.copy()
        
        if self.debug_mode:
            print(f"🔄 Aplicando estratégia: {regras.estrategia_credito_debito}")
        
        if regras.estrategia_credito_debito == "coluna_unica":
            df_resultado = self._estrategia_coluna_unica(df_resultado, regras)
            
        elif regras.estrategia_credito_debito == "colunas_separadas":
            df_resultado = self._estrategia_colunas_separadas(df_resultado, regras)
            
        elif regras.estrategia_credito_debito == "sinal_valor":
            df_resultado = self._estrategia_sinal_valor(df_resultado, regras)
            
        else:  # Fallback para detecção automática
            df_resultado = self._estrategia_auto_detectar(df_resultado, regras)
        
        return df_resultado
    
    def _estrategia_coluna_unica(self, df: pd.DataFrame, regras: RegrasNormalizacao) -> pd.DataFrame:
        """
        Estratégia 1: Uma coluna de valor + uma coluna de tipo
        Exemplo: Valor=150.00, Tipo='D' ou 'Débito'
        """
        df_resultado = df.copy()
        
        # Normaliza valores para positivo
        if 'valor' in df_resultado.columns:
            df_resultado['valor'] = df_resultado['valor'].apply(lambda x: abs(self._extrair_numero(x)))
        
        # Normaliza tipo de movimento
        if regras.coluna_tipo and regras.coluna_tipo in df_resultado.columns:
            df_resultado['tipo_movimento'] = df_resultado[regras.coluna_tipo].apply(
                lambda x: self._normalizar_tipo_movimento(x, regras.valores_credito, regras.valores_debito)
            )
        elif 'tipo_movimento' in df_resultado.columns:
            df_resultado['tipo_movimento'] = df_resultado['tipo_movimento'].apply(
                lambda x: self._normalizar_tipo_movimento(x, regras.valores_credito, regras.valores_debito)
            )
        
        return df_resultado
    
    def _estrategia_colunas_separadas(self, df: pd.DataFrame, regras: RegrasNormalizacao) -> pd.DataFrame:
        """
        Estratégia 2: Coluna de Crédito + Coluna de Débito separadas
        Exemplo: Credito=150.00, Debito=NaN ou Credito=NaN, Debito=75.50
        """
        df_resultado = df.copy()
        
        col_cred = regras.coluna_credito or 'credito'
        col_deb = regras.coluna_debito or 'debito'
        
        # Cria colunas unificadas
        valores_unificados = []
        tipos_movimento = []
        
        for _, row in df_resultado.iterrows():
            valor_credito = self._extrair_numero(row.get(col_cred, 0))
            valor_debito = self._extrair_numero(row.get(col_deb, 0))
            
            if valor_credito > 0:
                valores_unificados.append(valor_credito)
                tipos_movimento.append('C')
            elif valor_debito > 0:
                valores_unificados.append(valor_debito)
                tipos_movimento.append('D')
            else:
                valores_unificados.append(0)
                tipos_movimento.append('C')  # Default
        
        df_resultado['valor'] = valores_unificados
        df_resultado['tipo_movimento'] = tipos_movimento
        
        if self.debug_mode:
            creditos = sum(1 for t in tipos_movimento if t == 'C')
            debitos = sum(1 for t in tipos_movimento if t == 'D')
            print(f"📊 Colunas separadas unificadas: {creditos} créditos, {debitos} débitos")
        
        return df_resultado
    
    def _estrategia_sinal_valor(self, df: pd.DataFrame, regras: RegrasNormalizacao) -> pd.DataFrame:
        """
        Estratégia 3: Sinal do valor indica crédito (+) ou débito (-)
        Exemplo: Valor=+150.00 (crédito) ou Valor=-75.50 (débito)
        """
        df_resultado = df.copy()
        
        if 'valor' in df_resultado.columns:
            valores_originais = df_resultado['valor'].apply(self._extrair_numero_com_sinal)
            
            # Separa valor absoluto e tipo
            df_resultado['valor'] = valores_originais.apply(abs)
            df_resultado['tipo_movimento'] = valores_originais.apply(
                lambda x: 'C' if x >= 0 else 'D'
            )
        
        return df_resultado
    
    def _estrategia_auto_detectar(self, df: pd.DataFrame, regras: RegrasNormalizacao) -> pd.DataFrame:
        """
        Estratégia 4: Auto-detecção baseada na estrutura dos dados
        Analisa as colunas disponíveis e aplica a melhor estratégia
        """
        if self.debug_mode:
            print("🔍 Auto-detectando estratégia de crédito/débito...")
        
        colunas = [col.lower() for col in df.columns]
        
        # Detecta se há colunas separadas de crédito/débito
        has_credito = any('credit' in col or 'entrada' in col or 'receita' in col for col in colunas)
        has_debito = any('debit' in col or 'saida' in col or 'despesa' in col for col in colunas)
        
        if has_credito and has_debito:
            if self.debug_mode:
                print("📋 Detectado: Colunas separadas")
            regras.estrategia_credito_debito = "colunas_separadas"
            return self._estrategia_colunas_separadas(df, regras)
        
        # Detecta se há uma coluna de tipo
        has_tipo = any('tipo' in col or 'operacao' in col or 'movement' in col for col in colunas)
        
        if has_tipo:
            if self.debug_mode:
                print("📋 Detectado: Coluna única com tipo")
            regras.estrategia_credito_debito = "coluna_unica"
            return self._estrategia_coluna_unica(df, regras)
        
        # Default: Sinal do valor
        if self.debug_mode:
            print("📋 Detectado: Sinal do valor")
        regras.estrategia_credito_debito = "sinal_valor"
        return self._estrategia_sinal_valor(df, regras)
    
    def _normalizar_tipos_dados(self, df: pd.DataFrame, regras: RegrasNormalizacao) -> pd.DataFrame:
        """Normaliza tipos de dados conforme o contrato"""
        df_resultado = df.copy()
        
        # Data movimento
        if 'data_movimento' in df_resultado.columns:
            df_resultado['data_movimento'] = df_resultado['data_movimento'].apply(
                lambda x: self._normalizar_data(x, regras.formato_data)
            )
        
        # Valor
        if 'valor' in df_resultado.columns:
            df_resultado['valor'] = df_resultado['valor'].apply(self._extrair_numero)
        
        # Saldo final
        if 'saldo_final_linha' in df_resultado.columns:
            df_resultado['saldo_final_linha'] = df_resultado['saldo_final_linha'].apply(self._extrair_numero)
        
        # Descrição original (limpa espaços)
        if 'descricao_original' in df_resultado.columns:
            df_resultado['descricao_original'] = df_resultado['descricao_original'].astype(str).str.strip()
        
        return df_resultado
    
    def _validar_dados_finais(self, df: pd.DataFrame, regras: RegrasNormalizacao) -> pd.DataFrame:
        """Valida e filtra dados finais"""
        df_resultado = df.copy()
        
        # Remove registros inválidos
        filtros = []
        
        # Filtra valores zero se não permitido
        if not regras.aceitar_valores_zero and 'valor' in df_resultado.columns:
            filtros.append(df_resultado['valor'] > 0)
        
        # Filtra datas inválidas
        if 'data_movimento' in df_resultado.columns:
            filtros.append(df_resultado['data_movimento'] != '')
        
        # Filtra descrições vazias
        if 'descricao_original' in df_resultado.columns:
            filtros.append(df_resultado['descricao_original'].str.len() > 0)
        
        # Aplica filtros
        if filtros:
            filtro_final = filtros[0]
            for f in filtros[1:]:
                filtro_final = filtro_final & f
            df_resultado = df_resultado[filtro_final].reset_index(drop=True)
        
        return df_resultado
    
    # ==========================================
    # FUNÇÕES AUXILIARES DE NORMALIZAÇÃO
    # ==========================================
    
    def _extrair_numero(self, valor: Any) -> float:
        """Extrai número de qualquer formato de texto"""
        if pd.isna(valor) or valor == '' or valor is None:
            return 0.0
        
        valor_str = str(valor).strip()
        
        # Remove símbolos de moeda
        valor_str = re.sub(r'[R$\s]', '', valor_str)
        
        # Substitui vírgula por ponto
        valor_str = valor_str.replace(',', '.')
        
        # Remove outros caracteres não numéricos, exceto ponto e hífen
        valor_str = re.sub(r'[^\d\.\-]', '', valor_str)
        
        try:
            return float(valor_str)
        except:
            return 0.0
    
    def _extrair_numero_com_sinal(self, valor: Any) -> float:
        """Extrai número preservando o sinal"""
        if pd.isna(valor) or valor == '' or valor is None:
            return 0.0
        
        valor_str = str(valor).strip()
        
        # Preserva o sinal
        negativo = '-' in valor_str or valor_str.startswith('(') and valor_str.endswith(')')
        
        # Extrai o número
        numero = abs(self._extrair_numero(valor))
        
        return -numero if negativo else numero
    
    def _normalizar_data(self, data: Any, formato: str) -> str:
        """Normaliza data para ISO 8601 (YYYY-MM-DD)"""
        if pd.isna(data) or data == '' or data is None:
            return ''
        
        data_str = str(data).strip()
        
        # Padrões de data
        padroes = [
            r'(\d{4})-(\d{2})-(\d{2})',  # 2024-12-09
            r'(\d{2})/(\d{2})/(\d{4})',  # 09/12/2024
            r'(\d{2})-(\d{2})-(\d{4})',  # 09-12-2024
            r'(\d{4})/(\d{2})/(\d{2})',  # 2024/12/09
        ]
        
        for padrao in padroes:
            match = re.search(padrao, data_str)
            if match:
                if len(match.group(1)) == 4:  # Ano primeiro
                    return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
                else:  # Dia primeiro
                    return f"{match.group(3)}-{match.group(2)}-{match.group(1)}"
        
        return data_str  # Retorna original se não conseguir converter
    
    def _normalizar_tipo_movimento(self, tipo: Any, valores_credito: List[str] = None, 
                                  valores_debito: List[str] = None) -> str:
        """Normaliza tipo de movimento para C ou D"""
        if pd.isna(tipo) or tipo == '':
            return 'C'  # Default
        
        tipo_str = str(tipo).lower().strip()
        
        # Usa valores personalizados se fornecidos
        if valores_credito:
            if any(val.lower() in tipo_str for val in valores_credito):
                return 'C'
        
        if valores_debito:
            if any(val.lower() in tipo_str for val in valores_debito):
                return 'D'
        
        # Padrões padrão
        credito_patterns = ['c', 'credit', 'credito', 'entrada', 'deposito', 'receita', 'recebimento']
        debito_patterns = ['d', 'debit', 'debito', 'saida', 'pagamento', 'despesa', 'saque']
        
        if any(pattern in tipo_str for pattern in credito_patterns):
            return 'C'
        elif any(pattern in tipo_str for pattern in debito_patterns):
            return 'D'
        else:
            return 'C'  # Default para crédito


# ==========================================
# INTERFACE DE MAPEAMENTO MANUAL
# ==========================================

class InterfaceMapeamento:
    """Interface para criar mapeamentos de layouts desconhecidos"""
    
    def __init__(self):
        self.campos_obrigatorios = [
            'data_movimento',
            'descricao_original', 
            'valor',
            'tipo_movimento'
        ]
        
        self.campos_opcionais = [
            'codigo_historico',
            'saldo_final_linha',
            'identificador_banco'
        ]
    
    def criar_mapeamento_interativo(self, df_sample: pd.DataFrame) -> Dict[str, Any]:
        """
        Cria interface interativa para mapear novo layout
        Retorna estrutura para interface web ou CLI
        """
        
        colunas_encontradas = list(df_sample.columns)
        
        # Analisa tipos de dados das colunas
        analise_colunas = {}
        for col in colunas_encontradas:
            analise_colunas[col] = {
                'tipo_detectado': str(df_sample[col].dtype),
                'valores_exemplo': df_sample[col].head(3).tolist(),
                'sugestao_mapeamento': self._sugerir_mapeamento_automatico(col, df_sample[col])
            }
        
        return {
            'colunas_encontradas': colunas_encontradas,
            'campos_obrigatorios': self.campos_obrigatorios,
            'campos_opcionais': self.campos_opcionais,
            'analise_colunas': analise_colunas,
            'estrategias_credito_debito': [
                'coluna_unica',
                'colunas_separadas', 
                'sinal_valor',
                'auto_detectar'
            ],
            'preview_dados': df_sample.head(5).to_dict('records')
        }
    
    def _sugerir_mapeamento_automatico(self, nome_coluna: str, serie: pd.Series) -> str:
        """Sugere mapeamento automático baseado no nome e conteúdo da coluna"""
        nome_lower = nome_coluna.lower()
        
        # Sugestões por nome da coluna
        if any(word in nome_lower for word in ['data', 'date']):
            return 'data_movimento'
        elif any(word in nome_lower for word in ['descr', 'hist', 'operacao']):
            return 'descricao_original'
        elif any(word in nome_lower for word in ['valor', 'value', 'amount']):
            return 'valor'
        elif any(word in nome_lower for word in ['tipo', 'type', 'operacao']):
            return 'tipo_movimento'
        elif any(word in nome_lower for word in ['saldo', 'balance']):
            return 'saldo_final_linha'
        elif any(word in nome_lower for word in ['codigo', 'code', 'id']):
            return 'codigo_historico'
        
        return 'nao_mapear'


# ==========================================
# TESTE DO MÓDULO 3
# ==========================================

def testar_logica_decisao():
    """Testa a lógica de decisão com diferentes cenários"""
    
    print("🛠️ TESTE DO MÓDULO 3 - LÓGICA DE DECISÃO")
    print("=" * 60)
    
    # Cenário 1: Coluna única com tipo
    print("\n📊 CENÁRIO 1: Coluna única + Tipo")
    dados1 = {
        'Data': ['2024-12-01', '2024-12-02', '2024-12-03'],
        'Descricao': ['Salário', 'Mercado', 'Uber'],
        'Valor': [5000.0, -250.5, -45.0],
        'Tipo': ['entrada', 'saida', 'saida'],
        'Saldo': [15000.0, 14749.5, 14704.5]
    }
    
    df1 = pd.DataFrame(dados1)
    
    regras1 = RegrasNormalizacao(
        mapeamento_colunas={
            'Data': 'data_movimento',
            'Descricao': 'descricao_original',
            'Valor': 'valor',
            'Tipo': 'tipo_movimento',
            'Saldo': 'saldo_final_linha'
        },
        estrategia_credito_debito="coluna_unica",
        valores_credito=['entrada', 'credito'],
        valores_debito=['saida', 'debito']
    )
    
    processador = ProcessadorAvancado()
    resultado1 = processador.aplicar_mapeamento_completo(df1, regras1)
    
    print("Resultado normalizado:")
    print(resultado1[['data_movimento', 'valor', 'tipo_movimento', 'descricao_original']].to_string())
    
    # Cenário 2: Colunas separadas
    print("\n📊 CENÁRIO 2: Colunas separadas")
    dados2 = {
        'Data': ['2024-12-01', '2024-12-02', '2024-12-03'],
        'Historico': ['Depósito PIX', 'Pagamento Boleto', 'Transferência'],
        'Credito': [1500.0, np.nan, np.nan],
        'Debito': [np.nan, 200.0, 75.5],
        'Saldo_Final': [10500.0, 10300.0, 10224.5]
    }
    
    df2 = pd.DataFrame(dados2)
    
    regras2 = RegrasNormalizacao(
        mapeamento_colunas={
            'Data': 'data_movimento',
            'Historico': 'descricao_original',
            'Saldo_Final': 'saldo_final_linha'
        },
        estrategia_credito_debito="colunas_separadas",
        coluna_credito='Credito',
        coluna_debito='Debito'
    )
    
    resultado2 = processador.aplicar_mapeamento_completo(df2, regras2)
    
    print("Resultado normalizado:")
    print(resultado2[['data_movimento', 'valor', 'tipo_movimento', 'descricao_original']].to_string())
    
    print("\n✅ TESTE DO MÓDULO 3 CONCLUÍDO!")


if __name__ == "__main__":
    testar_logica_decisao()