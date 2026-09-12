# Alinhar selecao a plano

Projecao ortogonal dos vertices das faces selecionadas em um plano global.
Nao e rotacao rigida nem preservacao automatica das paredes adjacentes.

Exige objeto ativo nomeado, Edit Mode, faces selecionadas, malha exclusiva sem
modificadores/shape keys e unidades METRIC com escala correta.
O usuario/contexto deve fornecer ponto GLOBAL em mm, normal e deslocamento maximo.
Nao deduza o plano pela imagem quando cotas ou referencias estiverem ausentes.

Na raiz do pacote, no Python do hospedeiro:
```
python scripts/alinhar_selecao.py --porta PORTA --objeto NOME --ponto-mm X Y Z --normal NX NY NZ --maximo-mm LIMITE
```
Substitua todos os valores. A normal deve ser nao nula; o limite deve ser positivo.
O comando recusa antes de alterar se algum vertice excederia esse limite.
ALINHAMENTO_MEDIDO mede residuo ao plano e vertices nao selecionados preservados.
Colisao, forma das faces adjacentes e fabricacao continuam nao verificadas.
Ctrl+Z imediatamente desfaz, Ctrl+Shift+Z refaz. Nao automatize Undo global apos
trabalho externo. Timeout/INDETERMINADO exige inspecao antes de repetir.
