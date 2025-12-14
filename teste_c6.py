#!/usr/bin/env python3
"""
Teste específico do PDF c6_bank.pdf com senha
"""
import sys
import os
import asyncio

# Adiciona o diretório atual ao path para importar módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    import pdfplumber
    from dataclasses import asdict
    from modules.extratos import ExtratosModule
except ImportError as e:
    print(f"Erro ao importar: {e}")
    sys.exit(1)

async def testar_c6_pdf():
    arquivo_path = r"c:\Users\gabri\OneDrive\Área de Trabalho\Projetos\assistente-pessoal-main\test_extratos\c6_bank.pdf"
    senha = "024296"

    print(f"🔍 Testando arquivo: {arquivo_path}")
    print(f"🔒 Usando senha: {senha}")

    if not os.path.exists(arquivo_path):
        print("❌ Arquivo não encontrado!")
        return

    try:
        # Tenta abrir com senha
        print("📖 Tentando abrir PDF com senha...")
        pdf = pdfplumber.open(arquivo_path, password=senha)

        print("✅ PDF aberto com sucesso!")

        # Extrai texto
        texto = ""
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                texto += page_text + "\n"

        pdf.close()

        print(f"📄 Texto extraído ({len(texto)} caracteres)")
        print("-" * 50)
        # Mostra mais texto para ver se há saídas
        print(texto[:1000] + "..." if len(texto) > 1000 else texto)

        # Testa processamento
        print("\n🔄 Testando processamento...")
        extratos = ExtratosModule()

        anexo_simulado = {
            'file_name': 'c6_bank.pdf',
            'file_path': arquivo_path,
            'tipo': 'PDF'
        }

        resultado = await extratos._processar_extrato_attachment(anexo_simulado, "teste", senha)

        if resultado:
            print("✅ Processamento bem-sucedido!")
            print("📊 RESULTADO:")
            print(resultado)

            # Pergunta se quer salvar
            salvar = input("\n💾 Deseja salvar este extrato no sistema? (s/n): ").lower().strip()
            if salvar == 's' or salvar == 'sim':
                # Os dados estão armazenados temporariamente no módulo
                if hasattr(extratos, '_dados_temp') and extratos._dados_temp:
                    sucesso = await salvar_extrato_c6(extratos._dados_temp, "teste_user", arquivo_path)
                    if sucesso:
                        print("✅ Extrato do C6 salvo com sucesso no sistema!")
                        # Limpa dados temporários
                        extratos._dados_temp = None
                    else:
                        print("❌ Erro ao salvar extrato")
                else:
                    print("❌ Dados temporários não encontrados. O processamento pode ter falhado.")
        else:
            print("❌ Falha no processamento")

    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

async def salvar_extrato_c6(dados, user_id, arquivo_path):
    """Salva o extrato do C6 no sistema"""
    try:
        from modules.extratos import ExtratosModule, ExtratoBancario
        from uuid import uuid4
        from datetime import datetime

        # Cria instância do módulo
        extratos = ExtratosModule()

        # Cria objeto extrato
        extrato = ExtratoBancario(
            id=str(uuid4())[:8],
            banco=dados.get('banco', 'C6'),
            agencia=dados.get('agencia', ''),
            conta=dados.get('conta', ''),
            periodo=dados.get('periodo', ''),
            saldo_anterior=dados.get('saldo_anterior', 0.0),
            saldo_atual=dados.get('saldo_atual', 0.0),
            transacoes=dados.get('transacoes', []),
            arquivo_origem=arquivo_path,
            user_id=user_id,
            processado_em=datetime.now().isoformat()
        )

        # Salva
        extratos.extratos.append(asdict(extrato))
        extratos._save_data()

        # Integra com módulo de finanças
        await extratos._integrar_com_financas(extrato, user_id)

        return True

    except Exception as e:
        print(f"Erro ao salvar extrato: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(testar_c6_pdf())