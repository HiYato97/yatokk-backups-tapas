import html
import json
from datetime import datetime
from pathlib import Path
from utils_projeto import CSS_MODAL_INFO, gerar_componente_modal_info

BASE_DIR = Path(".").resolve()
AUTHOR_FILE = BASE_DIR / "author.json"
COMMENTS_FILE = BASE_DIR / "author_comments.json"
DATA_GERACAO = datetime.now().strftime("%d/%m/%Y %H:%M")

AUTHOR_PADRAO = {
    "data": {
        "display_name": "Nome do Autor",
        "username": "autor",
        "bio": "Escreva uma breve descrição sobre o autor aqui.",
        "location": "Brasil",
        "tools": "",
        "social_links": {}
    }
}

def carregar_dados_autor():
    if not AUTHOR_FILE.exists():
        with open(AUTHOR_FILE, "w", encoding="utf-8") as f:
            json.dump(AUTHOR_PADRAO, f, ensure_ascii=False, indent=2)
        return AUTHOR_PADRAO["data"]
    try:
        with open(AUTHOR_FILE, "r", encoding="utf-8") as f:
            dados = json.load(f)
            return dados.get("data", dados)
    except Exception:
        return AUTHOR_PADRAO["data"]

def carregar_comentarios_autor():
    if not COMMENTS_FILE.exists():
        return [], ""
    try:
        with open(COMMENTS_FILE, "r", encoding="utf-8") as f:
            dados = json.load(f)
            username_autor = dados.get("username", "").strip().lower()
            comentarios = dados.get("comments", [])
            return comentarios, username_autor
    except Exception:
        return [], ""

def encontrar_avatar():
    for ext in [".png", ".jpg", ".jpeg", ".webp"]:
        avatar_path = BASE_DIR / f"avatar{ext}"
        if avatar_path.exists():
            return avatar_path.relative_to(BASE_DIR).as_posix()
    return ""

def encontrar_mini_thumb(pasta_serie):
    for nome in ["series-mini-thumb.jpg", "series-mini-thumb.png", "cover.jpg", "cover.png"]:
        caminho = pasta_serie / nome
        if caminho.exists():
            return caminho.relative_to(BASE_DIR).as_posix()
            
    extensoes_validas = {".jpg", ".jpeg", ".png", ".webp"}
    try:
        for arquivo in pasta_serie.iterdir():
            if arquivo.is_file():
                nome_lower = arquivo.name.lower()
                if (nome_lower.startswith("img_") or nome_lower.startswith("cover")) and arquivo.suffix.lower() in extensoes_validas:
                    return arquivo.relative_to(BASE_DIR).as_posix()
    except Exception:
        pass

    pasta_episodes = pasta_serie / "episodes"
    if pasta_episodes.exists():
        for ext in ["*.jpg", "*.jpeg", "*.png", "*.webp"]:
            imagens = sorted(list(pasta_episodes.glob(f"**/{ext}")))
            if imagens:
                return imagens[0].relative_to(BASE_DIR).as_posix()
    return ""

def obter_metadados_serie(pasta_serie):
    titulo = pasta_serie.name
    genero = ""
    publish_date = "1970-01-01T00:00:00Z"
    likes = ""
    views = ""

    series_json = pasta_serie / "series.json"
    if series_json.exists():
        try:
            with open(series_json, "r", encoding="utf-8") as f:
                data = json.load(f)
                publish_date = data.get("publish_date", publish_date)
                likes = data.get("likes", "")
                views = data.get("views", "")
                
                s_data = data.get("data", data)
                titulo = s_data.get("title", titulo)
                genre = s_data.get("genre", {})
                if isinstance(genre, dict):
                    genero = genre.get("name", "")
                elif isinstance(genre, str):
                    genero = genre
        except Exception:
            pass

    if titulo == pasta_serie.name:
        manifest_json = pasta_serie / "manifest.json"
        if manifest_json.exists():
            try:
                with open(manifest_json, "r", encoding="utf-8") as f:
                    manifest_data = json.load(f)
                    titulo = manifest_data.get("series_title", titulo)
            except Exception:
                pass

    return html.unescape(titulo).strip(), genero, publish_date, likes, views

def listar_series():
    series = []
    for item in BASE_DIR.iterdir():
        if item.is_dir() and not item.name.startswith("."):
            html_files = list(item.glob("*_completo.html")) or list(item.glob("*.html"))
            if html_files:
                ficheiro_html = html_files[0]
                titulo, genero, publish_date, likes, views = obter_metadados_serie(item)
                capa = encontrar_mini_thumb(item)
                series.append({
                    "titulo": titulo,
                    "genero": genero,
                    "url": ficheiro_html.relative_to(BASE_DIR).as_posix(),
                    "capa": capa,
                    "publish_date": publish_date,
                    "likes": likes,
                    "views": views
                })
    return sorted(series, key=lambda x: x["publish_date"], reverse=True)

def obter_likes_comentario(c):
    # Busca em todas as chaves possíveis de likes no JSON
    for key in ["likes", "like_count", "likesCount", "likeCount", "favorite_count"]:
        if key in c and c[key] is not None:
            try:
                return int(c[key])
            except ValueError:
                pass
    return 0

def formatar_comentario_perfil(c, username_autor_json, index_global=0):
    user = c.get("display_name") or c.get("username") or "Anónimo"
    username_comentario = str(c.get("username", "")).strip().lower()
    text = c.get("text", "")
    date = c.get("date", "")
    likes = obter_likes_comentario(c)
    
    is_creator = False
    if username_autor_json and username_comentario and (username_comentario == username_autor_json):
        is_creator = True
    elif c.get("is_creator", False):
        is_creator = True

    badge = '<span class="badge-criador">Criador</span>' if is_creator else ''
    meta_likes = f"❤️ {likes}" if likes > 0 else ""
    meta_info = [m for m in [date, meta_likes] if m]
    meta_html = f'<div class="comentario-meta">{" • ".join(meta_info)}</div>' if meta_info else ''

    replies_html = ""
    if "replies" in c and isinstance(c["replies"], list) and c["replies"]:
        sub_items = []
        for r in c["replies"]:
            sub_items.append(formatar_comentario_perfil(r, username_autor_json, index_global))
        replies_html = f'<ul class="replies">{"".join(sub_items)}</ul>'

    return f'''
    <li class="comentario-item" data-likes="{likes}" data-creator="{str(is_creator).lower()}" data-index="{index_global}">
        <div class="comentario-header"><span class="autor">{user}</span> {badge}</div>
        <div class="comentario-texto">{text}</div>
        {meta_html}
        {replies_html}
    </li>'''

def gerar_html_index():
    autor = carregar_dados_autor()
    comentarios, username_autor_json = carregar_comentarios_autor()
    
    if not username_autor_json:
        username_autor_json = autor.get("username", "").strip().lower()

    series = listar_series()
    total_series = len(series)

    hub_path_pai = BASE_DIR.parent / "index.html"
    hub_button_html = '<a href="../index.html" class="hub-link">← Voltar ao Hub</a>' if hub_path_pai.exists() else ""

    nome_autor = autor.get("display_name") or autor.get("username") or "Autor"
    avatar_src = encontrar_avatar()

    avatar_html = f'<img src="{avatar_src}" alt="{nome_autor}" class="avatar">' if avatar_src else f'<div class="avatar-placeholder">{nome_autor[0].upper()}</div>'
    loc_html = f'<div class="author-meta"><span>📍 {autor["location"]}</span></div>' if autor.get("location") else ""
    tools_html = f'<div class="author-tools"><span>🛠️ {autor["tools"]}</span></div>' if autor.get("tools") else ""
    
    bio_text = autor.get("bio", "").replace("\n", "<br>")
    bio_html = f'<p class="bio">{bio_text}</p>' if bio_text else ""

    social_links_html = ""
    if username_autor_json:
        social_links_html += f'<a href="https://tapas.io/{username_autor_json}" target="_blank" class="social-link">🌐 Perfil no Tapas</a>'

    for plataforma, url in autor.get("social_links", {}).items():
        if url and url.strip():
            social_links_html += f'<a href="{url.strip()}" target="_blank" class="social-link">🔗 {plataforma}</a>'
    if social_links_html:
        social_links_html = f'<div class="social-links">{social_links_html}</div>'

    series_destaque = series[:3]
    
    generos_disponiveis = sorted(list(set(s["genero"] for s in series if s["genero"])))
    options_generos = ''.join([f'<option value="{g}">{g}</option>' for g in generos_disponiveis])

    cards_destaque_html = ""
    for item in series_destaque:
        thumb_html = f'<img src="{item["capa"]}" alt="{item["titulo"]}" class="card-thumb">' if item["capa"] else '<div class="card-thumb"></div>'
        tag_html = f'<div class="card-tag">{item["genero"]}</div>' if item["genero"] else ""
        stats_parts = []
        if item["likes"]: stats_parts.append(f"❤️ {item['likes']}")
        if item["views"]: stats_parts.append(f"👁️ {item['views']}")
        stats_html = f'<div class="card-stats">{" • ".join(stats_parts)}</div>' if stats_parts else ""

        cards_destaque_html += f'''
        <a href="{item['url']}" class="series-card">
            {thumb_html}
            <div class="card-info">
                <div class="card-title" title="{item['titulo']}">{item['titulo']}</div>
                <div class="card-author">{nome_autor}</div>
                {tag_html}
                {stats_html}
            </div>
        </a>
        '''

    cards_todos_html = ""
    for i, item in enumerate(series):
        thumb_html = f'<img src="{item["capa"]}" alt="{item["titulo"]}" class="card-thumb">' if item["capa"] else '<div class="card-thumb"></div>'
        tag_html = f'<div class="card-tag">{item["genero"]}</div>' if item["genero"] else ""
        stats_parts = []
        if item["likes"]: stats_parts.append(f"❤️ {item['likes']}")
        if item["views"]: stats_parts.append(f"👁️ {item['views']}")
        stats_html = f'<div class="card-stats">{" • ".join(stats_parts)}</div>' if stats_parts else ""

        cards_todos_html += f'''
        <a href="{item['url']}" class="series-card" data-genero="{item['genero']}" data-titulo="{item['titulo'].lower()}" data-date="{item['publish_date']}" data-index="{i}">
            {thumb_html}
            <div class="card-info">
                <div class="card-title" title="{item['titulo']}">{item['titulo']}</div>
                <div class="card-author">{nome_autor}</div>
                {tag_html}
                {stats_html}
            </div>
        </a>
        '''

    primeiros_comentarios = "".join([formatar_comentario_perfil(c, username_autor_json, i) for i, c in enumerate(comentarios[:10])])
    todos_comentarios = "".join([formatar_comentario_perfil(c, username_autor_json, i) for i, c in enumerate(comentarios)])
    total_comentarios = len(comentarios)
    escaped_nome = html.escape(nome_autor)
    modal_info_html = gerar_componente_modal_info(BASE_DIR.parent)

    js_code = """
    <script>
        function abrirModalSeries() {
            document.getElementById('modalSeries').classList.add('ativo');
        }
        function fecharModalSeries() {
            document.getElementById('modalSeries').classList.remove('ativo');
        }
        
        function abrirModalComentarios() {
            document.getElementById('modalComentarios').classList.add('ativo');
        }
        function fecharModalComentarios() {
            document.getElementById('modalComentarios').classList.remove('ativo');
        }

        function filtrarSeries() {
            const busca = document.getElementById('filtroBuscaSerie').value.toLowerCase();
            const genero = document.getElementById('filtroGeneroSerie').value;
            const ordem = document.getElementById('ordenarSeries').value;
            const grid = document.getElementById('gridModalSeries');
            let cards = Array.from(grid.getElementsByClassName('series-card'));

            cards.forEach(card => {
                const titulo = card.getAttribute('data-titulo');
                const genCard = card.getAttribute('data-genero');
                const matchBusca = titulo.includes(busca);
                const matchGenero = !genero || genCard === genero;

                if (matchBusca && matchGenero) {
                    card.setAttribute('data-visible', 'true');
                    card.style.display = 'flex';
                } else {
                    card.setAttribute('data-visible', 'false');
                    card.style.display = 'none';
                }
            });

            cards.sort((a, b) => {
                if (ordem === 'recentes') {
                    return b.getAttribute('data-date').localeCompare(a.getAttribute('data-date'));
                } else if (ordem === 'antigas') {
                    return a.getAttribute('data-date').localeCompare(b.getAttribute('data-date'));
                } else if (ordem === 'az') {
                    return a.getAttribute('data-titulo').localeCompare(b.getAttribute('data-titulo'));
                } else {
                    return parseInt(a.getAttribute('data-index')) - parseInt(b.getAttribute('data-index'));
                }
            });

            cards.forEach(card => grid.appendChild(card));
        }

        function filtrarComentarios() {
            const busca = document.getElementById('filtroBuscaComentario').value.toLowerCase();
            const ordem = document.getElementById('ordenarComentarios').value;
            const lista = document.getElementById('listaModalComentarios');
            
            // Pega apenas os comentários de primeiro nível (evita desestruturar as replies)
            let itens = Array.from(lista.children).filter(el => el.matches('li.comentario-item'));

            itens.forEach(item => {
                const texto = item.textContent.toLowerCase();
                const isCriador = item.getAttribute('data-creator') === 'true';
                const matchBusca = texto.includes(busca);
                let matchOrdem = true;

                if (ordem === 'criador') {
                    matchOrdem = isCriador;
                }

                if (matchBusca && matchOrdem) {
                    item.style.display = 'block';
                } else {
                    item.style.display = 'none';
                }
            });

            if (ordem === 'curtidos') {
                itens.sort((a, b) => {
                    let likesA = parseInt(a.getAttribute('data-likes')) || 0;
                    let likesB = parseInt(b.getAttribute('data-likes')) || 0;
                    return likesB - likesA;
                });
            } else if (ordem === 'antigos') {
                itens.sort((a, b) => {
                    let idxA = parseInt(a.getAttribute('data-index')) || 0;
                    let idxB = parseInt(b.getAttribute('data-index')) || 0;
                    return idxB - idxA;
                });
            } else {
                itens.sort((a, b) => {
                    let idxA = parseInt(a.getAttribute('data-index')) || 0;
                    let idxB = parseInt(b.getAttribute('data-index')) || 0;
                    return idxA - idxB;
                });
            }

            // Reorganiza no DOM mantendo as sublistas (replies) intactas
            itens.forEach(item => lista.appendChild(item));
        }
    </script>
    """

    css_styles = f"""
    <style>
        :root {{
            --bg-main: #0f0f10;
            --bg-card: #18181c;
            --bg-modal: #141417;
            --text-primary: #ffffff;
            --text-secondary: #9999a1;
            --accent: #ffcc00;
            --border-color: #27272e;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }}
        
        *::-webkit-scrollbar {{ width: 8px; height: 8px; }}
        *::-webkit-scrollbar-track {{ background: var(--bg-main); }}
        *::-webkit-scrollbar-thumb {{ background: var(--border-color); border-radius: 4px; }}
        *::-webkit-scrollbar-thumb:hover {{ background: #444450; }}

        body {{ background-color: var(--bg-main); color: var(--text-primary); padding: 60px 20px 30px 20px; min-height: 100vh; }}
        #versao {{
            position: fixed; top: 0; left: 0; right: 0; background: var(--bg-card); color: var(--text-secondary);
            padding: 0.4rem 1rem; text-align: center; z-index: 1000; font-size: 0.85rem; border-bottom: 1px solid var(--border-color);
            display: flex; justify-content: center; align-items: center; gap: 10px;
        }}
        {CSS_MODAL_INFO}
        .container {{ max-width: 1100px; margin: 0 auto; display: grid; grid-template-columns: 260px 1fr; gap: 40px; }}
        @media (max-width: 768px) {{ .container {{ grid-template-columns: 1fr; }} }}
        .sidebar {{ display: flex; flex-direction: column; align-items: center; text-align: center; }}
        .hub-link {{
            display: inline-flex; align-items: center; justify-content: center; gap: 8px; color: var(--text-secondary);
            text-decoration: none; font-size: 0.85rem; font-weight: 600; margin-bottom: 20px; padding: 8px 14px;
            border-radius: 6px; background: var(--bg-card); border: 1px solid var(--border-color); transition: all 0.2s; width: 100%;
        }}
        .hub-link:hover {{ color: var(--accent); border-color: var(--accent); }}
        .avatar {{ width: 150px; height: 150px; border-radius: 50%; object-fit: cover; margin-bottom: 20px; border: 3px solid var(--border-color); background: #222; }}
        .avatar-placeholder {{ width: 150px; height: 150px; border-radius: 50%; margin-bottom: 20px; border: 3px solid var(--border-color); background: #222; display: flex; align-items: center; justify-content: center; font-size: 3rem; font-weight: bold; color: var(--accent); }}
        .author-name {{ font-size: 1.8rem; font-weight: 700; margin-bottom: 8px; }}
        .author-meta, .author-tools {{ color: var(--text-secondary); font-size: 0.88rem; margin-bottom: 6px; display: flex; align-items: center; gap: 5px; justify-content: center; }}
        .author-tools {{ margin-bottom: 12px; }}
        .bio {{ color: var(--text-secondary); font-size: 0.95rem; margin: 10px 0 20px 0; line-height: 1.4; }}
        .social-links {{ display: flex; flex-direction: column; gap: 8px; width: 100%; }}
        .social-link {{ color: var(--text-secondary); text-decoration: none; font-size: 0.9rem; display: flex; align-items: center; justify-content: center; gap: 8px; padding: 8px 12px; border-radius: 6px; background: var(--bg-card); border: 1px solid var(--border-color); transition: all 0.2s; }}
        .social-link:hover {{ color: var(--text-primary); border-color: #444; }}
        .main-content {{ display: flex; flex-direction: column; }}
        
        .section-header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border-color); padding-bottom: 10px; margin-bottom: 20px; }}
        .section-header h2 {{ font-size: 1.2rem; font-weight: 700; color: var(--text-primary); }}
        .btn-expandir {{ background: transparent; border: 1px solid var(--border-color); color: var(--accent); padding: 6px 12px; border-radius: 6px; cursor: pointer; font-size: 0.85rem; font-weight: 600; transition: background 0.2s; }}
        .btn-expandir:hover {{ background: rgba(255,204,0,0.1); }}

        .series-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 20px; margin-bottom: 35px; }}
        .series-card {{ background: var(--bg-card); border-radius: 8px; overflow: hidden; text-decoration: none; color: inherit; display: flex; flex-direction: column; transition: transform 0.2s, box-shadow 0.2s; border: 1px solid var(--border-color); }}
        .series-card:hover {{ transform: translateY(-4px); box-shadow: 0 8px 20px rgba(0,0,0,0.4); }}
        .card-thumb {{ width: 100%; height: 180px; object-fit: cover; background: #25252b; display: block; }}
        .card-info {{ padding: 12px; display: flex; flex-direction: column; gap: 4px; }}
        .card-title {{ font-size: 0.95rem; font-weight: 700; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
        .card-author {{ font-size: 0.8rem; color: var(--text-secondary); }}
        .card-tag {{ font-size: 0.75rem; color: var(--accent); margin-top: 2px; }}
        .card-stats {{ font-size: 0.75rem; color: var(--text-secondary); margin-top: 4px; display: flex; gap: 8px; }}
        
        .comentario-item {{ background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 6px; padding: 12px; margin-bottom: 10px; font-size: 0.85rem; }}
        .comentario-header {{ display: flex; align-items: center; gap: 8px; }}
        .autor {{ font-weight: 600; color: var(--text-primary); }}
        .badge-criador {{ background: var(--accent); color: #000; font-size: 0.7rem; font-weight: 700; padding: 1px 6px; border-radius: 4px; text-transform: uppercase; }}
        .comentario-texto {{ color: var(--text-secondary); margin: 6px 0; white-space: pre-line; }}
        .comentario-meta {{ font-size: 0.75rem; color: var(--text-secondary); }}
        .replies {{ margin-left: 15px; padding-left: 10px; border-left: 2px solid var(--border-color); margin-top: 8px; list-style: none; }}

        .modal-overlay {{ position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.85); display: none; justify-content: center; align-items: center; z-index: 2000; padding: 20px; }}
        .modal-overlay.ativo {{ display: flex; }}
        .modal-container {{ background: var(--bg-modal); width: 100%; max-width: 800px; max-height: 85vh; border-radius: 12px; border: 1px solid var(--border-color); display: flex; flex-direction: column; overflow: hidden; }}
        .modal-header {{ padding: 15px 20px; border-bottom: 1px solid var(--border-color); display: flex; justify-content: space-between; align-items: center; }}
        .modal-header h3 {{ font-size: 1.1rem; }}
        .btn-fechar {{ background: transparent; border: none; color: var(--text-secondary); font-size: 1.2rem; cursor: pointer; }}
        .modal-filtros {{ padding: 12px 20px; border-bottom: 1px solid var(--border-color); display: flex; gap: 10px; flex-wrap: wrap; background: var(--bg-card); }}
        .modal-filtros input, .modal-filtros select {{ background: var(--bg-main); color: var(--text-primary); border: 1px solid var(--border-color); padding: 6px 10px; border-radius: 6px; font-size: 0.85rem; outline: none; }}
        .modal-filtros input {{ flex: 1; min-width: 150px; }}
        .modal-body {{ padding: 20px; overflow-y: auto; flex: 1; }}
    </style>
    """

    html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{escaped_nome} | Acervo de Séries</title>
    {css_styles}
</head>
<body>
    <div id="versao">
        <span>Acervo de Séries de <b>{escaped_nome}</b> | Gerado em {DATA_GERACAO}</span>
        {modal_info_html}
    </div>

    <div class="container">
        <aside class="sidebar">
            {hub_button_html}
            {avatar_html}
            <h1 class="author-name">{nome_autor}</h1>
            {loc_html}
            {tools_html}
            {bio_html}
            {social_links_html}
        </aside>

        <main class="main-content">
            <div class="section-header">
                <h2>Séries Destaque ({total_series} no total)</h2>
                <button class="btn-expandir" onclick="abrirModalSeries()">Ver todas as séries ↗</button>
            </div>
            <div class="series-grid">
                {cards_destaque_html}
            </div>

            <div class="section-header" style="margin-top: 15px;">
                <h2>Comentários do Perfil ({total_comentarios})</h2>
                <button class="btn-expandir" onclick="abrirModalComentarios()">Ler mais ↗</button>
            </div>
            <ul style="list-style: none;">
                {primeiros_comentarios}
            </ul>
        </main>
    </div>

    <div class="modal-overlay" id="modalSeries" onclick="if(event.target === this) fecharModalSeries()">
        <div class="modal-container">
            <div class="modal-header">
                <h3>Todas as Séries ({total_series})</h3>
                <button class="btn-fechar" onclick="fecharModalSeries()">✕</button>
            </div>
            <div class="modal-filtros">
                <input type="text" id="filtroBuscaSerie" placeholder="Pesquisar série..." oninput="filtrarSeries()">
                <select id="filtroGeneroSerie" onchange="filtrarSeries()">
                    <option value="">Todos os Gêneros</option>
                    {options_generos}
                </select>
                <select id="ordenarSeries" onchange="filtrarSeries()">
                    <option value="recentes">Ordenar por: Mais Recentes</option>
                    <option value="antigas">Ordenar por: Mais Antigas</option>
                    <option value="az">Ordenar por: A-Z</option>
                </select>
            </div>
            <div class="modal-body">
                <div class="series-grid" id="gridModalSeries" style="margin-bottom: 0;">
                    {cards_todos_html}
                </div>
            </div>
        </div>
    </div>

    <div class="modal-overlay" id="modalComentarios" onclick="if(event.target === this) fecharModalComentarios()">
        <div class="modal-container">
            <div class="modal-header">
                <h3>Comentários do Perfil ({total_comentarios})</h3>
                <button class="btn-fechar" onclick="fecharModalComentarios()">✕</button>
            </div>
            <div class="modal-filtros">
                <input type="text" id="filtroBuscaComentario" placeholder="Pesquisar nos comentários..." oninput="filtrarComentarios()">
                <select id="ordenarComentarios" onchange="filtrarComentarios()">
                    <option value="recentes">Ordenar por: Mais Recentes</option>
                    <option value="antigos">Ordenar por: Mais Antigos</option>
                    <option value="curtidos">Ordenar por: Mais Curtidos</option>
                    <option value="criador">Apenas do Criador</option>
                </select>
            </div>
            <div class="modal-body">
                <ul style="list-style: none;" id="listaModalComentarios">
                    {todos_comentarios}
                </ul>
            </div>
        </div>
    </div>

    {js_code}
</body>
</html>
"""

    caminho_index = BASE_DIR / "index.html"
    with open(caminho_index, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"✅ 'index.html' gerado com sucesso!")

if __name__ == "__main__":
    gerar_html_index()