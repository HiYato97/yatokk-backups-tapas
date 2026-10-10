import argparse
import html
import json
import os
import urllib.request
from pathlib import Path
from ebooklib import epub

BASE_DIR = Path(".").resolve()

# Tenta carregar o autor a partir do config.json da raiz (se existir)
AUTOR_NOME = "Autor Desconhecido"
CONFIG_FILE = BASE_DIR / "config.json"
if CONFIG_FILE.exists():
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            cfg = json.load(f)
            AUTOR_NOME = cfg.get("nome", AUTOR_NOME)
    except Exception:
        pass


def extrair_valor(dicionario, chaves, padrao=""):
    for chave in chaves:
        if isinstance(dicionario, dict) and chave in dicionario and dicionario[chave]:
            return dicionario[chave]
    return padrao


def baixar_ou_encontrar_capa(pasta_serie):
    """Localiza ou baixa a capa da série."""
    extensoes = [".jpg", ".jpeg", ".png", ".webp"]
    
    # Procura arquivos cover.* ou img_* na pasta
    for arquivo in pasta_serie.iterdir():
        if arquivo.is_file():
            nome_lower = arquivo.name.lower()
            if (nome_lower.startswith("cover") or nome_lower.startswith("img_")) and arquivo.suffix.lower() in extensoes:
                return arquivo

    # Caso não exista local, verifica no series.json
    series_json_path = pasta_serie / "series.json"
    if series_json_path.exists():
        try:
            with open(series_json_path, "r", encoding="utf-8") as f:
                data_raw = json.load(f)
                s_data = data_raw.get("data", data_raw) if isinstance(data_raw, dict) else {}
                url_capa = extrair_valor(s_data, ["thumb_url", "cover_url", "square_thumb_url", "thumb"])
                
                if url_capa:
                    ext = ".jpg"
                    if ".png" in url_capa.lower(): ext = ".png"
                    elif ".webp" in url_capa.lower(): ext = ".webp"
                    
                    caminho_destino = pasta_serie / f"cover{ext}"
                    req = urllib.request.Request(
                        url_capa,
                        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
                    )
                    with urllib.request.urlopen(req) as resp, open(caminho_destino, "wb") as out:
                        out.write(resp.read())
                    return caminho_destino
        except Exception as e:
            print(f"   ⚠️ Não foi possível baixar a capa: {e}")

    return None


def carregar_metadados(pasta_serie):
    meta = {
        "title": pasta_serie.name,
        "author": AUTOR_NOME,
        "genre": "",
        "description": "",
        "episodes": {}
    }

    series_json = pasta_serie / "series.json"
    if series_json.exists():
        try:
            with open(series_json, "r", encoding="utf-8") as f:
                d = json.load(f)
                s_data = d.get("data", d) if isinstance(d, dict) else {}
                meta["title"] = extrair_valor(s_data, ["title", "name"], pasta_serie.name)
                
                genre_raw = s_data.get("genre")
                if isinstance(genre_raw, dict):
                    meta["genre"] = genre_raw.get("name", "")
                elif isinstance(genre_raw, str):
                    meta["genre"] = genre_raw

                meta["description"] = extrair_valor(s_data, ["description", "summary", "synopsis"])
        except Exception:
            pass

    manifest_json = pasta_serie / "manifest.json"
    if manifest_json.exists():
        try:
            with open(manifest_json, "r", encoding="utf-8") as f:
                d = json.load(f)
                meta["episodes"] = d.get("episodes", d) if isinstance(d, dict) else {}
        except Exception:
            pass

    return meta


def criar_epub_serie(pasta_serie):
    pasta_serie = Path(pasta_serie).resolve()
    pasta_episodes = pasta_serie / "episodes"
    
    if not pasta_episodes.is_dir():
        print(f"⚠️ A pasta '{pasta_serie.name}' não possui uma subpasta 'episodes'. Pulando...")
        return False

    episodios = sorted([p for p in pasta_episodes.iterdir() if p.is_dir()])
    if not episodios:
        print(f"⚠️ Nenhum episódio encontrado em '{pasta_serie.name}'. Pulando...")
        return False

    meta = carregar_metadados(pasta_serie)
    print(f"\n📖 Gerando EPUB para: {meta['title']} ({len(episodios)} episódios)")

    book = epub.EpubBook()
    book.set_identifier(f"id_{pasta_serie.name}")
    book.set_title(meta["title"])
    book.set_language("pt-BR")
    book.add_author(meta["author"])

    # Estilo CSS com centralização da capa e formatação responsiva
    style = """
    body {
        margin: 0;
        padding: 20px 10px;
        text-align: center;
        font-family: sans-serif;
        background-color: #ffffff;
    }
    .cover-box {
        margin: 0 auto 20px auto;
        text-align: center;
        width: 100%;
    }
    .cover-img {
        max-width: 280px;
        max-height: 400px;
        width: auto;
        height: auto;
        border-radius: 6px;
        display: block;
        margin: 0 auto;
        box-shadow: 0 4px 10px rgba(0,0,0,0.15);
    }
    .main-title {
        font-size: 1.8em;
        font-weight: bold;
        margin: 15px 0 5px 0;
        color: #111;
    }
    .author-name {
        font-size: 1em;
        color: #555;
        margin-bottom: 10px;
        font-style: italic;
    }
    .genre-tag {
        font-size: 0.85em;
        color: #0066cc;
        font-weight: bold;
        margin-bottom: 15px;
    }
    .description-text {
        font-size: 0.95em;
        line-height: 1.5;
        color: #333;
        text-align: justify;
        max-width: 600px;
        margin: 20px auto 0 auto;
    }
    .chapter-title {
        font-size: 1.3em;
        font-weight: bold;
        margin: 20px 0 10px 0;
        color: #111;
    }
    .comic-page {
        max-width: 100%;
        height: auto;
        display: block;
        margin: 10px auto;
    }
    """
    css_item = epub.EpubItem(
        uid="style_nav",
        file_name="style/nav.css",
        media_type="text/css",
        content=style
    )
    book.add_item(css_item)

    spine_items = []
    caminho_capa = baixar_ou_encontrar_capa(pasta_serie)
    capa_html_tag = ""

    # Adiciona a imagem de capa ao pacote EPUB
    if caminho_capa and caminho_capa.exists():
        ext = caminho_capa.suffix.lower().replace(".", "")
        if ext == "jpg": ext = "jpeg"
        
        with open(caminho_capa, "rb") as f:
            capa_bytes = f.read()

        nome_imagem_capa = f"cover_img.{ext}"
        book.set_cover(nome_imagem_capa, capa_bytes)
        capa_html_tag = f'<div class="cover-box"><img src="{nome_imagem_capa}" alt="Capa" class="cover-img"/></div>'

    # --- 1. PÁGINA INICIAL ÚNICA: CAPA + INFORMAÇÕES DA SÉRIE ---
    rosto_page = epub.EpubHtml(
        title="Informações",
        file_name="info.xhtml",
        lang="pt-BR"
    )
    
    desc_clean = html.escape(str(meta["description"])).replace("\n", "<br/>")
    genero_str = f'<div class="genre-tag">Gênero: {html.escape(meta["genre"])}</div>' if meta['genre'] else ""

    rosto_page.content = f"""<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>{html.escape(meta['title'])}</title>
    <link rel="stylesheet" href="style/nav.css" type="text/css"/>
</head>
<body>
    {capa_html_tag}
    <h1 class="main-title">{html.escape(meta['title'])}</h1>
    <div class="author-name">Por {html.escape(meta['author'])}</div>
    {genero_str}
    <div class="description-text">
        {desc_clean}
    </div>
</body>
</html>"""
    rosto_page.add_item(css_item)
    book.add_item(rosto_page)
    spine_items.append(rosto_page)

    # --- 2. PROCESSA OS CAPÍTULOS E IMAGENS ---
    toc_items = [rosto_page]
    total_imagens = 0

    for idx, ep_folder in enumerate(episodios, start=1):
        folder_name = ep_folder.name
        ep_meta = meta["episodes"].get(folder_name, {})
        
        if isinstance(ep_meta, dict):
            ep_title = ep_meta.get("title", folder_name)
        else:
            ep_title = folder_name

        titulo_cap = f"Cap. {idx} - {html.escape(ep_title)}"
        
        images_dir = ep_folder / "images"
        html_imgs = []

        if images_dir.is_dir():
            exts = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
            arquivos_img = sorted([img for img in images_dir.iterdir() if img.suffix.lower() in exts])

            for img_path in arquivos_img:
                total_imagens += 1
                img_ext = img_path.suffix.lower().replace(".", "")
                if img_ext == "jpg": img_ext = "jpeg"
                
                epub_img_name = f"images/ep_{idx}_{img_path.name}"
                
                with open(img_path, "rb") as img_file:
                    img_item = epub.EpubItem(
                        uid=f"img_{idx}_{img_path.stem}",
                        file_name=epub_img_name,
                        media_type=f"image/{img_ext}",
                        content=img_file.read()
                    )
                    book.add_item(img_item)

                html_imgs.append(f'<img src="{epub_img_name}" class="comic-page" alt="Página {total_imagens}"/>')

        cap_page = epub.EpubHtml(
            title=ep_title,
            file_name=f"capitulo_{idx}.xhtml",
            lang="pt-BR"
        )
        cap_page.content = f"""<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>{titulo_cap}</title>
    <link rel="stylesheet" href="style/nav.css" type="text/css"/>
</head>
<body>
    <h2 class="chapter-title">{titulo_cap}</h2>
    {"".join(html_imgs)}
</body>
</html>"""
        cap_page.add_item(css_item)
        book.add_item(cap_page)

        spine_items.append(cap_page)
        toc_items.append(cap_page)

    # --- 3. FINALIZA NAVEGAÇÃO E SALVA O EPUB ---
    book.toc = toc_items
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    book.spine = ["nav"] + spine_items

    output_epub = pasta_serie / f"{pasta_serie.name}.epub"
    epub.write_epub(str(output_epub), book, {})

    print(f"   ✅ EPUB gerado com sucesso: {output_epub.name} ({total_imagens} imagens)")
    return True


def main():
    parser = argparse.ArgumentParser(description="Gera arquivos EPUB a partir de pastas de webcomics.")
    parser.add_argument(
        "--pastas", "--pasta",
        nargs="+",
        help="Caminho de uma ou mais pastas específicas para gerar o EPUB. Se omitido, processa todas as pastas do diretório."
    )
    args = parser.parse_args()

    if args.pastas:
        target_folders = [Path(p).resolve() for p in args.pastas]
        print(f"🎯 Processando {len(target_folders)} pasta(s) específica(s)...")
    else:
        target_folders = [item for item in BASE_DIR.iterdir() if item.is_dir() and not item.name.startswith(".")]
        print(f"🔍 Procurando séries para conversão EPUB em: {BASE_DIR}")

    processadas = 0
    for pasta in target_folders:
        if pasta.exists() and pasta.is_dir():
            if criar_epub_serie(pasta):
                processadas += 1
        else:
            print(f"❌ Pasta não encontrada: {pasta}")

    print(f"\n{'='*40}")
    print(f"✨ Concluído! {processadas} arquivo(s) EPUB gerado(s)." if processadas else "⚠️ Nenhuma série foi convertida.")


if __name__ == "__main__":
    main()