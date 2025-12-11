# 🎯 GUIA RÁPIDO - Comece em 5 Minutos

## 1️⃣ INSTALAR (1 min)

```bash
pip install transformers torch
```

⏏️ **Nota:** PyTorch é grande (~500MB), vai demorar um pouco.

---

## 2️⃣ TESTAR (2 min)

Copie e execute:

```python
from transformers import pipeline

# Criar classificador
classifier = pipeline("zero-shot-classification", 
                     model="facebook/bart-large-mnli")

# Testar com suas mensagens
resultado = classifier(
    "Tenho reunião amanhã às 14h",
    ["agenda", "tarefa", "lembrete", "conversa"]
)

print(resultado)
# Output: {'labels': ['agenda'], 'scores': [0.95]}
```

---

## 3️⃣ INTEGRAR (2 min)

No seu `middleware/ia_interpreter.py`, adicione na classe `IAInterpreter`:

```python
def __init__(self):
    # ... seu código ...
    
    # NOVO: Carrega Transformers
    try:
        from transformers import pipeline
        self.classifier = pipeline("zero-shot-classification")
    except:
        self.classifier = None

def interpretar(self, mensagem, contexto=None, arquivo_dados=None):
    # Seu interpretador local
    resultado = self._interpretar_local(mensagem)
    
    # Se confiança baixa, tenta Transformers
    if resultado.get('confianca', 0) < 0.8 and self.classifier:
        result_tf = self.classifier(
            mensagem,
            ['agenda', 'tarefa', 'lembrete', 'financeiro', 'email', 'sistema', 'conversa']
        )
        resultado['intencao'] = result_tf['labels'][0]
        resultado['confianca'] = result_tf['scores'][0]
    
    return resultado
```

---

## 🎯 ANTES vs DEPOIS

### ANTES:
```
Mensagem: "Me avisa em 1 hora"
Resultado: ❌ Não reconheceu como "lembrete"
```

### DEPOIS:
```
Mensagem: "Me avisa em 1 hora"
Resultado: ✅ Reconhece como "lembrete" (95% confiança)
```

---

## 📊 MODELOS RECOMENDADOS

| Modelo | Velocidade | Acurácia | Tamanho | Recomendação |
|--------|-----------|----------|--------|--------------|
| facebook/bart-large-mnli | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 1.6GB | 👍 USAR ESTE |
| microsoft/deberta-base | ⭐⭐⭐ | ⭐⭐⭐⭐ | 600MB | Alternativa |
| distilbert-base-cased | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | 268MB | Leve/Rápido |

---

## 🆘 TROUBLESHOOTING

### Erro: "No module named 'transformers'"
```bash
pip install transformers
```

### Erro: "No module named 'torch'"
```bash
pip install torch
```

### Lento na primeira execução?
- Normal! Está baixando o modelo (~1.6GB)
- Próximas vezes é rápido (cache)

### Quer modelo menor?
```python
classifier = pipeline(
    "zero-shot-classification",
    model="distilbert-base-cased"  # Mais leve
)
```

---

## 📝 EXEMPLOS DE USO

### Exemplo 1: Classificação Simples
```python
classifier = pipeline("zero-shot-classification")

msg = "Preciso comprar leite"
resultado = classifier(msg, ["tarefa", "agenda", "lembrete"])
print(resultado['labels'][0])  # Output: "tarefa"
```

### Exemplo 2: Com Confiança
```python
resultado = classifier("Me lembra em 30 min", 
                      ["lembrete", "tarefa"])

intenacao = resultado['labels'][0]
confianca = resultado['scores'][0]

if confianca > 0.8:
    print(f"✅ {intenacao} ({confianca:.0%})")
else:
    print("❓ Incerto, pedir confirmação")
```

### Exemplo 3: Várias Intenções
```python
mensagem = "Tenho reunião e preciso ir ao mercado"

intenacoes = ["agenda", "tarefa", "lembrete"]
resultado = classifier(mensagem, intenacoes)

# Retorna todas as possibilidades ordenadas
for intent, score in zip(resultado['labels'], resultado['scores']):
    print(f"{intent}: {score:.0%}")
```

---

## ⚡ PERFORMANCE

```
Local (Regex):          < 1ms   ⭐⭐⭐⭐⭐
HuggingFace (GPU):      20-50ms ⭐⭐⭐⭐
HuggingFace (CPU):      100-300ms ⭐⭐⭐
Gemini API:             500-2000ms ⭐⭐
```

**Recomendação:** 
1. Tenta Local (< 1ms)
2. Se falhar, tenta HuggingFace (~100ms)
3. Se ainda falhar, tenta Gemini

---

## 🎁 CHEAT SHEET

```python
# Setup
from transformers import pipeline
classifier = pipeline("zero-shot-classification")

# Usar
resultado = classifier(
    "sua mensagem",
    ["classe1", "classe2", "classe3"]
)

# Extrair
intencao = resultado['labels'][0]
confianca = resultado['scores'][0]
todas = list(zip(resultado['labels'], resultado['scores']))

# Verificar
if confianca > 0.8:
    # Usar resultado
    pass
else:
    # Pedir confirmação
    pass
```

---

## 📚 PRÓXIMAS ETAPAS

1. **Esta semana:**
   - ✅ Instalar e testar
   - ✅ Integrar com seu código
   - ✅ Medir melhoria

2. **Próximo mês:**
   - Setup Doccano
   - Treinar modelo Rasa
   - Deploy em produção

---

## 🔗 RECURSOS

- Docs: https://huggingface.co/docs/transformers
- Modelos: https://huggingface.co/models
- PT-BR: https://huggingface.co/models?language=pt

---

## ✅ CHECKLIST

- [ ] Instalar transformers
- [ ] Instalar torch
- [ ] Rodar primeiro exemplo
- [ ] Integrar no seu código
- [ ] Testar com suas mensagens
- [ ] Medir melhoria de acurácia

---

**Pronto! Você está preparado para melhorar seu interpretador!** 🚀

Qualquer dúvida, veja `OPCOES_IA_GRATIS_TREINAS.md`

