#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
🧪 GUIA DE TESTE PRÁTICO - COMO TESTAR O SISTEMA
Instruções passo a passo para testar o sistema completo
"""

def mostrar_guia():
    print("\n")
    print("╔" + "="*70 + "╗")
    print("║" + " "*70 + "║")
    print("║" + "  🧪 GUIA PRÁTICO DE TESTES - SISTEMA DE DOCUMENTOS  ".center(70) + "║")
    print("║" + " "*70 + "║")
    print("╚" + "="*70 + "╝")
    
    print("""
═══════════════════════════════════════════════════════════════════════

📋 TESTES DISPONÍVEIS

═══════════════════════════════════════════════════════════════════════

1️⃣  TESTE UNITÁRIO - SISTEMA DE SINÔNIMOS
   ─────────────────────────────────────────
   
   python teste_completo.py
   
   ✓ Verifica reconhecimento de tipos de documentos
   ✓ Testa extração com sinônimos
   ✓ Valida padrões de documentos brasileiros
   ✓ Testa confirmação interativa
   ✓ Valida edição de campos
   ✓ Testa seleção de múltiplas opções
   
   ⏱️  Tempo: ~5 segundos


2️⃣  TESTE DE INTEGRAÇÃO - AMBIENTE COMPLETO
   ──────────────────────────────────────────
   
   python teste_integracao.py
   
   ✓ Verifica se todos os módulos estão carregáveis
   ✓ Testa permissões do sistema
   ✓ Valida estrutura de dados JSON
   ✓ Verifica arquivos de configuração
   ✓ Confirma ambiente Python
   
   ⏱️  Tempo: ~2 segundos


3️⃣  TESTE MANUAL - FLUXO COM BOLETO REAL
   ──────────────────────────────────────
   
   VIA TELEGRAM BOT (@seu_bot):
   
   Passo 1: Envie uma imagem ou PDF de boleto
   └─> Bot deve extrair dados automaticamente
   
   Passo 2: Confirme o menu aparecerá:
   └─> Mostrará dados extraídos com emoji
   └─> Oferecerá opções de edição
   
   Passo 3: Responda com comando:
   
      /editar valor 250.00
      └─> Atualiza valor
      
      /editar beneficiario "Empresa Nova"
      └─> Atualiza beneficiário
      
      /confirmar
      └─> Mostra menu de ações
      
      /todas
      └─> Executa: agenda + despesa + pago
      
      /agenda
      └─> Apenas cria lembrete
      
      /despesa
      └─> Apenas registra como despesa
      
      /pago
      └─> Apenas marca como pago
      
      /cancelar
      └─> Descarta documento


4️⃣  TESTE MANUAL - FLUXO COM TRANSFER/PIX
   ────────────────────────────────────────
   
   Mesmos passos, mas com comprovante de:
   ✓ Transferência bancária (TED/DOC)
   ✓ PIX
   ✓ Comprovante de depósito
   
   Sistema identificará automaticamente o tipo


5️⃣  TESTE MANUAL - FLUXO COM IMPOSTO
   ──────────────────────────────────
   
   Envie comprovante de:
   ✓ DARF (Imposto Federal)
   ✓ DAS (Imposto INSS)
   ✓ GPS (Guia de Previdência)
   ✓ FGTS
   ✓ IPVA / IPTU
   
   Sistema reconhecerá e extrairá dados


═══════════════════════════════════════════════════════════════════════

🎯 CENÁRIOS DE TESTE RECOMENDADOS

═══════════════════════════════════════════════════════════════════════

CENÁRIO A: Extração Simples (Sucesso Total)
──────────────────────────────────────────

1. Envie boleto bem definido com:
   • Valor claro
   • Beneficiário legível
   • Vencimento visível

2. Sistema deve:
   ✅ Extrair todos os dados
   ✅ Mostrar confirmação com emojis
   ✅ Permitir edição
   ✅ Executar todas as 3 ações


CENÁRIO B: Extração com Edição (Validação de Feedback)
──────────────────────────────────────────────────────

1. Envie documento com um campo incorreto

2. Edite usando:
   /editar campo valor

3. Sistema deve:
   ✅ Aceitar nova informação
   ✅ Atualizar display
   ✅ Permitir novamente /editar ou /confirmar


CENÁRIO C: Múltiplas Ações Simultâneas (Processo Crítico)
──────────────────────────────────────────────────────────

1. Envie documento
2. Confirme com /todas

3. Sistema deve:
   ✅ Criar lembrete (calendar)
   ✅ Registrar em finanças
   ✅ Marcar como processado
   ✅ Tudo em uma transação única

Verificar em:
   • Google Calendar (if connected)
   • Planilha de finanças
   • Status do documento


CENÁRIO D: Tratamento de Erro (Robustez)
────────────────────────────────────────

1. Envie documento ilegível/corrompido

2. Sistema deve:
   ✅ Tentar OCR
   ✅ Se falhar, mostrar erro claro
   ✅ Sugerir próximos passos

3. Envie documento vazio

4. Sistema deve:
   ✅ Alertar que não encontrou dados
   ✅ Mostrar texto extraído
   ✅ Permitir /cancelar


═══════════════════════════════════════════════════════════════════════

📊 MÉTRICAS DE SUCESSO

═══════════════════════════════════════════════════════════════════════

TESTE UNITÁRIO (teste_completo.py):
✅ Todos 6 testes devem passar
✅ Tempo de execução: < 10 segundos
✅ Sem erros de import

TESTE DE INTEGRAÇÃO (teste_integracao.py):
✅ 8/8 módulos carregáveis
✅ 4/4 arquivos de config presentes
✅ 3/4 JSONs com dados
✅ Permissões de escrita OK

TESTE MANUAL (Telegram):
✅ Extração accuracy > 90%
✅ Menu de confirmação aparece em < 3s
✅ Edição funciona imediatamente
✅ 3 ações simultâneas completam em < 5s
✅ Sem crashes ou erros inesperados

TESTE DE CARGA (Futuro):
✅ 100 documentos/hora
✅ Sem memory leaks
✅ Tempo médio resposta: < 2s


═══════════════════════════════════════════════════════════════════════

⚙️  COMO EXECUTAR TESTES

═══════════════════════════════════════════════════════════════════════

1. Testes Rápidos (Recomendado para CI/CD):
   
   cd /caminho/do/projeto
   python teste_completo.py
   python teste_integracao.py


2. Teste Manual Completo:
   
   # Terminal 1: Iniciar Flask API
   python api_server.py
   
   # Terminal 2: Iniciar Telegram bot
   cd whatsapp_bot
   npm start
   
   # Terminal 3: Enviar testes via bot


3. Teste de Carga Simulado:
   
   # (TODO: criar teste_carga.py)
   python teste_carga.py --documentos 100 --tipo boleto


═══════════════════════════════════════════════════════════════════════

🔧 TROUBLESHOOTING

═══════════════════════════════════════════════════════════════════════

Erro: "Module not found: sinonimos_documentos"
→ Verifique se confirmacao_documentos.py existe
→ Verifique imports em faturas.py

Erro: "SyntaxError: unexpected indent"
→ Verificar indentação em faturas.py linha 315+
→ Remover código orphaned

Erro: "DocumentoExtraido not found"
→ Verifique confirmacao_documentos.py
→ Recrie com: create_file ...confirmacao_documentos.py

Erro: "processar_resposta returns wrong type"
→ Método retorna Tuple[str, Optional[Dict]]
→ Sempre desempacotar: resposta, dados = conf.processar_resposta(...)

Erro: "Permissão negada em data/"
→ Verificar chmod em Linux: chmod 755 data/
→ Verificar properties em Windows


═══════════════════════════════════════════════════════════════════════

📚 REFERÊNCIA RÁPIDA

═══════════════════════════════════════════════════════════════════════

Classes Principais:
  ✓ DocumentoExtraido         - Documento em memória
  ✓ ConfirmacaoDocumentos     - Sistema de confirmação
  ✓ ExtratorDocumentosBrasil  - OCR gratuito
  ✓ ExtratorDocumentos        - Impostos brasileiros

Métodos Principais:
  ✓ formatar_exibicao()       - Mostra na tela
  ✓ processar_resposta()      - Processa comando do usuário
  ✓ _processar_edicao()       - Edita campo
  ✓ _processar_opcoes()       - Seleciona ações

Comandos do Usuário:
  ✓ /confirmar, /ok, /sim     - Confirma dados
  ✓ /editar campo valor       - Edita um campo
  ✓ /agenda, /despesa, /pago  - Ações individuais
  ✓ /todas                    - Todas as 3 ações
  ✓ /cancelar, /nao           - Cancela documento


═══════════════════════════════════════════════════════════════════════
""")

if __name__ == '__main__':
    mostrar_guia()
