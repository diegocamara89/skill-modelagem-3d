# Edição por letras: o operador aponta, o agente repete, o operador diz "aplica"

Rota para o Blender **aberto**, com o operador na tela, em uma ou várias peças ao mesmo
tempo. Aqui a cena fica em **metros** (os verbos assumem 1 unidade = 1 mm quando a peça tem
dezenas de unidades, e dizem isso). As chamadas prontas de um objeto
(`chamadas_prontas.md`) exigem a cena em **mm** e um só objeto em edição: se a cena está em
metros ou há vários objetos em edição, é esta rota que vale.

## O protocolo, em quatro passos

1. **Operador marca.** Clique = A, `Shift+clique` = B, C… A ordem do clique é a letra,
   desenhada no viewport. Traço com a ferramenta Anotar (`D` + arrastar) para "esta região"
   (laço) ou "daqui até ali" (linha).
2. **Agente lê e repete em uma frase**, com peça, posição e o que entendeu do pedido:
   `python scripts/ponte_letras.py letras` e `... tracos`. **A captura de tela é último
   recurso, não rotina:** uma leitura estruturada custa 600–900 tokens, uma captura ~1 100.
   Se a leitura vier vazia, o primeiro diagnóstico é `estado` (objeto e modo), não uma
   imagem (ver "Leitura vazia não é ausência de marca").
3. **Operador diz "aplica"** (ou corrige). Nada é alterado antes disso.
4. **Agente aplica e devolve o resultado medido em uma linha.** Verbos prontos:
   `python scripts/verbos_letras.py mover|extrudar|preencher|arredondar|desfazer` e
   `python scripts/ponte_letras.py apagar`. Cada verbo guarda `<objeto>.ANTES_VERBO`, mede
   borda e não-manifold antes e depois e **restaura sozinho se piorar**.

## Antes de tudo (o agente faz, não pede)

- `python scripts/mcp_blender.py --testa-conexao`.
- Letras, Overlays e anotação na superfície vêm do complemento `bancada_viva`
  (`blender/bancada_viva.py`), ligado nas preferências e carregado a cada abertura do Blender. Se faltarem
  (`driver_namespace` sem `poc_letras_handler`), rodar `python scripts/instala_bancada_viva.py`.
- A captura do MCP (`ponte_letras.py captura`) desenha a cena por fora da janela e **não mostra as letras**. Para
  ver as letras numa imagem, capture a janela do Blender pelo sistema (no Windows, `PrintWindow` com a flag 2).
- Conferir `select_mouse` no keymap e dizer ao operador qual botão seleciona. Com o padrão,
  `Shift+botão direito` move o cursor 3D, não seleciona.

## O que dizer ao operador, em linguagem simples

- **Todas as peças em edição:** Modo de Objeto → `A` → `Tab`. `A` dentro do Edit Mode
  seleciona todas as faces e não cria letra nenhuma.
- **Limpar:** `Alt+A`. Zera as letras.
- **Canto → vértice (`1`); borda → aresta (`2`); superfície → face (`3`).** Clique em modo
  vértice sobre superfície lisa não pega nada.
- **Trocar de modo apaga as letras.** Para somar sem perder: `Shift+3`.
- Peças diferentes recebem a letra e o nome da peça embaixo; seleção por caixa entra no total
  sem letra.

## Leitura vazia não é ausência de marca

`letras`/`tracos` vazios não significam que o operador não marcou. Não pedir que ele escreva
letras à mão com a ferramenta Anotar: isso é traço geométrico, sem significado de texto para
o agente. Diagnosticar por leitura estruturada, sem print:

1. Rodar `estado` (objeto ativo, modo). Contorno laranja do objeto INTEIRO na tela do
   operador é seleção de **Modo de Objeto**; `letras`/`tracos` só existem com Edit Mode e
   elemento (vértice/aresta/face) selecionado. Se `estado` mostra `OBJECT`, dizer em uma
   frase ("você está em Modo de Objeto; Tab para entrar em edição e clicar na superfície"),
   sem propor outro protocolo.
2. Se o operador insiste que marcou e a leitura continua vazia em Edit Mode, aí sim uma
   captura é o próximo passo. Se ela mostrar caracteres desenhados à mão (A, B, C…), não ler
   a letra por OCR visual: explicar o protocolo real (clique em ordem, a letra aparece
   sozinha; ou traço de laço/linha apontando a região).
3. Se a captura mostra seleção de face real e a leitura ainda vem vazia, é objeto errado ou
   bug: não adivinhar, conferir `estado` de novo antes de repetir a leitura.

A captura, quando usada, **confirma** a leitura estruturada (peça, posição, contagem) e
nunca a substitui. Nunca declarar "A é a superfície tal" só porque pareceu isso numa imagem:
reler com `letras`/`tracos`/`identificar` e só então repetir o entendimento ao operador. A
mesma regra que proíbe aprovar forma só pelo render (`render_de_conferencia.md`) vale aqui.

## Regras de interpretação

- **Letras dizem onde, não quem é o modelo.** Pedido com "igual a", "simétrico a", "continua
  como": **perguntar qual lado é o modelo antes de medir**; senão o sentido pode sair
  invertido.
- **Correção do tamanho do defeito.** Resto, lasca, rebarba apontada → `apagar` no lugar, em
  segundos. Nunca reconstruir a peça por booleana para tirar um resíduo; reconstruir é para
  mudar forma.
- **Remover feição = remover todas as ocorrências.** "Tira a borda" vale para todo lugar onde
  a feição existe, não só onde há letra. Varrer a peça pela assinatura da feição (por
  exemplo, a cota do topo) e listar antes de cortar.
- **Simetria pode exigir acrescentar.** Espelhar um chanfro falha se o outro lado tem um
  recorte de origem: não há o que cortar. Medir os dois lados antes e escolher união ou
  diferença.
- **Ler a posição real de cada face antes de espelhar.** Os dois lados podem ter cotas
  diferentes entre parede e chanfro; preencher até a cota do outro lado pode saltar da
  parede.
- **Caixa de união só no pé da feição.** Uma tampa mais larga que a parede cria saliências
  fora da peça. Conferir X/Y/Z mín e máx da peça antes e depois de toda união.
- **Sobrecorte "invisível na impressão" é visível na tela.** Um recuo de centésimos de mm
  dentro da parede vira degrau que o operador aponta. Booleana coplanar com manifold3d
  aguenta: usar a face exata.
- **Marcas podem estar em outro objeto do que se supõe:** ler `objeto` de cada letra antes
  de converter coordenadas para o referencial local.

## Divisão de trabalho acordada com o operador

Ajuste de **mouse** (puxar vértice, apagar lasca, alisar borda) o operador faz mais rápido
sozinho no Blender. Ajuste de **régua** (espelhar exato, refazer com medida, provar que o
resto não mudou, regenerar, fatiar, conferir encaixe) é do agente. Não puxar para o agente o
que é de mouse.

## Identidade por gerador (`feicoes.json`)

Vale para peça gerada por código. O gerador grava, junto do STL, `<nome>.feicoes.json`: para
cada feição, nome e a geometria do cortador (origem, eixos, extensão).
`ponte_letras.py carregar --objeto NOME --stl --feicoes` cria o objeto na cena de trabalho,
rotula cada face com o atributo inteiro `rasgo` e cria um grupo de vértices por feição
(`scripts/feicoes.py` faz a classificação). Daí:

- `identificar` responde a feição do clique ou **recusa** (fora de feição / ambíguo, limiar
  80%);
- `expandir` acende a feição inteira em laranja;
- `atualizar` troca só a malha do objeto na cena, guardando a anterior.

Rotule a peça INTEIRA: senão o clique fora da feição testada responde "fora" e não ajuda.
Peça importada sem gerador não tem nome de feição: responder com peça + posição, não com
"fora".

## Prévia, aplicação e arquivo do operador

- Prévia: objeto `*_PROPOSTA` sobre o original, original oculto. "Aplica" troca `obj.data`
  dos originais; o anterior fica como `<objeto>.ANTES_<etapa>` com fake user. "Volta"
  reexibe.
- Criar cena/objeto marca `is_dirty`: se o operador salvar, a cena de trabalho entra no
  arquivo dele. Avisar antes e oferecer remover ao final.
- `salvar_copia` usa `bpy.data.libraries.write(caminho, {cena})`: grava só a cena de
  trabalho. Nunca `save_mainfile` na sessão do operador.
- Exportar STL do objeto e **reabrir o exportado** para medir; malha no Blender não é o
  arquivo.

## Limites conhecidos

- Os comandos prontos de um objeto (`chamadas_prontas.md`) recusam no fluxo "A + Tab em
  tudo"; por isso existem os `verbos_letras`, que aceitam tudo em edição.
- `bpy.ops` fora do contexto de janela falha pelo MCP; tudo aqui é feito em `bmesh`/dados.
