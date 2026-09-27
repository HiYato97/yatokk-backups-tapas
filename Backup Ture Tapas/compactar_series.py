import os
import shutil
import zipfile
from pathlib import Path

# Pasta base onde o script está sendo executado
BASE_DIR = Path(".").resolve()

# Conteúdo do arquivo LEIA-ME que será colocado em cada .zip
INSTRUCOES_TXT = """====================================================================
  PRESERVAÇÃO E LEITURA OFFLINE - ACERVO WEBCOMICS
====================================================================

Este arquivo contém o backup completo da webcomic, incluindo todos os 
capítulos, imagens e comentários preservados.

--------------------------------------------------------------------
COMO LER / USAR:
--------------------------------------------------------------------
1. Extraia TODO o conteúdo deste arquivo .zip em uma pasta no seu 
   computador ou celular.
2. Certifique-se de que a pasta 'episodes' e o arquivo '.html' 
   permaneçam na mesma pasta após extrair.
3. Clique duas vezes no arquivo '.html' para abri-lo em qualquer 
   navegador (Chrome, Edge, Firefox, Safari, etc.).
4. Não é necessária conexão com a internet para realizar a leitura.

--------------------------------------------------------------------
RECURSOS DA INTERFACE:
--------------------------------------------------------------------
- Painel Lateral (☰): Índice de capítulos, alternador de Tema (Escuro/Claro) 
  e controle de tamanho de fonte.
- Comentários: Clique no botão "💬 Ver Comentários" em cada capítulo 
  para ver as interações preservadas.
- Navegação Mobile: Barra inferior para alternar entre capítulos em celulares.

====================================================================
"""

def compactar_pasta_serie(pasta_serie):
    pasta_serie_abs = pasta_serie.resolve()
    caminho_zip = BASE_DIR / f"{pasta_serie_abs.name}.zip"

    # Ignora se for uma pasta oculta ou a pasta de saída de zips
    if pasta_serie_abs.name.startswith('.'):
        return False

    # Verifica se a pasta tem a estrutura de episódios antes de compactar
    if not (pasta_serie_abs / "episodes").exists():
        return False

    print(f"📦 Compactando: {pasta_serie_abs.name} ...")

    with zipfile.ZipFile(caminho_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # 1. Adiciona o arquivo LEIA-ME.txt na raiz do ZIP
        zipf.writestr("LEIA-ME.txt", INSTRUCOES_TXT)

        # 2. Adiciona todos os arquivos e subpastas da série no ZIP
        for raiz, _, arquivos in os.walk(pasta_serie_abs):
            for arquivo in arquivos:
                caminho_completo = Path(raiz) / arquivo
                
                # O caminho relativo garante que os arquivos fiquem organizados corretamente dentro do ZIP
                caminho_relativo = caminho_completo.relative_to(pasta_serie_abs)
                zipf.write(caminho_completo, arcname=caminho_relativo)

    print(f"  ✅ Concluído: {caminho_zip.name}")
    return True

def main():
    print(f"🔍 Procurando pastas de séries em: {BASE_DIR}\n")
    processadas = 0

    for item in BASE_DIR.iterdir():
        if item.is_dir():
            if compactar_pasta_serie(item):
                processadas += 1

    print(f"\n{'='*50}")
    print(f"✨ Sucesso! {processadas} arquivo(s) .zip gerado(s) na raiz.")
    print(f"Pronto para upload no Internet Archive!")

if __name__ == "__main__":
    main()
    
    