import pandas as pd
import os
from glob import glob
from collections import Counter

# ============================================
# CONFIGURAÇÕES
# ============================================

CAMINHO_PASTA = "/home/hugo/materias/MC859/Tiktok-Aesthetic-Subcultures/data_2"  # ou data_2, onde estão seus CSVs
ARQUIVO_SAIDA = "frequencia_criadores.csv"

print("="*60)
print("👤 ANALISANDO FREQUÊNCIA DOS CRIADORES")
print("="*60)

# 1. Ler todos os CSVs
print("\n📁 Lendo CSVs...")
arquivos = glob(os.path.join(CAMINHO_PASTA, "*.csv"))
print(f"Encontrados {len(arquivos)} arquivos")

dfs = []
for arq in arquivos:
    df_temp = pd.read_csv(arq)
    dfs.append(df_temp)

df = pd.concat(dfs, ignore_index=True)
print(f"Total de vídeos (bruto): {len(df)}")

# 2. Remover duplicatas (mesmo vídeo pode estar em várias pastas)
df = df.drop_duplicates(subset=['video_link'])
print(f"Após remover duplicatas: {len(df)}")

# 3. Verificar se a coluna 'criador' existe
if 'criador' not in df.columns:
    print("\n❌ Coluna 'criador' não encontrada!")
    print(f"Colunas disponíveis: {list(df.columns)}")
    exit(1)

# 4. Contar frequência dos criadores
print("\n👤 Contando frequência dos criadores...")
contador_criadores = Counter()

# Filtrar valores vazios/nulos
criadores_validos = df['criador'].dropna()
criadores_validos = criadores_validos[criadores_validos != ""]

contador_criadores.update(criadores_validos)

print(f"Total de criadores únicos: {len(contador_criadores)}")
print(f"Total de ocorrências: {sum(contador_criadores.values())}")

# 5. Mostrar TOP 50 criadores
print("\n" + "="*60)
print("🏆 TOP 50 CRIADORES MAIS FREQUENTES")
print("="*60)

top_50 = contador_criadores.most_common(50)

for i, (criador, freq) in enumerate(top_50, 1):
    print(f"{i:3d}. @{criador}: {freq:6,d} vídeos")

# 6. Salvar lista completa
print("\n💾 Salvando listas...")
df_criadores = pd.DataFrame(contador_criadores.most_common(), 
                            columns=['criador', 'frequencia'])
df_criadores.to_csv(ARQUIVO_SAIDA, index=False)
print(f"✅ Lista completa salva em: {ARQUIVO_SAIDA}")

# 7. Estatísticas adicionais
print("\n" + "="*60)
print("📈 ESTATÍSTICAS")
print("="*60)

# Criadores que aparecem apenas 1 vez
unicos = sum(1 for freq in contador_criadores.values() if freq == 1)
print(f"Criadores que aparecem apenas 1 vez: {unicos} ({100*unicos/len(contador_criadores):.1f}%)")

# Criadores com mais de 10 vídeos
frequentes = sum(1 for freq in contador_criadores.values() if freq >= 10)
print(f"Criadores com 10+ vídeos: {frequentes} ({100*frequentes/len(contador_criadores):.1f}%)")

# Criador mais frequente
mais_frequente = contador_criadores.most_common(1)[0]
print(f"\n🥇 Criador mais frequente: @{mais_frequente[0]} com {mais_frequente[1]} vídeos")

# 8. Salvar também um CSV com os vídeos de cada criador (opcional)
print("\n📝 Gerando lista de vídeos por criador...")
criador_para_videos = {}
for idx, row in df.iterrows():
    criador = row['criador']
    if pd.isna(criador) or criador == "":
        continue
    if criador not in criador_para_videos:
        criador_para_videos[criador] = []
    criador_para_videos[criador].append(row['video_link'])

# Salvar top 10 criadores com seus vídeos
top_10_nomes = [c for c, _ in top_50[:10]]
df_top_videos = []
for criador in top_10_nomes:
    for video in criador_para_videos.get(criador, [])[:10]:  # 10 vídeos por criador
        df_top_videos.append({'criador': criador, 'video_link': video})

df_top_videos = pd.DataFrame(df_top_videos)
df_top_videos.to_csv("top_criadores_videos.csv", index=False)
print(f"✅ Top criadores com vídeos salvos em: top_criadores_videos.csv")

print("\n" + "="*60)
print("🎉 ANÁLISE CONCLUÍDA!")
print("="*60)