from pathlib import Path

BASE_DIR = Path(".").resolve()

for pasta in BASE_DIR.iterdir():
    if pasta.is_dir() and not pasta.name.startswith('.'):
        extensoes = ['*.jpg', '*.jpeg', '*.png', '*.webp']
        imagens = []
        for ext in extensoes:
            imagens.extend(list(pasta.glob(f"**/{ext}")))
        
        episodios = set(img.parent for img in imagens)
        print(f"📁 Série: {pasta.name}")
        print(f"   ↳ Total de imagens encontradas: {len(imagens)}")
        print(f"   ↳ Total de pastas/episódios encontrados: {len(episodios)}")
        print("---")