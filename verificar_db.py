"""Script para verificar o banco de dados SQLite"""
from database.db_manager import get_database, Usuario, Boleto, Evento, Lembrete, Categoria, Gatilho

db = get_database()

print("\n📊 RESUMO DO BANCO SQLite:\n")
print("=" * 40)

with db.get_session() as s:
    print(f"👤 Usuários:   {s.query(Usuario).count()}")
    print(f"📋 Boletos:    {s.query(Boleto).count()}")
    print(f"📅 Eventos:    {s.query(Evento).count()}")
    print(f"⏰ Lembretes:  {s.query(Lembrete).count()}")
    print(f"🏷️  Categorias: {s.query(Categoria).count()}")
    print(f"⚡ Gatilhos:   {s.query(Gatilho).count()}")
    
    print("\n" + "=" * 40)
    print("\n📋 BOLETOS MIGRADOS:")
    for b in s.query(Boleto).all():
        print(f"  • R$ {b.valor:.2f} - {b.beneficiario} - Venc: {b.vencimento}")
    
    print("\n📅 EVENTOS MIGRADOS:")
    for e in s.query(Evento).all():
        print(f"  • {e.titulo} - {e.data}")
    
    print("\n🏷️ CATEGORIAS DISPONÍVEIS:")
    for c in s.query(Categoria).all():
        print(f"  {c.icone} {c.nome} ({c.tipo})")

print("\n✅ Banco de dados funcionando corretamente!")
print(f"📁 Arquivo: data/assistente.db")
