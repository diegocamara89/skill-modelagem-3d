# Entregas em movimento: visualizador interativo e vista explodida

Rota para: entregar uma peça ou um conjunto de forma que o operador possa
**inspecionar sozinho** (visualizador 3D) ou **ver como as peças se encaixam**
(GIF/MP4 de montagem/explosão). As duas são **complemento**, nunca substituto: a
conferência obrigatória continua sendo as **quatro vistas ortográficas** de
`referencias/render_de_conferencia.md`. Nenhuma delas prova dimensão, folga,
parede ou passagem de furo — isso continua com os verificadores de
`referencias/verificar.md`.

## Quando usar cada uma

| Situação | Use |
|---|---|
| o operador precisa girar, aproximar e apontar um detalhe com o mouse, sem depender de você estar presente | `scripts/visualizador_3d.py` |
| o que importa é mostrar COMO as peças se separam/encaixam (tampa, pino, encaixe) | `scripts/animacao_montagem.py` |
| conferir se a FORMA está certa antes de entregar (obrigatório, sempre) | `referencias/render_de_conferencia.md` — quatro vistas |
| medir dimensão, parede, folga, passagem de furo | `referencias/verificar.md` |

Nenhuma delas dispensa a outra. O visualizador e a animação são geometria **como
está**, no estado em que os arquivos de entrada chegaram — não reconstroem nem
corrigem nada.

## Conferência visual OBRIGATÓRIA: screenshot headless, não só estrutura do arquivo

**HTML gerar e não abrir não é conferência — é aparência de conferência.** Os
seis defeitos reais desta rota (câmera de topo, entidade HTML quebrada, eixo sem
cor, face sem gradiente, peça deitada de lado por Z-up×Y-up, enquadramento
minúsculo) só apareceram olhando um **screenshot renderizado de verdade**, em
DUAS rodadas — a validação por estrutura (round-trip do GLB, contagem de bytes)
NÃO pegou nenhum dos seis. **Reveja o screenshot depois de CADA correção**: os
defeitos 5 e 6 só apareceram numa segunda rodada, depois que os 4 primeiros já
tinham sido corrigidos — corrigir o que se vê não esgota o que ainda não foi
olhado de novo. Comando testado (Edge, headless, sem GPU real — `swiftshader` é
o rasterizador de software):

```
copy visualizador.html %TEMP%\vis_teste.html   REM caminho curto: o do scratchpad é longo demais para o Edge

"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" ^
  --headless=new --disable-gpu --enable-unsafe-swiftshader --use-angle=swiftshader ^
  --window-size=1100,750 --virtual-time-budget=8000 ^
  --screenshot=%TEMP%\vis_teste_shot.png ^
  file:///C:/Users/.../vis_teste.html
```

`--virtual-time-budget` dá tempo do three.js terminar de montar a cena antes do
screenshot disparar; sem isso a imagem pode sair em branco. Depois, **leia o
PNG** (não confie em "gerou sem erro") e, se precisar confirmar cor exata ou
medir ocupação de quadro, amostre/varra pixel com `PIL.Image.getpixel` — foi
assim que se confirmou o `&amp;middot;` (texto literal, não o caractere), o
eixo Z totalmente ausente (nenhum pixel azul-marinho na imagem inteira), a
"peça deitada" (canto errado do triedro de eixos em tela) e a ocupação de
quadro (bounding box das cores da peça, excluindo o cinza da grade e o branco
de fundo, dividida pela largura/altura da imagem).

## Opção 1 — visualizador 3D interativo (`scripts/visualizador_3d.py`)

Roda no **Python do hospedeiro**, não precisa de Blender. Gera **um** `.html` que
o operador abre por duplo clique no Windows e navega com o mouse (arrastar gira,
roda do mouse aproxima, botão direito translada).

**Como funciona por baixo.** `trimesh.viewer.notebook.scene_to_html()` já resolve
a parte difícil: embute a malha inteira em GLB (base64) **e** embute o próprio
three.js (biblioteca de renderização) como texto no mesmo arquivo — não há
`<script src=...>` nem chamada de rede.

**MEDIDO em 26/09/2026**, com as três peças de teste (caixa+tampa+pino,
112+8+98 vértices): o HTML gerado (735.953 bytes) **não contém** nenhuma
ocorrência de `"cdn."` nem de `"<script src="`; as únicas strings `"http"` que
sobram são um namespace XML (`http://www.w3.org/1999/xhtml`) e um comentário de
licença do three.js — nenhum dos dois busca nada pela rede. Geração levou 0,02s.

### Seis defeitos que só apareceram no screenshot, não na estrutura do arquivo

A primeira versão passou em toda checagem de **estrutura** (round-trip do GLB,
contagem de bytes, ausência de CDN) e ainda assim teve SEIS defeitos visuais
reais, em DUAS rodadas de revisão — cada um só apareceu depois de renderizar de
verdade (ver seção de conferência acima) e comparar contra a promessa da
legenda. Os quatro primeiros foram achados e corrigidos numa rodada; os dois
últimos (5 e 6) só apareceram numa SEGUNDA rodada, olhando a imagem já com os
quatro primeiros corrigidos — o que prova o próprio ponto desta seção: passar
num screenshot não esgota a conferência visual, é preciso olhar de novo depois
de cada correção.

1. **Câmera de topo, não isométrica.** `trimesh.viewer.notebook.scene_to_html`
   usa a câmera que `scene.camera` auto-gera na primeira leitura — que olha de
   CIMA, reto para baixo. MEDIDO: só a tampa aparecia, como um retângulo azul
   chapado. Corrigido com `_camera_isometrica`: monta a rotação (colunas =
   direita/cima/direção, mesma convenção de `render_de_conferencia.md`) e usa
   `camera.look_at(pontos, rotation=..., pad=...)` para a câmera enquadrar TODO
   o conjunto (peças + grade + eixos, via `Scene.bounds_corners`) a partir de um
   ângulo top-front-right.
2. **`&middot;` aparecendo como texto literal.** A legenda juntava as partes com
   a entidade HTML `"&middot;"` e SÓ DEPOIS escapava a string inteira com
   `html.escape` — que troca `&` por `&amp;`, virando `&amp;middot;`, que o
   navegador mostra como texto cru. Corrigido: cada parte é escapada
   individualmente e o separador passou a ser o CARACTERE unicode `·`
   (`"·"`), que `html.escape` não toca.
3. **Eixos sem cor (tudo cinza).** Duas causas, as duas medidas por screenshot:
   (a) eixo desenhado como `Path3D` com `.colors` por entidade — o exportador
   GLB do trimesh não propaga isso para um material que o three.js do template
   respeite (viravam linhas cinza, iguais à grade). Trocado por **cilindro
   sólido** colorido (mesmo mecanismo de material das peças). (b) mesmo colorido,
   o eixo Z nascia no canto EXATO da caixa envolvente e subia por DENTRO do
   sólido da peça — ficava 100% oculto (nenhum pixel azul-marinho na imagem
   inteira, medido por varredura de pixel). Corrigido empurrando a origem dos
   eixos para fora da caixa envolvente por uma casa de grade.
4. **Face sem gradiente nenhum (iluminação chapada).** A causa raiz não era falta
   de luz direcional — é que colorir via `ColorVisuals(face_colors=...)` faz o
   exportador GLB gravar um material SEM `metallicFactor`/`roughnessFactor`, e o
   glTF define o padrão da OMISSÃO como `metallicFactor=1.0` (metal liso), que
   não tem componente difusa (lambertiana). MEDIDO: com esse material, o canal R
   da peça ficava entre 91 e 98 em TODA a região visível, mesmo cruzando duas
   faces com ângulos bem diferentes em relação à câmera — batendo com
   `211×0.45≈95`, ou seja, só a luz AMBIENTE aparecia. Corrigido com um
   `PBRMaterial(metallicFactor=0.0, roughnessFactor=0.9)` explícito
   (`_material_solido`); depois do fix, as mesmas duas faces mediram R=148 e
   R=109 — variação real e visível. Também ajustada a direção padrão da câmera
   para `(1.25, -0.75, 0.85)` (assimétrica: com `|dx| = |dy|` as duas faces
   ortogonais de uma peça recebem exatamente o mesmo produto escalar com a luz
   e saem idênticas mesmo com o material corrigido).
5. **Peça deitada de lado — Z-up (peça/STL) contra Y-up (glTF/three.js).**
   Depois de corrigir os quatro defeitos acima, um screenshot novo mostrou a
   peça DEITADA: a tampa (que é o topo de verdade, no maior Z) aparecia como
   uma face LATERAL grande, a grade saía em PÉ (plano vertical em vez de chão),
   e via-se o fundo da caixa. Causa: peça de engenharia/impressão 3D é **Z-up**
   (Z = "para cima" do objeto físico), mas o three.js deste template trata **Y**
   como "para cima" — é convenção do `TrackballControls` embutido, que usa
   `camera.up` (glTF não tem esse campo por câmera; herda o padrão do three.js,
   `(0,1,0)`) para manter a orientação durante a órbita, e já realinha nisso
   antes do primeiro frame. Ajustar só a câmera não bastava, porque os
   CONTROLES continuavam usando Y como referência de "vertical". Corrigido
   girando a CENA INTEIRA (peças + grade + eixos **e** a câmera, que também é
   um nó do grafo) −90° em X antes de exportar (`_converter_z_up_para_y_up`,
   via `Scene.apply_transform` — que só mexe em matriz de nó, não em vértice
   nenhum): o Z físico da peça passa a coincidir com o Y do three.js, e toda a
   matemática em mm de `_grade_e_eixos`/`_camera_isometrica` (que roda ANTES
   dessa rotação, em coordenadas Z-up normais) continua correta.
6. **Conjunto ocupando só ~25-31% do quadro.** Medido por pixel (bounding box
   das cores da peça, excluindo grade cinza e fundo branco): 31% de largura e
   31% de altura antes da correção. Causa: a câmera enquadrava peças **+ grade
   + eixos**, e a grade se estende por design além da peça (é um chão de
   referência) — encolhendo a peça no quadro para caber tudo. Corrigido
   calculando o enquadramento (`_camera_isometrica`) só a partir dos cantos das
   PEÇAS (`cantos_pecas`, capturado antes de acrescentar grade/eixos à cena); a
   grade/eixos continuam desenhados e podem se estender para fora do quadro
   visível — isso é esperado, o assunto da foto é a peça. `pad` também caiu de
   1,4 para 1,15. Medido depois: 70% de largura, 72% de altura.

**Prova de que a malha está de verdade embutida** (não só "parece"): o base64 do
HTML foi decodificado, recarregado com `trimesh.load(..., file_type='glb')`, e
devolveu **7 geometrias** (3 peças + grade + 3 cilindros de eixo), com **320
vértices e 572 faces no total** — a soma das peças de entrada (224+12+192 = 428
faces) mais os 3 cilindros dos eixos (144 faces, 12 lados cada) e a grade (sem
face, é `Path3D`). Round-trip decodifica igual ao que foi escrito: não é
inspeção por aparência, é o dado batendo com o dado — mas note que essa prova
**não pegou nenhum dos seis defeitos da seção acima**: estrutura correta e
câmera de topo/cor errada/luz chapada/peça deitada de lado coexistem sem
contradição. As duas conferências são complementares, não substitutas uma da
outra.

### O que o script acrescenta (o template do trimesh não desenha nada disso)

1. **Cor sólida distinta por arquivo de entrada**, com material PBR fosco
   explícito (`_material_solido`: `metallicFactor=0.0, roughnessFactor=0.9`) —
   necessário para a luz direcional do template realmente sombrear cada face
   (ver defeito 4 acima). Paleta fixa de 10 cores, cicla se houver mais peças
   que cores.
2. **Grade discreta** (`Path3D`, cinza, sem promessa de cor) no plano XY, na
   cota Z mínima do conjunto, com espaçamento REDONDO (1-2-5 × 10ⁿ) escolhido a
   partir da diagonal da caixa envolvente — MEDIDO: peça de ~53mm de diagonal
   caiu em 20mm de espaçamento (ver `grade_e_eixos.grade_espacamento_mm` no
   relatório do teste).
3. **Três eixos coloridos** (X vermelho, Y verde, Z azul), como CILINDRO SÓLIDO
   (não `Path3D` — ver defeito 3 acima), com comprimento de 18% da diagonal,
   nascendo num canto empurrado para FORA da caixa envolvente por uma casa de
   grade (para não ficarem ocultos dentro do sólido da peça).
4. **Câmera isométrica explícita** (`_camera_isometrica`), enquadrando SÓ as
   peças (não a grade, que se estende por design além delas — ver defeito 6)
   com FOV estreito (28°) e `pad=1,15`, para reduzir a distorção de
   grande-angular e ocupar ~70% do quadro.
5. **Conversão Z-up → Y-up** (`_converter_z_up_para_y_up`), como ÚLTIMO passo
   antes de exportar: gira a cena inteira (peças, grade, eixos e a câmera)
   −90° em X, para o Z físico da peça virar o "para cima" que o
   `TrackballControls` do template espera (ver defeito 5 acima).
6. **Legenda** (nome + amostra de cor por peça), injetada como `<div>` HTML/CSS
   fixa no canto superior esquerdo — só aparece com **2 ou mais peças**.
7. **Luz ambiente extra** (`AmbientLight` a 0,45, injetada por substituição de
   texto), para a face de costas para a luz direcional não sair sem gradiente
   nenhum de sombra.

Grade e eixos são geometria real, inserida na cena **antes** do export: por isso
também viram parte do GLB embutido, sem precisar de nenhuma linha de JavaScript
própria (a câmera e a luz ambiente SÃO ajustes diretos na cena/HTML, não
geometria).

### Chamada testada

```
python scripts/visualizador_3d.py caixa.stl tampa.stl pino.stl \
    --saida visualizador.html --titulo "Conjunto de teste: caixa + tampa + pino"
```

Saída (relatório real do teste, resumido):

```json
{
  "bytes": 735953,
  "segundos": 0.02,
  "pecas": [
    {"nome": "caixa", "cor_rgb": [211, 84, 0], "vertices": 112, "faces": 224},
    {"nome": "tampa", "cor_rgb": [41, 128, 185], "vertices": 8, "faces": 12},
    {"nome": "pino", "cor_rgb": [39, 174, 96], "vertices": 98, "faces": 192}
  ],
  "grade_e_eixos": {
    "grade_espacamento_mm": 20.0, "eixos_comprimento_mm": 15.3,
    "eixos_raio_mm": 0.38, "eixos_origem_mm": [-51.0, -41.0, -7.25]
  },
  "depende_de_cdn": false,
  "legenda_visivel": true
}
```

Ocupação do quadro medida por pixel (bounding box das cores da peça, sem contar
grade/legenda): **70% de largura, 72% de altura**, com `pad=1,15`.

Com uma peça só (`legenda_visivel: false` medido), a legenda simplesmente não é
injetada, o resto é igual.

### Limites medidos

- **Escala real, sem normalização.** A grade usa a MESMA unidade numérica dos
  vértices do arquivo de entrada (mm, se a peça foi modelada em mm). Se as peças
  vierem em unidades diferentes entre si, o resultado será literalmente essa
  mistura — confira a origem antes de visualizar em conjunto.
- **Não preserva textura/material de origem.** GLB embutido vira cor sólida por
  peça; imagem ou PBR do arquivo original não aparece.
- **Arquivo com vários corpos (3MF/GLB de montagem) vira UMA peça.** O script
  concatena (`Scene.dump(concatenate=True)`) tudo que está no mesmo arquivo de
  entrada antes de colorir — para cor por corpo, separe em arquivos antes de
  chamar.
- **Tamanho cresce com a malha.** O GLB é binário, mas vai em base64 dentro do
  HTML: +33% de tamanho sobre o binário puro. Sem decimação aqui; para malha
  muito grande, decime antes (fora do escopo deste script).
- **A legenda e a luz ambiente são inseridas por substituição de texto** em
  marcadores conhecidos do template atual do trimesh (`<div
  id="container"></div>` e a linha exata que cria o `tracklight`). Se uma
  versão futura da biblioteca mudar esses marcadores, a falha é **visível e
  inofensiva**: HTML sem legenda ou sem a luz extra, nunca corrompido — não há
  tentativa de "adivinhar" outro ponto de inserção.
- **A conversão Z-up → Y-up assume que Z é "para cima" no arquivo de entrada.**
  É a convenção quase universal de STL/3MF/peça de engenharia e impressão 3D,
  e é a mesma que o resto da skill assume (grade no plano XY, por exemplo). Um
  arquivo que já veio em Y-up (comum em alguns pipelines de jogos/animação)
  sairia girado 90° na direção ERRADA — não há detecção automática de qual
  convenção o arquivo usa.
- **O enquadramento cobre só as PEÇAS, não a grade/eixos.** De propósito (ver
  defeito 6): a grade se estende além da peça como um chão de referência, e
  pode sair PARCIALMENTE fora do quadro visível — isso não é a peça sendo
  cortada, é o chão continuando além da foto.
- **Câmera é perspectiva, não ortográfica de verdade.** `_camera_isometrica`
  estreita o FOV (28°) e afasta a câmera para *parecer* isométrica, mas ainda
  tem alguma distorção de perspectiva perto das bordas — aceitável para
  inspeção visual, não para medir ângulo ou paralelismo na imagem (isso é
  render_de_conferencia.md, ortográfico de verdade).
- **A direção padrão da câmera é assimétrica de propósito** — `(1.25, -0.75,
  0.85)`, não `(1,-1,1)`. Ver defeito 4 acima: uma direção com `|dx| = |dy|`
  faz duas faces ortogonais de uma peça alinhada aos eixos saírem exatamente
  com o mesmo brilho, mesmo com o material corrigido.

## Opção 2 — animação de montagem / vista explodida (`scripts/animacao_montagem.py`)

Roda no **Python do hospedeiro**, não precisa de Blender. Recebe 2+ arquivos de
malha **já na pose montada** (as coordenadas de cada arquivo SÃO a posição final)
e gera um `.gif` (e, com `--mp4`, também um `.mp4` via ffmpeg) em que as peças se
afastam da posição montada e voltam a encaixar, num loop.

### Por que não o Blender

A animação é só **translação rígida** de corpos já válidos — nenhuma booleana,
nenhuma mudança de topologia. Um render de qualidade (Blender, como em
`render_de_conferencia.md`) resolveria um problema que não existe aqui, ao custo
de tudo que já está documentado em `scripts/roda_blender.py`: launcher da
Microsoft Store, stdout vazio, código de saída que não prova sucesso, e (para
formatos como 3MF) a ausência do importador em `--factory-startup`. Um
rasterizador numpy pequeno, com z-buffer **por pixel**, resolve sem nada disso.

**A armadilha que o z-buffer por pixel evita** (documentada porque já foi medida
em outro projeto, fora deste pacote): `Poly3DCollection` do matplotlib ordena por
**coleção inteira**, não por triângulo — uma peça da frente pode ficar atrás de
uma peça de trás só porque foi adicionada depois. Este script projeta cada
triângulo (convenção idêntica a `render_de_conferencia.md`: direção = do centro
da cena PARA a câmera), rasteriza com teste de profundidade **por pixel** e usa
*backface culling* (só desenha face cujo normal aponta para a câmera — válido
porque a entrada é sólido fechado e só recebe translação, que não muda normal
nenhuma).

### A regra de explosão, e o que quebrou na primeira tentativa

**MEDIDO em 26/09/2026, com caixa+tampa+pino**: a primeira versão movia toda peça
pela MESMA distância, cada uma na sua própria direção (centro do conjunto → centro
da peça). Resultado: caixa e tampa deram o **mesmo vetor unitário** (0,0,1) —
ambas estão centradas em X/Y e do mesmo lado do centro do conjunto em Z — e
mover as duas pelo mesmo vetor **não as separa uma da outra**: a distância
relativa entre elas fica igual, elas só "flutuam" juntas.

A correção: escalar o deslocamento de cada peça pela **proporção da sua própria
distância ao centro do conjunto** (ou, com eixo fixo, pela proporção da sua
própria projeção nesse eixo). A peça mais afastada recebe a `--distancia` cheia;
as mais próximas recebem uma fração. É essa fração que separa peças vizinhas
entre si, não só cada uma de um centro abstrato.

Medido depois da correção, mesma chamada, `--distancia` = 42,509mm (padrão, metade
da diagonal do conjunto):

| Peça | Deslocamento no pico (mm) | Norma (mm) |
|---|---|---|
| caixa | (0, 0, 3.35) | 3.35 — quase não se move: está perto do centro |
| tampa | (0, 0, 29.32) | 29.32 — sobe e se separa da caixa |
| pino | (−31.48, −21.25, −19.09) | 42.51 — é a mais afastada, recebe a distância cheia |

Duas regras de direção, mutuamente exclusivas:

- **Padrão** (sem `--direcao-explosao`): cada peça vai do centro do CONJUNTO para
  o centro da PRÓPRIA caixa envolvente, escalada pela proporção acima.
- **`--direcao-explosao DX DY DZ`**: eixo único para todas as peças; cada uma se
  afasta ao longo desse eixo, para o lado em que já está (sinal da projeção),
  escalada pela proporção da própria projeção nesse eixo. Útil para montagem
  empilhada (ex.: forçar a explosão só em Z).

Peça cujo centro coincide exatamente com o centro do conjunto (ou cuja projeção
no eixo fixo é zero) **não se move**, e isso entra no relatório em `avisos` — não
é silenciado.

### Enquadramento no pico: o bug dos 2 cantos em vez de 8

**MEDIDO em 26/09/2026, olhando o quadro do pico da explosão** (não a estrutura
do relatório): a tampa encostava/cortava na borda de cima do quadro. A causa era
`d["bounds"]` — a forma do trimesh de devolver so **2 pontos** (canto mínimo e
canto máximo da caixa envolvente), não os 8. Para uma câmera cujos eixos direita/
cima NÃO estão alinhados com X/Y/Z (qualquer vista isométrica está nesse caso), a
extensão projetada de uma caixa só é garantida pelos **8 cantos**: os 2 cantos
diagonais SUBESTIMAM a extensão nos outros 6. `ortho_scale_mm` media 131,3mm com
o bug e **161,8mm** depois da correção (+23%) — a câmera literalmente enquadrava
menos do que precisava.

Corrigido gerando as 8 combinações de `(x_min/x_max, y_min/y_max, z_min/z_max)`
por peça, no estado de pico da explosão, antes de calcular a escala da câmera —
mesma lógica de `Scene.bounds_corners` usada no visualizador (opção 1) e de
`obj.bound_box` em `render_de_conferencia.md`. **A lição vale para as duas
opções desta página**: caixa envolvente em vista angulada nunca se resume aos 2
cantos diagonais.

### Envelope do movimento

`(1 − cos(2π·i/(quadros−1))) / 2`: 0 no primeiro quadro (montada), 1 no meio
(pico da explosão), 0 no último quadro (montada de novo). Derivada zero nas duas
pontas — sem solavanco no loop do GIF.

### Chamada testada

```
python scripts/animacao_montagem.py caixa.stl tampa.stl pino.stl \
    --saida montagem.gif --mp4 --quadros 24 --fps 12
```

Medido (depois da correção do enquadramento): 1,94s de geração (24 quadros,
640×480, 428 faces no total), `ortho_scale_mm = 161,78`. GIF: 62.817 bytes. MP4
(h264, `-vf format=yuv420p`): confirmado com `ffmpeg -i` no arquivo gerado.

**Conferência visual obrigatória do teste**: 3 quadros extraídos do GIF com
`ffmpeg -i montagem.gif f_%03d.png` (início, meio e fim) e inspecionados por
leitura direta da imagem — não por o script ter terminado sem erro:

- quadro 1 (início): caixa com tampa encaixada em cima, pino quase invisível na
  base — condizente com a peça montada.
- quadro 13 (meio, pico da explosão): tampa claramente levantada e separada da
  caixa, com folga visível até a borda de cima do quadro (antes da correção do
  enquadramento, ela encostava/cortava ali); pino visivelmente deslocado para
  longe, para baixo e para o lado.
- quadro 24 (fim): idêntico ao quadro 1 — o loop fecha sem salto.

### Limites medidos

- **Não é render de apresentação.** Sem anti-serrilhado, sem sombra projetada,
  sem material de origem — sombreamento é só `0.35 + 0.65·max(0, normal·direção
  da câmera)`, achatado por face. Serve para **conferir o movimento**, não para
  aprovar a forma: isso continua sendo `render_de_conferencia.md`.
- **Custo cresce com (nº de triângulos) × (área de tela ocupada).** Nas peças de
  teste (428 faces, 640×480) ficou em frações de segundo por quadro. Malha de
  centenas de milhares de faces tem o mesmo problema já documentado em
  `render_de_conferencia.md` ("malha grande: recortar antes de renderizar") —
  decime ou recorte antes.
- **Backface culling assume sólido fechado com normal para fora.** Malha aberta,
  não-manifold ou com normal invertida pode faltar face na imagem. Isso é sintoma
  a investigar com `referencias/verificar.md`, não corrigido por este script.
- **A câmera é fixa e enquadra o PICO da explosão** (maior extensão possível),
  usando os cantos da caixa envolvente de cada peça — mesma lógica de
  `render_de_conferencia.md`. Se `--distancia` for muito maior que o necessário,
  a peça monta pequena no centro do quadro.
- **GIF funde o canal alfa sobre fundo branco** (formato GIF não tem alfa
  graduado); o MP4 herda o mesmo fundo. Os PNGs individuais de cada quadro (com
  `--manter-quadros`) continuam com fundo transparente de verdade.
- **MP4 é opcional e depende do `ffmpeg` do sistema** (padrão
  `C:\ffmpeg\bin\ffmpeg.exe`, com busca no PATH como alternativa). Se o ffmpeg
  falhar, o GIF sai normalmente e o motivo entra em `avisos` — a chamada não
  falha por causa do MP4.
