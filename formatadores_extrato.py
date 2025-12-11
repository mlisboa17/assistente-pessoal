"""
Funções auxiliares para formatação de extratos bancários
Adicionar ao api_server.py
"""

def _formatar_extrato_bancario(resultado, filename):
    """Formata resultado de extração de extrato bancário"""
    transacoes_novas = resultado.get('transacoes_novas', 0)
    transacoes_duplicadas = resultado.get('transacoes_duplicadas', 0)
    layout_reconhecido = resultado.get('layout_reconhecido', False)
    banco = resultado.get('banco_detectado', 'Desconhecido')
    nome_layout = resultado.get('nome_layout', '')
    
    msg = f"✅ *Extrato Processado com Sucesso!*\n\n"
    msg += f"📄 Arquivo: `{filename}`\n"
    msg += f"🏦 Banco: *{banco}*\n"
    
    if layout_reconhecido:
        msg += f"✨ Layout: _{nome_layout}_\n"
    else:
        msg += f"🆕 Layout: _Novo (aprendido)_\n"
    
    msg += f"\n📊 *Transações:*\n"
    msg += f"   • Novas: *{transacoes_novas}*\n"
    
    if transacoes_duplicadas > 0:
        msg += f"   • Duplicadas (ignoradas): {transacoes_duplicadas}\n"
    
    # Amostra de transações
    if 'transacoes_sample' in resultado:
        msg += f"\n💰 *Últimas 5 transações:*\n"
        for t in resultado['transacoes_sample'][:5]:
            tipo_simbolo = "+" if t.get('tipo_movimento') == 'C' else "-"
            msg += f"\n{tipo_simbolo} R$ {t.get('valor', 0):,.2f}\n"
            msg += f"   {t.get('data_movimento')} | {t.get('descricao_original', '')[:40]}\n"
    
    msg += f"\n\n✅ Extrato salvo no banco de dados!"
    msg += f"\n\n_Para ver relatórios, digite:_\n`financas resumo`"
    
    return msg


def _formatar_layout_desconhecido(resultado, filename):
    """Formata resultado quando layout não é reconhecido"""
    colunas = resultado.get('colunas_detectadas', [])
    fingerprint = resultado.get('fingerprint', '')
    
    msg = f"🆕 *Layout Novo Detectado!*\n\n"
    msg += f"📄 Arquivo: `{filename}`\n"
    msg += f"🔑 Fingerprint: `{fingerprint[:16]}...`\n"
    msg += f"📋 Colunas encontradas: {len(colunas)}\n\n"
    
    msg += f"💡 *O que fazer?*\n\n"
    msg += f"Este é um novo tipo de extrato que ainda não conheço.\n\n"
    msg += f"Opções:\n"
    msg += f"1️⃣ Envie mais detalhes sobre o banco\n"
    msg += f"2️⃣ O sistema aprenderá automaticamente\n"
    msg += f"3️⃣ Digite `mapear extrato` para configurar manualmente\n\n"
    msg += f"_Amostra das colunas:_\n"
    
    for i, col in enumerate(colunas[:10], 1):
        msg += f"{i}. `{col[:30]}`\n"
    
    if len(colunas) > 10:
        msg += f"... e mais {len(colunas) - 10} colunas\n"
    
    return msg


def _formatar_tarifas(tarifas):
    """Formata lista de tarifas bancárias"""
    total = sum(t['valor'] for t in tarifas)
    
    msg = f"💳 *TARIFAS BANCÁRIAS*\n"
    msg += f"{'='*40}\n\n"
    msg += f"Total encontrado: *{len(tarifas)} tarifa(s)*\n"
    msg += f"Valor total: *R$ {total:,.2f}*\n\n"
    
    # Agrupar por código
    por_codigo = {}
    for t in tarifas:
        cod = t['codigo']
        if cod not in por_codigo:
            por_codigo[cod] = []
        por_codigo[cod].append(t)
    
    for codigo, lista in sorted(por_codigo.items()):
        classif = lista[0]['classificacao']
        subtotal = sum(t['valor'] for t in lista)
        
        msg += f"\n🔹 *{classif['nome']}*\n"
        msg += f"   Código: {codigo}\n"
        msg += f"   {len(lista)} ocorrência(s) = R$ {subtotal:,.2f}\n"
        
        if classif['observacoes']:
            msg += f"   ℹ️ _{classif['observacoes'][:60]}_\n"
        
        # Mostrar valores individuais
        for t in lista[:3]:  # Máximo 3
            msg += f"   • R$ {t['valor']:,.2f}\n"
        
        if len(lista) > 3:
            msg += f"   ... e mais {len(lista) - 3}\n"
    
    msg += f"\n{'='*40}\n"
    msg += f"💰 *TOTAL: R$ {total:,.2f}*\n\n"
    msg += f"💡 _Dica: PIX é gratuito para PF!_"
    
    return msg
