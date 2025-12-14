#!/usr/bin/env python3
"""
🌐 Demonstração da Interface Web do Assistente Pessoal

Este script mostra como usar a interface web para:
- Visualizar o dashboard
- Listar extratos processados
- Fazer upload de novos extratos
- Ver relatórios financeiros

Uso:
    python demo_web_interface.py
"""

import requests
import json
import time
from pathlib import Path

class WebInterfaceDemo:
    def __init__(self, base_url="http://localhost:5001"):
        self.base_url = base_url

    def check_server(self):
        """Verifica se o servidor está rodando"""
        try:
            response = requests.get(f"{self.base_url}/health")
            if response.status_code == 200:
                print("✅ Servidor está rodando!")
                return True
            else:
                print("❌ Servidor não responde corretamente")
                return False
        except requests.exceptions.ConnectionError:
            print("❌ Não foi possível conectar ao servidor")
            print("💡 Execute: python api_server.py")
            return False

    def show_dashboard_info(self):
        """Mostra informações do dashboard"""
        print("\n📊 DASHBOARD")
        print("-" * 50)

        try:
            response = requests.get(f"{self.base_url}/")
            if response.status_code == 200:
                print("✅ Dashboard acessível em: http://localhost:5001/")
                print("📈 Funcionalidades disponíveis:")
                print("   • Visão geral com estatísticas")
                print("   • Últimos extratos processados")
                print("   • Ações rápidas")
                print("   • Menu lateral de navegação")
            else:
                print("❌ Erro ao acessar dashboard")
        except Exception as e:
            print(f"❌ Erro: {e}")

    def show_extratos_info(self):
        """Mostra informações da página de extratos"""
        print("\n📄 EXTRATOS BANCÁRIOS")
        print("-" * 50)

        try:
            response = requests.get(f"{self.base_url}/extratos")
            if response.status_code == 200:
                print("✅ Página de extratos acessível")
                print("🔍 Funcionalidades:")
                print("   • Lista de todos os extratos")
                print("   • Filtros por banco e período")
                print("   • Detalhes de cada extrato")
                print("   • Links para exportar dados")
            else:
                print("❌ Erro ao acessar página de extratos")
        except Exception as e:
            print(f"❌ Erro: {e}")

    def show_upload_info(self):
        """Mostra informações da página de upload"""
        print("\n📤 UPLOAD DE EXTRATOS")
        print("-" * 50)

        try:
            response = requests.get(f"{self.base_url}/upload-extrato")
            if response.status_code == 200:
                print("✅ Página de upload acessível")
                print("🎯 Funcionalidades:")
                print("   • Drag-and-drop de arquivos")
                print("   • Seleção de banco emissor")
                print("   • Suporte a senha de PDF")
                print("   • Processamento automático")
                print("   • Resultado em tempo real")
            else:
                print("❌ Erro ao acessar página de upload")
        except Exception as e:
            print(f"❌ Erro: {e}")

    def demo_api_endpoint(self):
        """Demonstra o uso da API"""
        print("\n🔌 API ENDPOINT")
        print("-" * 50)

        # Exemplo de mensagem para a API
        test_message = {
            "message": "/gastos",
            "user_id": "demo_user",
            "user_name": "Usuário Demo"
        }

        try:
            response = requests.post(
                f"{self.base_url}/process",
                json=test_message,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                result = response.json()
                print("✅ API funcionando!")
                print(f"📨 Mensagem enviada: {test_message['message']}")
                print(f"📬 Resposta: {result.get('response', 'N/A')[:100]}...")
            else:
                print("❌ Erro na API")
        except Exception as e:
            print(f"❌ Erro na API: {e}")

def main():
    print("🌐 DEMONSTRAÇÃO DA INTERFACE WEB")
    print("=" * 60)

    demo = WebInterfaceDemo()

    # Verifica servidor
    if not demo.check_server():
        return

    # Mostra funcionalidades
    demo.show_dashboard_info()
    demo.show_extratos_info()
    demo.show_upload_info()
    demo.demo_api_endpoint()

    print("\n🎉 Demonstração concluída!")
    print("\n💡 Para usar a interface web:")
    print("   1. Mantenha o servidor rodando: python api_server.py")
    print("   2. Abra http://localhost:5001 no navegador")
    print("   3. Explore as funcionalidades do menu lateral")
    print("   4. Faça upload de extratos PDFs para testar")

if __name__ == "__main__":
    main()