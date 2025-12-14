from modules.leitor_boletos import LeitorBoleto
import json

print('🧪 Testando com boleto real...')
leitor = LeitorBoleto()

try:
    dados = leitor.processar_boleto_arquivo(r'c:\Users\mlisb\Downloads\BOLETO_NFe002806803.PDF')
    print('✅ Dados extraídos:')
    print(json.dumps(dados.to_dict(), indent=2, ensure_ascii=False))

    # Validação
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