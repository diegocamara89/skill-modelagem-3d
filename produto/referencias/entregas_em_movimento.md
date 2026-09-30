# Entregas em movimento: visualizador interativo e vista explodida

Rota para entregar uma peça ou um conjunto de forma que o operador possa **inspecionar
sozinho** (visualizador 3D) ou **ver como as peças se encaixam** (GIF/MP4 de
montagem/explosão). As duas são **complemento**, nunca substituto da conferência
obrigatória: quatro vistas ortográficas, em `render_de_conferencia.md`, que também diz o que
imagem não prova. Dimensão, folga, parede e passagem de furo continuam com os verificadores
de `verificar.md`.

## Quando usar cada uma

| Situação | Use |
|---|---|
| o operador precisa girar, aproximar e apontar um detalhe com o mouse, sem depender de você estar presente | `scripts/visualizador_3d.py` |
| o que importa é mostrar COMO as peças se separam/encaixam (tampa, pino, encaixe) | `scripts/animacao_montagem.py` |
| conferir se a FORMA está certa antes de entregar (obrigatório, sempre) | `render_de_conferencia.md` |
| medir dimensão, parede, folga, passagem de furo | `verificar.md` |

Os dois scripts mostram a geometria **como está**, no estado em que os arquivos de entrada
chegaram: não reconstroem nem corrigem nada. Ambos rodam no **Python do hospedeiro**, sem
Blender.

## Conferência visual do HTML: screenshot headless

**Gerar o HTML e não abrir não é conferência.** Validar só a estrutura (round-trip do GLB,
contagem de bytes, ausência de CDN) não pega defeito visual. Renderize um screenshot de
verdade, **leia o PNG** e **reveja o screenshot depois de CADA correção**: corrigir o que se
vê não esgota o que ainda não foi olhado de novo. Comando (Edge, headless, sem GPU real;
`swiftshader` é o rasterizador de software):

```
copy visualizador.html %TEMP%\vis_teste.html   REM caminho curto: o do scratchpad é longo demais para o Edge

"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" ^
  --headless=new --disable-gpu --enable-unsafe-swiftshader --use-angle=swiftshader ^
  --window-size=1100,750 --virtual-time-budget=8000 ^
  --screenshot=%TEMP%\vis_teste_shot.png ^
  file:///C:/Users/.../vis_teste.html
```

`--virtual-time-budget` dá tempo do three.js montar a cena antes do screenshot; sem ele a
imagem pode sair em branco. Para confirmar cor exata ou ocupação de quadro, amostre pixels
com `PIL.Image.getpixel` (por exemplo, a caixa envolvente das cores da peça, sem a grade
cinza e o fundo branco, dividida pela largura/altura da imagem).

## Opção 1 — visualizador 3D interativo (`scripts/visualizador_3d.py`)

Gera **um** `.html` que o operador abre por duplo clique no Windows e navega com o mouse
(arrastar gira, roda aproxima, botão direito translada).

`trimesh.viewer.notebook.scene_to_html()` embute a malha inteira em GLB (base64) **e** o
próprio three.js no mesmo arquivo: não há `<script src=...>` nem chamada de rede (o relatório
traz `depende_de_cdn`).

### O que o script acrescenta ao template do trimesh, e por quê

Cada item abaixo corrige um defeito visual que a validação de estrutura não pega:

1. **Câmera isométrica explícita** (`_camera_isometrica`). A câmera automática do trimesh
   olha de cima, reto para baixo. O script monta a rotação (colunas = direita/cima/direção,
   mesma convenção de `render_de_conferencia.md`) e usa `camera.look_at(pontos, rotation=...,
   pad=...)`, com FOV estreito (28°) e `pad=1,15`, para a peça ocupar cerca de 70% do
   quadro. A direção padrão é assimétrica de propósito, `(1.25, -0.75, 0.85)`: com
   `|dx| = |dy|`, duas faces ortogonais de uma peça alinhada aos eixos saem com o mesmo
   brilho.
2. **Enquadramento só pelas peças** (`cantos_pecas`, capturados antes de acrescentar grade e
   eixos). A grade se estende além da peça por design (é um chão de referência) e pode sair
   parcialmente do quadro; isso não é a peça cortada. Enquadrar grade e eixos junto
   encolhe a peça.
3. **Material sólido fosco explícito** (`_material_solido`: `PBRMaterial(metallicFactor=0.0,
   roughnessFactor=0.9)`), cor distinta por arquivo de entrada (paleta fixa de 10, cicla).
   Colorir só por `ColorVisuals(face_colors=...)` grava um material sem
   `metallicFactor`/`roughnessFactor`, e o glTF assume por omissão `metallicFactor=1.0`
   (metal liso, sem componente difusa): só a luz ambiente aparece e a peça sai sem
   gradiente. Soma-se uma **luz ambiente** extra (`AmbientLight` a 0,45, por substituição de
   texto) para a face de costas para a luz direcional não sair chapada.
4. **Eixos coloridos como cilindro sólido** (X vermelho, Y verde, Z azul; comprimento de 18%
   da diagonal), nascendo num canto empurrado para **fora** da caixa envolvente por uma casa
   de grade. `Path3D` com `.colors` não propaga cor pelo exportador GLB (viram linhas cinza),
   e um eixo nascido dentro da caixa fica oculto dentro do sólido.
5. **Conversão Z-up → Y-up** (`_converter_z_up_para_y_up`) como ÚLTIMO passo antes de
   exportar: gira a cena inteira (peças, grade, eixos **e** a câmera) −90° em X via
   `Scene.apply_transform` (só matriz de nó, nenhum vértice muda). Peça de engenharia é
   Z-up; o `TrackballControls` do three.js usa Y como "para cima"; sem a conversão a peça
   aparece deitada. Toda a matemática em mm anterior roda em Z-up normal.
6. **Legenda** (nome + amostra de cor por peça) injetada como `<div>` HTML/CSS no canto
   superior esquerdo, só com **2 ou mais peças**. Cada parte do texto é escapada
   individualmente com `html.escape` e o separador é o caractere `·`; juntar com a entidade
   `&middot;` e escapar depois mostra `&amp;middot;` como texto cru.

A **grade** discreta (`Path3D`, cinza) fica no plano XY, na cota Z mínima do conjunto, com
espaçamento redondo (1-2-5 × 10ⁿ) escolhido pela diagonal da caixa envolvente. Grade e eixos
são geometria real inserida na cena antes do export, por isso viram parte do GLB embutido.

### Chamada

```
python scripts/visualizador_3d.py caixa.stl tampa.stl pino.stl \
    --saida visualizador.html --titulo "Conjunto de teste: caixa + tampa + pino"
```

O relatório traz `bytes`, `segundos`, `pecas` (nome, cor, vértices, faces),
`grade_e_eixos` (espaçamento, comprimento, raio e origem dos eixos), `depende_de_cdn` e
`legenda_visivel`.

### Limites

- **Escala real, sem normalização.** A grade usa a MESMA unidade numérica dos vértices do
  arquivo de entrada. Peças em unidades diferentes saem nessa mistura: confira a origem antes
  de visualizar em conjunto.
- **Não preserva textura/material de origem.** O GLB embutido vira cor sólida por peça.
- **Arquivo com vários corpos (3MF/GLB de montagem) vira UMA peça:** o script concatena
  (`Scene.dump(concatenate=True)`) tudo o que está no mesmo arquivo antes de colorir. Para
  cor por corpo, separe em arquivos antes de chamar.
- **Tamanho cresce com a malha:** o GLB vai em base64 dentro do HTML (+33% sobre o binário).
  Não há decimação aqui; para malha muito grande, decime antes.
- **Legenda e luz ambiente entram por substituição de texto** em marcadores do template atual
  do trimesh (`<div id="container"></div>` e a linha que cria o `tracklight`). Se a
  biblioteca mudar esses marcadores, a falha é **visível e inofensiva**: HTML sem legenda ou
  sem a luz extra, nunca corrompido.
- **Z-up → Y-up assume que Z é "para cima" no arquivo de entrada** (convenção de
  STL/3MF/engenharia/impressão 3D). Arquivo já em Y-up (comum em pipelines de jogos) sairia
  girado 90° na direção errada; não há detecção automática.
- **Câmera é perspectiva, não ortográfica.** O FOV estreito só *parece* isométrico, com
  alguma distorção perto das bordas: serve para inspeção visual, não para medir ângulo ou
  paralelismo (isso é `render_de_conferencia.md`).

## Opção 2 — animação de montagem / vista explodida (`scripts/animacao_montagem.py`)

Recebe 2+ arquivos de malha **já na pose montada** (as coordenadas de cada arquivo SÃO a
posição final) e gera um `.gif` (com `--mp4`, também um `.mp4` via ffmpeg) em que as peças
se afastam da posição montada e voltam a encaixar, em loop.

### Por que não o Blender

A animação é só **translação rígida** de corpos já válidos: nenhuma booleana, nenhuma
mudança de topologia. Um render de qualidade resolveria um problema que não existe aqui, ao
custo de tudo o que `scripts/roda_blender.py` documenta (launcher da Microsoft Store, stdout
vazio, código de saída que não prova sucesso, importador de 3MF ausente em
`--factory-startup`). Um rasterizador numpy pequeno, com z-buffer **por pixel**, resolve.

`Poly3DCollection` do matplotlib ordena por **coleção inteira**, não por triângulo: uma peça
da frente pode ficar atrás de uma de trás só por ter sido adicionada depois. Este script
projeta cada triângulo (direção = do centro da cena PARA a câmera, como em
`render_de_conferencia.md`), rasteriza com teste de profundidade por pixel e usa *backface
culling* (só desenha face cuja normal aponta para a câmera; válido porque a entrada é sólido
fechado e só recebe translação).

### Regra de explosão

Mover toda peça pela MESMA distância, cada uma na sua direção (centro do conjunto → centro da
peça), **não** separa peças que saem do mesmo lado: caixa e tampa, centradas em X/Y e do
mesmo lado do centro em Z, recebem o mesmo vetor e só "flutuam" juntas. Por isso o
deslocamento de cada peça é escalado pela **proporção da sua própria distância ao centro do
conjunto** (ou, com eixo fixo, da sua própria projeção nesse eixo): a peça mais afastada
recebe a `--distancia` cheia (padrão: metade da diagonal do conjunto) e as mais próximas uma
fração, o que separa peças vizinhas entre si. Duas regras de direção, exclusivas:

- **Padrão** (sem `--direcao-explosao`): cada peça vai do centro do CONJUNTO para o centro da
  PRÓPRIA caixa envolvente, escalada pela proporção acima.
- **`--direcao-explosao DX DY DZ`**: eixo único para todas; cada peça se afasta ao longo
  dele, para o lado em que já está (sinal da projeção), escalada pela proporção da própria
  projeção. Útil para montagem empilhada (por exemplo, explodir só em Z).

Peça cujo centro coincide com o centro do conjunto (ou cuja projeção no eixo fixo é zero)
**não se move**, e isso entra no relatório em `avisos`.

### Enquadramento no pico

A câmera é fixa e enquadra o **pico** da explosão. A extensão projetada de uma caixa
envolvente, numa câmera cujos eixos direita/cima não estão alinhados com X/Y/Z (toda vista
isométrica), só é garantida pelos **8 cantos**; os 2 cantos (mínimo e máximo) que o trimesh
devolve em `bounds` subestimam a extensão nos outros 6. O script gera as 8 combinações
`(x_min/x_max, y_min/y_max, z_min/z_max)` por peça, no estado de pico, antes de calcular a
escala da câmera (mesma lógica de `Scene.bounds_corners` no visualizador e de
`obj.bound_box` em `render_de_conferencia.md`). Vale para as duas opções desta página:
caixa envolvente em vista angulada nunca se resume a 2 cantos.

### Envelope do movimento

`(1 − cos(2π·i/(quadros−1))) / 2`: 0 no primeiro quadro (montada), 1 no meio (pico), 0 no
último (montada de novo). Derivada zero nas pontas: sem solavanco no loop do GIF.

### Chamada

```
python scripts/animacao_montagem.py caixa.stl tampa.stl pino.stl \
    --saida montagem.gif --mp4 --quadros 24 --fps 12
```

Conferência visual: extraia 3 quadros do GIF (início, meio, fim) com
`ffmpeg -i montagem.gif f_%03d.png` e **leia a imagem**. No início, peça montada; no meio,
peças separadas com folga até a borda do quadro; o último quadro idêntico ao primeiro (o
loop fecha sem salto). O script ter terminado sem erro não é conferência.

### Limites

- **Não é render de apresentação.** Sem anti-serrilhado, sombra projetada nem material de
  origem; sombreamento é só `0.35 + 0.65·max(0, normal·direção da câmera)`, achatado por
  face. Serve para **conferir o movimento**, não para aprovar a forma.
- **Custo cresce com (nº de triângulos) × (área de tela ocupada).** Malha de centenas de
  milhares de faces tem o problema de "Malha grande: recortar antes de renderizar"
  (`render_de_conferencia.md`): decime ou recorte antes.
- **Backface culling assume sólido fechado com normal para fora.** Malha aberta,
  não-manifold ou com normal invertida pode faltar face na imagem; isso é sintoma a
  investigar com `verificar.md`, não corrigido por este script.
- **Com `--distancia` muito maior que o necessário**, a peça monta pequena no centro do
  quadro (a câmera enquadra o pico).
- **GIF funde o alfa sobre fundo branco** (o formato não tem alfa graduado); o MP4 herda o
  fundo. Os PNGs de cada quadro (com `--manter-quadros`) continuam transparentes.
- **MP4 é opcional e depende do `ffmpeg` do sistema** (padrão `C:\ffmpeg\bin\ffmpeg.exe`,
  com busca no PATH como alternativa). Se o ffmpeg falhar, o GIF sai normalmente e o motivo
  entra em `avisos`.
