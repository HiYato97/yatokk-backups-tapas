import html
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def discover_images(series_dir: Path):
    candidates = []
    for folder in (series_dir / "episodes", series_dir):
        if not folder.exists():
            continue
        for child in sorted(folder.iterdir(), key=lambda p: p.name.lower()):
            if child.is_dir():
                images_dir = child / "images"
                if images_dir.exists():
                    files = sorted(images_dir.iterdir(), key=lambda p: p.name.lower())
                    for file in files:
                        if file.is_file() and file.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
                            candidates.append(str(file.relative_to(series_dir)))
                continue
            if child.is_file() and child.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
                candidates.append(str(child.relative_to(series_dir)))

    seen = []
    for entry in candidates:
        if entry not in seen:
            seen.append(entry)
    return seen


def read_series_info(series_dir: Path):
    data = {"title": series_dir.name, "description": "Leitura local, offline e otimizada para mobile.", "theme": "Diversos"}
    index_json = series_dir / "index.json"
    if index_json.exists():
        try:
            loaded = json.loads(index_json.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                data["title"] = loaded.get("title") or loaded.get("name") or data["title"]
                data["description"] = loaded.get("description") or loaded.get("bio") or data["description"]
                data["theme"] = loaded.get("genre") or loaded.get("theme") or loaded.get("tag") or data["theme"]
        except Exception:
            pass
    return data


def build_series_page(series_dir: Path):
    info = read_series_info(series_dir)
    images = discover_images(series_dir)
    if not images:
        images = ["cover.png", "cover.jpg", "cover.jpeg", "cover.webp"]

    slides_html = "\n".join(
        f'<img class="reader-image" src="{html.escape(image)}" alt="{html.escape(info["title"])} - imagem {idx + 1}" loading="lazy" data-index="{idx}" />'
        for idx, image in enumerate(images)
    )

    title = html.escape(info["title"])
    description = html.escape(info["description"]) if info["description"] else "Leitura local, offline e otimizada para mobile."
    theme = html.escape(info["theme"]) if info["theme"] else "Diversos"

    return f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <meta name="description" content="{description}" />
  <title>{title} | Leitura</title>
  <style>
    :root {{
      --bg-main: #0d1016;
      --bg-card: #171d27;
      --bg-soft: #101822;
      --text-primary: #f4f7fb;
      --text-secondary: #a8b2c1;
      --accent: #ffd84d;
      --border: #2b3645;
      --shadow: rgba(0, 0, 0, 0.28);
    }}
    * {{ box-sizing: border-box; }}
    html {{ scroll-behavior: smooth; }}
    body {{
      margin: 0; min-height: 100vh; background: linear-gradient(180deg, #12181f 0%, var(--bg-main) 100%);
      color: var(--text-primary); font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }}
    .topbar {{
      position: sticky; top: 0; z-index: 30; display: flex; align-items: center; justify-content: space-between; gap: 12px;
      background: rgba(23, 29, 39, 0.97); border-bottom: 1px solid var(--border); padding: 0.72rem 1rem;
      backdrop-filter: blur(10px);
    }}
    .topbar a {{ color: var(--text-primary); text-decoration: none; font-weight: 600; }}
    .topbar .meta {{ color: var(--text-secondary); font-size: 0.8rem; }}
    .container {{ max-width: 980px; margin: 0 auto; padding: 24px 18px 36px; }}
    .header-card {{ background: rgba(23, 29, 39, 0.86); border: 1px solid var(--border); border-radius: 18px; padding: 18px 18px 12px; box-shadow: 0 16px 32px var(--shadow); }}
    .eyebrow {{ color: var(--accent); font-size: 0.72rem; letter-spacing: 0.08em; text-transform: uppercase; font-weight: 700; }}
    .title {{ margin: 8px 0 10px; font-size: clamp(1.8rem, 3vw, 2.7rem); }}
    .subtitle {{ color: var(--text-secondary); line-height: 1.6; margin: 0; }}
    .reader-toolbar {{ display: flex; flex-wrap: wrap; gap: 10px; margin-top: 18px; }}
    .pill {{ display: inline-flex; align-items: center; gap: 8px; padding: 0.6rem 0.8rem; border-radius: 999px; background: rgba(255, 255, 255, 0.03); border: 1px solid var(--border); color: var(--text-secondary); font-size: 0.8rem; }}
    .viewer {{ margin-top: 22px; background: rgba(23, 29, 39, 0.86); border: 1px solid var(--border); border-radius: 18px; overflow: hidden; box-shadow: 0 16px 32px var(--shadow); }}
    .viewer-window {{ display: grid; place-items: center; min-height: 420px; padding: 14px; background: #0a0d12; }}
    .reader-image {{ display: none; width: 100%; max-width: 760px; border-radius: 10px; object-fit: contain; background: #111821; box-shadow: 0 10px 18px rgba(0, 0, 0, 0.24); }}
    .reader-image.active {{ display: block; }}
    .reader-controls {{ display: flex; align-items: center; justify-content: space-between; gap: 10px; padding: 14px 16px; border-top: 1px solid var(--border); flex-wrap: wrap; }}
    .nav-btn {{ border: 1px solid var(--border); background: var(--bg-soft); color: var(--text-primary); border-radius: 10px; padding: 0.8rem 1rem; cursor: pointer; font-weight: 700; }}
    .nav-btn:hover {{ border-color: #4b586a; }}
    .status {{ color: var(--text-secondary); font-size: 0.86rem; }}
    @media (max-width: 640px) {{
      .viewer-window {{ min-height: 280px; }}
      .reader-controls {{ justify-content: center; }}
      .nav-btn {{ flex: 1 1 42%; }}
    }}
  </style>
</head>
<body>
  <div class="topbar">
    <a href="../index.html">← Voltar ao acervo</a>
    <div class="meta">{title} · Leitura local</div>
  </div>

  <div class="container">
    <header class="header-card">
      <div class="eyebrow">{theme}</div>
      <h1 class="title">{title}</h1>
      <p class="subtitle">{description}</p>
      <div class="reader-toolbar">
        <span class="pill">📶 Offline</span>
        <span class="pill">📱 Mobile leve</span>
        <span class="pill">💾 Salva progresso</span>
      </div>
    </header>

    <section class="viewer" aria-live="polite">
      <div class="viewer-window">
        {slides_html}
      </div>
      <div class="reader-controls">
        <button class="nav-btn" id="prev-btn" type="button">← Anterior</button>
        <span class="status" id="status-label">Página 1 de {len(images)}</span>
        <button class="nav-btn" id="next-btn" type="button">Próximo →</button>
      </div>
    </section>
  </div>

  <script>
    const STORAGE_KEY = 'yatokk-reader-progress';
    const seriesKey = window.location.pathname || 'series';
    const images = Array.from(document.querySelectorAll('.reader-image'));
    const statusLabel = document.getElementById('status-label');
    const prevBtn = document.getElementById('prev-btn');
    const nextBtn = document.getElementById('next-btn');
    let currentIndex = 0;

    function loadProgress() {{
      try {{
        return JSON.parse(localStorage.getItem(STORAGE_KEY) || '{{}}');
      }} catch (_) {{
        return {{}};
      }}
    }}

    function saveProgress(index) {{
      const state = loadProgress();
      const currentTitle = document.title.replace(' | Leitura', '');
      state[seriesKey] = {{
        title: currentTitle,
        chapter: index + 1,
        page: index + 1,
        updatedAt: Date.now()
      }};
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    }}

    function renderImage(index) {{
      const safeIndex = Math.max(0, Math.min(index, images.length - 1));
      currentIndex = safeIndex;
      images.forEach((img, idx) => img.classList.toggle('active', idx === safeIndex));
      statusLabel.textContent = `Página ${safeIndex + 1} de ${images.length}`;
      saveProgress(safeIndex);
    }}

    prevBtn.addEventListener('click', () => {{
      if (currentIndex > 0) renderImage(currentIndex - 1);
    }});

    nextBtn.addEventListener('click', () => {{
      if (currentIndex < images.length - 1) renderImage(currentIndex + 1);
    }});

    document.addEventListener('keydown', (event) => {{
      if (event.target && ['INPUT', 'TEXTAREA', 'SELECT'].includes(event.target.tagName)) return;
      if (event.key === 'ArrowRight' || event.key === 'PageDown') {{
        event.preventDefault(); nextBtn.click();
      }}
      if (event.key === 'ArrowLeft' || event.key === 'PageUp') {{
        event.preventDefault(); prevBtn.click();
      }}
    }});

    let touchStartX = 0;
    let touchStartY = 0;
    document.addEventListener('touchstart', (event) => {{
      const touch = event.changedTouches[0];
      touchStartX = touch.clientX;
      touchStartY = touch.clientY;
    }}, {{ passive: true }});

    document.addEventListener('touchend', (event) => {{
      const touch = event.changedTouches[0];
      const diffX = touch.clientX - touchStartX;
      const diffY = touch.clientY - touchStartY;
      if (Math.abs(diffX) > 50 && Math.abs(diffX) > Math.abs(diffY)) {{
        if (diffX < 0) nextBtn.click();
        else prevBtn.click();
      }}
    }}, {{ passive: true }});

    const stored = loadProgress()[seriesKey];
    if (stored && typeof stored.page === 'number') {{
      currentIndex = Math.min(Math.max(stored.page - 1, 0), images.length - 1);
    }}
    renderImage(currentIndex);
  </script>
</body>
</html>
'''


def generate_series_pages():
    for child in sorted(BASE_DIR.iterdir(), key=lambda p: p.name.lower()):
        if not child.is_dir() or child.name.startswith('.'):
            continue
        if child.name == '__pycache__':
            continue
        output = child / f"{child.name}_completo.html"
        output.write_text(build_series_page(child), encoding="utf-8")
        print(f"Página gerada: {output.name}")


if __name__ == "__main__":
    generate_series_pages()
