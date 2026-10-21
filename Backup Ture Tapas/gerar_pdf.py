import argparse
import html
import json
import re
from pathlib import Path
from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, PageBreak, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

BASE_DIR = Path(".").resolve()


def carregar_dados_autor():
    author_file = BASE_DIR / "author.json"
    if author_file.exists():
        try:
            with open(author_file, "r", encoding="utf-8") as f:
                d = json.load(f)
                d_inner = d.get("data", d)
                return d_inner.get("display_name") or d_inner.get("username") or "Autor Desconhecido"
        except Exception:
            pass

    config_file = BASE_DIR / "config.json"
    if config_file.exists():
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                d = json.load(f)
                return d.get("nome") or d.get("author") or "Autor Desconhecido"
        except Exception:
            pass

    return "Autor Desconhecido"


def carregar_metadados_serie(pasta_serie):
    meta = {
        "title": pasta_serie.name,
        "genre": "",
        "description": "",
        "views": "",
        "likes": "",
        "subscribers": "",
        "publish_date": ""
    }

    caminho_series_json = pasta_serie / "series.json"
    if caminho_series_json.exists():
        try:
            with open(caminho_series_json, "r", encoding="utf-8") as f:
                data = json.load(f)
                meta["views"] = data.get("views", "")
                meta["likes"] = data.get("likes", "")
                meta["subscribers"] = data.get("subscribers", "")
                meta["publish_date"] = data.get("publish_date", "")
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
        except Exception:
            pass

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
                return f
    return None


class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            if self._pageNumber > 1:
                self.draw_header_footer(num_pages)
            super().showPage()
        super().save()

    def draw_header_footer(self, page_count):
        self.saveState()
        width, height = A4

        self.setFillColor(colors.HexColor("#718096"))
        self.setFont("Helvetica", 8)
        titulo_obra = getattr(self, "titulo_obra", "")
        self.drawString(35, height - 25, titulo_obra)

        self.setStrokeColor(colors.HexColor("#2D3748"))
        self.setLineWidth(0.5)
        self.line(35, height - 30, width - 35, height - 30)

        self.setFont("Helvetica", 8)
        page_text = f"Página {self._pageNumber} de {page_count}"
        self.drawRightString(width - 35, 20, page_text)
        self.line(35, 30, width - 35, 30)

        self.restoreState()


def encontrar_avatar_autor():
    for ext in [".png", ".jpg", ".jpeg", ".webp"]:
        avatar_path = BASE_DIR / f"avatar{ext}"
        if avatar_path.exists():
            return avatar_path
    return None

def limpar_html_para_reportlab(texto_html):
    """Converte tags HTML comuns em tags suportadas pelo ReportLab Paragraph."""
    if not texto_html:
        return ""
    t = re.sub(r'(?i)<br\s*/?>', '<br/>', texto_html)
    t = re.sub(r'(?i)<strong>', '<b>', t)
    t = re.sub(r'(?i)</strong>', '</b>', t)
    t = re.sub(r'(?i)<em>', '<i>', t)
    t = re.sub(r'(?i)</em>', '</i>', t)
    return t

def converter_serie_para_pdf(pasta_serie, autor_nome):
    pasta_serie = Path(pasta_serie).resolve()
    caminho_episodes = pasta_serie / "episodes"

    if not caminho_episodes.is_dir():
        print(f"⚠️ [PDF] A pasta '{pasta_serie.name}' não possui a pasta 'episodes'. Pulando.")
        return

    print(f"🔍 [PDF] Varrendo pastas de episódios em '{pasta_serie.name}'...")
    episodios = sorted([p for p in caminho_episodes.iterdir() if p.is_dir()])
    if not episodios:
        print(f"⚠️ [PDF] Nenhum episódio encontrado em '{pasta_serie.name}'. Pulando.")
        return
    print(f"   ✔️ Total de pastas de episódios encontradas: {len(episodios)}")

    meta = carregar_metadados_serie(pasta_serie)
    print(f"\n🚀 [PDF] Iniciando compilação de: '{meta['title']}'")

    pdf_nome = f"{pasta_serie.name}.pdf"
    pdf_path = pasta_serie / pdf_nome

    margin_x = 35
    margin_y = 45

    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        leftMargin=margin_x,
        rightMargin=margin_x,
        topMargin=margin_y,
        bottomMargin=margin_y
    )

    page_width, page_height = A4
    printable_width = page_width - (2 * margin_x) - 10
    printable_height = page_height - (2 * margin_y) - 10

    styles = getSampleStyleSheet()

    style_title = ParagraphStyle('CoverTitle', parent=styles['Title'], fontName='Helvetica-Bold', fontSize=24, leading=28, textColor=colors.HexColor("#1A202C"), alignment=1, spaceAfter=10)
    style_author = ParagraphStyle('CoverAuthor', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=12, leading=16, textColor=colors.HexColor("#4A5568"), alignment=1, spaceAfter=15)
    style_stats = ParagraphStyle('CoverStats', parent=styles['Normal'], fontName='Helvetica', fontSize=9, leading=14, textColor=colors.HexColor("#2B6CB0"), alignment=1, spaceAfter=15)
    style_desc = ParagraphStyle('CoverDesc', parent=styles['Normal'], fontName='Helvetica', fontSize=9.5, leading=14, textColor=colors.HexColor("#4A5568"), alignment=1, spaceAfter=15)
    style_toc_head = ParagraphStyle('TOCHead', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=16, leading=20, textColor=colors.HexColor("#1A202C"), alignment=0, spaceAfter=15)
    style_toc_item = ParagraphStyle('TOCItem', parent=styles['Normal'], fontName='Helvetica', fontSize=10, leading=16, textColor=colors.HexColor("#2B6CB0"), alignment=0)
    style_ep_title = ParagraphStyle('EpTitle', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=18, leading=22, textColor=colors.HexColor("#1A202C"), alignment=1, spaceAfter=10)
    style_creator_note = ParagraphStyle('CreatorNote', parent=styles['Normal'], fontName='Helvetica', fontSize=9.5, leading=14, textColor=colors.HexColor("#4A5568"))
    style_creator_name = ParagraphStyle('CreatorName', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10, leading=13, textColor=colors.HexColor("#1A202C"))

    story = []

    # Capa
    print("   📄 Adicionando página de rosto e informações...")
    story.append(Spacer(1, 10))
    story.append(Paragraph(html.escape(meta["title"]), style_title))
    story.append(Paragraph(f"Por <b>{html.escape(autor_nome)}</b>", style_author))

    stats_list = []
    if meta["genre"]: stats_list.append(f"<b>Gênero:</b> {html.escape(meta['genre'])}")
    if meta["views"]: stats_list.append(f"<b>Visualizações:</b> {meta['views']}")
    if meta["likes"]: stats_list.append(f"<b>Curtidas:</b> {meta['likes']}")
    if meta["subscribers"]: stats_list.append(f"<b>Inscritos:</b> {meta['subscribers']}")
    if stats_list:
        story.append(Paragraph(" &nbsp;&nbsp;|&nbsp;&nbsp; ".join(stats_list), style_stats))

    capa_path = encontrar_capa_serie(pasta_serie)
    if capa_path and capa_path.exists():
        try:
            with Image.open(capa_path) as img:
                w, h = img.size
                ratio = min((printable_width * 0.75) / w, 260 / h) * 0.99
                story.append(RLImage(str(capa_path), width=w * ratio, height=h * ratio))
                story.append(Spacer(1, 15))
        except Exception:
            pass

    if meta["description"]:
        desc_limpa = limpar_html_para_reportlab(meta["description"])
        story.append(Paragraph(f"<i>{desc_limpa}</i>", style_desc))

    story.append(PageBreak())

    # Sumário com leitura de cada episódio
    print("   📑 Construindo sumário (lendo títulos e metadados dos capítulos)...")
    story.append(Paragraph("Sumário", style_toc_head))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#E2E8F0"), spaceAfter=15))

    for idx, ep_path in enumerate(episodios, start=1):
        ep_info = carregar_dados_episodio(ep_path)
        data_ep = f" ({ep_info['publish_date']})" if ep_info['publish_date'] else ""
        item_text = f'<b>Cap. {idx}</b> — <a href="#cap_{idx}" color="#2B6CB0"><b>{html.escape(ep_info["title"])}</b></a>{data_ep}'
        story.append(Paragraph(item_text, style_toc_item))
        story.append(Spacer(1, 4))
        if idx % 10 == 0 or idx == len(episodios):
            print(f"      ... sumário processado até o capítulo {idx}/{len(episodios)}")

    story.append(PageBreak())

    avatar_autor = encontrar_avatar_autor()
    total_imagens_geral = 0

    # Processamento de Capítulos e Imagens
    for idx, ep_path in enumerate(episodios, start=1):
        ep_info = carregar_dados_episodio(ep_path)
        print(f"   📦 Processando Capítulo {idx}/{len(episodios)}: {ep_info['title']}")

        story.append(Spacer(1, 20))
        story.append(Paragraph(f'<a name="cap_{idx}"/>', style_toc_item))
        story.append(Paragraph(f'Capítulo {idx} — {html.escape(ep_info["title"])}', style_ep_title))

        if ep_info["publish_date"]:
            story.append(Paragraph(f"<font color='#718096'>Publicado em {ep_info['publish_date']}</font>", style_author))

        if ep_info["creator_note"]:
            note_clean = limpar_html_para_reportlab(ep_info["creator_note"])
            conteudo_nota = [
                Paragraph(html.escape(autor_nome), style_creator_name),
                Spacer(1, 3),
                Paragraph(note_clean, style_creator_note)
            ]

            if avatar_autor and avatar_autor.exists():
                try:
                    avatar_img = RLImage(str(avatar_autor), width=35, height=35)
                    t_data = [[avatar_img, conteudo_nota]]
                    t = Table(t_data, colWidths=[45, printable_width - 55])
                    t.setStyle(TableStyle([
                        ('VALIGN', (0,0), (-1,-1), 'TOP'),
                        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F7FAFC")),
                        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")),
                        ('ROUNDEDCORNERS', [4, 4, 4, 4]),
                        ('TOPPADDING', (0,0), (-1,-1), 8),
                        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
                        ('LEFTPADDING', (0,0), (-1,-1), 8),
                        ('RIGHTPADDING', (0,0), (-1,-1), 8),
                    ]))
                    story.append(Spacer(1, 10))
                    story.append(t)
                except Exception:
                    story.append(Paragraph(f"<b>{autor_nome}:</b><br/>{note_clean}", style_creator_note))
            else:
                story.append(Spacer(1, 10))
                story.append(Paragraph(f"<b>{autor_nome}:</b><br/>{note_clean}", style_creator_note))

        story.append(Spacer(1, 15))
        story.append(HRFlowable(width="60%", thickness=1, color=colors.HexColor("#CBD5E0"), spaceAfter=20))
        story.append(PageBreak())

        images_dir = ep_path / "images"
        if images_dir.is_dir():
            exts = ('.jpg', '.jpeg', '.png', '.gif', '.webp')
            arquivos_img = sorted([f for f in images_dir.iterdir() if f.suffix.lower() in exts])
            print(f"      🖼️ Adicionando {len(arquivos_img)} imagens...")

            for img_path in arquivos_img:
                try:
                    with Image.open(img_path) as img:
                        w, h = img.size
                        ratio = min(printable_width / w, printable_height / h) * 0.99
                        story.append(RLImage(str(img_path), width=w * ratio, height=h * ratio))
                        story.append(PageBreak())
                        total_imagens_geral += 1
                except Exception as e:
                    print(f"      ⚠️ Erro na imagem {img_path.name}: {e}")

    if story and isinstance(story[-1], PageBreak):
        story.pop()

    def canvas_factory(*args, **kwargs):
        c = NumberedCanvas(*args, **kwargs)
        c.titulo_obra = meta["title"]
        return c

        print("   💾 Iniciando montagem final e cálculo de páginas do PDF (isso pode demorar devido ao tamanho)...")
    try:
        doc.build(story, canvasmaker=canvas_factory)
        print(f"   ✅ [Sucesso] PDF gerado: {pdf_path.name} ({total_imagens_geral} imagens processadas)\n")
    except Exception as e:
        print(f"   ❌ [Erro] Falha ao gerar PDF de '{pasta_serie.name}': {e}\n")


def main():
    parser = argparse.ArgumentParser(description="Gera PDFs para séries de quadrinhos/manga.")
    parser.add_argument(
        "--pastas", "-p", nargs="*",
        help="Caminhos de pastas específicas para processar."
    )
    args = parser.parse_args()

    autor_nome = carregar_dados_autor()
    print(f"🚀 Gerando PDFs | Autor: {autor_nome}\n")

    if args.pastas:
        for p in args.pastas:
            pasta_alvo = Path(p).resolve() if Path(p).is_absolute() else BASE_DIR / p
            converter_serie_para_pdf(pasta_alvo, autor_nome)
    else:
        for item in BASE_DIR.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                converter_serie_para_pdf(item, autor_nome)


if __name__ == "__main__":
    main()
