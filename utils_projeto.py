import html
import json
from pathlib import Path

INFO_PADRAO = {
    "titulo_projeto": "Acervo de Preservação",
    "descricao": "Sistema de preservação e leitura offline.",
    "desenvolvedores": "",
    "github": "",
    "contato": "",
    "links_uteis": {}
}

CSS_MODAL_INFO = """
.btn-info-modal {
    background: transparent;
    border: 1px solid var(--border-color, #222428);
    color: var(--accent, #ffcb05);
    border-radius: 50%;
    width: 20px;
    height: 20px;
    font-size: 0.75rem;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
}
.btn-info-modal:hover { background: var(--border-color, #222428); }

.modal-info-overlay {
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background: rgba(0,0,0,0.8);
    display: none;
    justify-content: center;
    align-items: center;
    z-index: 3000;
    padding: 20px;
}
.modal-info-overlay.visivel { display: flex; }
.modal-info-box {
    background: var(--bg-card, #090a0a);
    border: 1px solid var(--border-color, #222428);
    border-radius: 8px;
    padding: 20px;
    max-width: 500px;
    width: 100%;
    color: var(--text-primary, #e1e3e6);
    position: relative;
}
.modal-info-box h3 { margin-bottom: 12px; font-size: 1.2rem; color: var(--accent, #ffcb05); }
.modal-info-box p, .modal-info-box li { font-size: 0.9rem; color: var(--text-muted, #737984); margin-bottom: 8px; line-height: 1.4; }
.modal-info-box ul { margin-left: 20px; margin-bottom: 10px; }
.modal-info-box a { color: var(--accent, #ffcb05); text-decoration: none; }
.modal-info-box a:hover { text-decoration: underline; }
.btn-fechar-modal-info {
    position: absolute; top: 15px; right: 15px;
    background: transparent; border: none; color: var(--text-muted, #737984); font-size: 1.1rem; cursor: pointer;
}
"""

def carregar_info_json(pasta_base):
    """Carrega o info.json da pasta fornecida ou cria um padrão se não existir."""
    info_file = Path(pasta_base) / "info.json"
    if not info_file.exists():
        try:
            with open(info_file, "w", encoding="utf-8") as f:
                json.dump(INFO_PADRAO, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
        return INFO_PADRAO

    try:
        with open(info_file, "r", encoding="utf-8") as f:
            dados = json.load(f)
            for k, v in INFO_PADRAO.items():
                dados.setdefault(k, v)
            return dados
    except Exception:
        return INFO_PADRAO

def gerar_componente_modal_info(pasta_base):
    """Retorna o HTML do conteúdo do modal baseado no info.json."""
    info = carregar_info_json(pasta_base)
    
    conteudo = f"<h3>{html.escape(info.get('titulo_projeto', 'Informações'))}</h3>"
    if info.get('descricao'):
        conteudo += f"<p>{html.escape(info['descricao']).replace(chr(10), '<br>')}</p>"
    if info.get('desenvolvedores'):
        conteudo += f"<p><strong>Desenvolvedor(es):</strong> {html.escape(info['desenvolvedores'])}</p>"
    if info.get('github'):
        conteudo += f'<p><strong>GitHub:</strong> <a href="{info["github"]}" target="_blank">{info["github"]}</a></p>'
    
    # Tratamento para contato (suporta texto ou dicionário com links HTML embutidos)
    contato = info.get('contato')
    if contato:
        if isinstance(contato, dict):
            conteudo += "<p><strong>Contato:</strong></p><ul>"
            for rede, link_html in contato.items():
                conteudo += f"<li><strong>{rede}:</strong> {link_html}</li>"
            conteudo += "</ul>"
        else:
            conteudo += f"<p><strong>Contato:</strong> {contato}</p>"
    
    # Tratamento para links úteis
    links_uteis = info.get('links_uteis', {})
    if links_uteis:
        conteudo += "<p><strong>Links Relacionados:</strong></p><ul>"
        for label, l_url in links_uteis.items():
            conteudo += f'<li><a href="{l_url}" target="_blank">{html.escape(label)}</a></li>'
        conteudo += "</ul>"

    html_modal = f"""
    <button class="btn-info-modal" onclick="document.getElementById('modalInfoProj').classList.add('visivel')" title="Informações do Projeto">ⓘ</button>
    
    <div class="modal-info-overlay" id="modalInfoProj" onclick="if(event.target === this) this.classList.remove('visivel')">
        <div class="modal-info-box">
            <button class="btn-fechar-modal-info" onclick="document.getElementById('modalInfoProj').classList.remove('visivel')">✕</button>
            {conteudo}
        </div>
    </div>
    """
    return html_modal