"""
✅ Módulo de Confirmação e Edição de Documentos Extraídos

Fluxo:
1. Mostra dados extraídos formatados
2. Permite edição de campos
3. Oferece 3 opções simultâneas: Agenda, Despesa, Pago
4. Executa todas as opções selecionadas
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import json


@dataclass
class DocumentoExtraido:
    """Documento extraído aguardando confirmação"""
    id: str
    tipo: str  # boleto, transferencia, pix, imposto, etc
    valor: float
    beneficiario: str
    pagador: str
    data: str
    descricao: str
    user_id: str
    
    # Dados extras por tipo
    dados_extras: Dict[str, Any] = None
    
    # Status
    confirmado: bool = False
    opcoes_selecionadas: List[str] = None  # ['agenda', 'despesa', 'pago']
    
    def __post_init__(self):
        if self.dados_extras is None:
            self.dados_extras = {}
        if self.opcoes_selecionadas is None:
            self.opcoes_selecionadas = []


class ConfirmacaoDocumentos:
    """Gerencia confirmação e edição de documentos extraídos"""
    
    def __init__(self):
        self.pendentes = {}  # user_id -> DocumentoExtraido
    
    def formatar_exibicao(self, doc: DocumentoExtraido) -> str:
        """Formata documento para exibição na tela"""
        
        tipos_emoji = {
            'boleto': '📄',
            'transferencia': '🏦',
            'pix': '📲',
            'imposto': '📋',
            'darf': '📋',
            'das': '📋',
            'gps': '📋',
            'fgts': '📋',
            'condominio': '🏢',
            'aluguel': '🏠',
            'luz': '💡',
            'agua': '💧',
            'gas': '⛽',
            'telefone': '☎️',
            'internet': '📡',
        }
        
        emoji = tipos_emoji.get(doc.tipo, '💰')
        
        msg = f"""
{emoji} *{doc.tipo.upper()} EXTRAÍDO*

{'═' * 50}
📊 *RESUMO DOS DADOS*
{'═' * 50}

💰 *Valor:* R$ {doc.valor:.2f}

📤 *Beneficiário:* {doc.beneficiario}
📥 *Pagador:* {doc.pagador}

📅 *Data:* {doc.data}
📝 *Descrição:* {doc.descricao}

"""
        
        # Dados extras por tipo
        if doc.tipo == 'boleto' and doc.dados_extras:
            msg += f"""
🏦 *DADOS DO BOLETO:*
  • Linha Digitável: `{doc.dados_extras.get('linha_digitavel', 'N/A')[:30]}...`
  • Código Barras: `{doc.dados_extras.get('codigo_barras', 'N/A')[:20]}...`
  • Banco: {doc.dados_extras.get('banco', 'N/A')}
  • Vencimento: {doc.dados_extras.get('vencimento', 'N/A')}

"""
        
        elif doc.tipo == 'pix' and doc.dados_extras:
            msg += f"""
📲 *DADOS DO PIX:*
  • Chave PIX: {doc.dados_extras.get('chave_pix', 'N/A')}
  • Tipo: {doc.dados_extras.get('tipo_chave', 'N/A')}
  • ID Transação: {doc.dados_extras.get('id_transacao', 'N/A')}

"""
        
        elif doc.tipo == 'transferencia' and doc.dados_extras:
            msg += f"""
🏦 *DADOS DA TRANSFERÊNCIA:*
  • Banco: {doc.dados_extras.get('banco_destino', 'N/A')}
  • Agência: {doc.dados_extras.get('agencia_destino', 'N/A')}
  • Conta: {doc.dados_extras.get('conta_destino', 'N/A')}

"""
        
        elif doc.tipo in ['darf', 'das', 'gps', 'fgts'] and doc.dados_extras:
            msg += f"""
📋 *DADOS DO IMPOSTO:*
  • Período: {doc.dados_extras.get('periodo_apuracao', 'N/A')}
  • Código Receita: {doc.dados_extras.get('codigo_receita', 'N/A')}
  • CNPJ/CPF: {doc.dados_extras.get('cnpj_cpf', 'N/A')}

"""
        
        msg += f"""
{'═' * 50}
✅ *CONFIRME OS DADOS*
{'═' * 50}

*Responda com uma das opções:*

1️⃣ *Está correto, proceder com tudo*
   `/confirmar` ou `/ok` ou `/sim`

2️⃣ *Editar algum campo*
   `/editar campo valor`
   
   Exemplo: `/editar valor 150.50`
   Exemplo: `/editar beneficiario "Nova Empresa"`
   Exemplo: `/editar data 2024-12-31`

3️⃣ *O que fazer com este documento?*
   
   Selecione uma ou mais opções:
   
   📅 `/agenda` - Agendar para pagar
   💰 `/despesa` - Registrar como despesa
   ✅ `/pago` - Marcar como pago agora
   
   💡 *Pode usar tudo junto:*
   `/agenda /despesa /pago` - Faz as 3 coisas!
   
   ou ainda `/todas` para as 3 opções

4️⃣ *Cancelar*
   `/cancelar` ou `/nao`

"""
        return msg
    
    def processar_resposta(self, mensagem: str, user_id: str) -> Tuple[str, Optional[Dict]]:
        """
        Processa resposta do usuário sobre confirmação
        
        Retorna: (mensagem_resposta, dados_processamento)
        dados_processamento = {
            'acao': 'confirmar|editar|processar|cancelar',
            'edicoes': {...},  # se for editar
            'opcoes': ['agenda', 'despesa', 'pago'],  # se for processar
            'documento': DocumentoExtraido
        }
        """
        
        if user_id not in self.pendentes:
            return "❌ Nenhum documento pendente para você.", None
        
        doc = self.pendentes[user_id]
        mensagem_lower = mensagem.lower().strip()
        
        # ✅ CONFIRMAÇÃO SIMPLES
        if mensagem_lower in ['confirmar', 'ok', 'sim', 'yes', 'confirmo', 'correto']:
            doc.confirmado = True
            doc.opcoes_selecionadas = ['agenda', 'despesa']  # Padrão
            
            return self._formatar_opcoes_acao(doc), {
                'acao': 'confirmar',
                'documento': doc
            }
        
        # ❌ CANCELAMENTO
        if mensagem_lower in ['cancelar', 'nao', 'no', 'cancel', 'voltar']:
            del self.pendentes[user_id]
            return "❌ Documento descartado.\n\nEnvie um novo para processar.", {
                'acao': 'cancelar',
                'documento': doc
            }
        
        # ✏️ EDIÇÃO DE CAMPO
        if mensagem_lower.startswith('/editar') or mensagem_lower.startswith('editar'):
            return self._processar_edicao(mensagem, doc, user_id)
        
        # 📋 SELEÇÃO DE OPÇÕES
        if any(op in mensagem_lower for op in ['/agenda', '/despesa', '/pago', '/todas']):
            return self._processar_opcoes(mensagem, doc, user_id)
        
        # Se não entendeu, pede esclarecimento
        return self._formatar_opcoes_acao(doc), None
    
    def _processar_edicao(self, mensagem: str, doc: DocumentoExtraido, user_id: str) -> Tuple[str, Dict]:
        """Processa edição de campo"""
        
        try:
            # Extrai campo e valor
            partes = mensagem.split(None, 2)  # Divide em max 3 partes
            
            if len(partes) < 3:
                return "❌ Formato inválido.\n\nUse: `/editar campo valor`\n\nCampos: valor, beneficiario, pagador, data, descricao", None
            
            _, campo, valor = partes
            campo = campo.lower().strip()
            valor = valor.strip().strip('"\'')
            
            # Campos editáveis
            campos_editaveis = {
                'valor': lambda v: float(v.replace(',', '.')),
                'beneficiario': str,
                'pagador': str,
                'data': str,  # Validação básica
                'descricao': str,
            }
            
            if campo not in campos_editaveis:
                return f"❌ Campo inválido: {campo}\n\nCampos válidos: {', '.join(campos_editaveis.keys())}", None
            
            # Converte valor
            try:
                valor_convertido = campos_editaveis[campo](valor)
            except Exception as e:
                return f"❌ Erro ao converter valor: {e}\n\nTente novamente.", None
            
            # Atualiza documento
            setattr(doc, campo, valor_convertido)
            
            msg = f"✅ Campo '{campo}' atualizado para: {valor_convertido}\n\n"
            msg += self.formatar_exibicao(doc)
            
            return msg, {
                'acao': 'editar',
                'campo': campo,
                'valor': valor_convertido,
                'documento': doc
            }
        
        except Exception as e:
            return f"❌ Erro ao processar edição: {e}", None
    
    def _processar_opcoes(self, mensagem: str, doc: DocumentoExtraido, user_id: str) -> Tuple[str, Dict]:
        """Processa seleção de opções"""
        
        opcoes = []
        mensagem_lower = mensagem.lower()
        
        # Verifica quais opções foram selecionadas
        if '/todas' in mensagem_lower or ('agenda' in mensagem_lower and 'despesa' in mensagem_lower and 'pago' in mensagem_lower):
            opcoes = ['agenda', 'despesa', 'pago']
        else:
            if '/agenda' in mensagem_lower or 'agenda' in mensagem_lower:
                opcoes.append('agenda')
            if '/despesa' in mensagem_lower or 'despesa' in mensagem_lower:
                opcoes.append('despesa')
            if '/pago' in mensagem_lower or 'pago' in mensagem_lower:
                opcoes.append('pago')
        
        if not opcoes:
            return f"❌ Nenhuma opção selecionada.\n\nUse: `/agenda`, `/despesa`, `/pago` ou `/todas`", None
        
        # Atualiza documento
        doc.opcoes_selecionadas = opcoes
        doc.confirmado = True
        
        # Formata resumo
        msg = "✅ *OPÇÕES SELECIONADAS:*\n\n"
        
        if 'agenda' in opcoes:
            msg += "📅 Agendar para pagar (lembrete)\n"
        if 'despesa' in opcoes:
            msg += "💰 Registrar como despesa (finanças)\n"
        if 'pago' in opcoes:
            msg += "✅ Marcar como pago agora\n"
        
        msg += f"\n⏳ Processando... Aguarde um momento.\n"
        
        return msg, {
            'acao': 'processar',
            'opcoes': opcoes,
            'documento': doc
        }
    
    def _formatar_opcoes_acao(self, doc: DocumentoExtraido) -> str:
        """Formata menu de opções de ação"""
        
        msg = f"""
{'═' * 50}
🎯 *O QUE FAZER COM ESTE {doc.tipo.upper()}?*
{'═' * 50}

Você pode escolher uma OU MAIS opções:

📅 */agenda* 
   → Agendar lembrete para pagar na data de vencimento

💰 */despesa*
   → Registrar como despesa/gastos no app de finanças

✅ */pago*
   → Marcar como já pago agora mesmo

🎯 */todas*
   → Faz as 3 coisas ao mesmo tempo!

🚫 */cancelar*
   → Descartar este documento

{'═' * 50}
📝 *Ou editar antes:*
/editar campo valor

Exemplos:
  /editar valor 250.50
  /editar beneficiario "Empresa XYZ"
  /editar data 2024-12-31

"""
        return msg
    
    def gerar_resposta_conclusao(self, resultados: Dict[str, Any]) -> str:
        """Gera mensagem de conclusão após processar as opções"""
        
        msg = f"""
✅ *DOCUMENTO PROCESSADO COM SUCESSO!*

{'═' * 50}
"""
        
        if resultados.get('agenda'):
            msg += f"""
📅 *AGENDA:* ✅
   Lembrete agendado para: {resultados['agenda'].get('data', 'N/A')}
   Descrição: {resultados['agenda'].get('descricao', 'N/A')}

"""
        
        if resultados.get('despesa'):
            msg += f"""
💰 *DESPESA:* ✅
   Registrada em: Finanças
   Categoria: {resultados['despesa'].get('categoria', 'N/A')}
   ID: {resultados['despesa'].get('id', 'N/A')}

"""
        
        if resultados.get('pago'):
            msg += f"""
✅ *BAIXA:* ✅
   Marcado como PAGO
   Data: {resultados['pago'].get('data', datetime.now().strftime('%d/%m/%Y'))}
   ID Documento: {resultados['pago'].get('id', 'N/A')}

"""
        
        msg += f"""
{'═' * 50}

📊 Resumo:
   💰 Valor: R$ {resultados.get('valor', 0):.2f}
   📝 Descrição: {resultados.get('descricao', 'N/A')}
   🏷️ Tipo: {resultados.get('tipo', 'N/A')}

{'═' * 50}
✨ Tudo pronto! Algo mais?
"""
        
        return msg


# Instância global
_confirmacao = None

def get_confirmacao_documentos() -> ConfirmacaoDocumentos:
    global _confirmacao
    if _confirmacao is None:
        _confirmacao = ConfirmacaoDocumentos()
    return _confirmacao
