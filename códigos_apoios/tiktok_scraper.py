import time
import random
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, WebDriverException, TimeoutException
from datetime import datetime
import json
import os

# Import do webdriver-manager
try:
    from webdriver_manager.chrome import ChromeDriverManager
    print("✅ webdriver-manager importado com sucesso!")
except ImportError:
    print("❌ webdriver-manager não encontrado. Instale com: pip install webdriver-manager")
    exit(1)

# ============================================================
# 🔧 CONFIGURAÇÕES QUE VOCÊ MUDA A CADA EXECUÇÃO
# ============================================================

NOME_DO_GRUPO = "altgirl"
HASHTAGS_DO_GRUPO = ['altgirl','altgirl','altgirlvibes','altgirledit','altgirlstyle','altgirltok','altgirlaesthetic','altgirlgirl','altgirlfashion','altgirlinspo','altgirllifestyle','altgirlroom','whatisaltgirl','AltGirl'

                ]

ARQUIVO_SAIDA = "altgirl.csv"

#'shoujogirl','shoujogirl','shoujogirlvibes','shoujogirledit','shoujogirlstyle','shoujogirltok','shoujogirlaesthetic','shoujogirlgirl','shoujogirlfashion','shoujogirlinspo','shoujogirllifestyle','shoujogirlroom','whatisshoujogirl','ShoujoGirl'
#'thoughtdaughter','thoughtdaughter','thoughtdaughtervibes','thoughtdaughteredit','thoughtdaughterstyle','thoughtdaughtermtok','thoughtdaughteraesthetic','thoughtdaughtergirl','thoughtdaughterfashion','thoughtdaughterinspo','thoughtdaughterlifestyle','thoughtdaughterroom','whatisthoughtdaughter','ThoughtDaughter'
#'lightacademia','lightacademia','lightacademiavibes','lightacademiaedit','lightacademiastyle','lightacademiatok','lightacademiaaesthetic','lightacademiagirl','lightacademiafashion','lightacademiainspo','lightacademialifestyle','lightacademiaroom','whatislightacademia','LightAcademia'
#'brat','brat','bratvibes','bratedit','bratstyle','brattok','brataesthetic','bratgirl','bratfashion','bratinspo ,   bratlifestyle   ,   bratroom    ,   whatisbrat  ,   Brat'
#'liminalspace','liminalspace','liminalspacevibes','liminalspaceedit','liminalspacestyle','liminalspacetok','liminalspaceaesthetic','liminalspacegirl','liminalspacefashion','liminalspaceinspo','liminalspacelifestyle','liminalspaceroom','whatisliminalspace','LiminalSpace'



# ============================================================
# CONFIGURAÇÕES GLOBAIS - AJUSTADAS PARA CONEXÃO LENTA
# ============================================================
VIDEOS_POR_HASHTAG = 280
MAX_SCROLLS = 50
SCROLLS_SEM_NOVOS_PARA_PARAR = 8  # Aumentado de 8 para 12 (mais paciência)
MIN_VIDEOS_PARA_AUTO_SKIP = 30

# 🔧 TEMPOS AJUSTADOS PARA CONEXÃO LENTA
TEMPO_ESPERA_VIDEO =15  # Aumentado de 15 para 30 segundos
TEMPO_ESPERA_HASHTAG = 15  # Novo: tempo para carregar página da hashtag
TEMPO_ENTRE_SCROLLS = (2, 4)  # Aumentado de (2,4) para (4,7) segundos
TEMPO_ENTRE_VIDEOS = (4, 6)  # Aumentado de (4,6) para (6,10) segundos
TENTATIVAS_REFRESH = 3  # Aumentado de 2 para 3 tentativas

# Tempo extra após scroll para garantir carregamento
TEMPO_EXTRA_APOS_SCROLL = 2

# Arquivos temporários
OUTPUT_TEMP = f"temp_{NOME_DO_GRUPO}.csv"
CHECKPOINT_FILE = f"checkpoint_{NOME_DO_GRUPO}.json"

def setup_driver():
    """Configura driver SEM LOGIN com timeouts maiores"""
    chrome_options = Options()
    chrome_options.page_load_strategy = 'eager'
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    
    print("\n🔧 Baixando/atualizando ChromeDriver compatível...")
    driver_path = ChromeDriverManager().install()
    service = Service(driver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # 🔧 Aumentando timeouts para conexão lenta
    driver.set_page_load_timeout(90)  # Aumentado de 45 para 90
    driver.set_script_timeout(60)
    
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    print(f"✅ ChromeDriver iniciado com sucesso!")
    return driver

def verificar_pagina_carregada(driver, tempo_extra=5):
    """Verifica se a página carregou conteúdo de vídeos - com espera extra"""
    # Espera um pouco extra para garantir que a página carregou
    time.sleep(tempo_extra)
    
    try:
        elementos = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/video/"]')
        if len(elementos) > 0:
            return True, f"{len(elementos)} vídeos encontrados"
        
        page_text = driver.page_source.lower()
        if "couldn't find this hashtag" in page_text or "no results found" in page_text or "nenhum resultado" in page_text:
            return False, "HASHTAG_NAO_ENCONTRADA"
        
        if "couldn't find" in page_text or "no results" in page_text:
            return False, "Página sem resultados"
        
        # Se a página tem texto mas poucos elementos, pode ser conexão lenta
        if len(page_text) > 1000 and len(elementos) == 0:
            return False, "Página carregada mas sem vídeos visíveis (pode ser conexão lenta)"
        
        if len(page_text) < 500:
            return False, "Página vazia"
        
        return False, "Sem vídeos visíveis"
    except:
        return False, "Erro ao verificar página"

def pausa_manual(mensagem, automatico=False):
    """Pausa o script e aguarda input do usuário"""
    if automatico:
        print(f"⚠️ {mensagem}")
        return False
    
    print(f"\n{'='*60}")
    print(f"⏸️  PAUSA MANUAL")
    print(f"{'='*60}")
    print(mensagem)
    print("\n👉 Ações possíveis:")
    print("   1. Aguarde a página carregar completamente")
    print("   2. Dê refresh na página se necessário")
    print("   3. Verifique sua conexão com a internet")
    print("\n⏎ Aperte ENTER quando estiver pronto para continuar...")
    input()
    print("\n✅ Continuando...")
    time.sleep(2)
    return True

def aguardar_carregamento_video(driver, link, tentativa=1):
    """Espera o vídeo carregar com timeout automático - mais paciente"""
    print(f"   ⏳ Aguardando carregamento do vídeo (até {TEMPO_ESPERA_VIDEO}s)...")
    
    inicio = time.time()
    ultimo_check = inicio
    
    while time.time() - inicio < TEMPO_ESPERA_VIDEO:
        # Verifica se já apareceu algum elemento do vídeo
        elementos = driver.find_elements(By.CSS_SELECTOR, 'div[data-e2e="video-desc"], strong[data-e2e="like-count"]')
        if len(elementos) > 0:
            tempo_total = int(time.time() - inicio)
            print(f"   ✅ Vídeo carregou após {tempo_total} segundos")
            return True
        
        # A cada 5 segundos, mostra que ainda está esperando
        if time.time() - ultimo_check >= 5:
            print(f"   ⏳ Ainda carregando... ({int(time.time() - inicio)}s / {TEMPO_ESPERA_VIDEO}s)")
            ultimo_check = time.time()
        
        time.sleep(1)
    
    print(f"   ⚠️ Vídeo não carregou após {TEMPO_ESPERA_VIDEO} segundos")
    
    # Se ainda tem tentativas, tenta refresh
    if tentativa < TENTATIVAS_REFRESH:
        print(f"   🔄 Tentativa {tentativa + 1}/{TENTATIVAS_REFRESH} - Dando refresh e aguardando mais...")
        driver.refresh()
        time.sleep(5)
        return aguardar_carregamento_video(driver, link, tentativa + 1)
    
    return False

def coletar_links_hashtag(driver, hashtag, limite=VIDEOS_POR_HASHTAG):
    """Coleta links de uma hashtag - com tempos maiores para conexão lenta"""
    links = set()
    
    print(f"\n{'='*60}")
    print(f"🔍 COLETANDO: #{hashtag}")
    print(f"{'='*60}")
    print(f"🎯 Objetivo: {limite} vídeos")
    print(f"⏱️  Carregamento: {TEMPO_ESPERA_HASHTAG}s inicial, {TEMPO_ENTRE_SCROLLS[0]}-{TEMPO_ENTRE_SCROLLS[1]}s entre scrolls")
    
    try:
        driver.get(f"https://www.tiktok.com/tag/{hashtag}")
        print(f"   ⏳ Aguardando {TEMPO_ESPERA_HASHTAG} segundos para carregar a página...")
        time.sleep(TEMPO_ESPERA_HASHTAG)
    except Exception as e:
        print(f"❌ Erro ao carregar página: {e}")
        return links
    
    # Verifica se a página carregou com mais paciência
    carregou, msg = verificar_pagina_carregada(driver, tempo_extra=5)
    
    if msg == "HASHTAG_NAO_ENCONTRADA":
        print(f"⚠️ Hashtag #{hashtag} não encontrada. Pulando...")
        return links
    
    if not carregou:
        print(f"⚠️ Problema detectado: {msg}")
        print("   Tentando refresh e aguardando mais...")
        
        # Tenta refresh e espera mais
        for tentativa in range(2):
            driver.refresh()
            print(f"   🔄 Refresh {tentativa + 1}/2 - aguardando {TEMPO_ESPERA_HASHTAG}s...")
            time.sleep(TEMPO_ESPERA_HASHTAG)
            carregou, msg = verificar_pagina_carregada(driver, tempo_extra=3)
            if carregou:
                print("   ✅ Página carregou após refresh!")
                break
        
        if not carregou:
            print(f"❌ Ainda não carregou: {msg}")
            resposta = input("Pular esta hashtag? (s/n): ")
            if resposta.lower() == 's':
                return links
            else:
                print("   Continuando mesmo assim...")
    
    scrolls_sem_novos = 0
    scrolls_atuais = 0
    tempo_ultimo_novo = time.time()
    
    print(f"\n📜 Iniciando rolagem para coletar vídeos...")
    
    while len(links) < limite and scrolls_sem_novos < SCROLLS_SEM_NOVOS_PARA_PARAR and scrolls_atuais < MAX_SCROLLS:
        # Rola a página
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        
        # Aguarda com tempo variável
        tempo_scroll = random.uniform(*TEMPO_ENTRE_SCROLLS)
        print(f"   ⏳ Aguardando {tempo_scroll:.1f}s após scroll...")
        time.sleep(tempo_scroll)
        
        # Tempo extra opcional
        if TEMPO_EXTRA_APOS_SCROLL > 0:
            time.sleep(TEMPO_EXTRA_APOS_SCROLL)
        
        scrolls_atuais += 1
        
        # Coleta links
        elementos = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/video/"]')
        novos = 0
        for el in elementos:
            try:
                link = el.get_attribute('href')
                if link and link not in links and '/video/' in link:
                    links.add(link)
                    novos += 1
            except:
                continue
        
        if novos == 0:
            scrolls_sem_novos += 1
            tempo_sem_novos = int(time.time() - tempo_ultimo_novo)
            print(f"   📊 {len(links)}/{limite} | {scrolls_sem_novos} scrolls sem novos | {tempo_sem_novos}s sem novos")
        else:
            scrolls_sem_novos = 0
            tempo_ultimo_novo = time.time()
            print(f"   📊 {len(links)}/{limite} vídeos coletados (+{novos})")
        
        # Se já tem vídeos suficientes e parou de encontrar, para automaticamente
        if len(links) >= MIN_VIDEOS_PARA_AUTO_SKIP and scrolls_sem_novos >= 4:
            print(f"\n✅ Já coletou {len(links)} vídeos e não encontra mais novos. Parando coleta para esta hashtag.")
            break
        
        # Se está sem novos há muito tempo, oferece pausa
        if scrolls_sem_novos >= 5 and len(links) > 0:
            print(f"\n⚠️ {scrolls_sem_novos} scrolls sem novos vídeos ({int(time.time() - tempo_ultimo_novo)}s)")
            resposta = input("Continuar rolando? (s/n): ")
            if resposta.lower() != 's':
                break
    
    print(f"\n✅ #{hashtag}: {len(links)} vídeos coletados")
    
    if len(links) < limite and len(links) < 10:
        resposta = input("   Coletou poucos vídeos. Continuar para próxima hashtag? (s/n): ")
        if resposta.lower() != 's':
            print("🛑 Parando coleta")
            return links
    
    return links

def parse_count(text):
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

def check_commercial_indicators(driver):
    indicators = {
        'patrocinado': False,
        'anuncio': False,
        'tiktok_shop': False,
        'business_account': False,
        'link_externo': False
    }
    try:
        desc_area = driver.find_elements(By.CSS_SELECTOR, 'div[data-e2e="video-desc"]')
        if desc_area:
            desc_text = desc_area[0].text.lower()
            if 'patrocinado' in desc_text or 'sponsored' in desc_text:
                indicators['patrocinado'] = True
            if 'anúncio' in desc_text or 'ad' in desc_text:
                indicators['anuncio'] = True
            if 'shop' in desc_text or 'comprar' in desc_text:
                indicators['tiktok_shop'] = True
            if 'business' in desc_text or 'negócios' in desc_text:
                indicators['business_account'] = True
        
        links = driver.find_elements(By.CSS_SELECTOR, 'div[data-e2e="video-desc"] a')
        for link in links:
            href = link.get_attribute('href')
            if href and 'tiktok.com' not in href:
                indicators['link_externo'] = True
                break
    except:
        pass
    return indicators

def extrair_video(driver, link):
    """Extrai dados do vídeo - com clique em 'Ler mais' para pegar TODAS as hashtags"""
    video_data = {
        'video_link': link,
        'criador': None,
        'descricao': None,
        'likes': None,
        'comentarios': None,
        'visualizacoes': None,
        'data_publicacao': None,
        'musica': None,
        'patrocinado': False,
        'anuncio': False,
        'tiktok_shop': False,
        'business_account': False,
        'link_externo': False,
        'conta_oficial': False,
        'hashtags': [],
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    try:
        # Aguarda o vídeo carregar
        if not aguardar_carregamento_video(driver, link):
            print(f"   ⚠️ Vídeo não carregou após {TENTATIVAS_REFRESH} tentativas. Pulando...")
            return video_data
        
        # ============================================================
        # 🔥 PARTE NOVA: CLICAR NO "LER MAIS" PARA EXPANDIR A DESCRIÇÃO
        # ============================================================
        try:
            # Procura pelo botão "more" ou "ler mais" (vários idiomas)
            botoes_expandir = driver.find_elements(By.XPATH, 
                "//button[contains(text(), 'more') or contains(text(), 'More') or contains(text(), 'mais') or contains(text(), 'Mais')]")
            
            if botoes_expandir:
                print(f"   🔘 Clicando em 'Ler mais' para expandir a descrição...")
                driver.execute_script("arguments[0].click();", botoes_expandir[0])
                time.sleep(1.5)  # Aguarda a expansão
            else:
                print(f"   ℹ️ Botão 'Ler mais' não encontrado (descrição já está expandida)")
        except Exception as e:
            print(f"   ℹ️ Erro ao procurar botão: {e}")
        
        # Criador
        try:
            creator = driver.find_element(By.CSS_SELECTOR, 'a[data-e2e="video-author-unique"]')
            video_data['criador'] = creator.text
        except:
            pass
        
        # ============================================================
        # 🔥 DESCRIÇÃO E HASHTAGS (AGORA COM TEXTO COMPLETO)
        # ============================================================
        try:
            desc = driver.find_element(By.CSS_SELECTOR, 'div[data-e2e="video-desc"]')
            # Texto completo da descrição (já expandida)
            video_data['descricao'] = desc.text[:500]  # limite de 500 caracteres
            
            # ============================================================
            # MÉTODO 1: Extrair hashtags pelos links /tag/ (mais confiável)
            # ============================================================
            hashtags = []
            for a in desc.find_elements(By.TAG_NAME, 'a'):
                href = a.get_attribute('href')
                # Verifica se é uma hashtag (links do tipo /tag/alguma-coisa)
                if href and '/tag/' in href:
                    # Extrai o nome da hashtag da URL
                    tag_name = href.split('/tag/')[-1].split('?')[0]
                    hashtags.append(f"#{tag_name}")
                elif a.text and a.text.startswith('#'):
                    hashtags.append(a.text)
            
            # ============================================================
            # MÉTODO 2 (fallback): regex para encontrar #palavras no texto
            # ============================================================
            if not hashtags:
                import re
                texto_completo = desc.text
                tags_encontradas = re.findall(r'#([a-zA-Z0-9_]+)', texto_completo)
                hashtags = [f"#{tag}" for tag in tags_encontradas]
            
            video_data['hashtags'] = hashtags
            print(f"   🏷️ {len(hashtags)} hashtags encontradas")
            
        except Exception as e:
            print(f"   ⚠️ Erro ao extrair descrição/hashtags: {e}")
        
        # ============================================================
        # Likes
        # ============================================================
        try:
            likes = driver.find_element(By.CSS_SELECTOR, 'strong[data-e2e="like-count"]')
            video_data['likes'] = parse_count(likes.text)
        except:
            pass
        
        # ============================================================
        # Comentários
        # ============================================================
        try:
            comments = driver.find_element(By.CSS_SELECTOR, 'strong[data-e2e="comment-count"]')
            video_data['comentarios'] = parse_count(comments.text)
        except:
            pass
        
        # ============================================================
        # Visualizações
        # ============================================================
        try:
            views = driver.find_element(By.CSS_SELECTOR, 'strong[data-e2e="play-count"]')
            video_data['visualizacoes'] = parse_count(views.text)
        except:
            pass
        
        # ============================================================
        # Data de publicação
        # ============================================================
        try:
            date = driver.find_element(By.CSS_SELECTOR, 'span[data-e2e="video-date"]')
            video_data['data_publicacao'] = date.text
        except:
            pass
        
        # ============================================================
        # Música
        # ============================================================
        try:
            music = driver.find_element(By.CSS_SELECTOR, 'div[data-e2e="video-music"]')
            video_data['musica'] = music.text[:100]
        except:
            pass
        
        # ============================================================
        # Indicadores comerciais (já existente)
        # ============================================================
        comercial = check_commercial_indicators(driver)
        video_data.update(comercial)
        
        # ============================================================
        # Conta oficial (verificada)
        # ============================================================
        try:
            verified = driver.find_elements(By.CSS_SELECTOR, 'svg[data-e2e="verified-badge"]')
            video_data['conta_oficial'] = len(verified) > 0
        except:
            pass
        
        print(f"   👤 {video_data['criador']} | 👍 {video_data['likes']} | 💬 {video_data['comentarios']} | 🏷️ {len(video_data['hashtags'])} hashtags")
        
    except Exception as e:
        print(f"   ❌ Erro extração: {e}")
    
    return video_data

def salvar_checkpoint(hashtag_atual, links_coletados, videos):
    checkpoint = {
        'hashtag_atual': hashtag_atual,
        'timestamp': datetime.now().isoformat(),
        'links_coletados': list(links_coletados),
        'videos_coletados': len(videos)
    }
    with open(CHECKPOINT_FILE, 'w') as f:
        json.dump(checkpoint, f, indent=2)
    print(f"\n💾 Checkpoint salvo! Última hashtag: {hashtag_atual}")

def carregar_checkpoint():
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, 'r') as f:
            checkpoint = json.load(f)
        print(f"\n📂 Checkpoint encontrado! Último progresso: {checkpoint['timestamp']}")
        print(f"   Última hashtag: {checkpoint['hashtag_atual']}")
        print(f"   {checkpoint['videos_coletados']} vídeos já coletados")
        return checkpoint
    return None

def main():
    print("="*70)
    print(f"🎯 TIKTOK SCRAPER - GRUPO: {NOME_DO_GRUPO}")
    print("="*70)
    print(f"📁 Arquivo de saída: {ARQUIVO_SAIDA}")
    print(f"🏷️ Hashtags: {', '.join(HASHTAGS_DO_GRUPO)}")
    print("="*70)
    print("\n⚙️  CONFIGURAÇÕES PARA CONEXÃO LENTA:")
    print(f"   - Timeout de página: 90 segundos")
    print(f"   - Espera vídeo: {TEMPO_ESPERA_VIDEO}s (com refresh automático)")
    print(f"   - Espera hashtag: {TEMPO_ESPERA_HASHTAG}s")
    print(f"   - Entre scrolls: {TEMPO_ENTRE_SCROLLS[0]}-{TEMPO_ENTRE_SCROLLS[1]}s")
    print(f"   - Entre vídeos: {TEMPO_ENTRE_VIDEOS[0]}-{TEMPO_ENTRE_VIDEOS[1]}s")
    print(f"   - Para após {SCROLLS_SEM_NOVOS_PARA_PARAR} scrolls sem novos")
    print("="*70)
    
    driver = setup_driver()
    
    print("\n🌐 Abrindo TikTok...")
    driver.get("https://www.tiktok.com")
    print("⏳ Aguardando 10 segundos para carregamento inicial...")
    time.sleep(10)
    
    carregou, _ = verificar_pagina_carregada(driver)
    if not carregou:
        pausa_manual("Verifique se a página do TikTok carregou corretamente.\nSe precisar fazer login ou resolver algo, faça agora.", automatico=False)
    
    checkpoint = carregar_checkpoint()
    if checkpoint:
        print("\n❓ Deseja retomar de onde parou? (s/n)")
        if input().lower() != 's':
            checkpoint = None
            if os.path.exists(CHECKPOINT_FILE):
                os.remove(CHECKPOINT_FILE)
    
    todos_links = set()
    hashtag_inicio = None
    
    if checkpoint:
        hashtag_inicio = checkpoint.get('hashtag_atual')
        todos_links = set(checkpoint.get('links_coletados', []))
        print(f"\n📂 Retomando com {len(todos_links)} links já coletados")
    
    print("\n" + "="*70)
    print("📹 FASE 1: COLETANDO LINKS DAS HASHTAGS")
    print("="*70)
    
    for hashtag in HASHTAGS_DO_GRUPO:
        if hashtag_inicio and hashtag != hashtag_inicio:
            continue
        hashtag_inicio = None
        
        links_hashtag = coletar_links_hashtag(driver, hashtag, VIDEOS_POR_HASHTAG)
        antes = len(todos_links)
        todos_links.update(links_hashtag)
        novos = len(todos_links) - antes
        print(f"\n📊 #{hashtag}: +{novos} novos links. Total acumulado: {len(todos_links)}")
        
        salvar_checkpoint(hashtag, todos_links, [])
        
        if novos == 0:
            print(f"⚠️ Nenhum vídeo coletado para #{hashtag}. Pulando...")
            continue
    
    print(f"\n✅ TOTAL DE LINKS ÚNICOS COLETADOS: {len(todos_links)}")
    
    if len(todos_links) > 0:
        print(f"\n{'='*70}")
        print("📹 FASE 2: EXTRAINDO DADOS DOS VÍDEOS")
        print(f"{'='*70}")
        
        videos = []
        
        if checkpoint and os.path.exists(OUTPUT_TEMP):
            try:
                df_existente = pd.read_csv(OUTPUT_TEMP, encoding='utf-8')
                videos = df_existente.to_dict('records')
                print(f"📂 Carregados {len(videos)} vídeos já extraídos")
            except:
                pass
        
        links_processados = {v['video_link'] for v in videos}
        links_restantes = [l for l in todos_links if l not in links_processados]
        
        print(f"📊 Links já processados: {len(links_processados)}")
        print(f"📊 Links restantes: {len(links_restantes)}")
        
        for i, link in enumerate(links_restantes, 1):
            print(f"\n[{i}/{len(links_restantes)}] {link[:70]}...")
            
            try:
                driver.get(link)
                
                # Aguarda extra com tempo maior
                tempo_espera = random.uniform(*TEMPO_ENTRE_VIDEOS)
                print(f"   ⏳ Aguardando {tempo_espera:.1f}s antes de extrair...")
                time.sleep(tempo_espera)
                
                video = extrair_video(driver, link)
                videos.append(video)
                
            except Exception as e:
                print(f"   ❌ Erro: {e}")
                continue
            
            if i % 10 == 0:
                df_v = pd.DataFrame(videos)
                df_v.to_csv(OUTPUT_TEMP, index=False, encoding='utf-8')
                print(f"\n💾 Checkpoint salvo após {len(videos)} vídeos")
                salvar_checkpoint("EXTRACAO", todos_links, videos)
        
        print(f"\n{'='*70}")
        print("💾 SALVANDO RESULTADO FINAL")
        print(f"{'='*70}")
        
        df_final = pd.DataFrame(videos)
        df_final.to_csv(ARQUIVO_SAIDA, index=False, encoding='utf-8')
        
        print(f"\n✅ Arquivo salvo: {ARQUIVO_SAIDA}")
        print(f"📊 Total de vídeos: {len(df_final)}")
        print(f"📊 Vídeos patrocinados: {df_final['patrocinado'].sum()}")
        print(f"📊 Vídeos com anúncio: {df_final['anuncio'].sum()}")
    
    if os.path.exists(CHECKPOINT_FILE):
        os.remove(CHECKPOINT_FILE)
    if os.path.exists(OUTPUT_TEMP):
        os.remove(OUTPUT_TEMP)
    
    driver.quit()
    print("\n✅ PROCESSO CONCLUÍDO!")

if __name__ == "__main__":
    main()