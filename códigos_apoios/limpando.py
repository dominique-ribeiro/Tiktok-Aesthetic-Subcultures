#NetworkX
#igraph
#graph-tool
#CPLEX pra Prog Inteirw
# pra detecção de comunidades: Louvain, Leiden
#python-igraf



import pandas as pd
import re
import emoji
import os
from glob import glob
from collections import Counter

# ============================================
# 1. CONFIGURAÇÕES INICIAIS
# ============================================

# Defina o caminho da pasta com os CSVs
CAMINHO_PASTA = "/home/hugo/materias/MC859/Tiktok-Aesthetic-Subcultures/data_2"

# ============================================
# 2. FUNÇÕES DE LIMPEZA
# ============================================

def extrair_criador_do_link(link):
    """
    Extrai o nome do criador do link do TikTok.
    Exemplo: https://www.tiktok.com/@amylian18/video/...
    Retorna: 'amylian18'
    """
    if pd.isna(link) or not isinstance(link, str):
        return None
    
    padrao = r'@([a-zA-Z0-9_\.]+)'
    match = re.search(padrao, link)
    
    if match:
        return match.group(1)
    return None


def limpar_hashtag(hashtag):
    """
    Limpa uma hashtag individual:
    - Remove emojis
    - Remove o '#' do início
    - Remove caracteres especiais (mantém letras, números, underscore)
    - Converte para minúsculas
    """
    if not isinstance(hashtag, str):
        return ""
    
    # 1. Remover emojis
    hashtag = emoji.replace_emoji(hashtag, replace='')
    
    # 2. Remover o '#' do início
    hashtag = hashtag.lstrip('#')
    
    # 3. Remover caracteres especiais (mantém a-z, A-Z, 0-9, _)
    hashtag = re.sub(r'[^a-zA-Z0-9_]', '', hashtag)
    
    # 4. Converter para minúsculas
    hashtag = hashtag.lower()
    
    # 5. Remover espaços extras
    hashtag = hashtag.strip()
    
    return hashtag


def limpar_lista_hashtags(lista_hashtags):
    """
    Recebe uma string representando uma lista Python ou uma lista já parseada.
    Retorna: lista de hashtags limpas.
    """
    if isinstance(lista_hashtags, list):
        hashtags_raw = lista_hashtags
    elif isinstance(lista_hashtags, str):
        if lista_hashtags.strip() in ['', '[]', 'nan', 'None']:
            return []
        try:
            hashtags_raw = eval(lista_hashtags)
        except:
            hashtags_raw = re.findall(r'#([^#\s]+)', lista_hashtags)
    else:
        return []
    
    if not isinstance(hashtags_raw, list):
        return []
    
    hashtags_limpas = [limpar_hashtag(tag) for tag in hashtags_raw]
    hashtags_limpas = [tag for tag in hashtags_limpas if tag]
    
    return hashtags_limpas


def limpar_valor_booleano(valor):
    """Converte valores para booleano (True/False)"""
    if pd.isna(valor):
        return False
    if isinstance(valor, bool):
        return valor
    if isinstance(valor, str):
        return valor.lower() in ['true', '1', 'yes', 'sim']
    if isinstance(valor, (int, float)):
        return bool(valor)
    return False


def limpar_e_salvar_csv(arquivo):
    """
    Lê um CSV, limpa os dados, e SALVA POR CIMA do arquivo original.
    """
    print(f"   📄 Lendo {os.path.basename(arquivo)}...")
    df = pd.read_csv(arquivo)
    tamanho_original = len(df)
    
    # --- Extrair criador do link ---
    df['criador'] = df['video_link'].apply(extrair_criador_do_link)
    
    # --- Limpar hashtags ---
    df['hashtags'] = df['hashtags'].apply(limpar_lista_hashtags)
    
    # --- Limpar colunas numéricas ---
    colunas_numericas = ['likes', 'comentarios', 'visualizacoes']
    for col in colunas_numericas:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # --- Limpar colunas booleanas ---
    colunas_booleanas = ['patrocinado', 'anuncio', 'tiktok_shop', 'business_account', 'conta_oficial']
    for col in colunas_booleanas:
        if col in df.columns:
            df[col] = df[col].apply(limpar_valor_booleano)
    
    # --- Converter timestamp ---
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    
    # --- Remover linhas sem hashtags (opcional, comente se não quiser) ---
    # df = df[df['hashtags'].map(len) > 0]
    
    # --- SALVAR POR CIMA DO ARQUIVO ORIGINAL ---
    df.to_csv(arquivo, index=False)
    
    print(f"   ✅ Salvo: {len(df)}/{tamanho_original} linhas mantidas")
    
    return len(df)


# ============================================
# 3. PROCESSAR TODOS OS CSVs DA PASTA
# ============================================

print("=" * 50)
print("🚀 INICIANDO LIMPEZA DOS CSVs (sobrescrevendo originais)")
print("=" * 50)

# Encontrar todos os arquivos CSV
arquivos = glob(os.path.join(CAMINHO_PASTA, "*.csv"))

if not arquivos:
    print(f"❌ Nenhum arquivo CSV encontrado em: {CAMINHO_PASTA}")
else:
    print(f"📁 Encontrados {len(arquivos)} arquivos CSV\n")
    
    total_videos_inicial = 0
    total_videos_final = 0
    
    for i, arquivo in enumerate(arquivos, 1):
        print(f"[{i}/{len(arquivos)}] Processando...")
        
        # Contar linhas originais (aproximado, só para estatística)
        df_temp = pd.read_csv(arquivo)
        linhas_antes = len(df_temp)
        total_videos_inicial += linhas_antes
        
        # Limpar e salvar
        linhas_depois = limpar_e_salvar_csv(arquivo)
        total_videos_final += linhas_depois
    
    print("\n" + "=" * 50)
    print("📊 RESUMO FINAL")
    print("=" * 50)
    print(f"✅ Arquivos processados: {len(arquivos)}")
    print(f"✅ Total de vídeos antes: {total_videos_inicial}")
    print(f"✅ Total de vídeos depois: {total_videos_final}")
    print(f"✅ Removidos: {total_videos_inicial - total_videos_final} (sem hashtags)")
    
    print("\n💡 Todos os CSVs foram sobrescritos com os dados limpos!")

print("\n" + "=" * 50)
print("🔍 EXEMPLO DO QUE FOI FEITO EM CADA ARQUIVO")
print("=" * 50)
print(""" 
Antes (coluna hashtags):
    "['#?gachallife💜même', '#fypp', '#fouryou']"

Depois (coluna hashtags):
    ['gachallifemme', 'fypp', 'fouryou']

Antes (coluna criador):
    vazia ou None

Depois (coluna criador):
    'amylian18' (extraído do video_link)
""")