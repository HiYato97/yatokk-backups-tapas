import os
import json
import html
from pathlib import Path

BASE_DIR = Path(".").resolve()
CONFIG_FILE = BASE_DIR / "config.json"

# Template padrão criado caso o config.json não exista
CONFIG_PADRAO = {
    "nome": "Nome do Autor",
    "bio": "Escreva uma breve descrição sobre o autor aqui.",
    "localizacao": "Brasil",
    "foto": "",
    "twitter": "",
    "linktree": "",
    "site": ""
}

def carregar_configuracao():
    """Carrega o config.json ou cria um modelo padrão se não existir."""
    if not CONFIG_FILE.exists():
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(CONFIG_PADRAO, f, ensure_ascii=False, indent=2)
        print(f"⚠️  Arquivo 'config.json' não encontrado. Criado um modelo padrão em: {CONFIG_FILE}")
        return CONFIG_PADRAO

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            dados = json.load(f)
            # Garante que todas as chaves esperadas existam
            for chave, valor in CONFIG_PADRAO.items():
                dados.setdefault(chave, valor)
            return dados
    except Exception as e:
        print(f"❌ Erro ao ler 'config.json': {e}. Usando valores padrão.")
        return CONFIG_PADRAO

def obter_metadados_serie(pasta_serie):
    """Extrai o título e gênero da série a partir dos metadados locais ou do nome da pasta."""
    titulo = pasta_serie.name
    genero = ""

    caminho_series_json = pasta_serie / "series.json"
    if caminho_series_json.exists():
        try:
            with open(caminho_series_json, "r", encoding="utf-8") as f:
                data = json.load(f)
                s_data = data.get("data", data)
                titulo = s_data.get("title", titulo)
                
                genre_data = s_data.get("genre", {})
                if isinstance(genre_data, dict):
                    genero = genre_data.get("name", "")
                elif isinstance(genre_data, str):
                    genero = genre_data
        except Exception:
            pass

    if titulo == pasta_serie.name:
        caminho_manifest = pasta_serie / "manifest.json"
        if caminho_manifest.exists():
            try:
                with open(caminho_manifest, "r", encoding="utf-8") as f:
                    manifest_data = json.load(f)
                    titulo = manifest_data.get("series_title", titulo)
            except Exception:
                pass

    return html.unescape(titulo).strip(), genero

def encontrar_capa_serie(pasta_serie):
    """Procura a imagem de capa da série."""
    extensoes_validas = {'.jpg', '.jpeg', '.png', '.webp'}

    # 1. Arquivo img_ ou cover na pasta da série
    try:
        for arquivo in pasta_serie.iterdir():
            if arquivo.is_file():
                nome_lower = arquivo.name.lower()
                ext_lower = arquivo.suffix.lower()
                if (nome_lower.startswith("img_") or nome_lower.startswith("cover")) and ext_lower in extensoes_validas:
                    return arquivo.relative_to(BASE_DIR).as_posix()
    except Exception:
        pass

    # 2. Primeira imagem de episódio
    pasta_episodes = pasta_serie / "episodes"
    if pasta_episodes.exists():
        for ext in ['*.jpg', '*.jpeg', '*.png', '*.webp']:
            imagens = sorted(list(pasta_episodes.glob(f"**/{ext}")))
            if imagens:
                return imagens[0].relative_to(BASE_DIR).as_posix()

    return ""

def listar_series():
    series = []
    for item in BASE_DIR.iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            html_files = list(item.glob("*_completo.html")) or list(item.glob("*.html"))
            if html_files:
                ficheiro_html = html_files[0]
                titulo_real, genero = obter_metadados_serie(item)
                capa = encontrar_capa_serie(item)
                
                series.append({
                    "titulo": titulo_real,
                    "genero": genero,
                    "url": ficheiro_html.relative_to(BASE_DIR).as_posix(),
                    "capa": capa
                })
    return sorted(series, key=lambda x: x["titulo"])

def gerar_html_index():
    autor = carregar_configuracao()
    series = listar_series()
    total_series = len(series)

    # Trata a foto de perfil (seja caminho local ou URL externa)
    foto_src = autor.get("foto", "").strip()
    if foto_src:
        avatar_html = f'<img src="{foto_src}" alt="{autor["nome"]}" class="avatar">'
    else:
        inicial = autor["nome"][0].upper() if autor["nome"] else "A"
        avatar_html = f'<div class="avatar-placeholder">{inicial}</div>'

    loc_html = f'<div class="author-meta"><span>📍 {autor["localizacao"]}</span></div>' if autor.get("localizacao") else ''
    bio_html = f'<p class="bio">{autor["bio"]}</p>' if autor.get("bio") else ''

    # Links de mídias sociais
    social_links_html = ""
    if autor.get("twitter"):
        social_links_html += f'<a href="{autor["twitter"]}" target="_blank" class="social-link">🐦 Twitter / X</a>'
    if autor.get("linktree"):
        social_links_html += f'<a href="{autor["linktree"]}" target="_blank" class="social-link">🔗 Linktree</a>'
    if autor.get("site"):
        social_links_html += f'<a href="{autor["site"]}" target="_blank" class="social-link">🌐 Website</a>'

    if social_links_html:
        social_links_html = f'<div class="social-links">{social_links_html}</div>'

    html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{autor["nome"]} | Acervo de Séries</title>
    <style>
        :root {{
            --bg-main: #0f0f10;
            --bg-card: #18181c;
            --text-primary: #ffffff;
            --text-secondary: #9999a1;
            --accent: #ffcc00;
            --border-color: #27272e;
        }}

        * {{ margin: 0; padding: 0; box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }}

        body {{
            background-color: var(--bg-main);
            color: var(--text-primary);
            padding: 30px 20px;
            min-height: 100vh;
        }}

        .container {{
            max-width: 1100px;
            margin: 0 auto;
            display: grid;
            grid-template-columns: 260px 1fr;
            gap: 40px;
        }}

        @media (max-width: 768px) {{
            .container {{
                grid-template-columns: 1fr;
            }}
        }}

        .sidebar {{
            display: flex;
            flex-direction: column;
            align-items: center;
            text-align: center;
        }}

        .avatar {{
            width: 150px;
            height: 150px;
            border-radius: 50%;
            object-fit: cover;
            margin-bottom: 20px;
            border: 3px solid var(--border-color);
            background: #222;
        }}

        .avatar-placeholder {{
            width: 150px;
            height: 150px;
            border-radius: 50%;
            margin-bottom: 20px;
            border: 3px solid var(--border-color);
            background: #222;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 3rem;
            font-weight: bold;
            color: var(--accent);
        }}

        .author-name {{
            font-size: 1.8rem;
            font-weight: 700;
            margin-bottom: 8px;
        }}

        .author-meta {{
            color: var(--text-secondary);
            font-size: 0.9rem;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 5px;
            justify-content: center;
        }}

        .bio {{
            color: var(--text-secondary);
            font-size: 0.95rem;
            margin: 10px 0 20px 0;
            line-height: 1.4;
        }}

        .social-links {{
            display: flex;
            flex-direction: column;
            gap: 8px;
            width: 100%;
        }}

        .social-link {{
            color: var(--text-secondary);
            text-decoration: none;
            font-size: 0.9rem;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            padding: 8px 12px;
            border-radius: 6px;
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            transition: all 0.2s;
        }}

        .social-link:hover {{
            color: var(--text-primary);
            border-color: #444;
        }}

        .main-content {{
            display: flex;
            flex-direction: column;
        }}

        .header-tabs {{
            display: flex;
            align-items: baseline;
            gap: 20px;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 12px;
            margin-bottom: 25px;
        }}

        .header-tabs h2 {{
            font-size: 1.2rem;
            font-weight: 700;
            color: var(--text-primary);
            border-bottom: 2px solid var(--text-primary);
            padding-bottom: 10px;
            margin-bottom: -13px;
        }}

        .series-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
            gap: 20px;
        }}

        .series-card {{
            background: var(--bg-card);
            border-radius: 8px;
            overflow: hidden;
            text-decoration: none;
            color: inherit;
            display: flex;
            flex-direction: column;
            transition: transform 0.2s, box-shadow 0.2s;
            border: 1px solid var(--border-color);
        }}

        .series-card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 8px 20px rgba(0,0,0,0.4);
        }}

        .card-thumb {{
            width: 100%;
            height: 180px;
            object-fit: cover;
            background: #25252b;
            display: block;
        }}

        .card-info {{
            padding: 12px;
            display: flex;
            flex-direction: column;
            gap: 4px;
        }}

        .card-title {{
            font-size: 0.95rem;
            font-weight: 700;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}

        .card-author {{
            font-size: 0.8rem;
            color: var(--text-secondary);
        }}

        .card-tag {{
            font-size: 0.75rem;
            color: var(--accent);
            margin-top: 2px;
        }}
    </style>
</head>
<body>

    <div class="container">
        <aside class="sidebar">
            {avatar_html}
            <h1 class="author-name">{autor["nome"]}</h1>
            {loc_html}
            {bio_html}
            {social_links_html}
        </aside>

        <main class="main-content">
            <div class="header-tabs">
                <h2>{total_series} Séries</h2>
            </div>

            <div class="series-grid">
"""

    for item in series:
        thumb_html = f'<img src="{item["capa"]}" alt="{item["titulo"]}" class="card-thumb">' if item["capa"] else '<div class="card-thumb"></div>'
        tag_html = f'<div class="card-tag">{item["genero"]}</div>' if item["genero"] else ''
        
        html_content += f"""
                <a href="{item['url']}" class="series-card">
                    {thumb_html}
                    <div class="card-info">
                        <div class="card-title" title="{item['titulo']}">{item['titulo']}</div>
                        <div class="card-author">{autor["nome"]}</div>
                        {tag_html}
                    </div>
                </a>
"""

    html_content += """
            </div>
        </main>
    </div>

</body>
</html>
"""

    caminho_index = BASE_DIR / "index.html"
    with open(caminho_index, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"✅ 'index.html' gerado com sucesso para '{autor['nome']}'!")

if __name__ == "__main__":
    gerar_html_index()