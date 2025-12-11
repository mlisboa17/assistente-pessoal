# 📄 Sistema de Processamento de Documentos e Imagens

## 🚀 Melhorias Implementadas

### ⏱️ **Delays Inteligentes**

O sistema agora aguarda o WhatsApp processar os arquivos antes de tentar baixá-los:

#### PDFs
- **Delay inicial**: 8 segundos após receber
- **Delay antes do download**: 5 segundos adicionais
- **Timeout de download**: 60 segundos
- **Timeout de processamento**: 120 segundos
- **Tentativas de download**: 3 tentativas com intervalo de 3 segundos

#### Imagens
- **Delay inicial**: 2 segundos após receber
- **Delay antes do download**: 3 segundos adicionais
- **Timeout de download**: 40 segundos
- **Timeout de processamento**: 90 segundos

#### Áudios
- **Delay inicial**: 1.5 segundos após receber
- Transcrição automática com Google Speech API

### 🎯 **Mensagens de Status**

O bot agora informa o usuário sobre o progresso:

**Para PDFs:**
```
📄 Processando arquivo: documento.pdf...
⏳ PDFs podem levar alguns segundos...
```

**Reações:**
- 📥 = Baixando arquivo
- ⏳ = Aguardando processamento
- ✅ = Processado com sucesso
- ❌ = Erro no processamento

### 🔄 **Sistema de Retry**

Se o download falhar, o sistema tenta até 3 vezes antes de desistir:
1. Tentativa 1: imediatamente
2. Tentativa 2: após 3 segundos
3. Tentativa 3: após mais 3 segundos

### ⚠️ **Tratamento de Erros**

**Timeout no Download:**
```
⏳ O arquivo ainda está sendo processado pelo WhatsApp.

📌 Aguarde 10 segundos e reenvie o arquivo.
```

**Timeout no Processamento:**
```
⏰ Tempo limite excedido ao processar arquivo.

O arquivo pode ser muito grande ou complexo.
Tente enviar um arquivo menor.
```

**Arquivo Corrompido:**
```
❌ Arquivo vazio ou corrompido. Tente reenviar.
```

## 📊 Tipos de Documentos Suportados

### Documentos Fiscais
- ✅ DAS (Documento de Arrecadação do Simples Nacional)
- ✅ GPS (Guia da Previdência Social)
- ✅ DARF (Documento de Arrecadação de Receitas Federais)
- ✅ FGTS (Guia de Recolhimento do FGTS)

### Extratos Bancários
- ✅ Extratos em PDF
- ✅ Extratos em formato OFX/QFX
- ✅ Detecção automática de banco

### Comprovantes
- ✅ Comprovantes de PIX
- ✅ Boletos bancários
- ✅ Recibos
- ✅ Notas fiscais

### Imagens
- ✅ Capturas de tela
- ✅ Fotos de documentos
- ✅ Comprovantes digitalizados

## 🛠️ Configurações Técnicas

### Limites de Tamanho
- **Axios**: `maxContentLength: Infinity`
- **Axios**: `maxBodyLength: Infinity`

### Timeouts por Tipo

| Tipo | Download | Processamento |
|------|----------|---------------|
| PDF  | 60s      | 120s          |
| Imagem | 40s    | 90s           |
| Áudio | 30s     | 60s           |
| Outros | 45s    | 60s           |

## 🎮 Como Usar

### Enviar PDF
1. Envie o arquivo PDF pelo WhatsApp
2. Aguarde a mensagem: "📄 Processando arquivo..."
3. O sistema processará automaticamente (pode levar até 2 minutos)
4. Receberá o resultado com os dados extraídos

### Enviar Imagem
1. Envie a imagem (comprovante, PIX, etc)
2. Aguarde a mensagem: "🧾 Analisando comprovante..."
3. Sistema extrai texto via OCR
4. Retorna dados estruturados

### Enviar Áudio
1. Envie mensagem de áudio
2. Sistema transcreve automaticamente
3. Processa o comando detectado

## ⚡ Dicas para Melhor Performance

### Para PDFs
- ✅ Evite arquivos maiores que 10MB
- ✅ PDFs com texto selecionável são mais rápidos
- ✅ Aguarde alguns segundos após enviar
- ✅ Se der erro, reenvie após 10 segundos

### Para Imagens
- ✅ Use boa iluminação ao fotografar
- ✅ Mantenha o documento reto e legível
- ✅ Evite reflexos e sombras
- ✅ Imagens menores processam mais rápido

### Para Áudios
- ✅ Fale claramente e devagar
- ✅ Evite ambientes barulhentos
- ✅ Áudios curtos (até 1 minuto) são ideais
- ✅ Fale em português do Brasil

## 🐛 Resolução de Problemas

### "O arquivo ainda está sendo processado"
**Solução:** Aguarde 10 segundos e reenvie o arquivo.

### "Tempo limite excedido"
**Soluções:**
- Reduza o tamanho do arquivo
- Converta PDF para imagem
- Envie em partes menores

### "Não consegui baixar"
**Soluções:**
- Verifique sua conexão de internet
- Reenvie o arquivo
- Tente em formato diferente

### "Servidor Python não está rodando"
**Solução:** 
```bash
python api_server.py
```

## 📝 Logs e Monitoramento

O sistema agora exibe logs detalhados no terminal:

```
📄 Usuário: [ARQUIVO: documento.pdf]
⏳ Aguardando 5s para PDF ser processado pelo WhatsApp...
📦 Arquivo baixado: 234.56 KB
✅ Processado com sucesso
📤 Resposta enviada!
```

## 🔮 Próximas Melhorias

- [ ] Suporte para arquivos Word (.docx)
- [ ] Suporte para planilhas Excel (.xlsx)
- [ ] OCR em múltiplos idiomas
- [ ] Compressão automática de arquivos grandes
- [ ] Cache de documentos processados
- [ ] Fila de processamento assíncrona

---

**Última atualização:** 08/12/2025
**Versão:** 2.0
