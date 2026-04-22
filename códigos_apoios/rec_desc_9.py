import pandas as pd
import os
import time
import random
import re
from glob import glob
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# ============================================================
# CONFIGURAÇÕES — ajuste aqui
# ============================================================

PASTA_ORIGEM  = "/home/hugo/materias/MC859/Tiktok-Aesthetic-Subcultures/data_2/9"
PASTA_DESTINO = "/home/hugo/materias/MC859/Tiktok-Aesthetic-Subcultures/data_2_2"

# Tempo (segundos) aguardando o vídeo carregar antes de desistir
TIMEOUT_VIDEO = 30

# Intervalo aleatório entre vídeos (evita ban)
ESPERA_MIN, ESPERA_MAX = 5, 9

# Quantas vezes tentar recarregar a página antes de marcar como erro
MAX_TENTATIVAS = 3

# ============================================================
# SETUP DO DRIVER
# ============================================================

def setup_driver():
    opts = Options()
    opts.add_argument("--start-maximized")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=opts
    )
    driver.set_page_load_timeout(60)
    return driver

# ============================================================
# EXTRAÇÃO DE DADOS
# ============================================================

def aguardar_video(driver, tentativa=1):
    """Aguarda o vídeo carregar. Retorna True se ok, False se timeout."""
    inicio = time.time()
    while time.time() - inicio < TIMEOUT_VIDEO:
        els = driver.find_elements(
            By.CSS_SELECTOR,
            'div[data-e2e="video-desc"], strong[data-e2e="like-count"]'
        )
        if els:
            return True
        time.sleep(1)

    if tentativa < MAX_TENTATIVAS:
        print(f"      ↻ timeout — tentativa {tentativa + 1}/{MAX_TENTATIVAS}")
        driver.refresh()
        time.sleep(4)
        return aguardar_video(driver, tentativa + 1)

    return False


def extrair_data(driver):
    """Lógica original que funciona — não alterar."""
    data_encontrada = None

    # Tentativa 1: seletor padrão
    try:
        elemento = driver.find_element(By.CSS_SELECTOR, 'span[data-e2e="video-date"]')
        texto = elemento.text.strip()
        if texto:
            data_encontrada = texto
    except: pass

    # Se encontrou formato curto (ex: "6-28"), completa com 2026
    if data_encontrada:
        if re.match(r'^\d{1,2}-\d{1,2}$', data_encontrada):
            return f"2026-{data_encontrada}"
        return data_encontrada

    # Tentativa 2: regex no código fonte (YYYY-MM-DD)
    try:
        page_source = driver.page_source
        match = re.search(r'(\d{4}-\d{1,2}-\d{1,2})', page_source)
        if match: return match.group(1)
    except: pass

    # Tentativa 3: regex formato curto no código fonte (M-D ou MM-DD)
    try:
        page_source = driver.page_source
        match = re.search(r'(\d{1,2}-\d{1,2})', page_source)
        if match: return f"2026-{match.group(1)}"
    except: pass

    return None


def extrair_descricao_hashtags(driver):
    """
    Clica em 'more/mais' para expandir e extrai descrição + hashtags.
    Retorna dict {'descricao': str, 'hashtags': list[str]}.
    """
    resultado = {'descricao': None, 'hashtags': []}

    # Clica em "more / mais" para expandir a descrição
    try:
        btn = driver.find_element(
            By.XPATH,
            "//button[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'more') "
            "or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'mais')]"
        )
        driver.execute_script("arguments[0].click();", btn)
        time.sleep(1.5)
    except Exception:
        pass  # sem botão "more" — descrição já está completa

    # Extrai o texto da descrição
    try:
        desc_el = driver.find_element(By.CSS_SELECTOR, 'div[data-e2e="video-desc"]')
        resultado['descricao'] = desc_el.text[:3000]  # limite de segurança

        # Hashtags via links /tag/
        tags = [
            a.get_attribute('href').split('/tag/')[-1].split('?')[0]
            for a in desc_el.find_elements(By.TAG_NAME, 'a')
            if '/tag/' in (a.get_attribute('href') or '')
        ]

        # Fallback: regex no texto
        if not tags:
            tags = re.findall(r'#([a-zA-Z0-9_]+)', resultado['descricao'])

        resultado['hashtags'] = list(dict.fromkeys(tags))  # remove duplicatas, mantém ordem
    except Exception:
        pass

    return resultado


def processar_video(driver, url):
    """
    Abre o vídeo e extrai todos os dados.
    Retorna dict com os dados ou levanta exceção em caso de falha grave.
    """
    driver.get(url)

    if not aguardar_video(driver):
        raise TimeoutError(f"Vídeo não carregou após {MAX_TENTATIVAS} tentativas: {url}")

    # Data ANTES de clicar em qualquer coisa
    data = extrair_data(driver)

    # Descrição e hashtags (com clique em "more")
    info = extrair_descricao_hashtags(driver)

    return {
        'data_publicacao': data,
        'descricao':       info['descricao'],
        'hashtags':        str(info['hashtags']),
    }

# ============================================================
# GESTÃO DO CSV — a lógica de checkpoint fica aqui
# ============================================================

def carregar_ou_inicializar(path_origem, path_destino):
    """
    Se o arquivo de destino já existe → retoma de onde parou.
    Se não existe            → copia o original e adiciona coluna 'status'.
    """
    if os.path.exists(path_destino):
        df = pd.read_csv(path_destino)
        print(f"   ↩  Retomando: {len(df[df['status'] == 'done'])} / {len(df)} já prontos")
    else:
        df = pd.read_csv(path_origem)
        df['status'] = 'pending'
        # Garante que as colunas de destino existem
        for col in ('descricao', 'hashtags', 'data_publicacao'):
            if col not in df.columns:
                df[col] = None
        df.to_csv(path_destino, index=False)
        print(f"   ✦  Novo arquivo criado com {len(df)} vídeos para processar")

    return df


def salvar_linha(df, idx, dados, path_destino):
    """
    Atualiza uma linha no DataFrame e salva o CSV imediatamente.
    Esta é a operação atômica que garante o checkpoint.
    """
    for chave, valor in dados.items():
        df.at[idx, chave] = valor
    df.to_csv(path_destino, index=False)


# ============================================================
# LOOP PRINCIPAL
# ============================================================

def processar_arquivo(driver, path_origem, path_destino):
    nome = os.path.basename(path_origem)
    print(f"\n{'─'*60}")
    print(f"📄 {nome}")

    df = carregar_ou_inicializar(path_origem, path_destino)

    pendentes = df[df['status'] == 'pending']
    if pendentes.empty:
        print("   ✓ Arquivo completo, pulando.")
        return

    print(f"   ⏳ {len(pendentes)} vídeos pendentes\n")

    for i, (idx, row) in enumerate(pendentes.iterrows(), 1):
        url = row.get('video_link')

        if not url or pd.isna(url):
            salvar_linha(df, idx, {'status': 'error'}, path_destino)
            print(f"   [{i:>4}] ⚠  URL inválida — marcada como error")
            continue

        print(f"   [{i:>4}/{len(pendentes)}] {url[:65]}...")

        try:
            dados = processar_video(driver, url)
            dados['status'] = 'done'
            salvar_linha(df, idx, dados, path_destino)
            print(
                f"          ✅ data={dados['data_publicacao']} | "
                f"desc={len(dados['descricao'] or '')}c | "
                f"tags={dados['hashtags']}"
            )
        except KeyboardInterrupt:
            # Salva o que estava em andamento como 'pending' (não altera)
            # e propaga o KeyboardInterrupt para o loop externo
            print("\n   ⚠  Interrompido pelo usuário. Progresso salvo.")
            raise
        except Exception as e:
            salvar_linha(df, idx, {'status': 'error'}, path_destino)
            print(f"          ❌ Erro: {e}")

        espera = random.uniform(ESPERA_MIN, ESPERA_MAX)
        time.sleep(espera)


def main():
    os.makedirs(PASTA_DESTINO, exist_ok=True)

    arquivos = sorted(glob(os.path.join(PASTA_ORIGEM, "*.csv")))
    print(f"{'='*60}")
    print(f"RECOLETA TIKTOK")
    print(f"{'='*60}")
    print(f"Arquivos encontrados: {len(arquivos)}")
    print(f"Destino: {PASTA_DESTINO}")
    print(f"\nCheckpoint: coluna 'status' diretamente no CSV de destino.")
    print(f"Para retomar, basta executar o script novamente.\n")

    if not arquivos:
        print("Nenhum arquivo .csv encontrado em PASTA_ORIGEM.")
        return

    driver = setup_driver()

    try:
        for path_origem in arquivos:
            nome_base = os.path.splitext(os.path.basename(path_origem))[0]
            path_destino = os.path.join(PASTA_DESTINO, f"{nome_base}.csv")

            try:
                processar_arquivo(driver, path_origem, path_destino)
            except KeyboardInterrupt:
                break  # sai do loop de arquivos, vai pro finally
            except Exception as e:
                print(f"\n❌ Erro inesperado em {nome_base}: {e}")
                continue

    finally:
        driver.quit()

        # ── Resumo ──────────────────────────────────────────
        print(f"\n{'='*60}")
        print("RESUMO")
        print(f"{'='*60}")
        csvs = glob(os.path.join(PASTA_DESTINO, "*.csv"))
        total_done = total_pending = total_error = 0
        for f in csvs:
            try:
                df = pd.read_csv(f)
                if 'status' in df.columns:
                    total_done    += (df['status'] == 'done').sum()
                    total_pending += (df['status'] == 'pending').sum()
                    total_error   += (df['status'] == 'error').sum()
            except Exception:
                pass
        print(f"  ✅ done:    {total_done}")
        print(f"  ⏳ pending: {total_pending}  ← execute novamente para continuar")
        print(f"  ❌ error:   {total_error}")
        print(f"{'='*60}")


if __name__ == "__main__":
    main()