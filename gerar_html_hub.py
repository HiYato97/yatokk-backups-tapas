import json
from pathlib import Path


def gerar_hub_html():
    pasta_raiz = Path(".")
    artistas = []

    # Procura subpastas que possuem index.html
    for pasta in pasta_raiz.iterdir():
        if pasta.is_dir() and not pasta.name.startswith(".") and pasta.name != "tapas-backup":
            index_path = pasta / "index.html"
            config_path = pasta / "config.json"

            if index_path.exists():
                nome_artista = pasta.name
                bio = ""
                avatar_path = pasta / "avatar.png"

                # Se houver config.json, extrai dados adicionais
                if config_path.exists():
                    try:
                        with open(config_path, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            # Pega nome ou bio se existirem no JSON
                            nome_artista = data.get(
                                "author", data.get("name", pasta.name)
                            )
                            bio = data.get("bio", "")
                    except Exception:
                        pass

                artistas.append(
                    {
                        "pasta": pasta.name,
                        "nome": nome_artista,
                        "link": f"{pasta.name}/index.html",
                        "has_avatar": avatar_path.exists(),
                        "avatar_src": f"{pasta.name}/avatar.png",
                        "bio": bio,
                    }
                )

    # Ordena alfabeticamente pelo nome do artista
    artistas.sort(key=lambda x: x["nome"].lower())

    # HTML Template
    cards_html = ""
    for a in artistas:
        if a["has_avatar"]:
            thumb_html = f'<img src="{a["avatar_src"]}" alt="{a["nome"]}" class="card-thumb">'
        else:
            primeira_letra = a["nome"][0].upper() if a["nome"] else "?"
            thumb_html = f'<div class="card-thumb-placeholder">{primeira_letra}</div>'

        bio_html = (
            f'<p class="card-bio">{a["bio"]}</p>' if a["bio"] else ""
        )

        cards_html += f"""
        <a href="{a['link']}" class="artist-card">
            {thumb_html}
            <div class="card-info">
                <div class="card-title" title="{a['nome']}">{a['nome']}</div>
                {bio_html}
                <div class="card-tag">Ver Acervo →</div>
            </div>
        </a>"""

    html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hub de Artistas | Acervo Tapas</title>
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
            padding: 40px 20px;
            min-height: 100vh;
        }}

        .container {{
            max-width: 1000px;
            margin: 0 auto;
        }}

        .header {{
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}

        .header h1 {{
            font-size: 2rem;
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: 8px;
        }}

        .header p {{
            color: var(--text-secondary);
            font-size: 0.95rem;
        }}

        .artists-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 20px;
        }}

        .artist-card {{
            background: var(--bg-card);
            border-radius: 12px;
            overflow: hidden;
            text-decoration: none;
            color: inherit;
            display: flex;
            flex-direction: column;
            transition: transform 0.2s, box-shadow 0.2s, border-color 0.2s;
            border: 1px solid var(--border-color);
            align-items: center;
            padding: 20px 15px;
            text-align: center;
        }}

        .artist-card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 8px 20px rgba(0,0,0,0.4);
            border-color: #444;
        }}

        .card-thumb {{
            width: 100px;
            height: 100px;
            border-radius: 50%;
            object-fit: cover;
            border: 3px solid var(--border-color);
            margin-bottom: 15px;
            background: #222;
        }}

        .card-thumb-placeholder {{
            width: 100px;
            height: 100px;
            border-radius: 50%;
            border: 3px solid var(--border-color);
            margin-bottom: 15px;
            background: #222;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 2.5rem;
            font-weight: bold;
            color: var(--accent);
        }}

        .card-info {{
            display: flex;
            flex-direction: column;
            gap: 6px;
            width: 100%;
        }}

        .card-title {{
            font-size: 1.1rem;
            font-weight: 700;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}

        .card-bio {{
            font-size: 0.8rem;
            color: var(--text-secondary);
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
            line-height: 1.3;
        }}

        .card-tag {{
            font-size: 0.8rem;
            font-weight: 600;
            color: var(--accent);
            margin-top: 8px;
        }}
    </style>
</head>
<body>

    <div class="container">
        <header class="header">
            <h1>🎨 Hub de Artistas</h1>
            <p>Selecione um autor para navegar pelo acervo de séries e quadrinhos.</p>
        </header>

        <main class="artists-grid">
            {cards_html if cards_html else '<p style="color: var(--text-secondary);">Nenhum acervo de artista encontrado.</p>'}
        </main>
    </div>

</body>
</html>
"""

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"Hub gerado com sucesso contendo {len(artistas)} artista(s)!")


if __name__ == "__main__":
    gerar_hub_html()