# Preencher ou ligar bordas

Esta operacao cria SUPERFICIE, nao promete volume fechado.
Use modo contorno para um unico loop fechado plano estritamente convexo.
Use modo ponte para duas arestas paralelas separadas; cria uma face entre elas.
Nao serve para remendar qualquer buraco nem reconstruir encontros de solidos.

Exige objeto ativo nomeado em Edit Mode, selecao de ARESTAS visiveis, malha
exclusiva sem modificadores/shape keys e unidades METRIC com escala correta.
As arestas selecionadas devem estar soltas ou na borda, nunca internas.
Declare tolerancia computacional de planaridade em mm.

Na raiz do pacote, no Python do hospedeiro:
```
python scripts/preencher_selecao.py --porta PORTA --objeto NOME --modo ponte --tolerancia-mm TOLERANCIA --captura TOKEN
```
Troque ponte por contorno para fechar o loop. Substitua os outros valores reais.
SUPERFICIE_CRIADA confirma uma face usando os vertices delimitados e preservados.
Volume fechado, colisao, orientacao global e fabricacao nao foram verificados.
Ctrl+Z imediatamente desfaz, Ctrl+Shift+Z refaz. Nao automatize Undo global depois
de trabalho externo. Em timeout/INDETERMINADO, inspecione antes de repetir.

Antes da primeira escrita, execute `python scripts/capturar_selecao.py --porta PORTA --objeto NOME`.
Use o campo `captura` como TOKEN. A proxima operacao pode usar `captura_depois` da
anterior; nao recapture automaticamente para contornar selecao que mudou.
A ferramenta recusa captura desatualizada antes da escrita. Falha com recuperacao
confirmada retorna FALHA_RESTAURADA; INDETERMINADO/FALHA_COM_ALTERACAO exigem inspecao.
