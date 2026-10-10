import html
import json
import os
from datetime import datetime
from pathlib import Path

# Importa o módulo isolado de informações do projeto
from utils_projeto import CSS_MODAL_INFO, gerar_componente_modal_info

BASE_DIR = Path(".").resolve()
CONFIG_FILE = BASE_DIR / "config.json"
DATA_GERACAO = datetime.now().strftime("%d/%m/%Y %H:%M")

# Template padrão genérico/universal com o campo tools
CONFIG_PADRAO = {
    "nome": "Nome do Autor",
    "bio": "Escreva uma breve descrição sobre o autor aqui.",
    "localizacao": "Brasil",
    "foto": "",
    "perfil_original": "",
    "tools": "",
    "redes_sociais": {
        "Twitter / X": "",
        "Website": ""
    }
}


def carregar_configuracao():
    """Carrega o config.json ou cria um modelo padrão se não existir."""
    if not CONFIG_FILE.exists():
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(CONFIG_PADRAO, f, ensure_ascii=False, indent=2)
        print(
            f"⚠ Arquivo 'config.json' não encontrado. Criado modelo padrão em: {CONFIG_FILE}"
        )
        return CONFIG_PADRAO

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            dados = json.load(f)
            
            # Garante retrocompatibilidade e campos básicos
            dados.setdefault("nome", CONFIG_PADRAO["nome"])
            dados.setdefault("bio", "")
            dados.setdefault("localizacao", "")
            dados.setdefault("foto", "")
            dados.setdefault("perfil_original", "")
            dados.setdefault("tools", "")
            
            # Trata redes sociais genéricas
            if "redes_sociais" not in dados or not isinstance(dados["redes_sociais"], dict):
                dados["redes_sociais"] = {}

            # Converte chaves legadas antigas para a nova estrutura se existirem
            chaves_legadas = {
                "twitter": "Twitter / X",
                "linktree": "Linktree",
                "site": "Website"
            }
            for chave_old, label in chaves_legadas.items():
                if dados.get(chave_old) and label not in dados["redes_sociais"]:
                    dados["redes_sociais"][label] = dados[chave_old]

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
    extensoes_validas = {".jpg", ".jpeg", ".png", ".webp"}

    # 1. Arquivo img_ ou cover na pasta da série
    try:
        for arquivo in pasta_serie.iterdir():
            if arquivo.is_file():
                nome_lower = arquivo.name.lower()
                ext_lower = arquivo.suffix.lower()
                if (
                    nome_lower.startswith("img_")
                    or nome_lower.startswith("cover")
                ) and ext_lower in extensoes_validas:
                    return arquivo.relative_to(BASE_DIR).as_posix()
    except Exception:
        pass

    # 2. Primeira imagem de episódio
    pasta_episodes = pasta_serie / "episodes"
    if pasta_episodes.exists():
        for ext in ["*.jpg", "*.jpeg", "*.png", "*.webp"]:
            imagens = sorted(list(pasta_episodes.glob(f"**/{ext}")))
            if imagens:
                return imagens[0].relative_to(BASE_DIR).as_posix()

    return ""


def listar_series():
    series = []
    for item in BASE_DIR.iterdir():
        if item.is_dir() and not item.name.startswith("."):
            html_files = list(item.glob("*_completo.html")) or list(
                item.glob("*.html")
            )
            if html_files:
                ficheiro_html = html_files[0]
                titulo_real, genero = obter_metadados_serie(item)
                capa = encontrar_capa_serie(item)

                series.append(
                    {
                        "titulo": titulo_real,
                        "genero": genero,
                        "url": ficheiro_html.relative_to(BASE_DIR).as_posix(),
                        "capa": capa,
                    }
                )
    return sorted(series, key=lambda x: x["titulo"])


def gerar_html_index():
    autor = carregar_configuracao()
    series = listar_series()
    total_series = len(series)

    # Verifica se existe um arquivo index.html na pasta pai (Hub)
    hub_file = BASE_DIR.parent / "index.html"
    has_hub = hub_file.exists()

    hub_button_html = ""
    if has_hub:
        hub_button_html = (
            '<a href="../index.html" class="hub-link">← Voltar ao Hub</a>'
        )

    # Trata a foto de perfil
    foto_src = autor.get("foto", "").strip()
    if foto_src:
        avatar_html = f'<img src="{foto_src}" alt="{autor["nome"]}" class="avatar">'
    else:
        inicial = autor["nome"][0].upper() if autor["nome"] else "A"
        avatar_html = f'<div class="avatar-placeholder">{inicial}</div>'

    loc_html = (
        f'<div class="author-meta"><span>📍 {autor["localizacao"]}</span></div>'
        if autor.get("localizacao")
        else ""
    )
    
    # Campo Tools (Ferramentas)
    tools_html = (
        f'<div class="author-tools"><span>🛠️ {autor["tools"]}</span></div>'
        if autor.get("tools")
        else ""
    )

    bio_html = f'<p class="bio">{autor["bio"]}</p>' if autor.get("bio") else ""

    # Botão do Perfil Original
    perfil_original_html = ""
    if autor.get("perfil_original"):
        perfil_original_html = (
            f'<a href="{autor["perfil_original"]}" target="_blank" class="social-link btn-perfil-original">'
            f'🌐 Perfil Original</a>'
        )

    # Links de mídias sociais genéricas
    social_links_html = ""
    if perfil_original_html:
        social_links_html += perfil_original_html

    redes = autor.get("redes_sociais", {})
    for nome_rede, url in redes.items():
        if url and url.strip():
            social_links_html += (
                f'<a href="{url.strip()}" target="_blank" class="social-link">🔗 {nome_rede}</a>'
            )

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
            padding-top: 60px;
            padding-bottom: 30px;
            padding-left: 20px;
            padding-right: 20px;
            min-height: 100vh;
        }}

        #versao {{
            position: fixed;
            top: 0; left: 0; right: 0;
            background: var(--bg-card);
            color: var(--text-secondary);
            padding: 0.4rem 1rem;
            text-align: center;
            z-index: 1000;
            font-size: 0.85rem;
            border-bottom: 1px solid var(--border-color);
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 10px;
        }}

        /* Estilos do Modal de Informação importados do utils_projeto */
        {CSS_MODAL_INFO}

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

        .hub-link {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            color: var(--text-secondary);
            text-decoration: none;
            font-size: 0.85rem;
            font-weight: 600;
            margin-bottom: 20px;
            padding: 8px 14px;
            border-radius: 6px;
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            transition: all 0.2s;
            width: 100%;
        }}

        .hub-link:hover {{
            color: var(--accent);
            border-color: var(--accent);
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

        .author-meta, .author-tools {{
            color: var(--text-secondary);
            font-size: 0.88rem;
            margin-bottom: 6px;
            display: flex;
            align-items: center;
            gap: 5px;
            justify-content: center;
        }}

        .author-tools {{
            margin-bottom: 12px;
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

        .btn-perfil-original {{
            border-color: rgba(255, 204, 0, 0.4);
            color: var(--accent);
            font-weight: 600;
        }}

        .btn-perfil-original:hover {{
            background: rgba(255, 204, 0, 0.1);
            border-color: var(--accent);
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

    <div id="versao">
        <span>Acervo de Séries de <b>{html.escape(autor["nome"])}</b> | Gerado em {DATA_GERACAO}</span>
        {gerar_componente_modal_info(BASE_DIR.parent)}
    </div>

    <div class="container">
        <aside class="sidebar">
            {hub_button_html}
            {avatar_html}
            <h1 class="author-name">{autor["nome"]}</h1>
            {loc_html}
            {tools_html}
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
        thumb_html = (
            f'<img src="{item["capa"]}" alt="{item["titulo"]}" class="card-thumb">'
            if item["capa"]
            else '<div class="card-thumb"></div>'
        )
        tag_html = (
            f'<div class="card-tag">{item["genero"]}</div>'
            if item["genero"]
            else ""
        )

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