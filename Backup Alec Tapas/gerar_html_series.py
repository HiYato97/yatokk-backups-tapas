from utils_projeto import CSS_MODAL_INFO, gerar_componente_modal_info
import html
import json
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
    --accent: #ffcb05;
    --accent-hover: #ffffff;
    --sidebar-width: 280px;
    --danger: #dc2626;
    --danger-hover: #991b1b;
    --success: #16a34a;
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
    --danger: #ef4444;
    --danger-hover: #b91c1c;
    --success: #22c55e;
}

* { margin: 0; padding: 0; box-sizing: border-box; }
html { scroll-behavior: smooth; font-size: 16px; }

/* SCROLLBARS ESCURAS */
*::-webkit-scrollbar { width: 8px; height: 8px; }
*::-webkit-scrollbar-track { background: var(--bg-body); }
*::-webkit-scrollbar-thumb { background: var(--border-color); border-radius: 4px; }
*::-webkit-scrollbar-thumb:hover { background: #444450; }

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    background-color: var(--bg-body);
    color: var(--text-primary);
    line-height: 1.6;
    font-size: 1rem;
    overflow-x: hidden;
    padding-bottom: 70px;
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
    height: calc(100vh - 31px - 54px);
    background: var(--bg-sidebar);
    padding: 50px 15px 30px 15px;
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
.painel-controles button, .select-capitulos {
    background: var(--bg-body);
    color: var(--text-primary);
    border: 1px solid var(--border-color);
    padding: 6px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.8rem;
    width: 100%;
}
.select-capitulos {
    margin-bottom: 8px;
    outline: none;
}

.btn-full-width { grid-column: span 2; }

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
    transition: background 0.2s ease;
}
.sidebar a:hover { background: var(--bg-card); }

.conteudo {
    margin-left: var(--sidebar-width);
    margin-top: 31px;
    padding: 30px;
    transition: margin-left 0.25s ease;
}
.conteudo.expandido { margin-left: 0; }

.series-banner {
    max-width: 850px;
    margin: 0 auto 15px auto;
    border-radius: 8px;
    overflow: hidden;
    border: 1px solid var(--border-color);
    background: var(--bg-card);
}
.series-banner img {
    width: 100%;
    height: auto;
    display: block;
    margin: 0;
}

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
    max-width: 160px;
    height: auto;
    border-radius: 6px;
    border: 1px solid var(--border-color);
}
.series-info { flex: 1; }
.series-title { font-size: 1.8rem; margin-bottom: 5px; color: var(--text-primary); }
.series-meta { font-size: 0.85rem; color: var(--text-muted); margin-bottom: 10px; display: flex; flex-wrap: wrap; gap: 10px; align-items: center; }
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
.capitulo-header {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    border-bottom: 1px solid var(--border-color);
    padding-bottom: 8px;
    margin-bottom: 12px;
}
.capitulo h2 {
    font-size: 1.15rem;
    color: var(--text-primary);
}
.capitulo-data {
    font-size: 0.75rem;
    color: var(--text-muted);
}

img { max-width: 100%; height: auto; display: block; margin: 10px auto; border-radius: 2px; }

/* CREATOR NOTE ESTILOS */
.creator-note-box {
    display: flex;
    gap: 15px;
    margin: 20px 0;
    align-items: flex-start;
}
.creator-avatar {
    width: 45px;
    height: 45px;
    border-radius: 50%;
    object-fit: cover;
    background: #222;
    flex-shrink: 0;
}
.creator-avatar-placeholder {
    width: 45px;
    height: 45px;
    border-radius: 50%;
    background: #222;
    color: var(--accent);
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
    font-size: 1.2rem;
    flex-shrink: 0;
}
.creator-content {
    flex: 1;
}
.creator-info-line {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 6px;
}
.creator-name {
    font-weight: 600;
    font-size: 0.95rem;
    color: var(--text-primary);
}
.creator-tag {
    background: #d97706;
    color: #fff;
    font-size: 0.7rem;
    padding: 1px 6px;
    border-radius: 4px;
    font-weight: 600;
    text-transform: uppercase;
}
.creator-text {
    font-size: 0.9rem;
    color: var(--text-muted);
    line-height: 1.5;
}

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

.comentarios-filtros {
    display: flex;
    gap: 8px;
    margin-bottom: 12px;
}
.comentarios-filtros select {
    background: var(--bg-card);
    color: var(--text-primary);
    border: 1px solid var(--border-color);
    padding: 5px 8px;
    border-radius: 4px;
    font-size: 0.8rem;
    outline: none;
    flex: 1;
}

.comentario-item { padding: 8px 0; border-bottom: 1px dashed var(--border-color); font-size: 0.85rem; }
.autor { font-weight: 600; color: var(--text-primary); }
.badge-criador { background: var(--accent); color: #000; font-size: 0.7rem; font-weight: 700; padding: 1px 5px; border-radius: 3px; text-transform: uppercase; }
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

/* MODAL COMENTÁRIOS MOBILE */
.modal-overlay {
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background: rgba(0, 0, 0, 0.85);
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
.btn-fechar-modal { background: transparent; border: none; color: var(--text-primary); font-size: 1.1rem; cursor: pointer; }

/* BARRA NAVEGAÇÃO MOBILE */
.mobile-nav-bar {
    display: flex;
    position: fixed; 
    bottom: 0; 
    left: 0; 
    right: 0; 
    height: 54px;
    background: var(--bg-sidebar); 
    border-top: 1px solid var(--border-color);
    justify-content: space-around; 
    align-items: center; 
    z-index: 1002;
    padding: 0 10px;
}
.mobile-nav-btn {
    background: transparent; border: none; color: var(--text-primary);
    font-size: 0.8rem; cursor: pointer; flex: 1; height: 100%;
}

#topoBtn {
    position: fixed; 
    bottom: 70px;
    right: 20px;
    background: var(--bg-card); 
    color: var(--text-primary);
    border: 1px solid var(--border-color); 
    width: 38px; 
    height: 38px;
    border-radius: 4px; 
    cursor: pointer; 
    display: none; 
    align-items: center; 
    justify-content: center;
    z-index: 1001;
}
#topoBtn.visivel { display: flex; }

/* --- MODO LEITURA IMERSIVO --- */
body.modo-imersivo #versao,
body.modo-imersivo #toggleSidebarBtn,
body.modo-imersivo .sidebar,
body.modo-imersivo .series-banner,
body.modo-imersivo .series-header,
body.modo-imersivo .capitulo-header,
body.modo-imersivo .creator-note-box,
body.modo-imersivo .comentarios-wrapper,
body.modo-imersivo .nav-botoes,
body.modo-imersivo #topoBtn,
body.modo-imersivo .mobile-nav-bar {
    display: none !important;
}

body.modo-imersivo {
    background: #000000 !important;
    padding-bottom: 0 !important;
}

body.modo-imersivo .conteudo {
    margin-left: 0 !important;
    margin-top: 0 !important;
    padding: 0 !important;
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
}

body.modo-imersivo .capitulo {
    display: none;
    max-width: 100% !important;
    width: 100%;
    min-height: 100vh;
    padding: 0 !important;
    margin: 0 !important;
    border: none !important;
    background: #000000 !important;
}

body.modo-imersivo .capitulo.cap-ativo-imersivo {
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
}

body.modo-imersivo img {
    display: none !important;
    max-width: 100%;
    height: auto;
    margin: 0 auto !important;
    border-radius: 0 !important;
}

body.modo-imersivo img.pag-ativa-imersivo {
    display: block !important;
}

/* CONTROLES E HUD IMERSIVO COMPACTOS */
.imersivo-controles {
    display: none;
    position: fixed;
    top: 15px;
    right: 15px;
    z-index: 9999;
    background: rgba(0,0,0,0.75);
    padding: 6px 12px;
    border-radius: 20px;
    border: 1px solid rgba(255,255,255,0.2);
    backdrop-filter: blur(5px);
}
body.modo-imersivo .imersivo-controles { display: flex; gap: 10px; align-items: center; }

.btn-sair-imersivo {
    background: var(--danger);
    color: #fff;
    border: none;
    padding: 6px 14px;
    border-radius: 12px;
    font-size: 0.85rem;
    cursor: pointer;
}

.imersivo-hud-bottom {
    display: none;
    position: fixed;
    bottom: 6px;
    left: 50%;
    transform: translateX(-50%);
    z-index: 9999;
    background: rgba(0,0,0,0.85);
    color: #ffffff;
    padding: 4px 10px;
    border-radius: 12px;
    font-size: 0.75rem;
    border: 1px solid rgba(255,255,255,0.2);
    backdrop-filter: blur(5px);
    align-items: center;
    gap: 8px;
    white-space: nowrap;
}
body.modo-imersivo .imersivo-hud-bottom { display: flex; }

.imersivo-nav-btn {
    background: rgba(255, 255, 255, 0.15);
    border: 1px solid rgba(255, 255, 255, 0.3);
    color: #ffffff;
    padding: 3px 8px;
    border-radius: 8px;
    font-size: 0.75rem;
    font-weight: 600;
    cursor: pointer;
}
.imersivo-nav-btn:active {
    background: var(--accent);
    color: #000;
}

@media (max-width: 768px) {
    .conteudo { margin-left: 0 !important; padding: 15px 10px; }
    .series-header { flex-direction: column; align-items: center; text-align: center; }
}
""" + CSS_MODAL_INFO

JS_SCRIPT = """
let tamanhoFontePixels = 16;
let temaEscuro = true;
let capAtualIndex = 1;
let pagAtualIndex = 1;
let totalCapitulos = 0;
let modoImersivoAtivo = false;

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

function ordenarComentariosNaSecao(selectEl, listaId, sincronizarComId = null) {
    const ordem = selectEl.value;
    
    if (sincronizarComId) {
        const outroSelect = document.getElementById(sincronizarComId);
        if (outroSelect && outroSelect.value !== ordem) {
            outroSelect.value = ordem;
        }
    }

    const lista = document.getElementById(listaId);
    if (!lista) return;
    
    let itens = Array.from(lista.children).filter(el => el.matches('li.comentario-item'));

    itens.forEach(item => {
        const isCriador = item.getAttribute('data-creator') === 'true';
        if (ordem === 'criador') {
            item.style.display = isCriador ? 'block' : 'none';
        } else {
            item.style.display = 'block';
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
            return idxA - idxB;
        });
    } else {
        itens.sort((a, b) => {
            let idxA = parseInt(a.getAttribute('data-index')) || 0;
            let idxB = parseInt(b.getAttribute('data-index')) || 0;
            return idxB - idxA;
        });
    }

    itens.forEach(item => lista.appendChild(item));
}

function irParaCapitulo(index) {
    if (!index || index < 1) return;
    capAtualIndex = parseInt(index);
    pagAtualIndex = 1;

    if (modoImersivoAtivo) {
        atualizarModoImersivoPagina();
    } else {
        const el = document.getElementById(`cap${capAtualIndex}`);
        if (el) el.scrollIntoView({ behavior: 'smooth' });
    }
    sincronizarSelectsCapitulos();
}

function capAnterior() { if (capAtualIndex > 1) irParaCapitulo(capAtualIndex - 1); }
function capProximo() { if (capAtualIndex < totalCapitulos) irParaCapitulo(capAtualIndex + 1); }

function sincronizarSelectsCapitulos() {
    const selSidebar = document.getElementById('selectCapitulosSidebar');
    const selMobile = document.getElementById('selectCapitulosMobile');
    if (selSidebar) selSidebar.value = capAtualIndex;
    if (selMobile) selMobile.value = capAtualIndex;
}

function abrirModalComentarios() {
    const capEl = document.getElementById(`cap${capAtualIndex}`);
    if (!capEl) return;
    const listaOriginal = capEl.querySelector('.comentarios-lista');
    const modalBody = document.getElementById('modalComentariosBody');
    document.getElementById('modalTitle').textContent = `Comentários - Cap. ${capAtualIndex}`;
    
    if (listaOriginal) {
        const selectOriginalId = `ordem-cap${capAtualIndex}`;
        const selectOriginal = document.getElementById(selectOriginalId);
        const ordemAtual = selectOriginal ? selectOriginal.value : 'recentes';

        modalBody.innerHTML = `
            <div class="comentarios-conteudo aberto" style="border:none; padding:0;">
                <div class="comentarios-filtros">
                    <select id="modal-select-ordem" onchange="ordenarComentariosNaSecao(this, 'modal-lista-comentarios', '${selectOriginalId}')">
                        <option value="recentes">Mais Recentes</option>
                        <option value="antigos">Mais Antigos</option>
                        <option value="curtidos">Mais Curtidos</option>
                        <option value="criador">Apenas do Criador</option>
                    </select>
                </div>
                <ul class="comentarios-lista" id="modal-lista-comentarios" style="list-style:none;">
                    ${listaOriginal.innerHTML}
                </ul>
            </div>
        `;

        const selectModal = document.getElementById('modal-select-ordem');
        if (selectModal) {
            selectModal.value = ordemAtual;
            ordenarComentariosNaSecao(selectModal, 'modal-lista-comentarios');
        }
    } else {
        modalBody.innerHTML = '<p style="color:var(--text-muted); text-align:center;">Sem comentários neste capítulo.</p>';
    }
    document.getElementById('modalComentarios').classList.add('visivel');
}

function fecharModalComentarios() {
    document.getElementById('modalComentarios').classList.remove('visivel');
}

function atualizarCapituloAtualVisivel() {
    if (modoImersivoAtivo) return;
    const capitulos = document.querySelectorAll('.capitulo');
    totalCapitulos = capitulos.length;
    let indexEncontrado = 1;
    capitulos.forEach((cap, idx) => {
        const rect = cap.getBoundingClientRect();
        if (rect.top <= window.innerHeight / 2 && rect.bottom >= 0) {
            indexEncontrado = idx + 1;
        }
    });
    if (capAtualIndex !== indexEncontrado) {
        capAtualIndex = indexEncontrado;
        sincronizarSelectsCapitulos();
    }
    const btnPrev = document.getElementById('mobileBtnPrev');
    const btnNext = document.getElementById('mobileBtnNext');
    if (btnPrev) btnPrev.disabled = capAtualIndex <= 1;
    if (btnNext) btnNext.disabled = capAtualIndex >= totalCapitulos;
}

function irParaTopo() { window.scrollTo({top: 0, behavior: 'smooth'}); }

// --- MODO LEITURA IMERSIVO (PÁGINA POR PÁGINA) ---
function toggleModoImersivo() {
    modoImersivoAtivo = document.body.classList.toggle('modo-imersivo');
    const btnFS = document.getElementById('btnFullscreen');
    const btnFSNav = document.getElementById('mobileBtnFullscreen');
    
    if (modoImersivoAtivo) {
        if (btnFS) btnFS.textContent = '❌ Sair Leitura';
        if (btnFSNav) btnFSNav.textContent = '❌ Sair';
        pagAtualIndex = 1;
        atualizarModoImersivoPagina();
    } else {
        if (btnFS) btnFS.textContent = '📖 Modo Imersivo';
        if (btnFSNav) btnFSNav.textContent = '📖 Imersivo';
        document.querySelectorAll('.capitulo').forEach(c => c.classList.remove('cap-ativo-imersivo'));
        document.querySelectorAll('img').forEach(i => i.classList.remove('pag-ativa-imersivo'));
        
        const capEl = document.getElementById(`cap${capAtualIndex}`);
        if (capEl) capEl.scrollIntoView();
    }
}

function obterImagensDoCapituloAtual() {
    const capEl = document.getElementById(`cap${capAtualIndex}`);
    if (!capEl) return [];
    return Array.from(capEl.querySelectorAll('img'));
}

function atualizarModoImersivoPagina() {
    if (!modoImersivoAtivo) return;

    const capitulos = document.querySelectorAll('.capitulo');
    totalCapitulos = capitulos.length;

    capitulos.forEach((cap, idx) => {
        if (idx + 1 === capAtualIndex) {
            cap.classList.add('cap-ativo-imersivo');
        } else {
            cap.classList.remove('cap-ativo-imersivo');
        }
    });

    const imgs = obterImagensDoCapituloAtual();
    if (imgs.length === 0) return;

    if (pagAtualIndex > imgs.length) pagAtualIndex = imgs.length;
    if (pagAtualIndex < 1) pagAtualIndex = 1;

    imgs.forEach((img, idx) => {
        if (idx + 1 === pagAtualIndex) {
            img.classList.add('pag-ativa-imersivo');
        } else {
            img.classList.remove('pag-ativa-imersivo');
        }
    });

    const info = document.getElementById('imersivoInfoText');
    if (info) {
        info.textContent = `Cap. ${capAtualIndex}/${totalCapitulos} • Pág. ${pagAtualIndex}/${imgs.length}`;
    }
}

function imersivoProximaPagina() {
    if (!modoImersivoAtivo) return;
    const imgs = obterImagensDoCapituloAtual();
    if (pagAtualIndex < imgs.length) {
        pagAtualIndex++;
        atualizarModoImersivoPagina();
    } else if (capAtualIndex < totalCapitulos) {
        capAtualIndex++;
        pagAtualIndex = 1;
        sincronizarSelectsCapitulos();
        atualizarModoImersivoPagina();
    }
}

function imersivoPaginaAnterior() {
    if (!modoImersivoAtivo) return;
    if (pagAtualIndex > 1) {
        pagAtualIndex--;
        atualizarModoImersivoPagina();
    } else if (capAtualIndex > 1) {
        capAtualIndex--;
        sincronizarSelectsCapitulos();
        const imgsPrev = obterImagensDoCapituloAtual();
        pagAtualIndex = imgsPrev.length > 0 ? imgsPrev.length : 1;
        atualizarModoImersivoPagina();
    }
}

// --- ATALHOS DE TECLADO ---
document.addEventListener('keydown', (e) => {
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.tagName === 'SELECT') return;
    
    if (e.key === 'ArrowRight' || e.key === 'd' || e.key === 'D') {
        modoImersivoAtivo ? imersivoProximaPagina() : capProximo();
    }
    if (e.key === 'ArrowLeft' || e.key === 'a' || e.key === 'A') {
        modoImersivoAtivo ? imersivoPaginaAnterior() : capAnterior();
    }
    if (e.key === 'f' || e.key === 'F') toggleModoImersivo();
});

window.addEventListener('scroll', () => {
    document.getElementById('topoBtn').classList.toggle('visivel', window.scrollY > 300);
    atualizarCapituloAtualVisivel();
});

document.addEventListener('DOMContentLoaded', () => { 
    atualizarCapituloAtualVisivel();
});
"""

def encontrar_imagem_local(pasta_serie, nomes_possiveis):
    for nome in nomes_possiveis:
        for ext in [".jpg", ".jpeg", ".png", ".webp"]:
            caminho = pasta_serie / f"{nome}{ext}"
            if caminho.exists():
                return caminho.name
    return ""

def encontrar_avatar_autor():
    for ext in [".png", ".jpg", ".jpeg", ".webp"]:
        avatar_path = BASE_DIR / f"avatar{ext}"
        if avatar_path.exists():
            return avatar_path.relative_to(BASE_DIR).as_posix()
    return ""

def carregar_dados_autor():
    author_file = BASE_DIR / "author.json"
    if author_file.exists():
        try:
            with open(author_file, 'r', encoding='utf-8') as f:
                dados = json.load(f)
                d = dados.get("data", dados)
                return d.get("display_name") or d.get("username") or "Autor"
        except Exception:
            pass
    return "Autor"

def formatar_item_comentario(c, index_global=0):
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
            sub_h, sub_count = formatar_item_comentario(r, index_global)
            sub_items.append(sub_h)
            total += sub_count
        replies_html = f'<ul class="replies">{"".join(sub_items)}</ul>'

    item_html = f'''
    <li class="comentario-item" data-likes="{likes}" data-creator="{str(is_creator).lower()}" data-index="{index_global}">
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
    for idx, c in enumerate(comments):
        c_html, count = formatar_item_comentario(c, idx)
        if c_html:
            html_items.append(c_html)
            total_comentarios += count

    id_conteudo = f"coms-{id_cap}"
    lista_id = f"lista-{id_cap}"
    select_id = f"ordem-{id_cap}"
    
    return f'''
    <div class="comentarios-wrapper">
        <button class="btn-toggle-comentarios" onclick="toggleComentarioIndividual('{id_conteudo}', this)">
            <span>💬 Ver Comentários ({total_comentarios})</span>
            <span>▼</span>
        </button>
        <div class="comentarios-conteudo" id="{id_conteudo}">
            <div class="comentarios-filtros">
                <select id="{select_id}" onchange="ordenarComentariosNaSecao(this, '{lista_id}')">
                    <option value="recentes">Mais Recentes</option>
                    <option value="antigos">Mais Antigos</option>
                    <option value="curtidos">Mais Curtidos</option>
                    <option value="criador">Apenas do Criador</option>
                </select>
            </div>
            <ul class="comentarios-lista" id="{lista_id}" style="list-style:none;">{"".join(html_items)}</ul>
        </div>
    </div>'''

def extrair_valor(dicionario, chaves, padrao=""):
    for chave in chaves:
        if isinstance(dicionario, dict) and chave in dicionario and dicionario[chave]:
            return dicionario[chave]
    return padrao

def formatar_data_amigavel(data_str):
    if not data_str:
        return ""
    try:
        dt = datetime.fromisoformat(data_str.replace("Z", "+00:00"))
        return dt.strftime("%d/%m/%Y")
    except Exception:
        return data_str

def carregar_dados_serie(pasta_serie):
    series_json_path = pasta_serie / "series.json"

    metadata = {
        "title": pasta_serie.name,
        "local_thumb": encontrar_imagem_local(pasta_serie, ["series-thumb", "cover", "img_"]),
        "local_header": encontrar_imagem_local(pasta_serie, ["series-header", "header", "banner"]),
        "genre": "",
        "likes": "",
        "views": "",
        "subscribers": "",
        "publish_date": "",
        "description": ""
    }

    if series_json_path.exists():
        try:
            with open(series_json_path, 'r', encoding='utf-8') as f:
                data_raw = json.load(f)
                metadata["likes"] = data_raw.get("likes", "")
                metadata["views"] = data_raw.get("views", "")
                metadata["subscribers"] = data_raw.get("subscribers", "")
                metadata["publish_date"] = formatar_data_amigavel(data_raw.get("publish_date", ""))
                metadata["description"] = data_raw.get("description", "")

                s_data = data_raw.get("data", {})
                metadata["title"] = extrair_valor(s_data, ["title", "name"], pasta_serie.name)
                
                genre_raw = s_data.get("genre")
                if isinstance(genre_raw, dict):
                    metadata["genre"] = genre_raw.get("name", "")
                elif isinstance(genre_raw, str):
                    metadata["genre"] = genre_raw

        except Exception as e:
            print(f"   ⚠ Erro ao ler series.json: {e}")

    return metadata

def carregar_dados_episodio(ep_path):
    index_json = ep_path / "index.json"
    ep_data = {
        "title": ep_path.name,
        "publish_date": "",
        "creator_note": ""
    }
    if index_json.exists():
        try:
            with open(index_json, 'r', encoding='utf-8') as f:
                data = json.load(f)
                d_inner = data.get("data", data)
                ep_data["title"] = d_inner.get("title", ep_path.name)
                pub = d_inner.get("publish_date") or data.get("relative_publish_date", "")
                ep_data["publish_date"] = formatar_data_amigavel(pub)
                ep_data["creator_note"] = d_inner.get("creator_note", "")
        except Exception:
            pass
    return ep_data

def processar_serie(pasta_serie):
    pasta_serie_abs = pasta_serie.resolve()
    caminho_episodes = pasta_serie_abs / "episodes"
    
    if not caminho_episodes.is_dir():
        return False

    episodios = sorted([p for p in caminho_episodes.iterdir() if p.is_dir()])
    if not episodios:
        return False

    meta = carregar_dados_serie(pasta_serie_abs)
    print(f"\n📂 Processando série: {meta['title']} ({len(episodios)} episódios)")

    nome_autor = carregar_dados_autor()
    avatar_autor = encontrar_avatar_autor()
    
    if avatar_autor:
        avatar_rel_path = Path(BASE_DIR / avatar_autor).relative_to(pasta_serie_abs, walk_up=True).as_posix()
        avatar_creator_html = f'<img src="{avatar_rel_path}" alt="{nome_autor}" class="creator-avatar">'
    else:
        avatar_creator_html = f'<div class="creator-avatar-placeholder">{nome_autor[0].upper()}</div>'

    hub_path_pai = BASE_DIR.parent / "index.html"
    hub_path_raiz = BASE_DIR / "index.html"
    
    if hub_path_pai.exists():
        botao_voltar_html = '<a href="../index.html" class="btn-voltar-index">← Voltar ao Início</a>'
    elif hub_path_raiz.exists():
        botao_voltar_html = '<a href="index.html" class="btn-voltar-index">← Voltar ao Início</a>'
    else:
        botao_voltar_html = '<a href="../index.html" class="btn-voltar-index">← Voltar ao Início</a>'

    banner_html = f'<div class="series-banner"><img src="{meta["local_header"]}" alt="Banner"></div>' if meta["local_header"] else ''
    thumb_html = f'<img src="{meta["local_thumb"]}" class="series-thumb" alt="Capa">' if meta["local_thumb"] else ''
    genre_html = f'<span class="series-genre">{html.escape(str(meta["genre"]))}</span>' if meta["genre"] else ''
    
    stats_parts = []
    if meta["views"]: stats_parts.append(f"👁️ {meta['views']} views")
    if meta["subscribers"]: stats_parts.append(f"👥 {meta['subscribers']} inscritos")
    if meta["likes"]: stats_parts.append(f"❤️ {meta['likes']} likes")
    if meta["publish_date"]: stats_parts.append(f"📅 Publicado em {meta['publish_date']}")
    
    meta_info_str = " • ".join([p for p in [genre_html] + stats_parts if p])

    desc_str = str(meta["description"])
    desc_formatted = desc_str if ("<p>" in desc_str or "<br>" in desc_str) else html.escape(desc_str).replace("\n", "<br>")

    header_html = f'''
    {banner_html}
    <div class="series-header">
        {thumb_html}
        <div class="series-info">
            <h1 class="series-title">{html.escape(meta["title"])}</h1>
            <div class="series-meta">{meta_info_str}</div>
            <div class="series-desc">{desc_formatted}</div>
        </div>
    </div>'''

    indice_items = []
    select_options = []
    capitulos_html = []

    for idx, ep_path in enumerate(episodios, start=1):
        id_cap = f"cap{idx}"
        ep_info = carregar_dados_episodio(ep_path)
        titulo_limpo = html.escape(ep_info["title"])
        data_ep_html = f'<span class="capitulo-data">{ep_info["publish_date"]}</span>' if ep_info["publish_date"] else ''
        
        indice_items.append(f'<li><a href="#{id_cap}">Cap. {idx} - {titulo_limpo}</a></li>')
        select_options.append(f'<option value="{idx}">Cap. {idx} - {titulo_limpo}</option>')

        imgs_html = []
        images_path = ep_path / "images"
        if images_path.is_dir():
            exts = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
            for img in sorted(images_path.iterdir()):
                if img.suffix.lower() in exts:
                    rel_path = img.relative_to(pasta_serie_abs).as_posix()
                    imgs_html.append(f'<img src="{rel_path}" alt="{img.name}">')

        creator_note_html = ""
        if ep_info["creator_note"]:
            creator_note_html = f'''
            <div class="creator-note-box">
                {avatar_creator_html}
                <div class="creator-content">
                    <div class="creator-info-line">
                        <span class="creator-name">{html.escape(nome_autor)}</span>
                        <span class="creator-tag">Creator</span>
                    </div>
                    <div class="creator-text">{ep_info["creator_note"]}</div>
                </div>
            </div>'''

        comments_file = ep_path / "comments.json"
        comentarios_html = processar_comentarios(comments_file, id_cap)

        nav_prev = f'<a href="#cap{idx-1}">◀ Anterior</a>' if idx > 1 else ''
        nav_next = f'<a href="#cap{idx+1}">Próximo ▶</a>' if idx < len(episodios) else ''

        capitulos_html.append(f'''
        <div class="capitulo" id="{id_cap}">
            <div class="capitulo-header">
                <h2>Capítulo {idx} - {titulo_limpo}</h2>
                {data_ep_html}
            </div>
            {"".join(imgs_html)}
            {creator_note_html}
            {comentarios_html}
            <div class="nav-botoes">
                <a href="#topo">⬆ Topo</a>
                {nav_prev}
                {nav_next}
            </div>
        </div>''')

    options_html_str = "".join(select_options)

    html_final = f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=yes, maximum-scale=5.0">
    <title>{html.escape(meta["title"])}</title>
    <style>{CSS_ESTILOS}</style>
</head>

<body id="topo">
    <div id="versao">
        <span>Série: <b>{html.escape(meta["title"])}</b> | Gerado em {DATA_GERACAO}</span>
        {gerar_componente_modal_info(BASE_DIR.parent)}
    </div>
    
    <button id="toggleSidebarBtn" onclick="toggleSidebar()">☰ Painel</button>

    <div class="sidebar oculto" id="sidebar">
        {botao_voltar_html}
        <div class="painel-controles">
            <h3>Seletor Rápido</h3>
            <select id="selectCapitulosSidebar" class="select-capitulos" onchange="irParaCapitulo(this.value)">
                {options_html_str}
            </select>

            <h3>Opções da Página</h3>
            <div class="botoes-grid">
                <button onclick="mudarTema()">Tema</button>
                <button id="btnFullscreen" onclick="toggleModoImersivo()">📖 Leitura Imersiva</button>
                <button onclick="alterarFonte(1)">A+</button>
                <button onclick="alterarFonte(-1)">A-</button>
                <button id="btnGlobalComentarios" class="btn-full-width" onclick="toggleTodosComentarios()">Exibir Comentários</button>
            </div>
        </div>

        <h2>Índice</h2>
        <ul>{"".join(indice_items)}</ul>
    </div>

    <div class="conteudo expandido" id="conteudo">
        {header_html}
        {"".join(capitulos_html)}
    </div>

    <!-- ELEMENTOS DO MODO IMERSIVO -->
    <div class="imersivo-controles">
        <button class="btn-sair-imersivo" onclick="toggleModoImersivo()">❌ Sair do Modo Leitura</button>
    </div>

    <div id="imersivoHud" class="imersivo-hud-bottom">
        <button class="imersivo-nav-btn" onclick="imersivoPaginaAnterior()">← Anterior</button>
        <span id="imersivoInfoText">Cap. 1 • Pág. 1/1</span>
        <button class="imersivo-nav-btn" onclick="imersivoProximaPagina()">Próximo →</button>
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
        <button class="mobile-nav-btn" id="mobileBtnPrev" onclick="capAnterior()">◀</button>
        <select id="selectCapitulosMobile" class="select-capitulos" style="flex:2; margin:0 4px;" onchange="irParaCapitulo(this.value)">
            {options_html_str}
        </select>
        <button class="mobile-nav-btn" id="mobileBtnFullscreen" onclick="toggleModoImersivo()">📖 Imersivo</button>
        <button class="mobile-nav-btn" id="mobileBtnComms" onclick="abrirModalComentarios()">💬</button>
        <button class="mobile-nav-btn" id="mobileBtnNext" onclick="capProximo()">▶</button>
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