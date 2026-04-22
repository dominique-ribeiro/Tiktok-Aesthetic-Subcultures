"""
Leiden sobre hashtag_graph.graphml

Fluxo:
  1_grafo_hashtags.py  →  hashtag_graph.graphml
  este script          →  hashtag_graph_com_clusters.csv   ← lido pelo script 2
                       →  grafo_videos_com_leiden.graphml  ← visualização

Correções em relação à versão anterior:
  - Constrói o mapeamento video_link → índice inteiro explicitamente,
    evitando quebra quando IDs não são 0-indexados contíguos.
  - Saída em CSV usa coluna 'cluster' (esperada pelo script 2).
  - Exporta todos os atributos originais dos nós, não só id/label/category.
"""

import igraph as ig
import networkx as nx
import pandas as pd
from collections import Counter

GRAFO_ENTRADA = "/home/hugo/materias/MC859/Tiktok-Aesthetic-Subcultures/grafos/hashtag_graph.graphml"
CSV_SAIDA     = "/home/hugo/materias/MC859/Tiktok-Aesthetic-Subcultures/grafos/hashtag_graph_com_clusters.csv"
GRAPHML_SAIDA = "/home/hugo/materias/MC859/Tiktok-Aesthetic-Subcultures/grafos/grafo_videos_com_leiden.graphml"

# ── 1. Carregar o graphml gerado pelo script 1 ────────────────
print("Carregando grafo...")
G_nx = nx.read_graphml(GRAFO_ENTRADA)
print(f"  Nós: {G_nx.number_of_nodes():,}")
print(f"  Arestas: {G_nx.number_of_edges():,}")

# ── 2. Converter para igraph mantendo mapeamento explícito ────
# NetworkX usa strings como IDs; igraph precisa de índices inteiros.
# Construímos o mapeamento aqui para nunca depender de ordenação implícita.
print("\nConvertendo para igraph...")

nodes = list(G_nx.nodes())
node_para_idx = {node: i for i, node in enumerate(nodes)}

g = ig.Graph()
g.add_vertices(len(nodes))

# Copia todos os atributos dos nós
atributos_nos = list(next(iter(G_nx.nodes(data=True)))[1].keys())
for attr in atributos_nos:
    g.vs[attr] = [G_nx.nodes[n].get(attr, "") for n in nodes]

# Guarda o video_link (ID do nó no NetworkX) como atributo explícito
g.vs['video_link'] = nodes

# Adiciona arestas com peso
arestas = []
pesos   = []
for u, v, data in G_nx.edges(data=True):
    arestas.append((node_para_idx[u], node_para_idx[v]))
    pesos.append(float(data.get('weight', 1)))

g.add_edges(arestas)
g.es['weight'] = pesos

print(f"  Grafo igraph: {g.vcount():,} nós, {g.ecount():,} arestas")
print(f"  Densidade: {g.density():.6f}")

# ── 3. Filtrar arestas fracas ─────────────────────────────────
PESO_MIN = 2  # arestas com peso 1 = apenas 1 hashtag em comum, muito ruído
print(f"\nFiltrando arestas com peso < {PESO_MIN}...")
g.es.select(weight_lt=PESO_MIN).delete()
print(f"  Arestas após filtro: {g.ecount():,}")

if g.ecount() > 10_000_000:
    print(f"  ⚠ Ainda {g.ecount():,} arestas — considere aumentar PESO_MIN para 3 ou 4")

# ── 4. Leiden ─────────────────────────────────────────────────
# resolution: valores menores → comunidades maiores e menos numerosas
#             valores maiores → comunidades menores e mais numerosas
# Para dados de hashtags de TikTok, 0.05 costuma gerar comunidades temáticas
# coerentes. Ajuste se os clusters ficarem grandes demais ou pequenos demais.
RESOLUTION = 0.05

print(f"\nExecutando Leiden (resolution={RESOLUTION})...")
try:
    particao = g.community_leiden(
        weights='weight',
        resolution=RESOLUTION,
        n_iterations=-1   # roda até convergir
    )
    print(f"  Comunidades encontradas: {len(particao)}")
    print(f"  Modularidade: {particao.modularity:.4f}")

except MemoryError:
    print("  MemoryError — tentando Louvain como fallback...")
    particao = g.community_multilevel(weights='weight')
    print(f"  Comunidades (Louvain): {len(particao)}")
    print(f"  Modularidade: {particao.modularity:.4f}")

g.vs['cluster'] = particao.membership

# ── 5. Salvar graphml com clusters ────────────────────────────
print(f"\nSalvando graphml...")
# igraph não escreve booleans corretamente em graphml — converte para str
for attr in g.vs.attributes():
    if attr != 'cluster':
        try:
            sample = g.vs[0][attr]
            if isinstance(sample, bool):
                g.vs[attr] = [str(v) for v in g.vs[attr]]
        except Exception:
            pass

g.write_graphml(GRAPHML_SAIDA)
print(f"  ✅ {GRAPHML_SAIDA}")

# ── 6. Salvar CSV com coluna 'cluster' ────────────────────────
# Este CSV é a entrada do script 2_grafos_bipartidos.py
print("Salvando CSV com clusters...")

# Reconstrói o dataframe completo a partir dos atributos dos nós
registros = []
for v in g.vs:
    reg = {attr: v[attr] for attr in g.vs.attributes()}
    registros.append(reg)

df_saida = pd.DataFrame(registros)

# Garante que 'video_link' é a primeira coluna e 'cluster' está presente
cols = ['video_link', 'cluster'] + [c for c in df_saida.columns
                                     if c not in ('video_link', 'cluster')]
df_saida = df_saida[cols]

df_saida.to_csv(CSV_SAIDA, index=False)
print(f"  ✅ {CSV_SAIDA}")
print(f"  Linhas: {len(df_saida):,}")
print(f"  Colunas: {list(df_saida.columns)}")

# ── 7. Estatísticas ───────────────────────────────────────────
print(f"\n{'='*55}")
print("ESTATÍSTICAS DAS COMUNIDADES")
print(f"{'='*55}")

contagem = Counter(particao.membership)
print(f"Total de comunidades:  {len(contagem)}")
print(f"Maior comunidade:      {max(contagem.values()):,} nós")
print(f"Menor comunidade:      {min(contagem.values()):,} nós")
print(f"Média por comunidade:  {sum(contagem.values())/len(contagem):.1f} nós")

print("\nTop 10 maiores comunidades:")
for com_id, tamanho in contagem.most_common(10):
    # Quais grupos originais predominam nesta comunidade
    grupos = [g.vs['grupo_original'][i]
              for i in range(g.vcount())
              if particao.membership[i] == com_id]
    top_grupos = Counter(grupos).most_common(3)
    grupos_str = ", ".join(f"{gr}:{n}" for gr, n in top_grupos)
    print(f"  Cluster {com_id:>3}: {tamanho:>6,} nós  ({grupos_str})")

print("\n✅ Concluído!")