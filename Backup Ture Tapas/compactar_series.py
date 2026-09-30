import os
import shutil
import zipfile
from pathlib import Path

# Pasta base onde o script está sendo executado
BASE_DIR = Path(".").resolve()

# Conteúdo do arquivo LEIA-ME que será colocado em cada .zip
INSTRUCOES_TXT = """====================================================================
  PRESERVAÇÃO E LEITURA - ACERVO WEBCOMICS (TAPAS) TURE
====================================================================

Esta página oferece um backup da Webcomic do Ture, Bruno tem um namorado  postadas na plataforma Tapas até a presente data (26/09/2026), incluindo todos os capítulos, imagens e comentários preservados.

--------------------------------------------------------------------
COMO LER / USAR ONLINE (RECOMENDADO):
--------------------------------------------------------------------
Para a melhor experiência de leitura (página principal, índice navegável e modo escuro), acesse o leitor web oficial:
🔗 https://hiyato97.github.io/yatokk-backups-tapas/Backup%20Ture%20Tapas/index.html

💡 Dicas para celular:
- Ao acessar pelo navegador do celular, use a Barra Inferior para alternar facilmente entre capítulos e abrir a caixa de Comentários.
- Você pode alternar entre o Modo Escuro / Claro e ajustar o Tamanho da Fonte (A+ / A-) no painel de opções no topo.

--------------------------------------------------------------------
COMO LER / USAR OFFLINE (COMPUTADOR):
--------------------------------------------------------------------
Se preferir baixar os arquivos para ler sem internet, faça o download do arquivo .ZIP na seção "Download Options" abaixo.

1. Extraia todo o conteúdo do arquivo .zip em uma pasta no seu computador.
2. Certifique-se de que a pasta 'episodes' e o arquivo '..._completo.html' 
   estejam juntos no mesmo diretório.
3. Clique duas vezes no arquivo '.html' para abri-lo em qualquer 
   navegador de internet (Chrome, Edge, Firefox, Safari, etc.).
4. Não é necessária conexão com a internet para ler a HQ.

⚠️ OBSERVAÇÃO PARA CELULARES (OFFLINE): 
Ao tentar abrir o arquivo HTML baixado diretamente no celular, as imagens podem não carregar devido a restrições de segurança do sistema (Android/iOS) para arquivos locais. Para ler no celular, utilize preferencialmente o link online acima.

--------------------------------------------------------------------
RECURSOS DISPONÍVEIS NA INTERFACE:
--------------------------------------------------------------------
- Painel Lateral (☰): Índice de capítulos, alternador de Tema (Claro/Escuro) 
  e ajuste de tamanho de fonte (A+/A-).
- Comentários: Clique no botão "💬 Ver Comentários" em cada capítulo para 
  expandir os comentários preservados da época da publicação.
- Navegação Mobile: Barra inferior para avançar ou voltar capítulos facilmente 
  em telas de smartphone.
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
    
    