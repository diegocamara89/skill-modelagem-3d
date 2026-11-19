# Malha pintada (3MF multicor do Bambu): reduzir, marcar região, mexer na forma

Medido no Mini Jesus (15–17/10/2026): malha de 1,59 milhão de triângulos, 37 mm de altura, pintura em
4 cores por triângulo (`paint_color`), impressa em PETG na A1. Ferramentas de 3MF e de fatiamento ficam na skill
`bambu-a1` (`scripts/tmf.py`, `pintura_3mf.py`, `limpa_pintura_3mf.py`, `reduz_malha_pintada.py`).

## Reduzir sem perder a pintura

- `bambu-a1/scripts/reduz_malha_pintada.py entrada.model saida.model N`: decimação quádrica (pymeshlab) com peso
  alto nos vértices de divisa de cor, e cada triângulo novo herda a cor do original mais próximo.
- 1,59 mi → 160 mil: volume 3201 contra 3202 mm³, área de cada cor ±0,2%, desvio máximo 0,013 mm. Fatiou igual ao
  original, **inclusive no suporte**.
- 1,59 mi → 50 mil: desvio máximo 0,037 mm, mas o fatiador gerou **3× mais suporte** (facetas passam do
  ângulo-limite). Reduzir até ~10% e medir o suporte no fatiador, nunca só o desvio.
- Reduzir não resolveu a falta de memória do Studio (ficou em ~12 GB com as duas malhas): ver `bambu-a1`.

## Marcar uma região (ex.: a faixa do manto) para pintar

- **Não copiar rótulo de uma malha para outra por vizinho mais próximo**: a borda serrilha (divisa de 675 mm
  contra 153 da borda limpa) e criam-se ilhas.
- Separar por vinco (ângulo entre faces vizinhas) funciona na malha **reduzida** (limiar 25° isolou a faixa) e
  **vaza na densa**: vinco arredondado tem ângulo pequeno entre triângulos vizinhos (1.018 mm² em vez de 308).
- Para pôr a divisa no fundo do vinco: miolos das duas regiões como sementes e Dijkstra no grafo de faces com custo
  alto ao cruzar aresta côncava (`limpa_pintura_3mf.py --divisa A,B`). O mesmo método, partindo da pele do
  pescoço, separou o aro da gola da faixa sem corte reto.
- Mostrar a região marcada no Blender **antes** de pintar: a primeira tentativa pegou o manto embaixo da faixa.

## Mudar a forma para tirar suporte (testado e recusado)

- Achatar o topo 0,64–0,8 mm (mover vértices, pintura intacta): a 1ª camada vira disco cheio, mas o disco liso
  aparece de cima. Recusado pelo dono.
- Rampa de 45° sob balanço por camadas (cada camada contém a de cima encolhida de uma altura de camada, só dentro de
  caixas): 24 mm³, tirou o suporte da gola. Como peça separada no mesmo objeto, dar `objectid` próprio ao arquivo
  novo (ver `bambu-a1`, armadilhas) e **pintar a rampa pela cor vizinha**: branca fixa criou 21 trocas de cor.
  Saldo no 1 boneco: suporte 0,3 → 0,2 g, +6 trocas, +8 min. Não compensou.

## Relevo de tecido (crochê) por deslocamento

- Deslocar vértices pela normal com padrão de ponto em V (projeção cilíndrica nas paredes e plana em cima). Só deu
  certo com o perfil do ponto suave (`(1 − d²)²`) e as normais suavizadas (15 passes de média com vizinhos): perfil
  com borda vertical virou 75 mil faces sobre si mesmas.
- No rosto e no cabelo o padrão embaralha; o dono descartou.
