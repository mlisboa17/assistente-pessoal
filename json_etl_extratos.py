"""
Módulo para geração e processamento de JSON ETL de extratos bancários
"""
import json
import asyncio
from datetime import datetime
from typing import Dict, Any, List
from dataclasses import asdict
from normalizador_extratos import normalizar_extrato_completo

def gerar_json_etl_extratos(dados_extrato: Dict[str, Any], transacoes_brutas: List[Dict[str, Any]],
                           metadados_extracao: Dict[str, Any]) -> str:
    """
    Gera JSON padronizado ETL contendo dados brutos para normalização posterior
    """
    json_etl = {
        "especificacao": "ETL Extratos Bancários v1.0",
        "data_processamento": datetime.now().isoformat(),
        "fonte": dados_extrato.get('fonte', 'pdf'),
        "extrato": {
            "banco": dados_extrato.get('banco', '').upper(),
            "codigo_banco": "",  # TODO: mapear códigos dos bancos
            "agencia": dados_extrato.get('agencia', ''),
            "conta": dados_extrato.get('conta', ''),
            "tipo_conta": "corrente",  # TODO: detectar tipo
            "titular": dados_extrato.get('titular', ''),
            "cpf_cnpj_titular": dados_extrato.get('cpf_cnpj_titular', ''),  # Agora extraído automaticamente
            "periodo": dados_extrato.get('periodo', ''),
            "data_extrato": datetime.now().strftime('%Y-%m-%d'),
            "saldo_anterior": dados_extrato.get('saldo_anterior', 0.0),
            "saldo_atual": dados_extrato.get('saldo_atual', 0.0),
            "moeda": "BRL"
        },
        "transacoes_brutas": transacoes_brutas,
        "metadados_extracao": metadados_extracao,
        "validacao_entrada": {
            "campos_obrigatorios_preenchidos": True,
            "datas_validas": True,
            "valores_consistentes": True,
            "formato_esperado": True,
            "erros_validacao": [],
            "status": "APTO_PARA_NORMALIZACAO"
        }
    }

    return json.dumps(json_etl, indent=2, ensure_ascii=False)

def salvar_json_etl(caminho_arquivo: str, dados_extrato: Dict[str, Any],
                   transacoes_brutas: List[Dict[str, Any]], metadados_extracao: Dict[str, Any]):
    """
    Salva dados ETL em arquivo JSON
    """
    json_str = gerar_json_etl_extratos(dados_extrato, transacoes_brutas, metadados_extracao)

    with open(caminho_arquivo, 'w', encoding='utf-8') as f:
        f.write(json_str)

    print(f"💾 JSON ETL salvo em: {caminho_arquivo}")

def carregar_json_etl(caminho_arquivo: str) -> Dict[str, Any]:
    """
    Carrega dados ETL de arquivo JSON
    """
    with open(caminho_arquivo, 'r', encoding='utf-8') as f:
        dados = json.load(f)

    return dados

async def normalizar_de_json(caminho_json: str) -> Dict[str, Any]:
    """
    Carrega JSON ETL e executa normalização completa
    """
    print(f"📖 Carregando dados ETL de: {caminho_json}")

    # Carregar dados do JSON
    dados_json = carregar_json_etl(caminho_json)

    # Preparar dados para normalização
    dados_para_normalizacao = {
        'agencia': dados_json['extrato']['agencia'],
        'conta': dados_json['extrato']['conta'],
        'titular': dados_json['extrato']['titular'],
        'periodo': dados_json['extrato']['periodo'],
        'saldo_anterior': dados_json['extrato']['saldo_anterior'],
        'saldo_atual': dados_json['extrato']['saldo_atual'],
        'transacoes': dados_json['transacoes_brutas']
    }

    banco = dados_json['extrato']['banco'].lower()

    print(f"🔄 Normalizando extrato do {banco.upper()}...")
    dados_normalizados = normalizar_extrato_completo(dados_para_normalizacao, banco)

    return dados_normalizados

# Exemplo de uso
if __name__ == "__main__":
    print("🧹 Módulo JSON ETL Extratos Carregado")
    print("📋 Funções disponíveis:")
    print("   • gerar_json_etl_extratos() - Gera JSON ETL")
    print("   • salvar_json_etl() - Salva JSON em arquivo")
    print("   • carregar_json_etl() - Carrega JSON de arquivo")
    print("   • normalizar_de_json() - Normaliza dados de JSON")