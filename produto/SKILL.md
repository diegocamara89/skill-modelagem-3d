---
name: modelagem-3d
description: Projetar, reconstruir, editar e verificar peças 3D a partir de fotos, medidas ou malhas. FreeCAD por código como prioridade, com a bancada de marcas (o operador clica na peça e vê A, B, C…, com notas); Blender para ajuste orgânico de malha e apresentação; SolidCraft só a pedido. Preserva receitas, versões e verificações de encaixe e exportação. Use desde o primeiro pedido de peça 3D, inclusive só conceito ("vamos modelar...").
---

# Modelagem 3D — receitas para executar e conferir

Receitas com chamadas testadas, não doutrina. Use a referência da rota, execute o que está
escrito e **meça** o resultado. Nenhuma etapa aqui é concluída por aparência.

Versões do pacote e das bibliotecas: só em `INVENTARIO.json`, com o hash de cada arquivo.
Dentro do Blender, `bl_ferramentas.confere_versao("<versão do inventário>")` recusa versão
errada; no Python do hospedeiro o módulo não importa (`No module named 'bmesh'`): leia o
inventário.

## Padrão: FreeCAD por código, com a bancada de marcas

Peças novas, edição CAD e **revisão com o operador** acontecem no **FreeCAD**, numa janela só
(decisão do dono em 10/11/2026; antes era SolidCraft). Leia `referencias/freecad.md`. Motivo: o
operador precisa marcar vários pontos na peça, ver cada marca e o agente ler sem print; só o FreeCAD
deixou fazer isso dentro do próprio CAD.

- **Operador vai apontar algo na peça** (falha, local de furo, região): abra a bancada com
  `python scripts/abrir_bancada_freecad.py <projeto> [--documento X.FCStd] [--importar a.stl b.step]`
  e leia `<projeto>/marcas.json`. Nunca peça print, nunca mande marcar em outro programa.
- **Cálculo sem janela:** `FreeCADCmd.exe script.py`.
- A execução e a verificação não dependem de automação de mouse, teclado, menus ou capturas do
  desktop: **não usar Computer Use**.

Mantenha parâmetros e operações editáveis na fonte e no `.FCStd`. Preserve originais aprovados;
confira o estado do documento, geometria e exportações. Mostre alterações significativas pela
janela/API ou imagens geradas pelo CAD; não acumule toda a modelagem sem retorno ao operador.
Capturas internas são artefatos de conferência, não controle de computador; gere em lote,
sem repetir por rotina. Exportar STL ou gravar um gerador não deve abrir Blender automaticamente.

## Quando mudar de ferramenta

- **SolidCraft:** só quando o dono pedir (ex.: ver a árvore de operações sendo construída). Não tem
  marcação por letras: se o operador precisar apontar na peça, volte ao FreeCAD. Leia
  `referencias/solidcraft.md`. Fórmulas de vigas, seções e estimativas em Python existentes
  continuam disponíveis com qualquer CAD; não são FEM (FEM: `referencias/freecad.md`, seção 5).
- **Blender:** edição orgânica/local de malha, scripts que dependem de `bpy`/`bmesh`, render de
  apresentação ou preservação da fonte Blender já editada pelo operador. Leia `referencias/blender.md`
  e a referência da operação. Malha triangulada por si só não obriga Blender: FreeCAD possui
  ferramentas de malha e a bancada marca em malha e em sólido. As letras do Blender
  (`edicao_por_letras.md`) valem só quando o trabalho já está no Blender.
- **Receitas externas:** rosca, pintura3MF, NumPy/manifold3d e verificadores validados continuam
  em uso, sem reescrita só para torná-los nativos do CAD. Não carregar as três rotas por rotina.

Antes de sair do FreeCAD, indique a necessidade concreta e o que será transferido. Uma falha
não autoriza reconstruir tudo em outro programa: investigue, preserve a versão válida e escolha
a menor intervenção. Não converter projeto aprovado só para cumprir a prioridade do CAD.
**Trocar de ferramenta padrão exige testar o fluxo inteiro do operador (marcar, ver, corrigir,
o agente ler), não só criar e exportar:** a troca para o SolidCraft em 07/11/2026 falhou por isso.
Para MakerWorld parametrizável, preparar e testar SCAD explícito; STL/STEP/CSG não provam
preservação do gerador. Nenhum conversor geral entre estes CADs e SCAD está comprovado.

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

**Na reconstrução por medidas e fotos:** nomeie os dois contatos, eixo e tipo de distância antes de aplicar a
cota (face interna/externa, projeção ou percurso). Espessura de parede inclinada é a distância perpendicular
entre suas faces, não a altura vertical. Em cada correção, confira também as cotas confirmadas que precisam
permanecer fixas; uma consequência em outra dimensão deve ser mostrada, não escondida como compensação.
Detalhes e estimativas por foto: `referencias/validacao_medidas_html.md`.

**Versão aprovada:** edição manual não atualiza o gerador. Registre qual é a fonte vigente; antes de reutilizar
um gerador antigo, incorpore as correções e compare sua saída com o artefato aprovado, sem sobrescrevê-lo.
Não imponha reconstrução paramétrica a uma edição simples. Ver `referencias/recuperar_salvar_exportar.md`.

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
| **O operador aponta na tela** e o trabalho NÃO está no Blender | bancada do FreeCAD: `referencias/freecad.md`, seção 0 |
| **O operador aponta na tela** com o trabalho já no Blender (letras por clique, traços) | `referencias/edicao_por_letras.md` |
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
| criar ou editar CAD no FreeCAD (prioridade); bancada de marcas; cálculo estrutural FEM | `referencias/freecad.md` |
| operador marcar pontos/traços com letras e notas na peça | `scripts/abrir_bancada_freecad.py`, `freecad/bancada_freecad.py` |
| reaproveitar geradores de malha e verificadores existentes | `referencias/criar_e_parametrizar.md` |
| SolidCraft, só a pedido do dono | `referencias/solidcraft.md` |
| no Blender: abrir, inspecionar e ler seleção | `referencias/inspecionar_e_selecionar.md` |
| deslocar região delimitada; preencher vão entre dois limites | `referencias/editar_localizado.md` |
| combinar versões da mesma malha sem booleana; achar de qual malha um cupom saiu | `referencias/transplante_de_deslocamento.md` |
| conferir malha, junção, região preservada, dimensões, furo passante | `referencias/verificar.md` |
| **projetar para imprimir**: folgas calibradas, rosca, espessura mínima, rebaixo, ranhura, gravação, família de tamanhos, licença de peça de terceiros | `referencias/projetar_para_imprimir.md` |
| malha pintada (3MF multicor): reduzir sem perder a pintura, marcar região por vinco, mexer na forma para tirar suporte, relevo de tecido | `referencias/malha_pintada.md` |
| conceitos e validação das fotos e medidas com o operador antes de modelar (página de bancada) | `referencias/validacao_medidas_html.md`, `assets/pagina_bancada.html`, `scripts/nova_pagina_bancada.py` |
| **conferir a FORMA antes de entregar**: quatro vistas ortográficas | `referencias/render_de_conferencia.md` |
| visualizador 3D (.html) ou GIF/MP4 de montagem/vista explodida | `referencias/entregas_em_movimento.md` |
| desfazer, refazer, salvar, exportar, deixar retomável | `referencias/recuperar_salvar_exportar.md` |
| dependências e execução do Blender em processo separado | `referencias/mapa_de_ferramentas.md` |
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
