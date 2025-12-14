# Cole este código no final do api_server.py, ANTES do if __name__ == '__main__':

from formatadores_extrato import _formatar_extrato_bancario, _formatar_layout_desconhecido, _formatar_tarifas

@app.route('/process-extrato', methods=['POST'])
def process_extrato():
    """Processa extrato bancário PDF - Sistema Zero"""
    try:
        data = request.json
        file_base64 = data.get('file', '')
        filename = data.get('filename', 'extrato.pdf')
        user_id = data.get('user_id', 'whatsapp_user')
        senha = data.get('senha', None)  # Senha do PDF se necessário
        
        if not file_base64:
            return jsonify({
                'success': False,
                'response': '❌ Nenhum arquivo recebido.'
            }), 400
        
        if not extrator_bancario:
            return jsonify({
                'success': False,
                'response': '❌ Sistema de extração bancária não disponível.'
            }), 500
        
        # Decodifica e salva PDF temporariamente
        file_bytes = base64.b64decode(file_base64)
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            f.write(file_bytes)
            file_path = f.name
        
        try:
            # Processa extrato
            resultado = extrator_bancario.processar_extrato(file_path, senha_pdf=senha)
            
            if resultado['status'] == 'sucesso':
                return jsonify({
                    'success': True,
                    'response': _formatar_extrato_bancario(resultado, filename)
                })
            elif resultado['status'] == 'layout_desconhecido':
                return jsonify({
                    'success': True,
                    'response': _formatar_layout_desconhecido(resultado, filename)
                })
            elif resultado['status'] == 'senha_necessaria':
                return jsonify({
                    'success': False,
                    'response': f"🔒 PDF protegido por senha\n\nEnvie novamente com:\n`extrato senha:SUASENHA`"
                })
            else:
                return jsonify({
                    'success': False,
                    'response': f"❌ Erro: {resultado.get('mensagem', 'Erro desconhecido')}"
                })
        
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'response': f'❌ Erro ao processar extrato: {str(e)}'
        }), 500


@app.route('/process-tarifas', methods=['POST'])
def process_tarifas():
    """Analisa tarifas bancárias em um extrato"""
    try:
        data = request.json
        file_base64 = data.get('file', '')
        filename = data.get('filename', 'extrato.pdf')
        senha = data.get('senha', None)
        
        if not file_base64:
            return jsonify({
                'success': False,
                'response': '❌ Nenhum arquivo recebido.'
            }), 400
        
        if not tarifas_bancarias:
            return jsonify({
                'success': False,
                'response': '❌ Módulo de tarifas não disponível.'
            }), 500
        
        # Decodifica PDF
        file_bytes = base64.b64decode(file_base64)
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            f.write(file_bytes)
            file_path = f.name
        
        try:
            # Extrai tarifas usando tabula
            import tabula
            import pandas as pd
            import re
            
            dfs = tabula.read_pdf(file_path, pages='all', multiple_tables=True,
                                lattice=False, stream=True, guess=True, password=senha)
            
            if not dfs:
                return jsonify({
                    'success': False,
                    'response': '❌ Não foi possível extrair dados do PDF.'
                })
            
            df = pd.concat(dfs, ignore_index=True)
            
            # Procurar tarifas (códigos 9903, 13013, 13373)
            tarifas = []
            
            for idx, row in df.iterrows():
                valores = [str(v).strip() for v in row.values if pd.notna(v) and str(v).strip() and str(v) != 'nan']
                if valores:
                    linha = ' '.join(valores)
                    
                    # Procurar códigos de tarifa
                    match_codigo = re.search(r'\b(9903|13013|13373)(?:\.0)?\b', linha)
                    match_debito = re.search(r'([\d.,]+)\s*\([\-]\)', linha)
                    
                    if match_codigo and match_debito:
                        codigo = match_codigo.group(1)
                        valor_str = match_debito.group(1).replace('.', '').replace(',', '.')
                        
                        try:
                            valor = float(valor_str)
                            classificacao = tarifas_bancarias.classificar_tarifa(codigo)
                            
                            tarifas.append({
                                'codigo': codigo,
                                'valor': valor,
                                'classificacao': classificacao,
                                'linha': linha[:100]
                            })
                            
                            # Registrar no histórico
                            tarifas_bancarias.registrar_tarifa_historico(
                                codigo=codigo,
                                valor=valor,
                                data_transacao=datetime.now().strftime('%Y-%m-%d'),
                                linha_original=linha[:200]
                            )
                        except:
                            pass
            
            if tarifas:
                return jsonify({
                    'success': True,
                    'response': _formatar_tarifas(tarifas)
                })
            else:
                return jsonify({
                    'success': True,
                    'response': '✅ *Nenhuma tarifa bancária encontrada!*\n\nSeu extrato não possui cobranças de tarifas. 🎉'
                })
        
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'response': f'❌ Erro ao analisar tarifas: {str(e)}'
        }), 500
