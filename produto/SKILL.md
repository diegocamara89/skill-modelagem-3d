---
name: modelagem-3d
description: Use quando o pedido envolver criar, inspecionar, editar ou verificar geometria 3D — criar peça paramétrica por código, abrir e inspecionar malha, orientar seleção no Blender, editar pelas letras apontadas na tela, deslocar região delimitada, preencher vão entre limites, conferir malha e junção, projetar folga e encaixe para imprimir, desfazer, salvar ou exportar. TRIGGERS (PT) modelar, criar peça, geometria, malha, STL, 3MF, Blender, letras na tela, selecionar face, rampa, preencher vão, região protegida, não-manifold, folga, encaixe, exportar STL, desfazer no Blender, conferir malha. TRIGGERS (EN) model this part, mesh, select face, fill gap, ramp, non-manifold, clearance, export STL, undo in Blender.
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
| validar a interpretação das fotos e medidas com o operador antes de modelar | `referencias/validacao_medidas_html.md` |
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
