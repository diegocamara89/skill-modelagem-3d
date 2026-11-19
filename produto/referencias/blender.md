# Blender — receitas preservadas para exceções

Leia somente quando a operação exigir Blender, conforme `SKILL.md`.
Operar por API/scripts; sem controle do desktop.

## Conectar ao Blender, por agente (rota de exceção)

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
(`mapa_balanco.py`). Só quando o trabalho já está no Blender (peça feita no FreeCAD se mostra na
janela do FreeCAD, não aqui), mostre a cada geometria nova, sem esperar o pedido: o operador aponta o defeito mais cedo do que
qualquer verificação. Em correções sucessivas, apresente a mudança aplicada e a medida antes de iniciar a próxima;
não acumule correções para mostrar apenas o render final. Exportar o objeto já visível não exige importar uma cópia:
o gancho reconhece os cabeçalhos `ponte_peca` e `poc_rasgos` dos exportadores da própria skill.
Para pedir medida, marque no modelo (`--marcar A=x,y,z B=x,y,z`, em mm) e pergunte "meça de A
até B", em vez de descrever o ponto em texto.

**Peça ao vivo no Blender (quando esta rota for necessária).** Escreva o gerador no contrato da ponte: `PARAMS = [("chave", "Rótulo",
padrão, mín, máx), ...]` (mm) e `def gera(**medidas) -> Manifold`; exponha como medida tudo que o operador pode querer
ajustar (larguras, folgas, diâmetro de cada furo). Mostre com `python scripts/mostrar_no_blender.py gera.py`: vira
`AG_<pasta>_<arquivo>` com painel na chave inglesa (Modificadores), onde o operador muda as medidas e a peça se refaz em
ms, grava arredondamento/chanfro em arestas selecionadas (refeitos a cada geração) e pega a face inteira (face lógica:
aresta viva = dobra > 30° ou troca de forma do gera.py fora do plano). Chamar de novo recarrega o código e mantém o
que o operador mexeu: **leia `medidas` e `acabamentos` do retorno antes de mudar qualquer coisa**. Erro no gera.py
mantém a peça anterior (`ERRO_NO_GERA`). Para imprimir, `--exportar peca.stl` grava a peça como está no Blender, com
acabamentos. O gancho `mostra-ao-gerar`, somente com `MODS_DIEGO_MOSTRAR_AUTOMATICO=1` na sessão, mostra todo `gera*.py` gravado em projeto 3D (blender/ponte_peca.py).

**Um Blender por sessão.** A porta vem de `scripts/porta_sessao.py` (registro em
`%LOCALAPPDATA%\mods-diego\blender-sessoes.json`); sem o Blender desta sessão, `mostrar_no_blender.py` abre outro já
na porta dela. Nunca use o Blender de outra sessão; `python scripts/porta_sessao.py --lista` mostra quem usa qual.

**Letras.** O complemento `blender/bancada_viva.py`, instalado por `scripts/instala_bancada_viva.py`, deixa as letras
A, B, C ligadas a cada abertura do Blender, com Overlays e anotação na superfície. Não é preciso instalar por sessão.

