import pandas as pd
import os
import time
import random
import json
import re
from glob import glob
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, WebDriverException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

# ============================================================
# CONFIGURAÇÕES
# ============================================================

PASTA_ORIGEM = "/home/hugo/materias/MC859/Tiktok-Aesthetic-Subcultures/data_2"
PASTA_DESTINO = "/home/hugo/materias/MC859/Tiktok-Aesthetic-Subcultures/data_2_2"
CHECKPOINT_DIR = "/home/hugo/materias/MC859/Tiktok-Aesthetic-Subcultures/checkpoints_recolecao"

# Garantir que as pastas existem
os.makedirs(PASTA_DESTINO, exist_ok=True)
os.makedirs(CHECKPOINT_DIR, exist_ok=True)

# Configurações de tempo
TEMPO_ESPERA_VIDEO = 30
TEMPO_ENTRE_VIDEOS = (8, 12)
TENTATIVAS_REFRESH = 3
MAX_VIDEOS_POR_ARQUIVO = None  # None = todos, ou coloque um número para testar

# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def parse_count(text):
    """Converte texto de contagem (K, M) para número"""
    if not text:
        return None
    text = str(text).strip().upper().replace(',', '')
    multiplier = 1
    if 'K' in text:
        multiplier = 1000
        text = text.replace('K', '')
    elif 'M' in text:
        multiplier = 1000000
        text = text.replace('M', '')
    try:
        return int(float(text) * multiplier)
    except:
        return None


def aguardar_carregamento_video(driver, tentativa=1):
    """Espera o vídeo carregar com timeout automático"""
    print(f"   ⏳ Aguardando carregamento (até {TEMPO_ESPERA_VIDEO}s)...")
    inicio = time.time()
    
    while time.time() - inicio < TEMPO_ESPERA_VIDEO:
        elementos = driver.find_elements(By.CSS_SELECTOR, 'div[data-e2e="video-desc"], strong[data-e2e="like-count"]')
        if len(elementos) > 0:
            print(f"   ✅ Vídeo carregou após {int(time.time() - inicio)}s")
            return True
        time.sleep(1)
    
    if tentativa < TENTATIVAS_REFRESH:
        print(f"   🔄 Tentativa {tentativa+1}/{TENTATIVAS_REFRESH} - Refresh...")
        driver.refresh()
        time.sleep(5)
        return aguardar_carregamento_video(driver, tentativa + 1)
    
    print(f"   ❌ Vídeo não carregou após {TEMPO_ESPERA_VIDEO}s")
    return False


def extrair_data_publicacao(driver):
    """
    Extrai a data de publicação do vídeo.
    Chamar esta função ANTES de clicar em "Ler mais".
    """
    try:
        # Seletor que funcionou no teste
        elemento = driver.find_element(By.CSS_SELECTOR, 'span[data-e2e="video-date"]')
        texto = elemento.text.strip()
        if texto:
            print(f"   📅 Data: {texto}")
            return texto
    except:
        pass
    
    # Fallback: regex no código fonte
    try:
        page_source = driver.page_source
        match = re.search(r'(\d{4}-\d{1,2}-\d{1,2})', page_source)
        if match:
            data = match.group(1)
            print(f"   📅 Data (regex): {data}")
            return data
    except:
        pass
    
    print(f"   ⚠️ Data não encontrada")
    return None


def extrair_marcacao_ia(driver):
    """
    Verifica se o vídeo tem marcação de IA.
    Só marca como True se encontrar a frase exata "labeled as AI-generated".
    """
    # Apenas esta frase exata (em inglês, como o TikTok exibe)
    FRASE_IA = "labeled as ai-generated"
    
    try:
        # Procura na descrição
        desc = driver.find_element(By.CSS_SELECTOR, 'div[data-e2e="video-desc"]')
        texto_desc = desc.text.lower()
        
        if FRASE_IA in texto_desc:
            print(f"   🤖 IA detectada: '{FRASE_IA}'")
            return True
            
    except:
        pass
    
    # Procura no código fonte da página
    try:
        page_source = driver.page_source.lower()
        if FRASE_IA in page_source:
            print(f"   🤖 IA detectada (página): '{FRASE_IA}'")
            return True
    except:
        pass
    
    print(f"   ✅ Sem marcação IA")
    return False


def extrair_descricao_e_hashtags(driver):
    """
    Extrai descrição completa e todas as hashtags (com clique em 'Ler mais')
    """
    resultado = {
        'descricao_completa': None,
        'hashtags': []
    }
    
    try:
        # Tenta clicar no "Ler mais"
        try:
            botoes = driver.find_elements(By.XPATH, 
                "//button[contains(text(), 'more') or contains(text(), 'More') or contains(text(), 'mais') or contains(text(), 'Mais')]")
            if botoes:
                print(f"   🔘 Clicando em 'Ler mais'...")
                driver.execute_script("arguments[0].click();", botoes[0])
                time.sleep(1.5)
        except:
            pass
        
        # Pega a descrição completa
        desc = driver.find_element(By.CSS_SELECTOR, 'div[data-e2e="video-desc"]')
        texto_completo = desc.text
        resultado['descricao_completa'] = texto_completo[:2000]
        
        # Extrai hashtags
        hashtags = []
        for a in desc.find_elements(By.TAG_NAME, 'a'):
            href = a.get_attribute('href')
            if href and '/tag/' in href:
                tag_name = href.split('/tag/')[-1].split('?')[0]
                hashtags.append(tag_name)
            elif a.text and a.text.startswith('#'):
                hashtags.append(a.text[1:])
        
        if not hashtags:
            tags_encontradas = re.findall(r'#([a-zA-Z0-9_]+)', texto_completo)
            hashtags = tags_encontradas
        
        resultado['hashtags'] = hashtags
        print(f"   🏷️ {len(hashtags)} hashtags encontradas")
        
    except Exception as e:
        print(f"   ⚠️ Erro ao extrair descrição/hashtags: {e}")
    
    return resultado

def obter_checkpoint_arquivo(nome_arquivo):
    """Carrega checkpoint de um arquivo específico"""
    checkpoint_file = os.path.join(CHECKPOINT_DIR, f"{nome_arquivo}.json")
    if os.path.exists(checkpoint_file):
        with open(checkpoint_file, 'r') as f:
            return json.load(f)
    return None


def salvar_checkpoint_arquivo(nome_arquivo, checkpoint):
    """Salva checkpoint de um arquivo específico"""
    checkpoint_file = os.path.join(CHECKPOINT_DIR, f"{nome_arquivo}.json")
    with open(checkpoint_file, 'w') as f:
        json.dump(checkpoint, f, indent=2)


def remover_checkpoint_arquivo(nome_arquivo):
    """Remove checkpoint após conclusão do arquivo"""
    checkpoint_file = os.path.join(CHECKPOINT_DIR, f"{nome_arquivo}.json")
    if os.path.exists(checkpoint_file):
        os.remove(checkpoint_file)


def processar_video(driver, row, video_link):
    """Processa um único vídeo"""
    
    print(f"   📹 Processando: {video_link[:70]}...")
    
    try:
        driver.get(video_link)
        
        if not aguardar_carregamento_video(driver):
            print(f"   ❌ Falha no carregamento, pulando...")
            return row
        
        # 1. PRIMEIRO: extrai a data (antes de qualquer clique)
        data_publicacao = extrair_data_publicacao(driver)
        
        # 2. DEPOIS: extrai descrição e hashtags (com clique em "Ler mais")
        novos_dados = extrair_descricao_e_hashtags(driver)
        
        # 3. POR FIM: verifica marcação de IA (frase exata)
        marcacao_ia = extrair_marcacao_ia(driver)
        
        # Atualiza a linha
        row['descricao'] = novos_dados['descricao_completa']
        row['hashtags'] = novos_dados['hashtags']
        row['data_publicacao'] = data_publicacao
        row['marcado_ia'] = marcacao_ia
        
        print(f"   ✅ Sucesso: {len(novos_dados['hashtags'])} hashtags | Data: {data_publicacao} | IA: {marcacao_ia}")
        
    except Exception as e:
        print(f"   ❌ Erro: {e}")
    
    return row


def processar_arquivo(driver, arquivo_origem, arquivo_destino, nome_base):
    """Processa um arquivo CSV inteiro"""
    
    print(f"\n{'='*70}")
    print(f"📁 Processando: {nome_base}.csv")
    print(f"{'='*70}")
    
    # Carregar checkpoint se existir
    checkpoint = obter_checkpoint_arquivo(nome_base)
    indices_processados = checkpoint.get('processados', []) if checkpoint else []
    
    # Ler o CSV original
    df = pd.read_csv(arquivo_origem)
    total_videos = len(df)
    print(f"📊 Total de vídeos no arquivo: {total_videos}")
    print(f"📊 Vídeos já processados anteriormente: {len(indices_processados)}")
    
    # Garantir que as novas colunas existem
    if 'marcado_ia' not in df.columns:
        df['marcado_ia'] = False
    
    # Filtrar vídeos que faltam processar
    indices_para_processar = [i for i in range(total_videos) if i not in indices_processados]
    
    if MAX_VIDEOS_POR_ARQUIVO:
        indices_para_processar = indices_para_processar[:MAX_VIDEOS_POR_ARQUIVO]
    
    print(f"📊 Vídeos a processar nesta sessão: {len(indices_para_processar)}")
    
    if not indices_para_processar:
        print("✅ Todos os vídeos já foram processados! Salvando arquivo...")
        df.to_csv(arquivo_destino, index=False)
        remover_checkpoint_arquivo(nome_base)
        return True
    
    # Processar cada vídeo
    for i, idx in enumerate(indices_para_processar, 1):
        print(f"\n[{i}/{len(indices_para_processar)}] Vídeo {idx+1}/{total_videos}")
        
        row = df.iloc[idx].to_dict()
        video_link = row.get('video_link')
        
        if not video_link or pd.isna(video_link):
            print(f"   ⚠️ Link inválido, pulando...")
            indices_processados.append(idx)
            continue
        
        # Processar o vídeo
        row = processar_video(driver, row, video_link)
        
        # Atualizar o DataFrame
        for key, value in row.items():
            df.at[idx, key] = value
        
        # Registrar como processado
        indices_processados.append(idx)
        
        # Salvar checkpoint a cada vídeo
        salvar_checkpoint_arquivo(nome_base, {
            'processados': indices_processados,
            'ultimo_atualizacao': datetime.now().isoformat(),
            'total_videos': total_videos
        })
        
        # Salvar o CSV parcial
        df.to_csv(arquivo_destino, index=False)
        
        # Aguardar entre vídeos
        tempo_espera = random.uniform(*TEMPO_ENTRE_VIDEOS)
        print(f"   ⏳ Aguardando {tempo_espera:.1f}s antes do próximo...")
        time.sleep(tempo_espera)
    
    # Arquivo concluído
    print(f"\n✅ {nome_base}.csv concluído! {len(indices_processados)}/{total_videos} vídeos processados.")
    df.to_csv(arquivo_destino, index=False)
    remover_checkpoint_arquivo(nome_base)
    
    return True


def main():
    """Função principal"""
    
    print("="*70)
    print("🔄 RECOLETA COMPLETA - HASHTAGS, DESCRIÇÃO, DATA E IA")
    print("="*70)
    print(f"📁 Pasta de origem: {PASTA_ORIGEM}")
    print(f"📁 Pasta de destino: {PASTA_DESTINO}")
    print(f"💾 Checkpoints: {CHECKPOINT_DIR}")
    print("="*70)
    print("\n📋 DADOS QUE SERÃO RECOLETOS:")
    print("   ✅ Descrição completa (após 'Ler mais')")
    print("   ✅ Todas as hashtags")
    print("   ✅ Data de publicação")
    print("   ✅ Marcação de conteúdo gerado por IA")
    print("="*70)
    
    # Listar todos os CSVs
    arquivos = glob(os.path.join(PASTA_ORIGEM, "*.csv"))
    arquivos = [f for f in arquivos if not f.endswith('_2.csv')]
    print(f"\n📄 Arquivos CSV encontrados: {len(arquivos)}")
    
    if not arquivos:
        print("❌ Nenhum arquivo CSV encontrado!")
        return
    
    # Configurar driver
    print("\n🚀 Iniciando navegador...")
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_page_load_timeout(90)
    
    try:
        for i, arquivo in enumerate(arquivos, 1):
            nome_base = os.path.splitext(os.path.basename(arquivo))[0]
            nome_destino = f"{nome_base}_2.csv"
            arquivo_destino = os.path.join(PASTA_DESTINO, nome_destino)
            
            print(f"\n{'#'*70}")
            print(f"📦 ARQUIVO {i}/{len(arquivos)}: {nome_base}.csv")
            print(f"{'#'*70}")
            
            try:
                processar_arquivo(driver, arquivo, arquivo_destino, nome_base)
            except Exception as e:
                print(f"❌ Erro ao processar {nome_base}.csv: {e}")
                continue
    
    except KeyboardInterrupt:
        print("\n\n⚠️ PROCESSO INTERROMPIDO PELO USUÁRIO")
        print("Os checkpoints foram salvos. Execute novamente para continuar.")
    
    finally:
        driver.quit()
        
        print("\n" + "="*70)
        print("📊 RESUMO FINAL")
        print("="*70)
        
        arquivos_processados = glob(os.path.join(PASTA_DESTINO, "*_2.csv"))
        print(f"✅ Arquivos salvos: {len(arquivos_processados)}")
        
        checkpoints_restantes = glob(os.path.join(CHECKPOINT_DIR, "*.json"))
        if checkpoints_restantes:
            print(f"\n⚠️ Checkpoints pendentes ({len(checkpoints_restantes)} arquivos não concluídos)")
            print("Execute o script novamente para continuar.")


if __name__ == "__main__":
    main()