"""
📚 Guia de Uso - Módulo de Extratos Bancários
Como usar o novo recurso de processamento de extratos
"""

def guia_extratos():
    """Exibe guia de uso dos extratos bancários"""

    print("""
📊 MÓDULO DE EXTRATOS BANCÁRIOS - GUIA COMPLETO
===============================================

🎯 FUNCIONALIDADES
• Processamento automático de PDFs de extratos bancários
• Suporte a 7 bancos brasileiros
• Extração inteligente de transações
• Categorização automática
• Integração com controle financeiro

🏦 BANCOS SUPORTADOS
• Itaú
• Bradesco
• Santander
• Nubank
• Banco do Brasil
• Caixa Econômica
• Banco Inter

📝 COMANDOS DISPONÍVEIS

1. /extrato [anexo PDF]
   • Processa um PDF de extrato bancário
   • Extrai automaticamente todas as transações
   • Importa para o controle financeiro
   • Exemplo: envie um PDF do Itaú junto com o comando

2. /extratos
   • Lista todos os extratos já processados
   • Mostra resumo de cada extrato
   • Últimos 5 extratos processados

💡 DICAS DE USO

• Arquivos: Use PDFs originais dos bancos (não fotos)
• Qualidade: PDFs com texto claro funcionam melhor
• Formatos: Funciona com extratos de conta corrente e cartão
• Categorias: O sistema tenta categorizar automaticamente

🔧 DEPENDÊNCIAS NECESSÁRIAS
• pdfplumber (instalado)
• pandas (instalado)
• tabula-py (opcional, para tabelas complexas)

📊 INTEGRAÇÃO COM FINANÇAS
• Todas as transações extraídas são automaticamente
  importadas para o módulo de finanças
• Aparecem no /gastos e relatórios financeiros
• Categorizadas automaticamente quando possível

🧪 TESTE O SISTEMA
python test_extratos.py

🚀 PRONTO PARA USAR!
""")

if __name__ == "__main__":
    guia_extratos()