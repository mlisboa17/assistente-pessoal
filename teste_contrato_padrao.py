"""
🧪 TESTE DO SISTEMA ZERO - Contrato Padronizado
Demonstração completa do novo contrato de dados para conciliação bancária
"""

from modules.extratobancario_importacao_discere import SistemaExtratoZero, TransactionRecord
from modules.modulo3_logica_decisao import ProcessadorAvancado, RegrasNormalizacao, InterfaceMapeamento
import json

def criar_mapeamento_padronizado():
    """Cria mapeamento seguindo o contrato padronizado"""
    
    print("🎯 SISTEMA ZERO - CONTRATO PADRONIZADO")
    print("=" * 60)
    
    sistema = SistemaExtratoZero()
    
    # 1. Analisa o arquivo para criar mapeamento
    print("📋 Analisando layout do extrato...")
    info = sistema.criar_mapeamento_interativo('extrato_teste.csv')
    
    if 'erro' in info:
        print(f"❌ Erro: {info['erro']}")
        return
    
    print(f"Fingerprint: {info['fingerprint'][:16]}...")
    print(f"Colunas encontradas: {info['colunas_originais']}")
    
    # 2. Cria mapeamento seguindo o CONTRATO PADRONIZADO com MÓDULO 3
    print("\n🎯 MAPEAMENTO AVANÇADO COM MÓDULO 3:")
    
    # Interface inteligente de mapeamento
    interface = InterfaceMapeamento()
    df_sample = sistema.extrator.extrair_de_arquivo('extrato_teste.csv')
    analise_inteligente = interface.criar_mapeamento_interativo(df_sample.head(3))
    
    print("📊 Análise inteligente das colunas:")
    for col, analise in analise_inteligente['analise_colunas'].items():
        sugestao = analise['sugestao_mapeamento']
        print(f"  '{col}' → '{sugestao}' (exemplos: {analise['valores_exemplo']})")
    
    # Mapeamento otimizado com regras avançadas
    mapeamento_padronizado = {
        'Data': 'data_movimento',           # ISO 8601: YYYY-MM-DD
        'Descricao': 'descricao_original',  # Texto bruto do extrato
        'Valor': 'valor',                   # Valor sempre positivo
        'Tipo': 'tipo_movimento',           # "C" (Crédito) ou "D" (Débito)
        'Saldo': 'saldo_final_linha'        # Saldo após esta transação
    }
    
    # Define regras avançadas de normalização
    regras_avancadas = RegrasNormalizacao(
        mapeamento_colunas=mapeamento_padronizado,
        estrategia_credito_debito="coluna_unica",
        valores_credito=['entrada', 'credito', 'c', 'receita'],
        valores_debito=['saida', 'debito', 'd', 'despesa'],
        aceitar_valores_zero=False,
        validar_saldo=True
    )
    
    for col_original, campo_padrao in mapeamento_padronizado.items():
        print(f"  '{col_original}' → '{campo_padrao}'")
    
    # 3. Salva o mapeamento
    print("\n💾 Salvando mapeamento padronizado...")
    sucesso = sistema.salvar_mapeamento(
        info['fingerprint'],
        'CSV Bancário Padrão Brasil',
        'Sistema Bancário Brasileiro',
        mapeamento_padronizado
    )
    
    if not sucesso:
        print("❌ Erro ao salvar mapeamento")
        return
    
    # 4. Processa o extrato com o novo contrato
    print("\n🚀 Processando extrato com contrato padronizado...")
    resultado = sistema.processar_extrato('extrato_teste.csv')
    
    print(f"\n📊 RESULTADO DO PROCESSAMENTO:")
    print(f"Status: {resultado['status']}")
    print(f"Layout conhecido: {resultado['layout_conhecido']}")
    print(f"Transações encontradas: {resultado['transacoes_encontradas']}")
    print(f"Transações novas: {resultado['transacoes_novas']}")
    print(f"Transações duplicadas: {resultado['transacoes_duplicadas']}")
    
    # 5. Mostra as transações no formato JSON padrão
    if resultado['dados']:
        print(f"\n📋 EXEMPLO DE TRANSAÇÃO (Formato JSON Padronizado):")
        primeira_transacao = resultado['dados'][0]
        print(json.dumps(primeira_transacao, indent=2, ensure_ascii=False))
        
        print(f"\n📝 TODAS AS TRANSAÇÕES:")
        for i, transacao in enumerate(resultado['dados'], 1):
            print(f"\n{i}. Transação:")
            print(f"   ID Hash: {transacao['id_hash_unico'][:16]}...")
            print(f"   Data: {transacao['data_movimento']}")
            print(f"   Valor: R$ {transacao['valor']:.2f}")
            print(f"   Tipo: {'Crédito' if transacao['tipo_movimento'] == 'C' else 'Débito'}")
            print(f"   Descrição: {transacao['descricao_original']}")
            if transacao.get('saldo_final_linha'):
                print(f"   Saldo Final: R$ {transacao['saldo_final_linha']:.2f}")
    
    # 6. Demonstra verificação de duplicidade
    print(f"\n🔍 TESTE DE DUPLICIDADE:")
    print("Processando o mesmo arquivo novamente...")
    resultado2 = sistema.processar_extrato('extrato_teste.csv')
    print(f"Transações novas na 2ª execução: {resultado2['transacoes_novas']}")
    print(f"Transações duplicadas na 2ª execução: {resultado2['transacoes_duplicadas']}")
    
    print(f"\n✅ SISTEMA ZERO FUNCIONANDO COM CONTRATO PADRONIZADO!")
    print("=" * 60)

def exemplo_json_padrao():
    """Mostra exemplo do JSON no formato do contrato"""
    
    print("\n📄 EXEMPLO DO CONTRATO DE DADOS (JSON):")
    print("=" * 50)
    
    exemplo_transacoes = [
        {
            "id_hash_unico": "b574a38f7d2c8e9a1b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b",
            "data_movimento": "2025-12-05",
            "valor": 1250.00,
            "tipo_movimento": "C",
            "descricao_original": "Transferência Recebida - PIX João Silva",
            "codigo_historico": "PIX",
            "saldo_final_linha": 15250.00,
            "identificador_banco": "202512050012A"
        },
        {
            "id_hash_unico": "e14c99a0f2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9",
            "data_movimento": "2025-12-05",
            "valor": 75.30,
            "tipo_movimento": "D",
            "descricao_original": "Pagamento de Boleto - Fornecedor X",
            "codigo_historico": "PGTO",
            "saldo_final_linha": 15174.70,
            "identificador_banco": "202512050013B"
        }
    ]
    
    print(json.dumps(exemplo_transacoes, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    criar_mapeamento_padronizado()
    exemplo_json_padrao()