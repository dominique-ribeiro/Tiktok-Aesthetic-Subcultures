import igraph as ig
import pandas as pd

# ============================================
# 1. LISTA DAS COMUNIDADES QUE VOCÊ QUER MANTER
# ============================================

comunidades_para_manter = [
    11.0, 48.0, 56.0, 96.0, 3.0, 8.0, 115.0, 53.0, 83.0, 198.0,
    69.0, 4.0, 15.0, 121.0, 213.0, 297.0, 760.0, 582.0, 376.0,
    1.0, 1344.0, 126.0, 2342.0, 161.0, 692.0, 63.0, 434.0
]

# Converter para inteiro (já que as comunidades são números inteiros)
comunidades_para_manter = [int(c) for c in comunidades_para_manter]

print("="*60)
print("🎯 FILTRANDO GRAFO POR COMUNIDADES")
print("="*60)
print(f"Comunidades a manter: {sorted(comunidades_para_manter)}")
print(f"Total: {len(comunidades_para_manter)} comunidades")

# ============================================
# 2. CARREGAR O GRAFO COMPLETO
# ============================================

print("\n📁 Carregando grafo completo...")

g = None
metodos = [
    lambda: ig.Graph.Read_GraphML("grafo_videos_com_leiden.graphml"),
    lambda: ig.Graph.Read_Graphml("grafo_videos_com_leiden.graphml"),
    lambda: ig.load("grafo_videos_com_leiden.graphml"),
]

for metodo in metodos:
    try:
        g = metodo()
        print(f"   ✅ Carregado com sucesso!")
        break
    except:
        continue

if g is None:
    print("❌ Não foi possível carregar o grafo!")
    exit(1)

print(f"   Nós originais: {g.vcount():,}")
print(f"   Arestas originais: {g.ecount():,}")
print(f"   Comunidades originais: {len(set(g.vs['leiden'])):,}")

# ============================================
# 3. SELECIONAR OS NÓS DAS COMUNIDADES DESEJADAS
# ============================================

print("\n🔧 Selecionando nós das comunidades desejadas...")

# Criar lista de índices dos nós a manter
indices_para_manter = []
for i in range(g.vcount()):
    if g.vs['leiden'][i] in comunidades_para_manter:
        indices_para_manter.append(i)

print(f"   Nós selecionados: {len(indices_para_manter):,}")

# ============================================
# 4. CRIAR SUBGRAFO
# ============================================

print("\n🔧 Criando subgrafo filtrado...")
g_filtrado = g.subgraph(indices_para_manter)

print(f"   ✅ Grafo filtrado criado!")
print(f"   Nós no grafo filtrado: {g_filtrado.vcount():,}")
print(f"   Arestas no grafo filtrado: {g_filtrado.ecount():,}")

# ============================================
# 5. SALVAR O GRAFO FILTRADO
# ============================================

print("\n💾 Salvando grafo filtrado...")
g_filtrado.write_graphml("grafo_videos_filtrado.graphml")
print(f"   ✅ grafo_videos_filtrado.graphml")

# ============================================
# 6. CRIAR CSV COM OS NÓS FILTRADOS
# ============================================

print("\n📊 Criando CSV com os nós filtrados...")

df_filtrado = pd.DataFrame({
    'id': g_filtrado.vs['id'] if 'id' in g_filtrado.vs.attributes() else range(g_filtrado.vcount()),
    'label': g_filtrado.vs['label'] if 'label' in g_filtrado.vs.attributes() else '',
    'category': g_filtrado.vs['category'] if 'category' in g_filtrado.vs.attributes() else '',
    'comunidade': g_filtrado.vs['leiden']
})

df_filtrado.to_csv("nodes_filtrados.csv", index=False)
print(f"   ✅ nodes_filtrados.csv")


# ============================================
# 8. SALVAR ARQUIVO DE ARESTAS FILTRADO (OPCIONAL)
# ============================================

print("\n🔧 Criando CSV de arestas filtradas...")

edges = []
for edge in g_filtrado.es:
    source = edge.source
    target = edge.target
    weight = edge['weight'] if 'weight' in edge.attributes() else 1
    edges.append({
        'Source': source,
        'Target': target,
        'Weight': weight
    })

df_edges = pd.DataFrame(edges)
df_edges.to_csv("edges_filtradas.csv", index=False)
print(f"   ✅ edges_filtradas.csv ({len(df_edges)} arestas)")

print("\n" + "="*60)
print("🎉 PROCESSO CONCLUÍDO!")
print("="*60)
print("\n📁 Arquivos gerados:")
print("   - grafo_videos_filtrado.graphml (para abrir no Gephi)")
print("   - nodes_filtrados.csv")
print("   - edges_filtradas.csv")