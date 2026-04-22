import igraph as ig
import pandas as pd
from collections import Counter
import ast

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
# 2. CARREGAR DADOS ORIGINAIS (para as hashtags)
# ============================================

print("\n📁 Carregando dados originais dos vídeos...")

# Tentar carregar o CSV original com os vídeos
import os
caminho_csv = "../data_2_2/country_2.csv"  # ajuste o caminho se necessário

# Ou usar o CSV de nós que você já tem
if os.path.exists("nodes_20-04.csv"):
    df_nodes = pd.read_csv("nodes_20-04.csv")
    print(f"   ✅ nodes_list.csv carregado com {len(df_nodes)} vídeos")
    
    # Se tiver a coluna de hashtags
    if 'hashtags' in df_nodes.columns:
        # Converter string de lista para lista real
        def parse_hashtags(x):
            if isinstance(x, list):
                return x
            if isinstance(x, str):
                try:
                    return ast.literal_eval(x)
                except:
                    return []
            return []
        df_nodes['hashtags_lista'] = df_nodes['hashtags'].apply(parse_hashtags)
    else:
        print("   ⚠️ Coluna 'hashtags' não encontrada")
else:
    print("   ⚠️ nodes_list.csv não encontrado, apenas categorias serão analisadas")
    df_nodes = None

# ============================================
# 3. CRIAR A TABELA DE COMUNIDADES
# ============================================

print("\n🔧 Criando tabela de comunidades...")

# Dicionário para armazenar dados de cada comunidade
comunidades_dict = {}

for i in range(g.vcount()):
    comunidade = g.vs['leiden'][i]
    categoria = g.vs['category'][i]
    
    if comunidade not in comunidades_dict:
        comunidades_dict[comunidade] = {
            'total_videos': 0,
            'categorias': Counter(),
            'hashtags': Counter()
        }
    
    comunidades_dict[comunidade]['total_videos'] += 1
    comunidades_dict[comunidade]['categorias'][categoria] += 1
    
    # Adicionar hashtags se disponível
    if df_nodes is not None and i < len(df_nodes):
        hashtags = df_nodes.iloc[i].get('hashtags_lista', [])
        if isinstance(hashtags, list):
            for tag in hashtags:
                comunidades_dict[comunidade]['hashtags'][tag] += 1

print(f"✅ Processadas {len(comunidades_dict)} comunidades")

# ============================================
# 4. ORDENAR POR TAMANHO (MAIOR PARA MENOR)
# ============================================

comunidades_ordenadas = sorted(
    comunidades_dict.items(),
    key=lambda x: x[1]['total_videos'],
    reverse=True
)

# ============================================
# 5. CRIAR DATAFRAME PARA O CSV
# ============================================

print("\n📊 Criando DataFrame...")

# Construir linhas do DataFrame
rows = []
for com_id, data in comunidades_ordenadas:
    row = {
        'comunidade_id': com_id,
        'total_videos': data['total_videos'],
        'num_categorias': len(data['categorias']),
        'num_hashtags': len(data['hashtags'])
    }
    
    # ========== TOP 10 CATEGORIAS ==========
    top_categorias = data['categorias'].most_common(10)
    for j, (cat, qtd) in enumerate(top_categorias, 1):
        row[f'cat_{j}_nome'] = cat
        row[f'cat_{j}_qtd'] = qtd
        row[f'cat_{j}_pct'] = f"{100 * qtd / data['total_videos']:.1f}%"
    
    # Preencher o resto com vazio se tiver menos de 10
    for j in range(len(top_categorias) + 1, 11):
        row[f'cat_{j}_nome'] = ''
        row[f'cat_{j}_qtd'] = 0
        row[f'cat_{j}_pct'] = ''
    
    # ========== TOP 10 HASHTAGS ==========
    top_hashtags = data['hashtags'].most_common(10)
    for j, (tag, qtd) in enumerate(top_hashtags, 1):
        row[f'hashtag_{j}_nome'] = tag
        row[f'hashtag_{j}_qtd'] = qtd
    
    # Preencher o resto com vazio se tiver menos de 10
    for j in range(len(top_hashtags) + 1, 11):
        row[f'hashtag_{j}_nome'] = ''
        row[f'hashtag_{j}_qtd'] = 0
    
    rows.append(row)

# Criar DataFrame
df_comunidades = pd.DataFrame(rows)

# ============================================
# 6. SALVAR CSV
# ============================================

df_comunidades.to_csv("comunidades_completas.csv", index=False)
print(f"\n✅ CSV salvo: comunidades_completas.csv")
print(f"   Total de comunidades: {len(df_comunidades)}")
print(f"   Colunas: {len(df_comunidades.columns)}")

# ============================================
# 7. MOSTRAR PRÉVIA
# ============================================

print("\n📋 PRÉVIA DAS PRIMEIRAS 3 COMUNIDADES:")
print("="*80)

for i in range(min(3, len(df_comunidades))):
    row = df_comunidades.iloc[i]
    print(f"\n🏷️  Comunidade {int(row['comunidade_id'])}:")
    print(f"   Total de vídeos: {int(row['total_videos']):,}")
    print(f"   Número de categorias: {int(row['num_categorias'])}")
    print(f"   Número de hashtags: {int(row['num_hashtags']):,}")
    
    print("\n   📂 TOP 5 CATEGORIAS:")
    for j in range(1, 6):
        cat = row.get(f'cat_{j}_nome', '')
        if cat:
            qtd = int(row[f'cat_{j}_qtd'])
            pct = row[f'cat_{j}_pct']
            print(f"      {j}. {cat}: {qtd:,} ({pct})")
    
    print("\n   🏷️  TOP 5 HASHTAGS:")
    for j in range(1, 6):
        tag = row.get(f'hashtag_{j}_nome', '')
        if tag:
            qtd = int(row[f'hashtag_{j}_qtd'])
            print(f"      {j}. #{tag}: {qtd:,}")
    
    print("-" * 50)

# ============================================
# 8. SALVAR VERSÃO SIMPLES
# ============================================

df_simples = pd.DataFrame([
    {
        'comunidade_id': com_id,
        'total_videos': data['total_videos'],
        'num_categorias': len(data['categorias']),
        'num_hashtags': len(data['hashtags']),
        'top_5_categorias': ', '.join([f"{cat}({qtd})" for cat, qtd in data['categorias'].most_common(5)]),
        'top_5_hashtags': ', '.join([f"#{tag}({qtd})" for tag, qtd in data['hashtags'].most_common(5)])
    }
    for com_id, data in comunidades_ordenadas
])

df_simples.to_csv("comunidades_resumo.csv", index=False)
print(f"\n✅ Versão resumo salva: comunidades_resumo.csv")

print("\n🎉 PROCESSO CONCLUÍDO!")