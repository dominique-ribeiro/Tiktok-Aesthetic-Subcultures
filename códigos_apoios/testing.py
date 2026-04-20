import time
import random
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

CHROMEDRIVER_PATH = './chromedriver'

# Grupos que faltaram (corrigindo possíveis erros de digitação)
GRUPO_SAD = [
    'sadcore', 'sadaesthetic', 'sadaesthetics', 'sadcorevibes', 
    'sadcoreedit', 'whatissadcore'
]

GRUPO_DOLL = [
    'dollcore', 'dollcoreaesthetic', 'dollcorevibes', 'dollcoreedit',  # Corrigido: dollcore (com dois Ls)
    'doolcore', 'doolaesthetic'  # Mantém os antigos por segurança
]

GRUPO_DREAM = [
    'dreamcore', 'dreamcorevibes', 'dreamcoresongs', 'dreamcoreedit', 
    'dreamcorelifestyle', 'dreamaesthetic', 'dreamtok'
]

STUCK_TIMEOUT = 30  # Menor para teste rápido

def setup_driver():
    chrome_options = Options()
    chrome_options.page_load_strategy = 'eager'
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--start-maximized")
    service = Service(executable_path=CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_page_load_timeout(30)
    return driver

def coletar_links_grupo(driver, grupo_hashtags, nome_grupo, limite=50):
    """Coleta links para um grupo com limite"""
    links = set()
    
    print(f"\n{'='*50}")
    print(f"📹 COLETANDO GRUPO {nome_grupo}")
    print(f"{'='*50}")
    
    for tag in grupo_hashtags:
        print(f"\n🔍 #{tag}")
        try:
            driver.get(f"https://www.tiktok.com/tag/{tag}")
            time.sleep(3)
            
            # Rola algumas vezes
            for _ in range(3):
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
            
            # Coleta links
            elements = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/video/"]')
            novos = 0
            for e in elements[:limite]:
                try:
                    link = e.get_attribute('href')
                    if link and link not in links:
                        links.add(link)
                        novos += 1
                except:
                    continue
            
            print(f"   Encontrados {novos} novos links. Total: {len(links)}")
            
            if len(links) >= limite:
                break
                
        except Exception as e:
            print(f"   Erro: {e}")
            continue
    
    print(f"\n✅ Grupo {nome_grupo}: {len(links)} links coletados")
    return links

def coletar_grupos_faltantes():
    """Coleta apenas os grupos que não apareceram"""
    driver = setup_driver()
    
    print("="*70)
    print("🎯 COLETANDO GRUPOS FALTANTES")
    print("="*70)
    print("\n⚠️ Faça login manualmente se necessário (30s)...")
    
    driver.get("https://www.tiktok.com/tag/fyp")
    time.sleep(30)
    
    # Coleta cada grupo
    links_sad = coletar_links_grupo(driver, GRUPO_SAD, "SAD", limite=100)
    links_doll = coletar_links_grupo(driver, GRUPO_DOLL, "DOLL", limite=100)
    links_dream = coletar_links_grupo(driver, GRUPO_DREAM, "DREAM", limite=100)
    
    # Salva os links coletados
    todos_links = {
        'SAD': list(links_sad),
        'DOLL': list(links_doll),
        'DREAM': list(links_dream)
    }
    
    import json
    with open('links_faltantes.json', 'w') as f:
        json.dump(todos_links, f, indent=2)
    
    print(f"\n{'='*70}")
    print("📊 RESULTADO:")
    print(f"   SAD: {len(links_sad)} links")
    print(f"   DOLL: {len(links_doll)} links")
    print(f"   DREAM: {len(links_dream)} links")
    print(f"\n💾 Links salvos em 'links_faltantes.json'")
    
    driver.quit()
    
    return todos_links

if __name__ == "__main__":
    coletar_grupos_faltantes()