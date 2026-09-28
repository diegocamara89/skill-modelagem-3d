# Projetar para imprimir: regras medidas

Rota para: "que folga eu uso?", "como prendo isso num tampo?", "vai imprimir sem suporte?",
"põe minha marca", "gera em vários tamanhos". Cada regra abaixo saiu de peça impressa e
conferida pelo operador. **Todo valor vale nas condições declaradas**; fora delas é
`A_CALIBRAR`, e o que se diz é o que seria preciso medir.

Condição comum a todas as linhas medidas, salvo indicação: Bambu Lab A1, bico 0,4, PETG.

## 1. Folgas calibradas

| Encaixe | Folga | Condições | Resultado |
|---|---|---|---|
| Pino em furo | **0,3 no diâmetro** (0,15 por lado) | furo ⌀3,2 × 5,0, pino ⌀2,9 × 4,7; camada 0,08; pino deitado a 30°, furo em pé | "encaixe perfeito" (23/09/2026) |
| Disco parado dentro de tubo (círculo em círculo, eixo vertical) | **0,10 por lado** | ⌀35 a 60; camada 0,2; os dois em pé | 0,25 folgado → 0,15 ainda folgado → **0,10 perfeito** (27/09/2026) |
| Lingueta em entalhe (anti-giro) | **0,10 por lado** | lingueta 2,0 de largura, 1,3 de entrada; camada 0,2 | 0,40 → 0,20 → **0,10 perfeito** (27/09/2026) |
| Rosca trapezoidal | **0,3 radial** (0,6 no diâmetro) | passo 3, flancos a 45°, profundidade 1,0, ⌀ nominal 40; camada 0,2; macho e porca em pé | "entra com folga", rosqueia à mão (26/09/2026) |

**Encaixe parado aceita folga menor que encaixe que gira.** O disco da segunda linha não
se move depois de montado: folga pequena demais só pede um empurrão para entrar, não
trava nada. Numa peça que gira, a folga que decide é a do eixo, não a do alojamento. Antes
de apertar, diga qual das duas é, e por que a outra não muda.

Abaixo de 0,10 por lado a primeira camada, mais larga, tende a prender, mesmo com
`elefant_foot_compensation` no perfil.

## 2. Prender peça num tampo ou chapa: rosca e porca, não garra

Garras flexíveis (abas com gancho que estalam por baixo) impressas **em pé** quebraram no
primeiro encaixe. Tinham 1,2 mm de espessura, com a deformação calculada em ~2%, e
dobravam justamente na direção em que as camadas descolam. Além disso, cada espessura de
tampo pedia uma garra diferente.

O que funcionou foi tubo com rosca por fora mais porca recartilhada por baixo:

- não dobra nada, é só aperto;
- a mesma peça serve para qualquer espessura até o comprimento da rosca (4 a 12 mm e 4 a
  30 mm com dois comprimentos de tubo);
- rosca e porca imprimem em pé, sem suporte, com flancos a 45°.

Para caber no furo, a crista da rosca fica abaixo do furo menos a folga. Para não afinar a
parede no fundo da rosca, engrosse por dentro onde a passagem já é estreitada por outra
feição.

Se garra for inevitável: calcule a deformação (1,5·t·δ/L²) antes de desenhar, e oriente a
peça para a garra não dobrar entre camadas.

## 3. Rosca helicoidal: gere o filete como malha, não por varredura do kernel

Medido em 26/09/2026, build123d 0.11.1:

| Tentativa | O que aconteceu |
|---|---|
| `sweep(perfil, Helix(...), is_frenet=True)` unido ao tubo | `is_valid` verdadeiro, e o STL exportado saiu com **250 a 500 arestas abertas** |
| recortar a hélice longa (passar da ponta e aparar) | o kernel caiu (*access violation*), sem exceção Python |
| recortar a rosca fêmea de um anel com o "macho" | sólido inválido, 2 a 7 corpos |

O que funcionou:

1. O filete é gerado **como malha fechada** em numpy: o perfil trapezoidal é repetido a
   cada passo angular, com tampas nas pontas.
2. Ele é unido ao corpo por **manifold3d** (`Mesh64`). O corpo sai do build123d pela
   `tessellate`, com a mesma tolerância da exportação.
3. Na porca, o filete interno é **somado** a um anel (não recortado), meio passo defasado
   na **mesma hélice** do parafuso, e limitado à altura da porca por interseção com um
   cilindro.
4. A hélice nasce dentro do tubo, para não precisar aparar a ponta. O chanfro de entrada
   faz o acabamento.

Conferência mínima:

- `check_mesh.py` em cada peça roscada: 0 abertas, 0 não-manifold, 1 componente;
- interferência porca × parafuso por interseção manifold em **várias alturas**, porque a
  fase muda com a altura;
- fatiar e confirmar que os flancos a 45° não pedem suporte.

Peça roscada gerada assim sai só em STL; não há STEP.

## 4. Espessura mínima que imprimiu (PETG, bico 0,4, camada 0,08, arachne)

| feição | falhou | imprimiu |
|---|---|---|
| aro de óculos (parede quase vertical) | 0,63 mm — não fechou | 1,09 mm |
| elo de colar | 0,30 mm | 0,9 mm contínuo; 1,7 escolhido pela estética |
| haste de óculos | 0,91 mm — quebrou ao tirar o suporte | 2,09 mm, presa à cabeça |

Vale só nessas condições. `wall_generator = arachne` faz parte da condição: o *classic* só
faz filete inteiro e some com feição de 2,6 filetes sem avisar.

## 5. Feição delicada: presa à peça é melhor que avulsa

O óculos preso ao rosto é parede quase vertical e se sustentou sozinho. Avulso, precisou de
placa de base e 27 pilares para ter contato com a mesa, e saiu inutilizável. Antes de
separar uma feição para imprimir à parte, meça o balanço dela **no lugar**
(`scripts/mapa_balanco.py`).

Quando a peça é mesmo avulsa, escolha a orientação que **não gera interface de suporte**:
das três flores, a que soldou foi a única com interface; a inclinada a 30° não teve
nenhuma e saiu no alicate. Critério de suporte: skill `bambu-a1`, `references/suportes.md`.

## 6. Rebaixo para o dedo e outros negativos sem suporte

| Desenho | Resultado |
|---|---|
| serrilha: sulcos em V de 90°, 0,6 de fundo, 1,2 de largura | **não serve**: o dedo não entra, e a tampa não gira |
| rebaixo de 0,8 de fundo e fundo plano, 4 de largura | funcional, mas feio; o fundo sai em ponte |
| **gota**: rebaixo de **1,4** de fundo, ~7 de largura na boca, paredes a 45°, fundo em ponte de ≤ 4,4 | **aprovado** |

Com a face rebaixada virada para a mesa, parede a 45° fecha 0,2 por camada e não pede
suporte. Fundo plano vira ponte: curta (≤ ~5 mm) sai bem; longa, não. Com `enable_support`
ligado, o fatiador põe interface de suporte dentro de um rebaixo de fundo plano. Fatie com
o suporte ligado só para localizar balanço, e confirme que o único aviso é essa ponte.

## 7. Gravação de marca ou texto

- **Grave na face que sai para cima na impressão.** Se ela não for a face visível no uso,
  vire a peça na hora de imprimir: gravação na face da mesa vira ponte.
- **Espelhe o que vai ser lido por baixo** (fundo de tampa, face de baixo de porca):
  desenhe como visto por baixo e espelhe em x.
- **Tamanho mínimo:** letra em negrito de ~2,8 mm e traço de símbolo ≥ 0,7, para 0,4 de
  profundidade (duas camadas de 0,2).
- **Encaixe automático:** calcule a região livre (entre pino e parede, fora de recortes e
  do rebaixo da face oposta, com margem) e encolha só o que não couber. Texto em arco ao
  longo da borda usa muito mais espaço que texto reto: cada letra é posicionada pelo centro
  da própria face (o `Text` do build123d dá uma face por letra).
- **Confira no G-code:** pontos dentro da gravação sem plástico na última camada, e com
  plástico na camada de controle logo abaixo. Uma medida sem controle não diz se o leitor
  funciona.

- **Fatie um arquivo por vez.** Cada fatiamento leva minutos e o dono fica esperando: confira
  primeiro só o arquivo que ele vai imprimir. As outras variantes (família de tamanhos,
  publicação) vêm depois, uma por comando, e só quando o pedido exigir. Regra completa na skill
  `bambu-a1` (quarta regra).

## 8. Família de tamanhos

- Tudo que encaixa fica em **valor absoluto**: folgas, rosca, pino, nervuras, espessuras.
  Só os raios acompanham o tamanho, com os afastamentos medidos na peça impressa.
- Uma função `params(tamanho)` gera o conjunto. Confira **cada** tamanho: montagem,
  interferência, rosca, e a feição que encolhe mais rápido (a passagem de cabo caiu de 19
  para 6,5 mm do maior para o menor furo).
- Uma escala simples quebra tudo o que é absoluto: a parede de 1,0 vira 0,67, a folga de
  0,25 vira 0,17 e prende. Não escale.

## 9. Iterar com impressão física

- **Uma mudança por vez em cada impressão.** Folga e nervura mexidas juntas não dizem qual
  resolveu.
- **Mudança fora de encaixe preserva o teste já impresso.** Aba maior e borda arredondada
  não invalidaram a impressão em andamento, porque a parte interna saiu idêntica: compare o
  volume dentro da região de encaixe, com diferença de 0,0000.
- **Quando só uma peça muda, entregue um arquivo só com ela** para o teste (4 min em vez
  de 55), além do kit completo.
- Guarde cada versão (`saida/vN/`, e a malha anterior no Blender como `.ANTES_vN`); nunca
  sobrescreva.

## 10. Peça de terceiros: licença antes de planejar publicação

Antes de propor "adaptar e publicar", leia a licença do modelo de origem. A Standard
Digital File License do MakerWorld proíbe distribuir derivados, inclusive remix. O caminho
foi projetar do zero a partir dos requisitos: mecanismo, folgas e medidas próprias, crédito
como "inspirado em". Isso não é parecer jurídico; diga ao dono o que a licença diz e deixe
a decisão com ele.

## 11. Grade de nervuras: rigidez, furos e o arquivo que vai para o fatiador

- **Em nervura, a altura conta ao cubo e a largura, linear.** Para economizar material,
  afine a largura e nunca a altura. Medido em simulação de placa validada contra a solução
  clássica (erro de 0,1%): linha única de 0,45×4 mm, com o mesmo peso de uma placa com
  colares, deu 1,9× a rigidez; grade reta venceu a diagonal com a mesma massa. Ao simular
  nervura fina numa malha regular, rasterize por **fração de cobertura**: o modo binário errou
  40% e deu o mesmo resultado para larguras diferentes.
- **Nervura só é contínua se a corda existe.** Anéis isolados não formam viga; meça corredores
  retos sem nervura antes de aplicar conta de seção T.
- **Toda feição nova confere contra TODOS os furos da peça.** Duas grades atravessaram os
  quatro furos de parafuso dos cantos; só apareceu na interseção com os furos.
- **O arquivo para o fatiador leva vértices soldados.** Malha gravada como triângulos soltos
  (`process=False` no trimesh) fez o fatiador fechar furos de parafuso — até num bloco simples
  com furo. Solde (`merge_vertices`) antes de gravar e confira cada furo e fenda no G-code,
  em todas as camadas, antes de entregar (receita na skill `bambu-a1`).
