"""
🏦 Módulo Python Boleto
Geração e processamento de boletos bancários brasileiros
Usa a biblioteca pyboleto para criar boletos de cobrança
Compatível com múltiplos bancos brasileiros
"""

import os
import re
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict

try:
    from pyboleto import BoletoBradesco, BoletoItau, BoletoBB, BoletoCaixa
    PYBOLETO_AVAILABLE = True
except ImportError:
    PYBOLETO_AVAILABLE = False
    print("⚠️ Biblioteca pyboleto não instalada. Instale com: pip install pyboleto")

# Validação brasileira
try:
    from validate_docbr import CNPJ, CPF
    VALIDATE_AVAILABLE = True
except ImportError:
    VALIDATE_AVAILABLE = False

@dataclass
class DadosSacado:
    """Dados do sacado (pagador)"""
    nome: str
    endereco: str
    bairro: str
    cidade: str
    uf: str
    cep: str
    cpf_cnpj: str

@dataclass
class DadosCedente:
    """Dados do cedente (beneficiário)"""
    nome: str
    cpf_cnpj: str
    agencia: str
    conta: str
    codigo_beneficiario: str

@dataclass
class DadosBoleto:
    """Dados completos do boleto"""
    numero_documento: str
    valor: Decimal
    vencimento: datetime
    sacado: DadosSacado
    cedente: DadosCedente
    instrucoes: List[str] = None
    especie_documento: str = "DM"
    aceite: str = "N"
    carteira: str = "18"

class GeradorBoleto:
    """Gerador de boletos bancários brasileiros"""

    def __init__(self):
        if not PYBOLETO_AVAILABLE:
            raise ImportError("Biblioteca pyboleto não está instalada")

        self.bancos_suportados = {
            'bradesco': BoletoBradesco,
            'itau': BoletoItau,
            'bb': BoletoBB,
            'caixa': BoletoCaixa
        }

    def validar_cpf_cnpj(self, cpf_cnpj: str) -> bool:
        """Valida CPF ou CNPJ"""
        if not VALIDATE_AVAILABLE:
            return True  # Assume válido se não conseguir validar

        cpf_cnpj = re.sub(r'\D', '', cpf_cnpj)

        if len(cpf_cnpj) == 11:
            return CPF().validate(cpf_cnpj)
        elif len(cpf_cnpj) == 14:
            return CNPJ().validate(cpf_cnpj)
        else:
            return False

    def criar_boleto(self, dados: DadosBoleto, banco: str = 'bradesco') -> Optional[Any]:
        """
        Cria um boleto usando os dados fornecidos

        Args:
            dados: DadosBoleto com todas as informações
            banco: Nome do banco ('bradesco', 'itau', 'bb', 'caixa')

        Returns:
            Objeto boleto da biblioteca pyboleto ou None se erro
        """
        if banco not in self.bancos_suportados:
            print(f"❌ Banco {banco} não suportado")
            return None

        # Validações básicas
        if not self.validar_cpf_cnpj(dados.sacado.cpf_cnpj):
            print("❌ CPF/CNPJ do sacado inválido")
            return None

        if not self.validar_cpf_cnpj(dados.cedente.cpf_cnpj):
            print("❌ CPF/CNPJ do cedente inválido")
            return None

        try:
            # Cria o boleto
            BoletoClass = self.bancos_suportados[banco]
            boleto = BoletoClass()

            # Dados do cedente
            boleto.agencia_cedente = dados.cedente.agencia
            boleto.conta_cedente = dados.cedente.conta
            boleto.convenio = dados.cedente.codigo_beneficiario
            boleto.carteira = dados.carteira

            # Dados do sacado
            boleto.sacado_nome = dados.sacado.nome
            boleto.sacado_endereco = dados.sacado.endereco
            boleto.sacado_bairro = dados.sacado.bairro
            boleto.sacado_cidade = dados.sacado.cidade
            boleto.sacado_uf = dados.sacado.uf
            boleto.sacado_cep = dados.sacado.cep

            # Dados do boleto
            boleto.numero_documento = dados.numero_documento
            boleto.valor_documento = float(dados.valor)
            boleto.data_vencimento = dados.vencimento
            boleto.data_documento = datetime.now()
            boleto.especie_documento = dados.especie_documento
            boleto.aceite = dados.aceite

            # Instruções
            if dados.instrucoes:
                for i, instrucao in enumerate(dados.instrucoes[:5]):  # Máximo 5 instruções
                    setattr(boleto, f'instrucao{i+1}', instrucao)

            return boleto

        except Exception as e:
            print(f"❌ Erro ao criar boleto: {e}")
            return None

    def gerar_pdf(self, boleto: Any, caminho_saida: str) -> bool:
        """
        Gera PDF do boleto

        Args:
            boleto: Objeto boleto da pyboleto
            caminho_saida: Caminho onde salvar o PDF

        Returns:
            True se sucesso, False se erro
        """
        try:
            # Cria diretório se não existir
            os.makedirs(os.path.dirname(caminho_saida), exist_ok=True)

            # Gera PDF
            boleto.draw_boleto(caminho_saida)
            print(f"✅ Boleto gerado: {caminho_saida}")
            return True

        except Exception as e:
            print(f"❌ Erro ao gerar PDF: {e}")
            return False

    def gerar_codigo_barras(self, boleto: Any) -> Optional[str]:
        """
        Gera código de barras do boleto

        Args:
            boleto: Objeto boleto da pyboleto

        Returns:
            Código de barras como string ou None se erro
        """
        try:
            return boleto.barcode
        except Exception as e:
            print(f"❌ Erro ao gerar código de barras: {e}")
            return None

class ProcessadorBoleto:
    """Processador de boletos (leitura e validação)"""

    def __init__(self):
        self.gerador = GeradorBoleto()

    def validar_boleto_imagem(self, caminho_imagem: str) -> Dict[str, Any]:
        """
        Valida boleto a partir de imagem (usando OCR)

        Args:
            caminho_imagem: Caminho para a imagem do boleto

        Returns:
            Dicionário com dados extraídos
        """
        # TODO: Implementar OCR para extrair dados do boleto
        # Por enquanto retorna estrutura básica
        return {
            'status': 'não_implementado',
            'mensagem': 'Processamento de imagem ainda não implementado',
            'dados': {}
        }

    def validar_codigo_barras(self, codigo: str) -> Dict[str, Any]:
        """
        Valida código de barras do boleto

        Args:
            codigo: Código de barras como string

        Returns:
            Dicionário com validação e dados
        """
        try:
            # Validação básica do formato
            if not codigo or len(codigo) < 44:
                return {
                    'valido': False,
                    'erro': 'Código de barras inválido ou muito curto'
                }

            # Extrai informações básicas
            # Formato: 00190.00009 00000.000000 00000.000000 0 00000000000000
            # Posições: banco + moeda + DV + vencimento + valor + zeros + nosso_numero

            banco = codigo[:3]
            moeda = codigo[3:4]
            dv = codigo[4:5]
            vencimento_factor = int(codigo[5:9])
            valor = int(codigo[9:19]) / 100  # Últimos 2 dígitos são centavos

            # Calcula data de vencimento
            data_base = datetime(1997, 10, 7)
            data_vencimento = data_base + timedelta(days=vencimento_factor)

            return {
                'valido': True,
                'banco': banco,
                'moeda': moeda,
                'digito_verificador': dv,
                'data_vencimento': data_vencimento.strftime('%Y-%m-%d'),
                'valor': valor,
                'nosso_numero': codigo[24:34]  # Aproximado
            }

        except Exception as e:
            return {
                'valido': False,
                'erro': f'Erro na validação: {str(e)}'
            }

# Funções de conveniência
def criar_boleto_bradesco(dados: DadosBoleto) -> Optional[Any]:
    """Cria boleto Bradesco"""
    gerador = GeradorBoleto()
    return gerador.criar_boleto(dados, 'bradesco')

def criar_boleto_itau(dados: DadosBoleto) -> Optional[Any]:
    """Cria boleto Itaú"""
    gerador = GeradorBoleto()
    return gerador.criar_boleto(dados, 'itau')

def criar_boleto_bb(dados: DadosBoleto) -> Optional[Any]:
    """Cria boleto Banco do Brasil"""
    gerador = GeradorBoleto()
    return gerador.criar_boleto(dados, 'bb')

def criar_boleto_caixa(dados: DadosBoleto) -> Optional[Any]:
    """Cria boleto Caixa Econômica"""
    gerador = GeradorBoleto()
    return gerador.criar_boleto(dados, 'caixa')

# Exemplo de uso
if __name__ == "__main__":
    # Exemplo de dados para teste
    sacado = DadosSacado(
        nome="João Silva",
        endereco="Rua das Flores, 123",
        bairro="Centro",
        cidade="São Paulo",
        uf="SP",
        cep="01234-567",
        cpf_cnpj="123.456.789-00"
    )

    cedente = DadosCedente(
        nome="Empresa Exemplo Ltda",
        cpf_cnpj="12.345.678/0001-90",
        agencia="1234",
        conta="56789",
        codigo_beneficiario="1234567"
    )

    dados_boleto = DadosBoleto(
        numero_documento="001",
        valor=Decimal("150.00"),
        vencimento=datetime.now() + timedelta(days=30),
        sacado=sacado,
        cedente=cedente,
        instrucoes=[
            "Não aceitar após vencimento",
            "Multa de 2% após vencimento"
        ]
    )

    # Cria boleto
    boleto = criar_boleto_bradesco(dados_boleto)

    if boleto:
        print("✅ Boleto criado com sucesso!")
        print(f"Código de barras: {boleto.barcode}")

        # Gera PDF
        caminho_pdf = "boleto_exemplo.pdf"
        if GeradorBoleto().gerar_pdf(boleto, caminho_pdf):
            print(f"📄 PDF gerado: {caminho_pdf}")
    else:
        print("❌ Erro ao criar boleto")