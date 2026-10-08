---
name: modelagem-3d
description: Use quando o pedido envolver projetar, criar, inspecionar, editar ou verificar geometria 3D — desde o conceito (peça nova para prender, travar ou apoiar em objeto existente, a partir de fotos e medidas) até criar peça paramétrica por código, abrir e inspecionar malha, orientar seleção no Blender, editar pelas letras apontadas na tela, deslocar região delimitada, preencher vão entre limites, conferir malha e junção, projetar folga e encaixe para imprimir, desfazer, salvar ou exportar. Inclui a página HTML de bancada (conceitos, cotas e fotos) do projeto 3D. TRIGGERS (PT) modelar, vamos modelar, projetar peça, criar peça, conceito, ideias de peça, prendedor, trava, clipe, presilha, suporte, gancho, encaixe em grade ou gaiola, fotos da peça, medidas com paquímetro, comparar conceitos, página de revisão, geometria, malha, STL, 3MF, Blender, letras na tela, selecionar face, rampa, preencher vão, região protegida, não-manifold, folga, exportar STL, desfazer no Blender, conferir malha. TRIGGERS (EN) design a part, concept, latch, clip, bracket, model this part, mesh, select face, fill gap, ramp, non-manifold, clearance, export STL, undo in Blender.
---

# Modelagem 3D — receitas para executar e conferir

Receitas com chamadas testadas, não doutrina. Use a referência da rota, execute o que está
escrito e **meça** o resultado. Nenhuma etapa aqui é concluída por aparência.

Versões do pacote e das bibliotecas: só em `INVENTARIO.json`, com o hash de cada arquivo.
Dentro do Blender, `bl_ferramentas.confere_versao("<versão do inventário>")` recusa versão
errada; no Python do hospedeiro o módulo não importa (`No module named 'bmesh'`): leia o
inventário.

## Conectar ao Blender, por agente

A sessão aberta do Blender atende no socket **127.0.0.1:9876** (complemento MCP do Blender).
Os scripts desta skill falam com ele por `scripts/mcp_blender.py` e servem a qualquer agente
com terminal: `python scripts/sessao_blender.py --diagnosticar` confere a conexão. Não escreva
outro cliente de socket.

**Claude Code.** As ferramentas `mcp__Blender__*` podem vir diferidas: carregue pelo
`ToolSearch` (`execute_blender_code`, `get_objects_summary`, `get_screenshot_of_area_as_image`,
`render_viewport_to_path`). Antes de editar, consulte `bpy.data.filepath`, `bpy.data.is_dirty`,
objeto ativo e modo. A rota por letras usa o socket pelos scripts.

**Codex.** Com ferramentas diferidas, procure em `ALL_TOOLS` por nome ou descrição contendo
`blender`; se houver `tool_search`, use a descoberta do ambiente. Não conclua que o MCP está
ausente só porque não aparece na lista inicial.

1. Use `get_scene_info` (nesta integração, `mcp__blender_community__get_scene_info`) com
   `user_prompt` igual ao pedido real do usuário. Confira a cena retornada.
2. Para o contexto antes de carregar ou editar, `execute_blender_code` com `bpy.data.filepath`,
   `bpy.data.is_dirty`, objeto ativo e modo; para acompanhar marcações,
   `get_viewport_screenshot`. Uma chamada descoberta pode ser executada por `functions.exec`
   usando `tools.<nome>`.
3. `cua.getState()` com `apps: []`, métodos nativos ausentes ou `Codex auth token is
   unavailable` são do conector de computador/navegador, não do MCP do Blender. Não oriente
   logout, reinício ou reinstalação do Blender por causa deles; relate qual conexão foi testada.

**Antigravity.** Não tem MCP do Blender configurado: use o socket pelos scripts
(`sessao_blender.py --diagnosticar`, `ponte_letras.py`, `verbos_letras.py`) e renderize por
`scripts/render_conferencia.py`.

Em qualquer agente: se as duas vias falharem, investigue complemento e servidor a partir do
erro concreto, preservando a cena. Conexão confirmada não é modelo carregado: depois da
operação, confira objetos, arquivo e vista antes de dizer que está pronto.

**Blender em processo separado** (sem a sessão aberta): `scripts/trabalho_blender.py`, que usa
`roda_blender.py`. O executável vem de `--blender`, `BLENDER_EXE` ou
`%LOCALAPPDATA%/modelagem-3d/ambiente.json` (`{"blender_exe": "..."}`); `roda_blender.py
--achar` mostra a resolução. Terminal vazio não é falha: o auxiliar confere o arquivo de
resultado. Detalhes em `referencias/mapa_de_ferramentas.md`.

**Mostrar ao operador.** `python scripts/mostrar_no_blender.py peca.stl [outra.stl]` abre o Blender se estiver
fechado, carrega na cena `TRABALHO_AGENTE` como `AG_<arquivo>` e, nas vezes seguintes, troca só a malha: depois da
primeira vez nunca muda a cena da janela nem a vista. Devolve o peso do volume sólido e o contato com a mesa
(`mapa_balanco.py`). Mostre a cada geometria nova, sem esperar o pedido: o operador aponta o defeito mais cedo do que
qualquer verificação. Para pedir medida, marque no modelo (`--marcar A=x,y,z B=x,y,z`, em mm) e pergunte "meça de A
até B", em vez de descrever o ponto em texto.

**Letras.** O complemento `blender/bancada_viva.py`, instalado por `scripts/instala_bancada_viva.py`, deixa as letras
A, B, C ligadas a cada abertura do Blender, com Overlays e anotação na superfície. Não é preciso instalar por sessão.

## Três regras que valem em todas as rotas

1. **Meça, não presuma.** Ferramenta que devolve "concluído" não prova efeito:
   `transform.translate` com seleção vazia devolve `{'CANCELLED'}` sem erro e nada muda; a
   união booleana devolve sucesso e deixa faces de área nula; a exportação de 3MF aceita
   malha com defeito de forma.
2. **Validade geométrica não é atendimento ao pedido.** Malha fechada pode ter a forma
   errada. São verificações separadas, e as duas aparecem no registro. A forma se confere
   pelas quatro vistas de `referencias/render_de_conferencia.md`, obrigatórias para toda
   geometria criada ou visivelmente alterada.
3. **Diga o alcance.** Amostragem prova os pontos amostrados; uma seção prova aquele plano.
   Conclusão sem alcance declarado não vale.

## Classificar o pedido antes de agir

**Continuidade na modelagem:** correções de medidas, marcações e esclarecimentos do
operador mantêm a tarefa e a autorização já dadas. Reconheça e continue a próxima etapa
autorizada; não encerre apenas prometendo agir. Pare se houver cancelamento, limite
obrigatório ou informação indispensável ausente. Uma consulta ou planejamento isolado
continua sendo consulta ou planejamento, sem autorização implícita para fabricar outra versão.

| Pergunta | Respostas | Consequência |
|---|---|---|
| **O que fazer** | criar, editar, reconstruir, parametrizar | escolhe a rota |
| **Em que** | sólido, superfície, malha, montagem | escolhe o contrato de geometria |
| **Para quê** | visualização, intercâmbio, montagem, impressão, usinagem | escolhe quais verificações são exigidas |

Não imponha reconstrução nem impressão a todo pedido. Se a finalidade não foi dita e muda o
que é exigido, **pergunte**. "Borda", "casca" ou "fechado" são declaração de topologia,
separada da representação: casca **aberta** (borda obrigatória) ou **fechada** sem sólido
(borda proibida). Não deduza uma da outra.

## Fase 0: conceito e página de bancada

Carregue esta skill já no **primeiro** pedido de peça ("vamos modelar um prendedor"), antes
de qualquer geometria: a fase de conceito faz parte da modelagem.

- **Gatilho por evento:** chegaram fotos do objeto onde a peça vai prender, ou há mais de
  um mecanismo possível → crie **na hora** a página de bancada (`revisao.html` do projeto),
  com `scripts/nova_pagina_bancada.py` (modelo escuro em `assets/pagina_bancada.html`).
  Não substitua por esboço solto no chat nem por outro HTML.
- A mesma página evolui: conceitos → cotas → revisões. Peça **nova** que prende em objeto
  medido por foto (grade, porta, gaveta) segue a mesma rota de "reconstruir ou adaptar".
- **Precedência:** em projeto 3D, este padrão vence a skill genérica `html-handoff` (que usa
  CDN e não tem cotas editáveis). Pedido de "HTML conforme a skill" num projeto 3D = esta página.
- Ferragem: pergunte o que o operador tem antes de propor mecanismo que dependa de mola,
  ímã ou rolamento; mecanismo que depende de o plástico dobrar precisa ser dito como tal.
- **Estado do projeto:** medida e resposta que o operador confirmou, decisão tomada e teto combinado vão para
  `ESTADO.md` na raiz do projeto no momento em que são confirmados. Depois do resumo automático da conversa, esse
  arquivo é a memória: não pergunte de novo o que está nele.
- **Teto antes de fatiar:** antes do primeiro fatiamento do conjunto, combine o teto de material e de tempo e grave no
  `ESTADO.md` (`Teto de material: 50 g`, `Teto de tempo: 3 h`). Passar do teto não se apresenta como pronto: mostre
  o número e pergunte.

## Pré-mortem antes de fechar peça para imprimir

Para reconstruir ou adaptar uma peça a partir de fotos e medidas do operador, use o
**HTML de validação de medidas** de `referencias/validacao_medidas_html.md` antes de fechar
as dimensões. É o padrão de revisão visual: cotas identificadas, fotos associadas,
interpretações editáveis e pendências explícitas. Aproveite a página existente nas revisões.

Antes de gerar ou entregar o arquivo, suponha: **"a peça saiu da mesa e não serviu. Por
quê?"**. Liste as causas concretas desta peça, e cada uma termina numa verificação rodada
antes da entrega. Causa sem verificação possível vai ao registro como "não verificado". Não
escreva a história da falha: a prova é medida.

| Causa provável | Verificação |
|---|---|
| não encaixa na peça existente | interface medida no arquivo ou na peça original, nunca redesenhada; folga pela tabela de `projetar_para_imprimir.md`, seção 1 |
| encaixa, mas não permite desmontar | conferir entrada completa e retirada, além de jogo; distinguir guia extensa de lingueta curta, `projetar_para_imprimir.md`, seção 1 |
| malha com defeito no fatiador | `verificar.md`, topologia, medida no **arquivo exportado**, não na malha da cena |
| furo fechado ou não passante | `verificar.md`, furo passante; conferir no G-code |
| flutua ou balanço sem suporte | `scripts/mapa_balanco.py`: contato com a mesa maior que zero |
| parede fina some ou fura | `scripts/piso_espessura.py`; `projetar_para_imprimir.md`, seção 4 |
| quebra entre camadas | orientar a flexão da garra no plano das camadas; avaliar construção separada em `projetar_para_imprimir.md`, seções 2 e 12 |
| forma errada, embora a malha seja válida | quatro vistas de `render_de_conferencia.md` |
| encaixe em objeto existente (pino, furo, rosca) falha na peça inteira | cupom de teste antes do conjunto: série de 3 a 5 tamanhos, letra gravada em cada um; o operador diz qual serviu |
| consumo ou tempo fora do que o operador aceita | teto no `ESTADO.md` antes do 1º fatiamento; o `fatiado-confere` alerta |
| peça modular sobrepõe a vizinha | montar o arranjo mais denso permitido (em cruz, com vizinhos nos quatro lados) e checar interferência, não só em linha |
| quebra no aperto | caminho da força: para cada parafuso, contra o que ele empurra e a espessura ali; parede fina empurrada por parafuso não passa |
| pediu "sem suporte" e o fatiador gera suporte | fatiar com suporte automático ligado ANTES de mostrar; conferir `; FEATURE: Support` no G-code |
| ajuste do projeto ignorado pelo fatiador | conferir no G-code (skill `bambu-a1`) |

Inclua as causas que só esta peça tem; a tabela é o piso, não a lista inteira.

## Editar no Blender: qual rota

| Situação | Rota |
|---|---|
| **O operador aponta na tela** (letras por clique, traços), uma ou várias malhas em edição | `referencias/edicao_por_letras.md` |
| Um objeto só, operação simples e delimitada (mover, expandir, extrudar, alinhar, preencher, arredondar), cena em mm | `referencias/chamadas_prontas.md` |
| Deformação delimitada com transição e região protegida (subir borda, patamar, preservar encontros) | `referencias/sessao_e_edicao_guiada.md` |

Nas letras, o protocolo é: **operador marca → agente repete em uma frase → operador diz
"aplica" → agente aplica e devolve a medida em uma linha**. Três regras de lá valem em
qualquer rota: pedido com "igual a" exige perguntar qual lado é o modelo; a correção tem o
tamanho do defeito (resíduo se apaga no lugar, nunca se reconstrói a peça); remover uma
feição é remover todas as ocorrências dela.

Não escreva outro script para mudar um número: use a operação pronta. Antes de mover
vértice, identifique alvo, transição e região protegida; acertar a altura do alvo não aprova
a parede vizinha.

## Onde está cada receita

| Pedido | Referência |
|---|---|
| peça gerada por código com feições nomeadas: identificar, acender, trocar a malha na cena | `referencias/edicao_por_letras.md`, identidade |
| criar ou parametrizar peça por código (manifold3d; build123d quando precisar de STEP) | `referencias/criar_e_parametrizar.md` |
| abrir, inspecionar, orientar seleção, ler o que está selecionado | `referencias/inspecionar_e_selecionar.md` |
| deslocar região delimitada; preencher vão entre dois limites | `referencias/editar_localizado.md` |
| combinar versões da mesma malha sem booleana; achar de qual malha um cupom saiu | `referencias/transplante_de_deslocamento.md` |
| conferir malha, junção, região preservada, dimensões, furo passante | `referencias/verificar.md` |
| **projetar para imprimir**: folgas calibradas, rosca, espessura mínima, rebaixo, ranhura, gravação, família de tamanhos, licença de peça de terceiros | `referencias/projetar_para_imprimir.md` |
| conceitos e validação das fotos e medidas com o operador antes de modelar (página de bancada) | `referencias/validacao_medidas_html.md`, `assets/pagina_bancada.html`, `scripts/nova_pagina_bancada.py` |
| **conferir a FORMA antes de entregar**: quatro vistas ortográficas | `referencias/render_de_conferencia.md` |
| visualizador 3D (.html) ou GIF/MP4 de montagem/vista explodida | `referencias/entregas_em_movimento.md` |
| desfazer, refazer, salvar, exportar, deixar retomável | `referencias/recuperar_salvar_exportar.md` |
| que ferramenta existe, o que exige, rodar o Blender em processo separado | `referencias/mapa_de_ferramentas.md` |
| registrar o trabalho para outro agente continuar | `referencias/registro_de_trabalho.md` |
| escrever o meu próprio script que roda dentro do Blender | `referencias/sessao_e_edicao_guiada.md`, seção 5 |

Carregue a referência da rota em uso; ela aponta para as outras quando precisa.

## Antes de editar qualquer coisa de outra pessoa

- Use o destino já combinado; pergunte só se faltar. **Não sobrescreva o arquivo de origem**
  para gravar uma prévia.
- Com sessão do Blender aberta e trabalho do usuário, não carregue outro arquivo nela nem a
  encerre: cena com alterações não salvas perde trabalho.
- Trabalhe no objeto atual se for a preferência do usuário; não duplique a peça a cada
  operação.
- Registre um ponto de recuperação antes de alterar, e confira a recuperação pelo
  **conteúdo**, não por a chamada ter retornado.

## O que este pacote não faz

Não reconstrói CAD a partir de malha, não seleciona por imagem, não decide folga fora das
condições calibradas (`referencias/projetar_para_imprimir.md`, seção 1), não mede silhueta e
não aprova peça para fabricação. Espessura de parede em malha: `scripts/piso_espessura.py`,
só nas condições registradas. Quando o pedido cair fora, diga o limite e o que seria preciso.

**Não verifica que um furo é passante.** `furo: APROVADA` mede duas seções, não a passagem.
Se a passagem importa, diga que ela não foi verificada e use a dedução de
`referencias/verificar.md` (euler, componentes e volume).

## Licença

**MIT**, texto em `LICENSE`. Pode usar, copiar, modificar, distribuir e vender, mantendo o
aviso de copyright e a licença. A doutrina das vistas de conferência deriva de
earthtojake/text-to-cad (MIT), com crédito em `referencias/render_de_conferencia.md`.
