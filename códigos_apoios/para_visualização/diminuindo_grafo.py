import igraph as ig
import pandas as pd
import random
from collections import Counter

# ============================================
# 1. CARREGAR O GRAFO
# ============================================

print("📁 Carregando grafo filtrado...")

g = ig.Graph.Read_GraphML("grafo_videos_filtrado.graphml")
print(f"Nós originais: {g.vcount():,}")
print(f"Arestas originais: {g.ecount():,}")

# ============================================
# 2. ESCOLHA SUAS OPÇÕES AQUI!
# ============================================

# --- OPÇÃO 1: Aumentar peso mínimo das arestas ---
print("\n🔧 Opção 1: Removendo arestas com peso baixo...")
peso_minimo = 1  # MUDE AQUI: 2, 3, 4, 5...
g.es.select(weight_lt=peso_minimo).delete()
print(f"   Arestas após peso >= {peso_minimo}: {g.ecount():,}")

# --- OPÇÃO 2: Remover nós isolados (grau 0) ---
print("\n🔧 Opção 2: Removendo nós isolados...")
vertices_antes = g.vcount()
g = g.subgraph([v for v in range(g.vcount()) if g.degree(v) > 0])
print(f"   Nós após remover isolados: {g.vcount():,} (removidos: {vertices_antes - g.vcount():,})")

# --- OPÇÃO 3: Remover nós com grau baixo (poucas conexões) ---
print("\n🔧 Opção 3: Removendo nós com grau baixo...")
grau_minimo = 1  # MUDE AQUI: 1, 2, 3...
vertices_antes = g.vcount()
g = g.subgraph([v for v in range(g.vcount()) if g.degree(v) >= grau_minimo])
print(f"   Nós após grau >= {grau_minimo}: {g.vcount():,} (removidos: {vertices_antes - g.vcount():,})")

# --- OPÇÃO 4: Amostragem aleatória (pegar X% dos nós) ---
print("\n🔧 Opção 4: Amostragem aleatória...")
fracao = 0.3  # MUDE AQUI: 0.1, 0.2, 0.3, 0.5...
if fracao < 1.0:
    n_amostra = int(g.vcount() * fracao)
    random.seed(42)
    indices_amostra = random.sample(range(g.vcount()), n_amostra)
    g = g.subgraph(indices_amostra)
    print(f"   Nós após amostragem ({fracao*100:.0f}%): {g.vcount():,}")



# ============================================
# 3. ESTATÍSTICAS FINAIS
# ============================================

print("\n" + "="*60)
print("📊 GRAFO FINAL")
print("="*60)
print(f"Nós: {g.vcount():,}")
print(f"Arestas: {g.ecount():,}")
print(f"Densidade: {g.density():.6f}")

# Distribuição das comunidades
if 'leiden' in g.vs.attributes():
    contagem = Counter(g.vs['leiden'])
    print(f"\nComunidades no grafo final: {len(contagem)}")
    print("Top 10 maiores comunidades:")
    for com_id, tamanho in contagem.most_common(10):
        print(f"   Comunidade {int(com_id)}: {tamanho:,} nós")

# ============================================
# 4. SALVAR
# ============================================

print("\n💾 Salvando grafo reduzido...")
g.write_graphml("grafo_videos_reduzido.graphml")
print(f"✅ grafo_videos_reduzido.graphml")

# Salvar nós


print("\n🎉 PROCESSO CONCLUÍDO!")