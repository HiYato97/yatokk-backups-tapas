import json
import html
import urllib.request
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(".").resolve()
DATA_GERACAO = datetime.now().strftime("%d/%m/%Y %H:%M")

CSS_ESTILOS = """
:root {
    --bg-body: #000000;
    --bg-card: #090a0a;
    --bg-sidebar: #0d0e10;
    --border-color: #222428;
    --text-primary: #e1e3e6;
    --text-muted: #737984;
    --accent: #ffcb05; /* Tapas Yellow Accent */
    --accent-hover: #ffffff;
    --sidebar-width: 280px;
}

body.light {
    --bg-body: #f4f5f7;
    --bg-card: #ffffff;
    --bg-sidebar: #eaecef;
    --border-color: #d0d4dc;
    --text-primary: #22252a;
    --text-muted: #626875;
    --accent: #d97706;
    --accent-hover: #111827;
}

* { margin: 0; padding: 0; box-sizing: border-box; }
html { scroll-behavior: smooth; font-size: 16px; }

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    background-color: var(--bg-body);
    color: var(--text-primary);
    line-height: 1.6;
    font-size: 1rem;
    overflow-x: hidden;
    padding-bottom: 60px;
}

#versao {
    position: fixed;
    top: 0; left: 0; right: 0;
    background: var(--bg-sidebar);
    color: var(--text-muted);
    padding: 0.4rem 1rem;
    text-align: center;
    z-index: 1000;
    font-size: 0.85rem;
    border-bottom: 1px solid var(--border-color);
}

.btn-voltar-index {
    display: block;
    width: 100%;
    background: var(--bg-card);
    color: var(--text-primary);
    border: 1px solid var(--border-color);
    padding: 8px 12px;
    border-radius: 4px;
    text-decoration: none;
    font-size: 0.85rem;
    font-weight: 600;
    text-align: center;
    margin-bottom: 15px;
}

#toggleSidebarBtn {
    position: fixed;
    top: 36px;
    left: 10px;
    z-index: 1001;
    background: var(--bg-card);
    color: var(--text-primary);
    border: 1px solid var(--border-color);
    padding: 0.4rem 0.8rem;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.85rem;
}

.sidebar {
    position: fixed;
    top: 31px;
    left: 0;
    width: var(--sidebar-width);
    max-width: 85vw;
    height: calc(100vh - 31px);
    background: var(--bg-sidebar);
    padding: 50px 15px 20px 15px;
    border-right: 1px solid var(--border-color);
    z-index: 999;
    overflow-y: auto;
    transition: transform 0.25s ease;
}
.sidebar.oculto { transform: translateX(-100%); }

.painel-controles {
    background: var(--bg-card);
    padding: 12px;
    border-radius: 6px;
    margin-bottom: 20px;
    border: 1px solid var(--border-color);
}
.painel-controles h3 {
    font-size: 0.75rem;
    text-transform: uppercase;
    color: var(--text-muted);
    margin-bottom: 8px;
}
.botoes-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 6px;
}
.painel-controles button {
    background: var(--bg-body);
    color: var(--text-primary);
    border: 1px solid var(--border-color);
    padding: 6px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.8rem;
}

.sidebar h2 {
    font-size: 0.9rem;
    color: var(--text-muted);
    text-transform: uppercase;
    margin-bottom: 10px;
    padding-bottom: 5px;
    border-bottom: 1px solid var(--border-color);
}
.sidebar ul { list-style: none; }
.sidebar a {
    color: var(--text-primary);
    text-decoration: none;
    padding: 6px 8px;
    display: block;
    font-size: 0.85rem;
    border-radius: 4px;
}
.sidebar a:hover { background: var(--bg-card); }

.conteudo {
    margin-left: var(--sidebar-width);
    margin-top: 31px;
    padding: 30px;
    transition: margin-left 0.25s ease;
}
.conteudo.expandido { margin-left: 0; }

.series-header {
    max-width: 850px;
    margin: 0 auto 30px auto;
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 20px;
    display: flex;
    gap: 20px;
    align-items: flex-start;
}
.series-thumb {
    width: 130px;
    height: 130px;
    border-radius: 6px;
    object-fit: cover;
    border: 1px solid var(--border-color);
}
.series-info { flex: 1; }
.series-title { font-size: 1.8rem; margin-bottom: 5px; color: var(--text-primary); }
.series-meta { font-size: 0.85rem; color: var(--text-muted); margin-bottom: 10px; }
.series-genre {
    display: inline-block;
    background: var(--border-color);
    color: var(--text-primary);
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 600;
}
.series-desc { font-size: 0.95rem; margin-top: 10px; color: var(--text-primary); line-height: 1.5; }

.capitulo {
    margin-bottom: 30px;
    scroll-margin-top: 45px;
    background: var(--bg-card);
    padding: 15px;
    border-radius: 6px;
    border: 1px solid var(--border-color);
    max-width: 850px;
    margin-left: auto;
    margin-right: auto;
}
.capitulo h2 {
    font-size: 1.15rem;
    color: var(--text-primary);
    margin-bottom: 12px;
    border-bottom: 1px solid var(--border-color);
    padding-bottom: 8px;
}

img { max-width: 100%; height: auto; display: block; margin: 10px auto; border-radius: 2px; }

.comentarios-wrapper { margin-top: 15px; }
.btn-toggle-comentarios {
    background: var(--bg-body);
    color: var(--text-primary);
    border: 1px solid var(--border-color);
    padding: 10px 14px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.85rem;
    width: 100%;
    text-align: left;
    display: flex;
    justify-content: space-between;
}
.comentarios-conteudo {
    display: none;
    background: var(--bg-body);
    border: 1px solid var(--border-color);
    border-top: none;
    padding: 12px;
}
.comentarios-conteudo.aberto { display: block !important; }
.comentario-item { padding: 8px 0; border-bottom: 1px dashed var(--border-color); font-size: 0.85rem; }
.autor { font-weight: 600; color: var(--text-primary); }
.badge-criador { background: var(--border-color); color: var(--text-primary); font-size: 0.7rem; padding: 1px 5px; border-radius: 3px; }
.comentario-texto { color: var(--text-primary); margin: 2px 0; white-space: pre-line; }
.comentario-meta { font-size: 0.75rem; color: var(--text-muted); }
.replies { margin-left: 12px; padding-left: 10px; border-left: 2px solid var(--border-color); margin-top: 8px; list-style: none; }

.nav-botoes {
    margin-top: 15px;
    padding-top: 10px;
    border-top: 1px solid var(--border-color);
    display: flex;
    justify-content: space-between;
}
.nav-botoes a { color: var(--text-muted); text-decoration: none; font-size: 0.85rem; }

.modal-overlay {
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background: rgba(0, 0, 0, 0.8);
    display: none;
    justify-content: center;
    align-items: flex-end;
    z-index: 2000;
}
.modal-overlay.visivel { display: flex; }
.modal-conteudo {
    background: var(--bg-card);
    width: 100%;
    max-width: 600px;
    max-height: 80vh;
    border-top-left-radius: 12px;
    border-top-right-radius: 12px;
    border: 1px solid var(--border-color);
    display: flex;
    flex-direction: column;
}
.modal-header { padding: 12px 16px; border-bottom: 1px solid var(--border-color); display: flex; justify-content: space-between; }
.modal-body { padding: 16px; overflow-y: auto; }

.mobile-nav-bar {
    position: fixed; bottom: 0; left: 0; right: 0; height: 54px;
    background: var(--bg-sidebar); border-top: 1px solid var(--border-color);
    display: flex; justify-around; align-items: center; z-index: 1002;
}
.mobile-nav-btn { background: transparent; border: none; color: var(--text-primary); font-size: 0.85rem; cursor: pointer; flex: 1; height: 100%; }

#topoBtn {
    position: fixed; bottom: 70px; right: 20px;
    background: var(--bg-card); color: var(--text-primary);
    border: 1px solid var(--border-color); width: 38px; height: 38px;
    border-radius: 4px; cursor: pointer; display: none; align-items: center; justify-content: center;
}
#topoBtn.visivel { display: flex; }

@media (max-width: 768px) {
    .conteudo { margin-left: 0 !important; padding: 15px 10px; }
    .series-header { flex-direction: column; align-items: center; text-align: center; }
}
"""

JS_SCRIPT = """
let tamanhoFontePixels = 16;
let temaEscuro = true;
let capAtualIndex = 1;
let totalCapitulos = 0;

function mudarTema() { 
    temaEscuro = !temaEscuro; 
    document.body.classList.toggle('light', !temaEscuro); 
}

function alterarFonte(delta) { 
    tamanhoFontePixels = Math.min(Math.max(tamanhoFontePixels + (delta * 2), 12), 26); 
    document.documentElement.style.fontSize = tamanhoFontePixels + 'px'; 
}

function toggleSidebar() { 
    const sidebar = document.getElementById('sidebar');
    const conteudo = document.getElementById('conteudo');
    const btn = document.getElementById('toggleSidebarBtn');
    sidebar.classList.toggle('oculto');
    conteudo.classList.toggle('expandido');
    btn.textContent = sidebar.classList.contains('oculto') ? '☰ Painel' : '✕ Fechar';
}

function toggleComentarioIndividual(idConteudo, btnEl) {
    const el = document.getElementById(idConteudo);
    if (!el) return;
    el.classList.toggle('aberto');
}

function toggleTodosComentarios() {
    const conteudos = document.querySelectorAll('.comentarios-conteudo');
    const btnGlobal = document.getElementById('btnGlobalComentarios');
    const deveExibir = btnGlobal.textContent.trim() === 'Exibir Comentários';
    conteudos.forEach(el => {
        if (deveExibir) el.classList.add('aberto');
        else el.classList.remove('aberto');
    });
    btnGlobal.textContent = deveExibir ? 'Ocultar Comentários' : 'Exibir Comentários';
}

function irParaCapitulo(index) {
    const el = document.getElementById(`cap${index}`);
    if (el) el.scrollIntoView({ behavior: 'smooth' });
}

function capAnterior() { if (capAtualIndex > 1) irParaCapitulo(capAtualIndex - 1); }
function capProximo() { if (capAtualIndex < totalCapitulos) irParaCapitulo(capAtualIndex + 1); }

function abrirModalComentarios() {
    const capEl = document.getElementById(`cap${capAtualIndex}`);
    if (!capEl) return;
    const wrapperComentarios = capEl.querySelector('.comentarios-wrapper');
    const modalBody = document.getElementById('modalComentariosBody');
    document.getElementById('modalTitle').textContent = `Comentários - Cap. ${capAtualIndex}`;
    if (wrapperComentarios) {
        modalBody.innerHTML = wrapperComentarios.innerHTML;
        const lista = modalBody.querySelector('.comentarios-conteudo');
        if (lista) lista.style.display = 'block';
        const btn = modalBody.querySelector('.btn-toggle-comentarios');
        if (btn) btn.style.display = 'none';
    } else {
        modalBody.innerHTML = '<p style="color:var(--text-muted); text-align:center;">Sem comentários neste capítulo.</p>';
    }
    document.getElementById('modalComentarios').classList.add('visivel');
}

function fecharModalComentarios() {
    document.getElementById('modalComentarios').classList.remove('visivel');
}

function atualizarCapituloAtualVisivel() {
    const capitulos = document.querySelectorAll('.capitulo');
    totalCapitulos = capitulos.length;
    let indexEncontrado = 1;
    capitulos.forEach((cap, idx) => {
        const rect = cap.getBoundingClientRect();
        if (rect.top <= window.innerHeight / 2 && rect.bottom >= 0) {
            indexEncontrado = idx + 1;
        }
    });
    capAtualIndex = indexEncontrado;
    const btnPrev = document.getElementById('mobileBtnPrev');
    const btnNext = document.getElementById('mobileBtnNext');
    if (btnPrev) btnPrev.disabled = capAtualIndex <= 1;
    if (btnNext) btnNext.disabled = capAtualIndex >= totalCapitulos;
}

function irParaTopo() { window.scrollTo({top: 0, behavior: 'smooth'}); }

window.addEventListener('scroll', () => {
    document.getElementById('topoBtn').classList.toggle('visivel', window.scrollY > 300);
    atualizarCapituloAtualVisivel();
});
document.addEventListener('DOMContentLoaded', () => { atualizarCapituloAtualVisivel(); });
"""

def baixar_capa_local(url, pasta_serie):
    if not url:
        return ""

    extensao = ".jpg"
    if ".png" in url.lower():
        extensao = ".png"
    elif ".webp" in url.lower():
        extensao = ".webp"

    nome_ficheiro = f"cover{extensao}"
    caminho_local = pasta_serie / nome_ficheiro

    if caminho_local.exists():
        return nome_ficheiro

    try:
        print(f"   📥 Baixando capa da série...")
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req) as response, open(caminho_local, 'wb') as f:
            f.write(response.read())
        print(f"   ✅ Capa salva como: {nome_ficheiro}")
        return nome_ficheiro
    except Exception as e:
        print(f"   ⚠️ Não foi possível baixar a capa: {e}")
        return ""

def formatar_item_comentario(c):
    if not isinstance(c, dict):
        return "", 0
    user = c.get("display_name") or c.get("username") or "Anônimo"
    raw_text = c.get("text", "")
    text = html.unescape(raw_text).replace("<br>", "\n").replace("<br/>", "\n")
    date = c.get("date", "")
    likes = c.get("likes", 0)
    is_creator = c.get("is_creator", False)

    badge = '<span class="badge-criador">Criador</span>' if is_creator else ''
    meta_likes = f"❤️ {likes}" if likes > 0 else ""
    meta_info = [m for m in [date, meta_likes] if m]
    meta_html = f'<div class="comentario-meta">{" • ".join(meta_info)}</div>' if meta_info else ''

    total = 1
    replies_html = ""
    if "replies" in c and isinstance(c["replies"], list) and c["replies"]:
        sub_items = []
        for r in c["replies"]:
            sub_h, sub_count = formatar_item_comentario(r)
            sub_items.append(sub_h)
            total += sub_count
        replies_html = f'<ul class="replies">{"".join(sub_items)}</ul>'

    item_html = f'''
    <li class="comentario-item">
        <div class="comentario-header">
            <span class="autor">{user}</span> {badge}
        </div>
        <div class="comentario-texto">{text}</div>
        {meta_html}
        {replies_html}
    </li>'''
    return item_html, total

def processar_comentarios(caminho_json, id_cap):
    if not caminho_json.exists():
        return ""
    try:
        with open(caminho_json, 'r', encoding='utf-8') as f:
            comments = json.load(f)
    except Exception:
        return ""

    if not isinstance(comments, list) or not comments:
        return ""

    html_items = []
    total_comentarios = 0
    for c in comments:
        c_html, count = formatar_item_comentario(c)
        if c_html:
            html_items.append(c_html)
            total_comentarios += count

    id_conteudo = f"coms-{id_cap}"
    return f'''
    <div class="comentarios-wrapper">
        <button class="btn-toggle-comentarios" onclick="toggleComentarioIndividual('{id_conteudo}', this)">
            <span>💬 Ver Comentários ({total_comentarios})</span>
            <span>▼</span>
        </button>
        <div class="comentarios-conteudo" id="{id_conteudo}">
            <ul class="comentarios-lista">{"".join(html_items)}</ul>
        </div>
    </div>'''

def extrair_valor(dicionario, chaves, padrao=""):
    """Navega por dicionários buscando a primeira chave válida encontrada."""
    for chave in chaves:
        if isinstance(dicionario, dict) and chave in dicionario and dicionario[chave]:
            return dicionario[chave]
    return padrao

def carregar_dados_serie(pasta_serie):
    series_json_path = pasta_serie / "series.json"
    manifest_json_path = pasta_serie / "manifest.json"

    metadata = {
        "title": pasta_serie.name,
        "thumb_url": "",
        "local_thumb": "",
        "genre": "",
        "likes": 0,
        "description": "",
        "episodes": {}
    }

    if series_json_path.exists():
        try:
            with open(series_json_path, 'r', encoding='utf-8') as f:
                data_raw = json.load(f)
                
                # O JSON pode ter um wrapper "data" ou estar na raiz
                s_data = data_raw.get("data", data_raw) if isinstance(data_raw, dict) else {}

                # Busca Título
                metadata["title"] = extrair_valor(s_data, ["title", "name"], pasta_serie.name)
                
                # Busca Thumb / Capa
                metadata["thumb_url"] = extrair_valor(s_data, ["thumb_url", "cover_url", "square_thumb_url", "thumb"])

                # Busca Gênero
                genre_raw = s_data.get("genre")
                if isinstance(genre_raw, dict):
                    metadata["genre"] = genre_raw.get("name", "")
                elif isinstance(genre_raw, str):
                    metadata["genre"] = genre_raw

                # Busca Curtidas
                metadata["likes"] = extrair_valor(s_data, ["thumbsup_cnt", "like_cnt", "likes"], 0)

                # Busca Descrição / Sinopse
                metadata["description"] = extrair_valor(s_data, ["description", "summary", "synopsis"])

        except Exception as e:
            print(f"   ⚠️ Erro ao ler series.json: {e}")

    # Baixar ou carregar imagem da capa se houver URL
    if metadata["thumb_url"]:
        metadata["local_thumb"] = baixar_capa_local(metadata["thumb_url"], pasta_serie)

    if manifest_json_path.exists():
        try:
            with open(manifest_json_path, 'r', encoding='utf-8') as f:
                manifest_raw = json.load(f)
                m_data = manifest_raw.get("episodes", manifest_raw) if isinstance(manifest_raw, dict) else {}
                metadata["episodes"] = m_data
        except Exception as e:
            print(f"   ⚠️ Erro ao ler manifest.json: {e}")

    return metadata

def processar_serie(pasta_serie):
    pasta_serie_abs = pasta_serie.resolve()
    caminho_episodes = pasta_serie_abs / "episodes"
    
    if not caminho_episodes.is_dir():
        return False

    episodios = sorted([p for p in caminho_episodes.iterdir()])
    if not episodios:
        return False

    meta = carregar_dados_serie(pasta_serie_abs)
    print(f"\n📂 Processando série: {meta['title']} ({len(episodios)} episódios)")

    existe_index_raiz = (BASE_DIR / "index.html").exists()
    botao_voltar_html = '<a href="../index.html" class="btn-voltar-index">← Voltar ao Início</a>' if existe_index_raiz else ''

    # Header da Série
    thumb_html = f'<img src="{meta["local_thumb"]}" class="series-thumb" alt="Capa">' if meta["local_thumb"] else ''
    genre_html = f'<span class="series-genre">{html.escape(str(meta["genre"]))}</span>' if meta["genre"] else ''
    likes_html = f'❤️ {meta["likes"]} curtidas' if meta["likes"] else ''
    
    # Tratamento da descrição: permite quebra de linha ou HTML original
    desc_str = str(meta["description"])
    desc_formatted = desc_str if ("<p>" in desc_str or "<br>" in desc_str) else html.escape(desc_str).replace("\n", "<br>")

    header_html = f'''
    <div class="series-header">
        {thumb_html}
        <div class="series-info">
            <h1 class="series-title">{html.escape(meta["title"])}</h1>
            <div class="series-meta">{genre_html} {likes_html}</div>
            <div class="series-desc">{desc_formatted}</div>
        </div>
    </div>'''

    indice_items = []
    capitulos_html = []

    for idx, ep_path in enumerate(episodios, start=1):
        id_cap = f"cap{idx}"
        folder_name = ep_path.name
        
        ep_meta = meta["episodes"].get(folder_name, {})
        if isinstance(ep_meta, dict):
            ep_title = ep_meta.get("title", folder_name)
        else:
            ep_title = folder_name

        indice_items.append(f'<li><a href="#{id_cap}">Cap. {idx} - {html.escape(ep_title)}</a></li>')

        imgs_html = []
        comentarios_html = ""

        if ep_path.is_dir():
            images_path = ep_path / "images"
            if images_path.is_dir():
                exts = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
                for img in sorted(images_path.iterdir()):
                    if img.suffix.lower() in exts:
                        rel_path = img.relative_to(pasta_serie_abs).as_posix()
                        imgs_html.append(f'<img src="{rel_path}" alt="{img.name}">')

            comments_file = ep_path / "comments.json"
            comentarios_html = processar_comentarios(comments_file, id_cap)

        nav_prev = f'<a href="#cap{idx-1}">◀ Anterior</a>' if idx > 1 else ''
        nav_next = f'<a href="#cap{idx+1}">Próximo ▶</a>' if idx < len(episodios) else ''

        capitulos_html.append(f'''
        <div class="capitulo" id="{id_cap}">
            <h2>Capítulo {idx} - {html.escape(ep_title)}</h2>
            {"".join(imgs_html)}
            {comentarios_html}
            <div class="nav-botoes">
                <a href="#topo">⬆ Topo</a>
                {nav_prev}
                {nav_next}
            </div>
        </div>''')

    html_final = f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(meta["title"])}</title>
    <style>{CSS_ESTILOS}</style>
</head>
<body id="topo">
    <div id="versao">
        Série: <b>{html.escape(meta["title"])}</b> | Gerado em {DATA_GERACAO}
    </div>

    <button id="toggleSidebarBtn" onclick="toggleSidebar()">✕ Fechar</button>

    <div class="sidebar" id="sidebar">
        {botao_voltar_html}
        <div class="painel-controles">
            <h3>Opções</h3>
            <div class="botoes-grid">
                <button onclick="mudarTema()">Tema</button>
                <button onclick="alterarFonte(1)">A+</button>
                <button onclick="alterarFonte(-1)">A-</button>
                <button id="btnGlobalComentarios" onclick="toggleTodosComentarios()">Exibir Comentários</button>
            </div>
        </div>

        <h2>Índice</h2>
        <ul>{"".join(indice_items)}</ul>
    </div>

    <div class="conteudo" id="conteudo">
        {header_html}
        {"".join(capitulos_html)}
    </div>

    <div class="modal-overlay" id="modalComentarios" onclick="if(event.target === this) fecharModalComentarios()">
        <div class="modal-conteudo">
            <div class="modal-header">
                <h3 id="modalTitle">Comentários</h3>
                <button class="btn-fechar-modal" onclick="fecharModalComentarios()">✕</button>
            </div>
            <div class="modal-body" id="modalComentariosBody"></div>
        </div>
    </div>

    <div class="mobile-nav-bar">
        <button class="mobile-nav-btn" id="mobileBtnPrev" onclick="capAnterior()">◀ Anterior</button>
        <button class="mobile-nav-btn" id="mobileBtnComms" onclick="abrirModalComentarios()">💬 Comentários</button>
        <button class="mobile-nav-btn" id="mobileBtnNext" onclick="capProximo()">Próximo ▶</button>
    </div>

    <button onclick="irParaTopo()" id="topoBtn">↑</button>
    <script>{JS_SCRIPT}</script>
</body>
</html>'''

    output_file = pasta_serie_abs / f"{pasta_serie_abs.name}_completo.html"
    output_file.write_text(html_final, encoding="utf-8")
    print(f"   ✅ HTML gerado em: {output_file}")
    return True

def main():
    print(f"🔍 Procurando séries em: {BASE_DIR}")
    processadas = 0
    for item in BASE_DIR.iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            if processar_serie(item):
                processadas += 1

    print(f"\n{'='*40}")
    print(f"✨ Concluído! {processadas} série(s) processada(s)." if processadas else "⚠️ Nenhuma série processada.")

if __name__ == "__main__":
    main()