import igraph as ig
import pandas as pd

# ============================================
# 1. CARREGAR O GRAFO COM AS COMUNIDADES
# ============================================

print("📁 Carregando grafo com comunidades...")

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

print(f"Nós: {g.vcount():,}")
print(f"Comunidades: {len(set(g.vs['leiden'])):,}")

# ============================================
# 2. CARREGAR O CSV ORIGINAL DE NÓS
# ============================================

print("\n📁 Carregando nodes_list.csv...")

df_nodes = pd.read_csv("nodes_20-04.csv")
print(f"   Nós no CSV: {len(df_nodes)}")

# Verificar se o número de nós bate
if len(df_nodes) != g.vcount():
    print(f"   ⚠️ Atenção: CSV tem {len(df_nodes)} nós, grafo tem {g.vcount()} nós")
    print("   Tentando alinhar por ID...")

# ============================================
# 3. ADICIONAR A COLUNA DE COMUNIDADE
# ============================================

print("\n🔧 Adicionando coluna 'comunidade_leiden'...")

# Método 1: se a ordem é a mesma (recomendado)
if len(df_nodes) == g.vcount():
    df_nodes['comunidade_leiden'] = g.vs['leiden']
    print("   ✅ Coluna adicionada (mesma ordem)")
else:
    # Método 2: alinhar pelo ID (se houver coluna 'Id' ou 'id')
    print("   Alinhando por ID...")
    
    # Verificar qual coluna de ID existe
    col_id = None
    for possivel in ['Id', 'id', 'ID', 'node_id']:
        if possivel in df_nodes.columns:
            col_id = possivel
            break
    
    if col_id is None:
        print("   ❌ Não foi possível alinhar: coluna de ID não encontrada!")
        exit(1)
    
    # Criar dicionário: ID -> comunidade
    id_para_comunidade = {}
    for i in range(g.vcount()):
        node_id = g.vs['id'][i] if 'id' in g.vs.attributes() else str(i)
        id_para_comunidade[node_id] = g.vs['leiden'][i]
    
    # Aplicar ao DataFrame
    df_nodes['comunidade_leiden'] = df_nodes[col_id].astype(str).map(id_para_comunidade)
    print("   ✅ Coluna adicionada (alinhada por ID)")

# ============================================
# 4. VERIFICAR SE HÁ VALORES NULOS
# ============================================

nulos = df_nodes['comunidade_leiden'].isna().sum()
if nulos > 0:
    print(f"\n⚠️ Atenção: {nulos} nós não tiveram comunidade atribuída")

# ============================================
# 5. SALVAR NOVO CSV
# ============================================

print("\n💾 Salvando novo arquivo...")

df_nodes.to_csv("nodes_list_com_comunidades.csv", index=False)
print(f"✅ nodes_list_com_comunidades.csv salvo!")

# ============================================
# 6. MOSTRAR PRÉVIA
# ============================================

print("\n📋 PRÉVIA DO NOVO ARQUIVO:")
print("="*60)
print(df_nodes.head(10))
print("="*60)

print("\n📊 DISTRIBUIÇÃO DAS COMUNIDADES:")
print(df_nodes['comunidade_leiden'].value_counts().head(20))

print("\n🎉 PROCESSO CONCLUÍDO!")