# Arredondar uma quina

Dominio desta chamada: UMA aresta convexa manifold de 90 graus, em malha exclusiva
sem modificadores/shape keys, escala uniforme positiva sem cisalhamento, unidades METRIC.
Edit Mode, selecao de ARESTAS. Nao use para varios cantos ou angulos diferentes.

Na raiz do pacote, no Python do hospedeiro:
```
python scripts/arredondar_selecao.py --porta PORTA --objeto NOME --raio-mm RAIO --segmentos NUMERO
```
Substitua valores reais. Raio positivo, segmentos inteiros de 2 a 64.
Raio deve ficar abaixo da metade da menor aresta incidente, margem numerica 0.00001 mm.
A ferramenta usa bevel nativo com perfil circular 0.5 e mede os vertices do perfil.
PERFIL_MEDIDO confirma erro radial <=0.00001 mm e arestas manifold.
Isso nao mede o erro da aproximacao facetada entre os vertices; mais segmentos
reduzem a faceta. Colisao, auto-intersecao e fabricacao nao foram verificadas.
Distancia OFFSET so equivale a raio neste dominio de quina de 90 graus.
Ctrl+Z imediatamente desfaz, Ctrl+Shift+Z refaz. Nao automatize Undo global depois
de trabalho externo. Em timeout/INDETERMINADO inspecione antes de repetir.
