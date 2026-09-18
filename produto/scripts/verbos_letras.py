"""Verbos ligados às letras: operam nas faces selecionadas dos objetos em edição da cena ativa.

  python verbos_letras.py mover --eixo Z --mm 2
  python verbos_letras.py extrudar --mm 2
  python verbos_letras.py preencher --modo contorno|ponte
  python verbos_letras.py arredondar --raio 1 --seg 4
  python verbos_letras.py desfazer
Cada verbo guarda a malha anterior (<objeto>.ANTES_VERBO), mede saúde antes/depois e restaura se a malha piorar.
"""
import argparse, json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from ponte_letras import executa  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("verbo", choices=["mover", "extrudar", "preencher", "arredondar", "desfazer"])
ap.add_argument("--eixo", choices=["X", "Y", "Z"], default="Z")
ap.add_argument("--mm", type=float, default=1.0)
ap.add_argument("--modo", choices=["contorno", "ponte"], default="contorno")
ap.add_argument("--raio", type=float, default=1.0)
ap.add_argument("--seg", type=int, default=4)
a = ap.parse_args()
if a.verbo == "mover":
    out = executa("mover", eixo=a.eixo, mm=a.mm)
elif a.verbo == "extrudar":
    out = executa("extrudar", mm=a.mm)
elif a.verbo == "preencher":
    out = executa("preencher", modo=a.modo)
elif a.verbo == "arredondar":
    out = executa("arredondar", raio_mm=a.raio, segmentos=a.seg)
else:
    out = executa("desfazer")
print(json.dumps(out, ensure_ascii=False, indent=1, default=str))
