import pandas as pd
import glob
import os
import json
import csv
from collections import defaultdict
from itertools import combinations

# --- Configurações ---
FOLDER_PATH = '/home/hugo/materias/MC859/Tiktok-Aesthetic-Subcultures/data_2' 
OUTPUT_EDGES = 'edges_list.csv'
OUTPUT_NODES = 'nodes_list.csv'

# Sua lista de exclusão estendida
EXCLUDE_TAGS = {
    'fyp', 'aesthetic', 'edit', 'viral', 'foryou', 'foryoupage', 'core',
    'fyppppppppppppppppppppppp', 'fy', 'capcut', 'fypviral', 'moodboard', 'pinterest', 'vibes',
    'vibe', 'aestheticvideos', 'xyzbca', 'fypage', 'aestheticedits', 'tiktok', 
    'targetaudience', 'edits', 'fypp', 'aestheticedit', 'asthetic', 'fyy', 
    'foryoupag', 'repost', 'fyppp', 'viraltiktok', 'xybca', 'fyyyyyyyyyyyyyyyy',
    'fup', 'vaiprofycaramba', 'fu', 'paratiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii', 'parati', 
    'fouryou', 'aestetic', 'corecore', 'fashion', 'dreamcore', 'mecore', 'nature', 'fashion', 'outfit', 
}

def process_massive_graph():
    all_files = glob.glob(os.path.join(FOLDER_PATH, "*.csv"))
    tag_to_videos = defaultdict(list)
    video_metadata = {}

    print(">>> Fase 1: Indexando vídeos e hashtags...")
    video_id_counter = 0
    
    with open(OUTPUT_NODES, 'w', newline='', encoding='utf-8') as f_nodes:
        node_writer = csv.writer(f_nodes)
        node_writer.writerow(['Id', 'Label', 'Likes', 'Category'])

        for file in all_files:
            category = os.path.basename(file).replace('.csv', '')
            try:
                # Lendo apenas colunas necessárias para economizar RAM
                df = pd.read_csv(file, usecols=['video_link', 'likes', 'hashtags'])
                df = df.drop_duplicates(subset=['video_link'])
                
                for _, row in df.iterrows():
                    v_link = row['video_link']
                    if v_link not in video_metadata:
                        v_id = video_id_counter
                        video_metadata[v_link] = v_id
                        video_id_counter += 1
                        
                        # Salva nó no disco
                        node_writer.writerow([v_id, v_link, row['likes'], category])
                        
                        # Processa hashtags
                        try:
                            # Converte string '[#tag1, #tag2]' para lista
                            tags_raw = row['hashtags'].strip("[]").replace("'", "").replace("#", "").split(", ")
                            for t in tags_raw:
                                t = t.lower().strip()
                                if t and t not in EXCLUDE_TAGS:
                                    tag_to_videos[t].append(v_id)
                        except: continue
            except Exception as e:
                print(f"Erro no arquivo {file}: {e}")

    print(f">>> Total de vídeos únicos: {video_id_counter}")
    print(f">>> Total de hashtags únicas (pós-filtro): {len(tag_to_videos)}")

    print(">>> Fase 2: Gerando arestas (escrita direta em disco)...")
    edge_counts = defaultdict(int)
    
    # Para economizar RAM, vamos processar as combinações e contar pesos
    # Se o número de arestas for colossal, usamos um dicionário de contagem
    with open(OUTPUT_EDGES, 'w', newline='', encoding='utf-8') as f_edges:
        edge_writer = csv.writer(f_edges)
        edge_writer.writerow(['Source', 'Target', 'Weight', 'Type'])
        
        for tag, videos in tag_to_videos.items():
            # Limite de segurança: se uma tag aparece em mais de 1750 vídeos (mesmo pós filtro)
            # ela pode gerar 500k arestas sozinha. Vamos monitorar isso.
            if len(videos) > 1500: 
                print(f"Aviso: Tag #{tag} é muito comum ({len(videos)} vídeos). Ignorando para evitar explosão de dados.")
                continue
                
            if len(videos) > 1:
                for v1, v2 in combinations(videos, 2):
                    # Usamos uma chave ordenada para contar pesos
                    pair = tuple(sorted((v1, v2)))
                    edge_counts[pair] += 1
        
        print(">>> Escrevendo arestas no arquivo...")
        for (v1, v2), weight in edge_counts.items():
            edge_writer.writerow([v1, v2, weight, 'Undirected'])

    print(f"\n>>> CONCLUÍDO!")
    print(f"Arquivos gerados: {OUTPUT_NODES} e {OUTPUT_EDGES}")
    print("IMPORTANTE: Abra esses dois arquivos no Gephi (Import Spreadsheet).")

if __name__ == "__main__":
    process_massive_graph()
