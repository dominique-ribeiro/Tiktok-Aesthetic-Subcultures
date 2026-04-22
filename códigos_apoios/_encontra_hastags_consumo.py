import pandas as pd
import os
from glob import glob
import re

# ============================================
# 1. LISTA COMPLETA DE HASHTAGS DE CONSUMO
# ============================================

hashtags_consumo = [
    # Moda
    'outfit', 'ootd', 'look', 'style', 'fashion', 'moda', 'clothes', 'clothing',
    'wear', 'dress', 'outfitinspo', 'outfitidea', 'outfitideas', 'lookbook',
    'streetwear', 'fit', 'fits', 'fitcheck', 'tryon', 'tryonhaul', 'whatiwore',
    'dailyoutfit', 'summeroutfit', 'winteroutfit', 'falloutfit', 'springoutfit',
    'vintage',
    'haul', 'clothinghaul', 'sheinhaul', 'zarahaul', 'amazonhaul', 'haultok',
    'haulvideo', 'haulpost', 'haulcontent',
    'wardrobe', 'wardrobeessentials', 'capsulewardrobe', 'shoes', 'sneakers',
    'boots', 'heels', 'jeans', 'pants', 'leggings', 'shorts', 'skirt', 'top',
    'blouse', 'shirt', 'sweater', 'hoodie', 'jacket', 'coat', 'blazer',
    'lingerie', 'swimsuit', 'bikini', 'activewear', 'gymwear', 'sportswear',
    
    # Beleza
    'makeup', 'beauty', 'skincare', 'cosmetics', 'lipstick', 'foundation',
    'concealer', 'blush', 'bronzer', 'highlighter', 'eyeshadow', 'eyeliner',
    'mascara', 'brows', 'lashes', 'primer', 'setting spray', 'moisturizer',
    'serum', 'sunscreen', 'toner', 'cleanser', 'face wash', 'exfoliator',
    'haircare', 'hair', 'shampoo', 'conditioner', 'hair mask', 'hair oil',
    'perfume', 'fragrance', 'skincareroutine', 'beautyhaul', 'sephora', 'ulta',
    
    # Casa
    'roominspo', 'homeinspo', 'furniture',
    'homeimprovement', 'renovation', 'organization',
    'lighting', 'rug', 'curtain', 'pillow', 'blanket', 'wall art', 'mirror',
    
    # Compras
    'shopping', 'shop', 'buy', 'purchase', 'bought', 'sale', 'discount',
    'deal', 'clearance', 'blackfriday', 'primeday', 'shein', 'zara', 'hm',
    'forever21', 'asos', 'amazon', 'amazonfinds', 'walmart', 'target',
    'nike', 'adidas', 'gucci', 'prada', 'wishlist', 'gift', 'giftidea',
    'treatyourself', 'selfcare', 'retailtherapy', 'dollarstore', 'shopee',
    'comprinhas', 'comprinhasshein', 'compras', 'comprinha', 'mall', 'malltok',
    'shoppingtok',
    
    # Acessórios
    'jewelry', 'necklace', 'earrings', 'bracelet', 'ring', 'watch', 'bag',
    'handbag', 'purse', 'backpack', 'wallet', 'sunglasses', 'hat', 'scarf',
    'belt', 'hair clip', 'headband',
    
    # Tendências
    'core', 'aesthetic', 'vibe', 'trend', 'trending', 'moodboard',
    'cleangirl', 'thatgirl', 'cottagecore', 'darkacademia', 'coquette',
    'oldmoney', 'softgirl', 'gorpcore', 'grunge',
    
    # Genéricas
    'haul', 'unboxing', 'review', 'favorite', 'monthlyfavorite', 'empties',
    'projectpan', 'shopwithme', 'whatsinmybag', 'budget', 'affordable',
    'luxury', 'premium', 'giftguide', 'backtoschool', 'pet', 'baby',
]

# Converter para set para busca mais rápida
hashtags_consumo_set = set([tag.lower() for tag in hashtags_consumo])

print(f"📋 Total de hashtags de consumo: {len(hashtags_consumo_set)}")
print(f"   Exemplos: {list(hashtags_consumo_set)[:20]}")

# ============================================
# 2. FUNÇÃO PARA CLASSIFICAR VÍDEO
# ============================================

def video_e_consumo(hashtags_lista):
    """
    Verifica se um vídeo tem hashtag de consumo.
    hashtags_lista pode ser: lista, string com colchetes, ou string de texto.
    """
    if not hashtags_lista:
        return False
    
    # Se for string, tentar converter para lista
    if isinstance(hashtags_lista, str):
        # Se for string com colchetes (ex: "['tag1', 'tag2']")
        if hashtags_lista.startswith('['):
            try:
                import ast
                hashtags_lista = ast.literal_eval(hashtags_lista)
            except:
                # Se falhar, tenta extrair com regex
                import re
                hashtags_lista = re.findall(r"'([^']+)'", hashtags_lista)
        else:
            # String normal, dividir por espaço
            hashtags_lista = hashtags_lista.split()
    
    # Se não for lista, retorna False
    if not isinstance(hashtags_lista, list):
        return False
    
    # Verificar se alguma hashtag está na lista de consumo
    for tag in hashtags_lista:
        tag_clean = tag.lower().strip('#')
        if tag_clean in hashtags_consumo_set:
            return True
    
    return False

# ============================================
# 3. PROCESSAR TODOS OS CSVs DA PASTA data_2
# ============================================

PASTA_ORIGEM = "/home/hugo/materias/MC859/Tiktok-Aesthetic-Subcultures/data_2"
PASTA_DESTINO = "/home/hugo/materias/MC859/Tiktok-Aesthetic-Subcultures/data_2_com_consumo"

# Criar pasta de destino
os.makedirs(PASTA_DESTINO, exist_ok=True)

print("\n" + "="*60)
print("🛍️ CLASSIFICANDO VÍDEOS POR CONSUMO")
print("="*60)
print(f"📁 Pasta de origem: {PASTA_ORIGEM}")
print(f"📁 Pasta de destino: {PASTA_DESTINO}")

# Listar todos os CSVs
arquivos = glob(os.path.join(PASTA_ORIGEM, "*.csv"))
print(f"📄 Arquivos encontrados: {len(arquivos)}")

# Estatísticas gerais
total_videos = 0
total_consumo = 0
resultados_por_arquivo = []

# Processar cada arquivo
for i, arquivo in enumerate(arquivos, 1):
    nome_arquivo = os.path.basename(arquivo)
    print(f"\n[{i}/{len(arquivos)}] Processando: {nome_arquivo}")
    
    try:
        df = pd.read_csv(arquivo)
        print(f"   Vídeos: {len(df)}")
        
        # Verificar se coluna 'hashtags' existe
        if 'hashtags' not in df.columns:
            print(f"   ⚠️ Coluna 'hashtags' não encontrada! Pulando...")
            continue
        
        # Classificar vídeos
        df['consumo'] = df['hashtags'].apply(video_e_consumo)
        
        # Contar
        n_consumo = df['consumo'].sum()
        n_total = len(df)
        
        print(f"   🛍️ Vídeos de consumo: {n_consumo} ({100*n_consumo/n_total:.1f}%)")
        
        # Atualizar estatísticas
        total_videos += n_total
        total_consumo += n_consumo
        resultados_por_arquivo.append({
            'arquivo': nome_arquivo,
            'total_videos': n_total,
            'videos_consumo': n_consumo,
            'percentual': 100 * n_consumo / n_total
        })
        
        # Salvar arquivo processado
        arquivo_destino = os.path.join(PASTA_DESTINO, nome_arquivo)
        df.to_csv(arquivo_destino, index=False)
        print(f"   ✅ Salvo em: {arquivo_destino}")
        
    except Exception as e:
        print(f"   ❌ Erro: {e}")

# ============================================
# 4. RESUMO FINAL
# ============================================

print("\n" + "="*60)
print("📊 RESUMO FINAL")
print("="*60)
print(f"✅ Total de vídeos processados: {total_videos:,}")
print(f"✅ Vídeos com consumo identificado: {total_consumo:,}")
print(f"✅ Percentual geral: {100*total_consumo/total_videos:.1f}%")

# Salvar resultados por arquivo
df_resumo = pd.DataFrame(resultados_por_arquivo)
df_resumo.to_csv(os.path.join(PASTA_DESTINO, "resumo_consumo.csv"), index=False)
print(f"\n✅ Resumo salvo em: {PASTA_DESTINO}/resumo_consumo.csv")

# Mostrar top arquivos com mais consumo
print("\n📊 Top 10 arquivos com maior percentual de consumo:")
top_arquivos = df_resumo.nlargest(10, 'percentual')
for _, row in top_arquivos.iterrows():
    print(f"   {row['arquivo']}: {row['percentual']:.1f}% ({row['videos_consumo']:,}/{row['total_videos']:,})")

print("\n🎉 PROCESSO CONCLUÍDO!")