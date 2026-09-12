# Extrudar faces selecionadas

Use para criar volume novo a partir de um unico conjunto conectado de faces planas.
Para apenas deslocar vertices existentes, use mover_selecao.md.

Precondicoes: objeto ativo nomeado, Edit Mode, faces visiveis selecionadas, malha
exclusiva sem modificadores ou shape keys, unidades METRIC com escala correta.
Distancia positiva em mm, na normal global das faces. Nao adivinhe tolerancia:
a tolerancia de plano e um limite computacional declarado, nao folga de impressao.

No Python do hospedeiro, a partir da raiz do pacote:
```
python scripts/extrudar_selecao.py --porta PORTA --objeto NOME --distancia-mm DISTANCIA --tolerancia-plano-mm TOLERANCIA --captura TOKEN
```
Substitua os quatro valores pelo contexto real. Nao use a porta de outra sessao.
Nao precisa escrever codigo Blender; a ferramenta usa extrude_face_region nativo.

EXTRUSAO_MEDIDA confirma altura na normal e vertices preexistentes preservados.
Nao certifica colisao, auto-intersecao, espessura ou fabricacao. Inspecione a forma.
A operacao aparece na cena conectada e entra no Undo nativo (Ctrl+Z imediatamente,
Ctrl+Shift+Z para refazer). Nao use Undo global remoto apos trabalho externo.
Em timeout ou INDETERMINADO, inspecione antes de repetir: a extrusao pode ter ocorrido.

Antes da primeira escrita, execute `python scripts/capturar_selecao.py --porta PORTA --objeto NOME`.
Use o campo `captura` como TOKEN. A proxima operacao pode usar `captura_depois` da
anterior; nao recapture automaticamente para contornar selecao que mudou.
A ferramenta recusa captura desatualizada antes da escrita. Falha com recuperacao
confirmada retorna FALHA_RESTAURADA; INDETERMINADO/FALHA_COM_ALTERACAO exigem inspecao.
