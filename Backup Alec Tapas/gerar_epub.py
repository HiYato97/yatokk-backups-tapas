import os
import json
import html
import argparse
import mimetypes
from pathlib import Path
from PIL import Image
from ebooklib import epub

BASE_DIR = Path(".").resolve()

def carregar_config_autor():
    config_file = BASE_DIR / "config.json"
    if config_file.exists():
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                dados = json.load(f)
                return dados.get("nome", "Autor Desconhecido")
        except Exception:
            pass
    return "Autor Desconhecido"

def obter_metadados_serie(pasta_serie):
    titulo = pasta_serie.name
    genero = "Geral"
    descricao = ""

    caminho_series_json = pasta_serie / "series.json"
    if caminho_series_json.exists():
        try:
            with open(caminho_series_json, "r", encoding="utf-8") as f:
                data = json.load(f)
                s_data = data.get("data", data)
                titulo = s_data.get("title", titulo)
                descricao = s_data.get("description", "")
                
                genre_data = s_data.get("genre", {})
                if isinstance(genre_data, dict):
                    genero = genre_data.get("name", genero)
                elif isinstance(genre_data, str):
                    genero = genre_data
        except Exception:
            pass

    return html.unescape(titulo).strip(), genero, descricao

def obter_capa_e_imagens(pasta_serie):
    extensoes = ('*.jpg', '*.jpeg', '*.png', '*.webp', '*.JPG', '*.PNG', '*.JPEG')
    
    # 1. Procura a CAPA exclusivamente na raiz da pasta da série
    capa_encontrada = None
    for ext in extensoes:
        imagens_raiz = list(pasta_serie.glob(ext))
        if imagens_raiz:
            for img in imagens_raiz:
                nome_lower = img.name.lower()
                if "cover" in nome_lower or "banner" in nome_lower or "img_" in nome_lower:
                    capa_encontrada = img
                    break
            if not capa_encontrada:
                capa_encontrada = imagens_raiz[0]
            break

    # 2. Coleta todas as imagens da série (incluindo subpastas)
    todas_imagens = []
    for ext in extensoes:
        todas_imagens.extend(pasta_serie.rglob(ext))

    imagens_validas = []
    for img in todas_imagens:
        if img.suffix.lower() in ['.pdf', '.epub']:
            continue
        
        partes_caminho = [p.lower() for p in img.parts]
        if any(p in partes_caminho for p in ['cache', '.cache', 'thumb', 'thumbs', 'thumbnail', 'thumbnails']):
            continue
        if any(part.startswith('.') for part in img.parts):
            continue

        imagens_validas.append(img)

    if not imagens_validas:
        return None, []

    # Deduplicação e ordenação
    unicas_por_caminho = {}
    for img in imagens_validas:
        chave_relativa = img.relative_to(pasta_serie).as_posix()
        if chave_relativa not in unicas_por_caminho:
            unicas_por_caminho[chave_relativa] = img

    lista_final = list(unicas_por_caminho.values())
    lista_final.sort(key=lambda x: [int(c) if c.isdigit() else c.lower() for c in x.as_posix().split('/')])

    # Separa a capa das imagens do corpo
    if capa_encontrada:
        imagens_corpo = [img for img in lista_final if img.resolve() != capa_encontrada.resolve()]
    else:
        capa_encontrada = lista_final[0]
        imagens_corpo = lista_final[1:]

    return capa_encontrada, imagens_corpo

def converter_serie_para_epub(pasta_serie, autor_nome):
    if not pasta_serie.exists() or not pasta_serie.is_dir():
        print(f"❌ Erro: Pasta não encontrada: '{pasta_serie}'")
        return

    titulo, genero, descricao = obter_metadados_serie(pasta_serie)
    capa_path, imagens = obter_capa_e_imagens(pasta_serie)

    if not capa_path and not imagens:
        print(f"⚠️  Nenhuma imagem válida em: '{pasta_serie.name}'")
        return

    total_imagens = len(imagens) + (1 if capa_path else 0)
    print(f"🔄 Gerando EPUB para '{pasta_serie.name}' ({total_imagens} imagens)...")

    epub_nome = f"{pasta_serie.name}.epub"
    epub_path = pasta_serie / epub_nome

    book = epub.EpubBook()
    book.set_identifier(f"id_{pasta_serie.name.lower().replace(' ', '_')}")
    book.set_title(titulo)
    book.set_language('pt-BR')
    book.add_author(autor_nome)

    css_content = """
        @page { margin: 0; padding: 0; }
        body {
            margin: 0;
            padding: 0;
            background-color: #ffffff;
            color: #1a1a1a;
            font-family: sans-serif;
            text-align: center;
        }
        .cover-container { padding: 5% 5%; box-sizing: border-box; }
        h1 { font-size: 1.8em; margin-bottom: 0.2em; color: #111111; }
        h2 { font-size: 1.1em; color: #555555; margin-bottom: 1em; font-weight: normal; }
        .meta-badge { font-size: 0.9em; color: #2b6cb0; margin-bottom: 1.5em; }
        .cover-img { max-width: 80%; max-height: 50vh; height: auto; border-radius: 4px; }
        .desc { font-size: 0.85em; color: #666666; font-style: italic; margin-top: 1.5em; padding: 0 10%; }
        
        .page-image-container {
            width: 100vw;
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            margin: 0;
            padding: 0;
        }
        svg { width: 100%; height: 100%; }
    """
    style_item = epub.EpubItem(uid="style_nav", file_name="style/style.css", media_type="text/css", content=css_content)
    book.add_item(style_item)

    if capa_path and capa_path.exists():
        mime_type, _ = mimetypes.guess_type(capa_path)
        mime_type = mime_type or 'image/jpeg'
        capa_bytes = capa_path.read_bytes()
        capa_ext = capa_path.suffix.lower()
        book.set_cover(f"cover{capa_ext}", capa_bytes)

    desc_limpa = html.unescape(descricao) if descricao else ""
    if len(desc_limpa) > 300:
        desc_limpa = desc_limpa[:300] + "..."

    desc_html = f'<p class="desc">{desc_limpa}</p>' if desc_limpa else ''

    meta_page_content = f"""<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>{titulo}</title>
    <link rel="stylesheet" href="style/style.css" type="text/css"/>
</head>
<body>
    <div class="cover-container">
        <h1>{titulo}</h1>
        <h2>Por <b>{autor_nome}</b></h2>
        <div class="meta-badge"><b>Gênero:</b> {genero} &nbsp;|&nbsp; <b>Total de Imagens:</b> {total_imagens}</div>
        {desc_html}
    </div>
</body>
</html>"""

    page_info = epub.EpubHtml(title="Informações", file_name="info.xhtml", lang="pt-BR")
    page_info.content = meta_page_content
    page_info.add_item(style_item)
    book.add_item(page_info)

    spine = ['nav', page_info]

    for idx, img_path in enumerate(imagens, start=1):
        try:
            mime_type, _ = mimetypes.guess_type(img_path)
            mime_type = mime_type or 'image/jpeg'
            
            with Image.open(img_path) as img:
                img_w, img_h = img.size

            img_file_name = f"images/page_{idx:04d}{img_path.suffix}"
            img_item = epub.EpubItem(
                uid=f"img_{idx}",
                file_name=img_file_name,
                media_type=mime_type,
                content=img_path.read_bytes()
            )
            book.add_item(img_item)

            page_content = f"""<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>Página {idx}</title>
    <link rel="stylesheet" href="style/style.css" type="text/css"/>
</head>
<body style="margin:0; padding:0;">
    <div class="page-image-container">
        <svg xmlns="http://www.w3.org/2000/svg" version="1.1" viewBox="0 0 {img_w} {img_h}" width="100%" height="100%">
            <image width="{img_w}" height="{img_h}" href="{img_file_name}"/>
        </svg>
    </div>
</body>
</html>"""

            page_xhtml = epub.EpubHtml(title=f"Página {idx}", file_name=f"page_{idx:04d}.xhtml", lang="pt-BR")
            page_xhtml.content = page_content
            page_xhtml.add_item(style_item)
            book.add_item(page_xhtml)

            spine.append(page_xhtml)

        except Exception as e:
            print(f"   ⚠️ Erro na imagem {img_path.name}: {e}")

    book.spine = spine
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    try:
        epub.write_epub(str(epub_path), book, {})
        print(f"✅ EPUB gerado com sucesso: {epub_path.relative_to(BASE_DIR)}\n")
    except PermissionError:
        print(f"❌ ERRO: O arquivo '{epub_path.name}' está aberto em outro programa. Feche-o e tente novamente.\n")
    except Exception as e:
        print(f"❌ ERRO ao gerar EPUB de '{pasta_serie.name}': {e}\n")

def main():
    parser = argparse.ArgumentParser(description="Gera EPUBs para séries de quadrinhos/manga.")
    parser.add_argument(
        "--pastas", "-p",
        nargs="*",
        help="Caminhos ou nomes de pastas específicas para processar. Se omitido, processa todas."
    )
    args = parser.parse_args()

    autor_nome = carregar_config_autor()
    print(f"🚀 Gerando EPUBs para o autor: {autor_nome}\n")

    if args.pastas:
        for p in args.pastas:
            pasta_alvo = Path(p).resolve() if Path(p).is_absolute() else BASE_DIR / p
            converter_serie_para_epub(pasta_alvo, autor_nome)
    else:
        for item in BASE_DIR.iterdir():
            if item.is_dir() and not item.name.startswith('.') and not item.name.startswith('__'):
                converter_serie_para_epub(item, autor_nome)

if __name__ == "__main__":
    main()