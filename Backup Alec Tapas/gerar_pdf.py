import os
import json
import html
import argparse
from pathlib import Path
from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

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
            # Prefere imagem que contenha "cover", "banner" ou "img_" no nome se houver mais de uma na raiz
            for img in imagens_raiz:
                nome_lower = img.name.lower()
                if "cover" in nome_lower or "banner" in nome_lower or "img_" in nome_lower:
                    capa_encontrada = img
                    break
            if not capa_encontrada:
                capa_encontrada = imagens_raiz[0]
            break

    # 2. Coleta todas as imagens da série (incluindo episódios nas subpastas)
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
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_header_footer(self, page_count):
        self.saveState()
        width, height = A4

        self.setFillColor(colors.HexColor("#718096"))
        self.setFont("Helvetica", 8)
        titulo_obra = getattr(self, "titulo_obra", "")
        self.drawString(35, height - 25, titulo_obra)
        
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.5)
        self.line(35, height - 30, width - 35, height - 30)

        self.setFont("Helvetica", 8)
        page_text = f"Página {self._pageNumber} de {page_count}"
        self.drawRightString(width - 35, 20, page_text)
        self.line(35, 30, width - 35, 30)

        self.restoreState()

def converter_serie_para_pdf(pasta_serie, autor_nome):
    if not pasta_serie.exists() or not pasta_serie.is_dir():
        print(f"❌ Erro: Pasta não encontrada: '{pasta_serie}'")
        return

    titulo, genero, descricao = obter_metadados_serie(pasta_serie)
    capa_path, imagens = obter_capa_e_imagens(pasta_serie)

    if not capa_path and not imagens:
        print(f"⚠️  Nenhuma imagem encontrada em: '{pasta_serie.name}'")
        return

    total_imagens = len(imagens) + (1 if capa_path else 0)
    print(f"🔄 Processando PDF de '{pasta_serie.name}' ({total_imagens} imagens)...")

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

    style_title = ParagraphStyle(
        'CoverTitle', parent=styles['Title'], fontName='Helvetica-Bold',
        fontSize=24, leading=28, textColor=colors.HexColor("#1A202C"), alignment=1, spaceAfter=10
    )
    style_author = ParagraphStyle(
        'CoverAuthor', parent=styles['Normal'], fontName='Helvetica-Bold',
        fontSize=12, leading=16, textColor=colors.HexColor("#4A5568"), alignment=1, spaceAfter=15
    )
    style_badge = ParagraphStyle(
        'CoverBadge', parent=styles['Normal'], fontName='Helvetica',
        fontSize=10, leading=14, textColor=colors.HexColor("#2B6CB0"), alignment=1, spaceAfter=20
    )
    style_desc = ParagraphStyle(
        'CoverDesc', parent=styles['Normal'], fontName='Helvetica',
        fontSize=9.5, leading=14, textColor=colors.HexColor("#718096"), alignment=1, spaceAfter=15
    )

    story = []

    # PÁGINA DE CAPA / INFORMAÇÕES
    story.append(Spacer(1, 10))
    story.append(Paragraph(titulo, style_title))
    story.append(Paragraph(f"Por <b>{autor_nome}</b>", style_author))
    
    badge_text = f"<b>Gênero:</b> {genero} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Total de Imagens:</b> {total_imagens}"
    story.append(Paragraph(badge_text, style_badge))

    if capa_path and capa_path.exists():
        try:
            with Image.open(capa_path) as img:
                w, h = img.size
                max_w = printable_width * 0.7
                max_h = 280
                ratio = min(max_w / w, max_h / h) * 0.99
                final_w = w * ratio
                final_h = h * ratio

                story.append(RLImage(str(capa_path), width=final_w, height=final_h))
                story.append(Spacer(1, 15))
        except Exception as e:
            print(f"   ⚠️  Aviso ao carregar capa: {e}")

    if descricao:
        desc_limpa = html.unescape(descricao)
        if len(desc_limpa) > 300:
            desc_limpa = desc_limpa[:300] + "..."
        story.append(Paragraph(f"<i>{desc_limpa}</i>", style_desc))

    story.append(PageBreak())

    # PÁGINAS DO CORPO
    for img_path in imagens:
        try:
            with Image.open(img_path) as img:
                w, h = img.size
                ratio = min(printable_width / w, printable_height / h) * 0.99
                final_w = w * ratio
                final_h = h * ratio

                story.append(RLImage(str(img_path), width=final_w, height=final_h))
                story.append(PageBreak())
        except Exception as e:
            print(f"   ⚠️ Erro na imagem {img_path.name}: {e}")

    if story and isinstance(story[-1], PageBreak):
        story.pop()

    def canvas_factory(*args, **kwargs):
        c = NumberedCanvas(*args, **kwargs)
        c.titulo_obra = titulo
        return c

    try:
        doc.build(story, canvasmaker=canvas_factory)
        print(f"✅ PDF gerado com sucesso: {pdf_path.relative_to(BASE_DIR)}\n")
    except PermissionError:
        print(f"❌ ERRO: O arquivo '{pdf_path.name}' está aberto em outro programa. Feche-o e tente novamente.\n")
    except Exception as e:
        print(f"❌ ERRO ao gerar PDF de '{pasta_serie.name}': {e}\n")

def main():
    parser = argparse.ArgumentParser(description="Gera PDFs para séries de quadrinhos/manga.")
    parser.add_argument(
        "--pastas", "-p",
        nargs="*",
        help="Caminhos ou nomes de pastas específicas para processar. Se omitido, processa todas."
    )
    args = parser.parse_args()

    autor_nome = carregar_config_autor()
    print(f"🚀 Gerando PDFs para o autor: {autor_nome}\n")

    if args.pastas:
        for p in args.pastas:
            pasta_alvo = Path(p).resolve() if Path(p).is_absolute() else BASE_DIR / p
            converter_serie_para_pdf(pasta_alvo, autor_nome)
    else:
        for item in BASE_DIR.iterdir():
            if item.is_dir() and not item.name.startswith('.') and not item.name.startswith('__'):
                converter_serie_para_pdf(item, autor_nome)

if __name__ == "__main__":
    main()