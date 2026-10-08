"""Embute as imagens dentro da pagina de bancada, para ela abrir em qualquer visualizador.

Visualizador que abre o HTML como copia isolada (painel de arquivos do app, anexo, e-mail)
nao acha `imagens/` nem `saida/.../renders/`: a pagina mostra imagem quebrada. Este script
preenche o bloco /*ARQ*/ com data URIs comprimidos (fotos JPEG ate 1600 px, renders WebP);
os arquivos originais nao mudam. Rode de novo sempre que fotos ou renders mudarem.

Uso:
  python embute_arquivos.py <pasta do projeto>/revisao.html imagens saida/conceitos_r01/renders
"""
import base64
import io
import json
import pathlib
import re
import sys

from PIL import Image, ImageOps

EXT = {".png", ".jpg", ".jpeg", ".webp"}


def comprime(caminho):
    im = ImageOps.exif_transpose(Image.open(caminho))  # foto de celular: girar pela orientacao da camera
    buf = io.BytesIO()
    if im.mode in ("RGBA", "LA", "P"):
        im.convert("RGBA").save(buf, "WEBP", quality=88, method=6)
        tipo = "image/webp"
    else:
        im.thumbnail((1600, 1600))
        im.convert("RGB").save(buf, "JPEG", quality=82, optimize=True)
        tipo = "image/jpeg"
    return f"data:{tipo};base64," + base64.b64encode(buf.getvalue()).decode()


def main():
    html = pathlib.Path(sys.argv[1]).resolve()
    raiz = html.parent
    arq = {}
    for pasta in sys.argv[2:]:
        for f in sorted((raiz / pasta).iterdir()):
            if f.suffix.lower() in EXT:
                arq[f.relative_to(raiz).as_posix()] = comprime(f)
    texto = html.read_text(encoding="utf-8")
    bloco = "/*ARQ*/const ARQ=" + json.dumps(arq) + ";/*FIM ARQ*/"
    novo, n = re.subn(r"/\*ARQ\*/.*?/\*FIM ARQ\*/", lambda _: bloco, texto, flags=re.S)
    if n != 1:
        sys.exit("bloco /*ARQ*/ nao encontrado: gere a pagina pelo modelo atual")
    html.write_text(novo, encoding="utf-8")
    print(f"{len(arq)} arquivo(s) embutido(s); pagina com {html.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
