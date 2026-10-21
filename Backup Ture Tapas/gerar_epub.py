import argparse
import html
import json
import re
from pathlib import Path
from ebooklib import epub

BASE_DIR = Path(".").resolve()


def carregar_dados_autor():
    print("🔍 [Autor] Buscando informações do autor...")
    author_file = BASE_DIR / "author.json"
    if author_file.exists():
        try:
            with open(author_file, "r", encoding="utf-8") as f:
                d = json.load(f)
                d_inner = d.get("data", d)
                nome = d_inner.get("display_name") or d_inner.get("username")
                if nome:
                    print(f"   ✅ Autor encontrado em author.json: {nome}")
                    return nome
        except Exception:
            pass

    config_file = BASE_DIR / "config.json"
    if config_file.exists():
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                d = json.load(f)
                nome = d.get("nome") or d.get("author")
                if nome:
                    print(f"   ✅ Autor encontrado em config.json: {nome}")
                    return nome
        except Exception:
            pass

    print("   ⚠️ Autor não encontrado. Usando padrão: Autor Desconhecido")
    return "Autor Desconhecido"


def encontrar_avatar_autor():
    for ext in [".png", ".jpg", ".jpeg", ".webp"]:
        avatar_path = BASE_DIR / f"avatar{ext}"
        if avatar_path.exists():
            print(f"   👤 Avatar do autor localizado: {avatar_path.name}")
            return avatar_path
    return None


def carregar_metadados_serie(pasta_serie):
    print(f"   📖 Lendo metadados da série em: {pasta_serie.name}")
    meta = {
        "title": pasta_serie.name,
        "author": carregar_dados_autor(),
        "genre": "",
        "description": "",
        "views": "",
        "likes": "",
        "subscribers": ""
    }

    series_json = pasta_serie / "series.json"
    if series_json.exists():
        try:
            with open(series_json, "r", encoding="utf-8") as f:
                data = json.load(f)
                meta["views"] = data.get("views", "")
                meta["likes"] = data.get("likes", "")
                meta["subscribers"] = data.get("subscribers", "")
                meta["description"] = data.get("description", "")

                s_data = data.get("data", data)
                if isinstance(s_data, dict):
                    meta["title"] = s_data.get("title") or s_data.get("name") or meta["title"]
                    meta["description"] = s_data.get("description") or meta["description"]

                    genre_raw = s_data.get("genre")
                    if isinstance(genre_raw, dict):
                        meta["genre"] = genre_raw.get("name", "")
                    elif isinstance(genre_raw, str):
                        meta["genre"] = genre_raw
            print("      ✔️ series.json lido com sucesso.")
        except Exception as e:
            print(f"      ⚠️ Erro ao ler series.json: {e}")
    else:
        print("      ℹ️ series.json não encontrado. Usando padrões.")

    return meta


def carregar_dados_episodio(ep_path):
    ep_data = {
        "title": ep_path.name,
        "publish_date": "",
        "creator_note": ""
    }
    index_json = ep_path / "index.json"
    if index_json.exists():
        try:
            with open(index_json, "r", encoding="utf-8") as f:
                data = json.load(f)
                d_inner = data.get("data", data)
                if isinstance(d_inner, dict):
                    ep_data["title"] = d_inner.get("title", ep_path.name)
                    ep_data["publish_date"] = d_inner.get("publish_date") or data.get("relative_publish_date", "")
                    ep_data["creator_note"] = d_inner.get("creator_note", "")
        except Exception:
            pass
    return ep_data


def encontrar_capa_serie(pasta_serie):
    extensoes = (".jpg", ".jpeg", ".png", ".webp")
    for f in pasta_serie.iterdir():
        if f.is_file() and f.suffix.lower() in extensoes:
            n = f.name.lower()
            if "cover" in n or "header" in n or "banner" in n or "thumb" in n or "series" in n:
                print(f"   🖼️ Capa localizada: {f.name}")
                return f
    print("   ℹ️ Nenhuma capa dedicada encontrada na raiz.")
    return None


def limpar_html_para_epub(texto_html):
    """Garante que tags HTML básicas passem formatadas corretamente para o EPUB."""
    if not texto_html:
        return ""
    # Converte quebras de linha em <br/> mantendo o layout
    t = re.sub(r'(?i)<br\s*/?>', '<br/>', texto_html)
    return t


def criar_epub_serie(pasta_serie):
    pasta_serie = Path(pasta_serie).resolve()
    pasta_episodes = pasta_serie / "episodes"

    if not pasta_episodes.is_dir():
        print(f"⚠️ [EPUB] A pasta '{pasta_serie.name}' não possui a pasta 'episodes'. Pulando.")
        return False

    print(f"🔍 [EPUB] Varrendo pastas de episódios em '{pasta_serie.name}'...")
    episodios = sorted([p for p in pasta_episodes.iterdir() if p.is_dir()])
    if not episodios:
        print(f"⚠️ [EPUB] Nenhum episódio encontrado em '{pasta_serie.name}'. Pulando.")
        return False
    print(f"   ✔️ Total de pastas de episódios encontradas: {len(episodios)}")

    meta = carregar_metadados_serie(pasta_serie)
    print(f"\n🚀 [EPUB] Iniciando criação de e-book para: '{meta['title']}'")

    book = epub.EpubBook()
    book.set_identifier(f"id_{pasta_serie.name}")
    book.set_title(meta["title"])
    book.set_language("pt-BR")
    book.add_author(meta["author"])

    style = """
    body { margin: 0; padding: 15px 10px; text-align: center; font-family: sans-serif; background-color: #ffffff; color: #111111; }
    .cover-box { margin: 0 auto 20px auto; text-align: center; }
    .cover-img { max-width: 280px; max-height: 400px; width: auto; height: auto; border-radius: 6px; display: block; margin: 0 auto; }
    .main-title { font-size: 1.8em; font-weight: bold; margin: 15px 0 5px 0; color: #111; }
    .author-name { font-size: 1em; color: #555; margin-bottom: 10px; font-style: italic; }
    .stats-bar { font-size: 0.85em; color: #2b6cb0; margin-bottom: 15px; }
    .description-text { font-size: 0.95em; line-height: 1.5; color: #333; text-align: justify; max-width: 600px; margin: 20px auto; }
    .chapter-title { font-size: 1.4em; font-weight: bold; margin: 20px 0 5px 0; color: #111; }
    .chapter-date { font-size: 0.85em; color: #777; margin-bottom: 15px; }
    
    .creator-note-box {
        display: flex;
        align-items: flex-start;
        background: #f7fafc;
        border: 1px solid #cbd5e0;
        border-radius: 6px;
        padding: 12px;
        margin: 15px auto;
        max-width: 90%;
        text-align: left;
    }
    .creator-avatar {
        width: 36px;
        height: 36px;
        border-radius: 50%;
        object-fit: cover;
        margin-right: 12px;
        flex-shrink: 0;
    }
    .creator-content {
        font-size: 0.9em;
        color: #4a5568;
        line-height: 1.4;
        width: 100%;
    }
    .creator-name-tag {
        font-weight: bold;
        color: #1a202c;
        margin-bottom: 4px;
    }
    .comic-page { max-width: 100%; height: auto; display: block; margin: 10px auto; }
    """
    css_item = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style)
    book.add_item(css_item)

    spine_items = []
    capa_path = encontrar_capa_serie(pasta_serie)
    capa_html_tag = ""

    if capa_path and capa_path.exists():
        ext = capa_path.suffix.lower().replace(".", "")
        if ext == "jpg": ext = "jpeg"
        with open(capa_path, "rb") as f:
            book.set_cover(f"cover_img.{ext}", f.read())
        capa_html_tag = f'<div class="cover-box"><img src="cover_img.{ext}" alt="Capa" class="cover-img"/></div>'

    # Adiciona o avatar do autor ao EPUB, se existir
    avatar_path = encontrar_avatar_autor()
    avatar_epub_name = ""
    if avatar_path and avatar_path.exists():
        av_ext = avatar_path.suffix.lower().replace(".", "")
        if av_ext == "jpg": av_ext = "jpeg"
        avatar_epub_name = f"images/author_avatar.{av_ext}"
        with open(avatar_path, "rb") as av_file:
            avatar_item = epub.EpubItem(
                uid="author_avatar_img",
                file_name=avatar_epub_name,
                media_type=f"image/{av_ext}",
                content=av_file.read()
            )
            book.add_item(avatar_item)

    # Página de informações iniciais
    print("   📄 Criando página de informações e capa...")
    rosto_page = epub.EpubHtml(title="Informações", file_name="info.xhtml", lang="pt-BR")
    desc_clean = limpar_html_para_epub(meta["description"]).replace("\n", "<br/>")

    stats_parts = []
    if meta["genre"]: stats_parts.append(f"Gênero: {html.escape(meta['genre'])}")
    if meta["views"]: stats_parts.append(f"👁️ {meta['views']}")
    if meta["likes"]: stats_parts.append(f"❤️ {meta['likes']}")
    stats_html = f'<div class="stats-bar">{" • ".join(stats_parts)}</div>' if stats_parts else ""

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
    {stats_html}
    <div class="description-text">{desc_clean}</div>
</body>
</html>"""
    rosto_page.add_item(css_item)
    book.add_item(rosto_page)
    spine_items.append(rosto_page)

    toc_items = [rosto_page]
    total_imagens_geral = 0

    print("   📑 Construindo capítulos e organizando sumário...")
    for idx, ep_folder in enumerate(episodios, start=1):
        ep_info = carregar_dados_episodio(ep_folder)
        if idx % 10 == 0 or idx == len(episodios):
            print(f"      ... processado até o capítulo {idx}/{len(episodios)}")

        titulo_cap = f"Cap. {idx} — {html.escape(ep_info['title'])}"

        images_dir = ep_folder / "images"
        html_imgs = []

        if images_dir.is_dir():
            exts = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
            arquivos_img = sorted([img for img in images_dir.iterdir() if img.suffix.lower() in exts])

            for img_path in arquivos_img:
                total_imagens_geral += 1
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

                html_imgs.append(f'<img src="{epub_img_name}" class="comic-page" alt="Página {total_imagens_geral}"/>')

        date_html = f'<div class="chapter-date">{ep_info["publish_date"]}</div>' if ep_info["publish_date"] else ""
        
        note_html = ""
        if ep_info["creator_note"]:
            note_clean = limpar_html_para_epub(ep_info["creator_note"])
            avatar_tag = f'<img src="{avatar_epub_name}" class="creator-avatar" alt="Avatar"/>' if avatar_epub_name else ""
            note_html = f"""
            <div class="creator-note-box">
                {avatar_tag}
                <div class="creator-content">
                    <div class="creator-name-tag">{html.escape(meta['author'])}</div>
                    <div>{note_clean}</div>
                </div>
            </div>
            """

        cap_page = epub.EpubHtml(title=f"Cap. {idx} - {ep_info['title']}", file_name=f"capitulo_{idx}.xhtml", lang="pt-BR")
        cap_page.content = f"""<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>{titulo_cap}</title>
    <link rel="stylesheet" href="style/nav.css" type="text/css"/>
</head>
<body>
    <h2 class="chapter-title">{titulo_cap}</h2>
    {date_html}
    {note_html}
    {"".join(html_imgs)}
</body>
</html>"""
        cap_page.add_item(css_item)
        book.add_item(cap_page)

        spine_items.append(cap_page)
        toc_items.append(cap_page)

    book.toc = toc_items
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ["nav"] + spine_items

    output_epub = pasta_serie / f"{pasta_serie.name}.epub"
    print("   💾 Iniciando montagem final e salvando arquivo EPUB no disco...")
    epub.write_epub(str(output_epub), book, {})

    print(f"   ✅ [Sucesso] EPUB gerado: {output_epub.name} ({total_imagens_geral} imagens incluídas)\n")
    return True


def main():
    parser = argparse.ArgumentParser(description="Gera EPUBs com logs detalhados.")
    parser.add_argument("--pastas", "-p", nargs="+", help="Pastas específicas.")
    args = parser.parse_args()

    if args.pastas:
        target_folders = [Path(p).resolve() for p in args.pastas]
    else:
        target_folders = [item for item in BASE_DIR.iterdir() if item.is_dir() and not item.name.startswith(".")]

    autor_nome = carregar_dados_autor()
    print(f"🚀 [Início] Gerador de EPUB ativado. Autor: {autor_nome} | Total de pastas alvo: {len(target_folders)}\n")
    
    processadas = sum(1 for pasta in target_folders if pasta.is_dir() and criar_epub_serie(pasta))
    print(f"\n{'='*40}\n✨ [Fim] Concluído! {processadas} EPUB(s) gerado(s).")


if __name__ == "__main__":
    main()
