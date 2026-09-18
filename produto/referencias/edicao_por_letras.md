# Edição por letras: o operador aponta, o agente repete, o operador diz "aplica"

Rota para o Blender **aberto**, com o operador na tela. Nasceu de duas sessões reais em
18/09/2026, uma peça gerada por código e uma montagem importada de STL, e cada regra abaixo
custou uma rodada quando não existia. Custo por leitura: 600–900 tokens; uma captura de
tela custa ~1 100 e quase nunca é necessária, porque as letras já dão a posição.

## O protocolo, em quatro passos

1. **Operador marca.** Clique = A, `Shift+clique` = B, C… A ordem do clique é a letra, desenhada
   no viewport. Traço com a ferramenta Anotar (`D` + arrastar) para "esta região" (laço) ou
   "daqui até ali" (linha).
2. **Agente lê e repete em uma frase**, com peça, posição e o que entendeu do pedido.
   `python scripts/ponte_letras.py letras` e `... tracos`. Sem captura de tela.
3. **Operador diz "aplica"** (ou corrige). Nada é alterado antes disso.
4. **Agente aplica e devolve o resultado medido em uma linha.** Verbos prontos:
   `python scripts/verbos_letras.py mover|extrudar|preencher|arredondar|desfazer` e
   `python scripts/ponte_letras.py apagar`. Cada verbo guarda `<objeto>.ANTES_VERBO`, mede
   borda e não-manifold antes e depois e **restaura sozinho se piorar**.

## Antes de tudo (o agente faz, não pede)

- `python scripts/mcp_blender.py --testa-conexao`.
- **Ligar Overlays** do viewport se estiverem desligados: sem eles a seleção laranja não aparece
  e o operador conclui que não marcou nada. Medido: foi a causa de "não vejo o que selecionei".
- `python scripts/ponte_letras.py instalar_letras`. Some ao fechar o Blender; reinstalar por sessão.
- Anotação grudada na superfície: `tool_settings.annotation_stroke_placement_view3d = "SURFACE"`
  na cena ativa (é por cena).
- Conferir `select_mouse` no keymap e dizer ao operador qual botão seleciona. Com o padrão,
  `Shift+botão direito` move o cursor 3D, não seleciona.

## O que dizer ao operador, em linguagem simples

- **Todas as peças em edição:** Modo de Objeto → `A` → `Tab`. `A` dentro do Edit Mode seleciona
  todas as faces e não cria letra nenhuma.
- **Limpar:** `Alt+A`. Zera as letras.
- **Canto → vértice (`1`); borda → aresta (`2`); superfície → face (`3`).** Clique em modo
  vértice sobre superfície lisa não pega nada.
- **Trocar de modo apaga as letras.** Para somar sem perder: `Shift+3`.
- Peças diferentes recebem a letra e o nome da peça embaixo; seleção por caixa entra no total
  sem letra.

## Regras de interpretação (todas medidas em sessão)

- **Letras dizem onde, não quem é o modelo.** Pedido com "igual a", "simétrico a", "continua
  como": **perguntar qual lado é o modelo antes de medir**. Errado uma vez: inverti o sentido.
- **Correção do tamanho do defeito.** Resto, lasca, rebarba apontada → `apagar` no lugar, em
  segundos. Nunca reconstruir a peça por booleana para tirar um resíduo. Reconstruir é para
  mudar forma.
- **Remover feição = remover todas as ocorrências.** "Tira a borda" valia para duas laterais
  E para o fim da peça; só tirei onde havia letra. Varrer a peça pela assinatura da feição
  (ex.: topo em Z=4,2) e listar antes de cortar.
- **Simetria pode exigir acrescentar.** Espelhar um chanfro falhou porque o outro lado tinha
  um recorte de origem: não havia o que cortar. Medir os dois lados antes e escolher união ou
  diferença.
- **Ler a posição real de cada face antes de espelhar.** Parede em X=65 e chanfro em 64,8 de um
  lado; parede em 3,0 e chanfro em 3,2 do outro. Enchimento até 3,2 saltou 0,2 mm da parede.
- **Caixa de união só no pé da feição.** Tampa mais larga que a parede criou saliências fora da
  peça. Conferir X/Y/Z mín e máx da peça antes e depois de toda união.
- **Sobrecorte "invisível na impressão" é visível na tela.** 0,05 mm dentro da parede virou
  degrau que o operador apontou. Booleana coplanar com manifold3d aguentou: usar a face exata.
- **Peça sem gerador não tem nome de feição:** responder com peça + posição, não com "fora".
  Peça com gerador: rotular a peça INTEIRA, senão o clique fora da feição testada responde
  "fora" e não ajuda.
- **Encaixe conformado:** medir a folga padrão da peça (mediana das distâncias onde as partes
  se aproximam no conjunto montado) e desenhar a calha como a feição do outro lado dilatada
  por essa folga. Ajustar até a folga mínima medida bater; ajuste de círculo por mínimos
  quadrados errou o centro numa saliência em U.
- **Conjunto montado = transformação real dos objetos** da configuração montada. Medir encaixes
  nesse referencial, não no aberto.
- **trimesh `signed_distance`: positivo = DENTRO.** Interferência é `d > 0`; folga é `|d|` com
  `d < 0`. Lido ao contrário, "vi" interferência onde não havia.
- Folga de peça articulada impressa montada (0,3–0,4 mm) vira "suporte" no fatiador: resolver
  no fatiador (bloqueador, suporte só na mesa), não na geometria.
- Marcas podem estar em outro objeto do que se supõe: ler `objeto` de cada letra antes de
  converter coordenadas para o referencial local.

## Divisão de trabalho acordada com o operador

Ajuste de **mouse** (puxar vértice, apagar lasca, alisar borda) o operador faz mais rápido
sozinho no Blender. Ajuste de **régua** (espelhar exato, refazer com medida, provar que o resto
não mudou, regenerar, fatiar, conferir encaixe) é do agente. Não puxar para o agente o que é de
mouse.

## Identidade para peça gerada por código

O gerador grava, junto do STL, `<nome>.feicoes.json`: para cada feição, nome e a geometria do
cortador (origem, eixos, extensão). `ponte_letras.py carregar --objeto NOME --stl --feicoes`
cria o objeto na cena de trabalho, rotula cada face com o atributo inteiro `rasgo` e cria um
grupo de vértices por feição (`scripts/feicoes.py` faz a classificação). Daí:
`identificar` responde a feição do clique ou **recusa** (fora de feição / ambíguo, limiar 80%);
`expandir` acende a feição inteira em laranja; `atualizar` troca só a malha do objeto na cena,
guardando a anterior. Peça importada sem gerador não tem nome: o caminho é letra + posição.

## Prévia, aplicação e arquivo do operador

- Prévia: objeto `*_PROPOSTA` sobre o original, original oculto. "Aplica" troca `obj.data` dos
  originais, anterior fica como `<objeto>.ANTES_<etapa>` com fake user. "Volta" reexibe.
- Criar cena/objeto marca `is_dirty`: se o operador salvar, a cena de trabalho entra no arquivo
  dele. Avisar antes e oferecer remover ao final.
- `salvar_copia` usa `bpy.data.libraries.write(caminho, {cena})`: grava só a cena de trabalho.
  Nunca `save_mainfile` na sessão do operador.
- Exportar STL do objeto e **reabrir o exportado** para medir; malha no Blender não é o arquivo.

## Limites conhecidos

- Os comandos prontos de um objeto (`mover_selecao.py` etc.) exigem um só objeto em edição,
  malha não compartilhada e escala da cena em mm. No fluxo "A + Tab em tudo" eles recusam; por
  isso existem os `verbos_letras`, que aceitam tudo em edição e cena em metros (assumem
  1 unidade = 1 mm quando a peça tem dezenas de unidades, e dizem isso).
- `bpy.ops` fora do contexto de janela falha pelo MCP; tudo aqui é feito em `bmesh`/dados.
- Testado em Blender 5.2 LTS, cubo sintético (`mover` +2 → altura 22,0 e volume 8800,0;
  `extrudar` 2 → largura 22,0; `preencher` fecha furo de 4 arestas; `arredondar` 4 quinas;
  `apagar` lasca 0,4×2×3 → volume 8000,0 exato) e nas duas peças reais.
