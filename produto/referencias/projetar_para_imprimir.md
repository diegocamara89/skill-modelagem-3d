# Projetar para imprimir: regras medidas

Rota para: "que folga eu uso?", "como prendo isso num tampo?", "vai imprimir sem suporte?",
"põe minha marca", "gera em vários tamanhos". Cada regra abaixo saiu de peça impressa e
conferida pelo operador. **Todo valor vale nas condições declaradas**; fora delas é
`A_CALIBRAR`, e o que se diz é o que seria preciso medir.

Condição comum a todas as linhas medidas, salvo indicação: Bambu Lab A1, bico 0,4, PETG Masterprint 240 °C.

## 1. Folgas calibradas

| Encaixe | Folga | Condições | Resultado |
|---|---|---|---|
| Pino em furo | **0,3 no diâmetro** (0,15 por lado) | furo ⌀3,2 × 5,0, pino ⌀2,9 × 4,7; camada 0,08; pino deitado a 30°, furo em pé | encaixe perfeito |
| Disco parado dentro de tubo (círculo em círculo, eixo vertical) | **0,10 por lado** | ⌀35 a 60; camada 0,2; os dois em pé | perfeito (0,15 ainda folgado) |
| Lingueta em entalhe (anti-giro) | **0,10 por lado** | lingueta 2,0 de largura, 1,3 de entrada; camada 0,2 | perfeito (0,20 folgado) |
| Rosca trapezoidal | **0,3 radial** (0,6 no diâmetro) | passo 3, flancos a 45°, profundidade 1,0, ⌀ nominal 40; camada 0,2; macho e porca em pé | entra com folga, rosqueia à mão |
| Gaveta deslizante com guia | **0,4 por lado e 0,4 em cima**; guia: nervura 9,0 × 1,5 no piso do vão, canal 9,8 × 2,0 no fundo da gaveta (0,4 por lado, 0,5 sobre a nervura) | nervura e canal param 5,2 antes da frente: o canal fechado ali é o batente ao empurrar; corpo impresso de costas, gaveta em pé; camada 0,2; validada em PLA e repetida em PETG (organizador Skadis, 30/09/2026) | validada |
| Tampa deslizante em trilhos | **0,15 por lado** na lateral, **0,2 em cima** | tampa deitada, caixa de pé; camada 0,2 (a folga vertical é múltiplo da camada) | corre sem jogo |
| Trilho rabo de andorinha a 45° (base 5, ponta 10, altura 2,5) | **0,15** no trilho de baixo, **0,2** nos laterais | módulo corre da frente para trás; peças de costas na mesa; camada 0,2 | encaixa firme, sem jogo |
| Trava de lingueta (estalo) | lingueta 1,2 de espessura, ressalto 1,0 com rampa de 45° atrás, fenda 0,8 dos lados | lingueta na parede de cima do módulo; camada 0,2 | estala e segura |

**Encaixe parado aceita folga menor que encaixe que gira.** O disco da segunda linha não
se move depois de montado: folga pequena demais só pede um empurrão para entrar, não
trava nada. Numa peça que gira, a folga que decide é a do eixo, não a do alojamento. Antes
de apertar, diga qual das duas é, e por que a outra não muda.

Abaixo de 0,10 por lado a primeira camada, mais larga, tende a prender, mesmo com
`elefant_foot_compensation` no perfil.

**Medir encaixe no conjunto montado.** Use a transformação real dos objetos na
configuração montada, não a posição aberta.

- `trimesh.proximity.signed_distance`: **positivo = dentro**. Interferência é `d > 0`; folga
  é `|d|` com `d < 0`. Lido ao contrário, "vê-se" interferência onde não há.
- **Encaixe conformado:** meça a folga padrão da peça (mediana das distâncias onde as partes
  se aproximam no conjunto montado) e desenhe a calha como a feição do outro lado dilatada
  por essa folga, ajustando até a folga mínima medida bater. Ajuste de círculo por mínimos
  quadrados errou o centro numa saliência em U.
- Folga de peça articulada impressa já montada (0,3 a 0,4 mm) vira "suporte" no fatiador:
  resolva no fatiador (bloqueador, suporte só na mesa), não na geometria.

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
| parede fina quase vertical (aro) | 0,63 mm — não fechou | 1,09 mm |
| feição fina contínua (elo) | 0,30 mm | 0,9 mm |
| haste fina presa por um lado | 0,91 mm — quebrou ao tirar o suporte | 2,09 mm, presa à peça |

Vale só nessas condições. `wall_generator = arachne` faz parte da condição: o *classic* só
faz filete inteiro e some com feição de 2,6 filetes sem avisar.

**Engrossar feição fina de uma malha até o mínimo:** `scripts/piso_espessura.py V.npy F.npy
--alvo 0.9 --saida X`. Os valores da tabela acima saíram assim.

1. Mede a espessura em **todos** os vértices (raio para dentro ao longo de −normal).
2. Separa feição fina de **vinco de relevo**: vinco também dá raio curto, mas o material em
   volta é grosso. Só conta como fino se a **mediana** da espessura dos vizinhos num raio
   (padrão 1,5 mm) também estiver abaixo do alvo.
3. Desloca pela **magnitude escalar** suavizada ao longo da normal. **Nunca suavize o
   vetor**: numa lâmina as duas faces têm normais opostas e a média se anula.
4. Taubin (λ 0,5 / μ −0,53) só onde mexeu, +2 anéis.

**Limite do filtro:** o raio tem de ser **menor** que a feição. Em feição pequena a
vizinhança pega o miolo grosso e descarta a feição como vinco: reduza `--raio-relevo` e
confira no render quais vértices mexeram.

## 5. Feição delicada: presa à peça é melhor que avulsa

Feição quase vertical presa à peça se sustenta sozinha; separada, pede base e pilares e pode
sair inutilizável. Antes de separar uma feição para imprimir à parte, meça o balanço dela
**no lugar** (`scripts/mapa_balanco.py arquivo.3mf [--limiar 30]`: por corpo, área voltada
para baixo por faixa de inclinação, medida da horizontal, e área de contato com a mesa).
Contato de 0,0 mm² quer dizer que a peça flutua e imprime inteira sobre suporte: pode ser
intencional, mas tem de ser decisão.

Quando a peça é mesmo avulsa, escolha a orientação que **não gera interface de suporte**: o
que solda é a interface, não a quantidade de suporte. Critério de suporte: skill `bambu-a1`,
`references/suportes.md`.

## 6. Rebaixo para o dedo e outros negativos sem suporte

| Desenho | Resultado |
|---|---|
| serrilha: sulcos em V de 90°, 0,6 de fundo, 1,2 de largura | **não serve**: o dedo não entra, e a tampa não gira |
| rebaixo de 0,8 de fundo e fundo plano, 4 de largura | funcional, mas feio; o fundo sai em ponte |
| **gota**: rebaixo de **1,4** de fundo, ~7 de largura na boca, paredes a 45°, fundo em ponte de ≤ 4,4 | **aprovado** |

Com a face rebaixada virada para a mesa, parede a 45° fecha 0,2 por camada e não pede
suporte. Fundo plano vira ponte: curta (≤ ~5 mm) sai bem; longa, não. Ponte longa em PETG tem receita
própria (skill `bambu-a1`, `references/ponte-e-teto.md`).

**Ranhura estreita (< 2 mm) sempre em pé, nunca como teto.** Ranhura de 1,9 mm impressa
deitada saiu com material preso dentro e travou o encaixe. Oriente a peça para as paredes da
ranhura ficarem verticais; se o resto da peça criar balanço nessa orientação, faça esse
balanço a 45°. Com `enable_support`
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

## 10. Peça de terceiros: licença lida na fonte original

Antes de excluir, adaptar ou publicar uma peça de outro autor, abra a página do **autor
original** e leia a licença lá. Não herde a licença do arquivo por onde a peça chegou.

- Muitas peças funcionais são abertas: o Skadis T-Clip System (Line Arc Line, Printables
  256896) é **CC BY 4.0**, com remix e uso comercial permitidos e crédito obrigatório. Pode ir
  dentro do arquivo publicado, com o crédito no texto.
- A Standard Digital File License (SDFL) do MakerWorld proíbe distribuir o arquivo e derivados,
  inclusive remix. Aí o caminho é projetar do zero a partir dos requisitos (mecanismo, folgas e
  medidas próprias) e dar crédito como "inspirado em".

Isso não é parecer jurídico: diga ao dono o que a licença diz, com o link, e deixe a decisão
com ele.

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

## 12. Reaproveitar mecanismos antes de inventar

Para encaixes ou mecanismos, procure primeiro referências existentes e evidência de
uso compatível antes de criar outra solução ou propor um cupom. Prefira arquivos já
fornecidos e peças que o usuário usa; amplie a busca se faltar referência adequada.
Popularidade, download ou malha fechada não equivalem a validação funcional.

| Função necessária | Construção a considerar | Limite |
|---|---|---|
| orientar deslizamento | guia e ranhura correspondentes | não garantem retenção contra retirada |
| limitar fechamento e esconder folga | frente alargada ou ombro | não impedem saída no sentido oposto |
| impedir separação numa direção | colar, ressalto ou trava | conferir montagem, curso permitido e resistência separadamente |
| eliminar teto difícil de imprimir | separar corpo e tampa/bandeja | acrescenta interface de montagem a conferir |

Estas são opções de construção, não produtos certificados. Inspecione os dois lados
da interface no referencial de montagem. Preserve as condições relevantes ao adaptar:
perfil, folga, engate, espessura, orientação de impressão, material/processo e carga.
Não escale automaticamente uma folga nem transfira aprovação para a parte modificada.

No registro do trabalho, use uma ficha curta: **função → construção → origem/licença
→ evidência → condições preservadas/alteradas → limite e próxima verificação**.
Diferencie geometria nominal, uso relatado e medição física; registre o que cada um
sustenta. Reutilize arquivos conforme a licença; refazer a geometria não dispensa
conferir os termos aplicáveis (caso medido: seção 10 deste arquivo). Referências
privadas permanecem fora do pacote.

Experiência anterior pode reduzir ou dispensar cupons quando cobre a incerteza atual.
Se mudou uma condição crítica, teste apenas essa diferença, com alcance declarado;
não revalide automaticamente tudo nem chame a adaptação inteira de validada.
