# Receita proposta: seleção e edição guiada no Blender

Referência para incorporação ao plugin em planejamento; não é uma skill instalada. Não contém geometria, nomes, medidas nem caminhos de projetos de clientes.

## Quando usar

Quando o usuário quer selecionar uma região no Blender, pedir uma alteração em linguagem natural e acompanhar o resultado. Aproveitar o MCP e a API Python existentes; não criar outro editor ou transporte.

## Diagnosticar antes de orientar

Consultar o objeto ativo, `bpy.context.mode`, `mesh_select_mode`, sombreamento e sobreposições. Em Edit Mode, ler a seleção com `bmesh.from_edit_mesh`; a malha de Object Mode pode estar desatualizada. Seleção existente com destaque invisível pode ser apenas sobreposição desligada. Não concluir que o clique falhou pela aparência.

## Orientação ao usuário

Manter o mouse na área 3D ao usar atalhos. No mapa de teclas Blender consultado nesta instalação, versão 5.2.1 LTS:

- Tab alterna Object Mode e Edit Mode quando o contexto permite.
- Z abre o menu de sombreamento; escolher Sólido.
- Shift + Alt + Z alterna sobreposições. Confirmado consultando `wm.context_toggle` com `data_path=space_data.overlay.show_overlays` no keymap ativo. Verificar novamente em mapas personalizados.
- Sólido + Edit Mode + sobreposições ativadas mostra superfícies preenchidas com arestas de edição por cima. Wireframe como sombreamento não é necessário.
- Em seleção de malha, 3 da fileira superior seleciona faces; não confundir com o teclado numérico.
- Clique seleciona uma face; Shift + clique acrescenta outras. B permite seleção por caixa. Explicar o efeito de X-Ray sobre a seleção de superfícies ocultas.
- Em STL, uma face frequentemente é apenas um triângulo, não uma superfície funcional inteira.
- Ctrl + Z desfaz; Ctrl + Shift + Z refaz no mapa padrão. Para scripts, ver a seção seguinte.

Alternativa visual: usar o botão Mostrar sobreposições, com dois círculos sobrepostos, na área 3D. O ícone alterna a opção; a seta adjacente abre configurações.

## Da seleção ao pedido

Ler a seleção atual e localizar limites e superfícies adjacentes. Uma seleção ampla não fornece automaticamente direção, origem e destino. Confirmar somente ambiguidades materiais; não repetir confirmações já respondidas. Excluir seleções acidentais conforme o usuário indicar.

Antes de preencher uma região, distinguir borda aberta, rebaixo, ranhura e mero efeito de sombreamento. Medir a geometria e relacionar a escala da cena às unidades usadas. Não inferir que uma região é dispensável apenas por sua aparência.

## Editar, desfazer e verificar

Respeitar a preferência por trabalhar no objeto atual. Não duplicar a peça a cada operação se o usuário não quer isso. A existência de Ctrl+Z não garante que qualquer mutação direta de dados feita por um MCP esteja registrada no histórico.

Neste fluxo foi possível registrar pontos com `bpy.ops.ed.undo_push` em contexto válido de VIEW_3D, antes e depois de editar em Object Mode. O teste de `undo` recuperou exatamente o hash de coordenadas e conectividade anterior; `redo` recuperou o posterior. Isso demonstra esse caminho específico, não todos os operadores e modos. Reobter referências a objetos e malhas após undo/redo.

Agrupar a mudança lógica para que o histórico seja compreensível. Em validação do adaptador, usar geometria sintética para testar undo/redo por identidade; não executar continuamente testes destrutivos de histórico durante edição humana concorrente.

Verificar fronteiras, arestas não-manifold, degenerações, componentes e medidas pertinentes após alterações. União booleana pode gerar faces de área zero mesmo quando não há bordas abertas; conferir ambos. Limitar correções numéricas à região alterada e justificar a tolerância na escala real.

Preservação precisa de um alvo explícito e comparação geométrica. Contar faces cujos vértices estão fora de uma caixa não prova preservação: triângulos podem atravessar a caixa. Distinguir retesselação de alteração da superfície.

Inspecionar a junção de perto: malha fechada não prova ausência de ranhuras ou desníveis indesejados. Manter separadas a validade topológica, a conformidade visual e a validação física de encaixe.

Restaurar as sobreposições após a apresentação para o usuário continuar selecionando. Informar o modo deixado ativo. Não sobrescrever o arquivo de origem ao salvar uma prévia; atualizar apenas o destino acordado.


## Lições do experimento: roteiro a tornar executável no M1

Esta seção registra observações e decisões do teste local. Não é um algoritmo genérico implementado. Os novos exemplos sintéticos e os scripts distribuíveis ainda precisam ser construídos e executados. Não usar o projeto privado como fixture.

| Sintoma observado | Diagnóstico usado | Ação e limite |
|---|---|---|
| MCP sem resposta | handshake, disponibilidade da aplicação e versão | abrir a aplicação restabeleceu a conexão; conexão falha não provava complemento antigo. Não reinstalar por inferência |
| Clique parecia não selecionar | contar faces no BMesh e ler sobreposições | havia seleção com destaque desligado; ensinar o controle correto. Atalho foi confirmado pelo keymap após orientações textuais erradas |
| Seleção incluía superfície lateral | inspecionar coordenadas e imagem da seleção | perguntar somente sobre essa exclusão e respeitar a resposta; não editar tudo que foi selecionado automaticamente |
| Pedido de rampa sem limites inequívocos | ler superfícies adjacentes e examinar seção | confirmar destino e região protegida antes de construir |
| União sem bordas abertas, mas com degenerações | contar faces de área nula/quase nula separadamente | correção local de vértices coincidentes/arestas degeneradas, seguida de nova medição. Sem limpeza global indiscriminada |
| Primeira rampa deixou ranhura | inspeção ampliada da junção | prolongar o volume para interseção com material existente; conferir toda a junção no alcance declarado. Estanqueidade não detectou esse defeito |
| Comparação de preservação encontrou faces diferentes | examinar se a seleção por caixa incluía triângulos que cruzavam a região | distinguir mudança de tesselação de mudança da superfície; a segunda comparação comprovou somente a região superior declarada, não toda a peça |
| Dúvida sobre Ctrl+Z em script | registrar antes/depois e testar undo/redo | assinaturas de coordenadas e conectividade foram recuperadas. A conclusão vale para o caminho testado, não para toda mutação Python |

### Procedimento que a receita de preenchimento precisa ensinar

1. Capturar a seleção viva em Edit Mode e o estado da geometria. Obter escala de unidade e transformação; converter para um sistema comum antes de comparar distâncias. Sincronizar dados ao sair de Edit Mode, quando necessário.
2. Identificar dois limites e a faixa de ligação. A seleção serve como indicação, não como inferência automática de intenção. Excluir as regiões protegidas e obter confirmação somente dos limites ainda ambíguos.
3. Examinar uma seção no sentido do preenchimento. No teste local, segmentos foram obtidos pela interseção de arestas com um plano. Para distribuir, tratar arestas/vértices coplanares, duplicação e segmentos desconexos ou usar biblioteca existente que trate esses casos. O snippet particular não demonstrou cobertura desses casos.
4. Construir um volume fechado cuja superfície superior ligue os limites acordados. Fazer o volume interceptar o sólido existente nas junções e ajustar sua largura à região. Derivar a sobreposição da geometria e tolerância do trabalho; não usar constante universal. Se houver superfícies curvas/ambíguas fora da receita, parar nesse limite em vez de improvisar.
5. Registrar recuperação, aplicar a união pela ferramenta existente e inspecionar o resultado. No teste foi usado Boolean UNION com solver EXACT. Não promover essa escolha a solução universal; indicar domínio e comportamento em falha.
6. Medir degenerações além de bordas e incidência das arestas. Se necessário, aplicar merge/dissolve somente aos elementos da região e com tolerância declarada, menor que os detalhes a preservar. Medir novamente e recusar a conclusão se a correção eliminar detalhe protegido ou introduzir defeito.
7. Comparar as superfícies protegidas com método e tolerância explícitos, e verificar ranhura/desnível por seção ou superfície, além da imagem ampliada. Conservar os achados que ainda não puderem ser decididos. Contagem de faces igual ou dimensões externas iguais não prova preservação.
8. Conferir undo/redo no cenário sintético pelo estado recuperado. Depois de cada restauração, buscar novamente objetos e dados; referências antigas podem estar inválidas. Em uso corrente, não executar testes repetidos do histórico enquanto o usuário edita.
9. Salvar no destino combinado, associar verificações ao resultado correto, restaurar a apresentação combinada e indicar como continuar selecionando. Se houver exportação, reabrir e conferir o artefato entregue na cobertura exigida pela finalidade.

### Formato obrigatório do exemplo executável

Gerador sintético + pedido de entrada + parâmetros e unidades + sequência de ferramentas + valores/estados esperados por verificação + comandos de recuperação + limitações. Incluir uma variante com junção defeituosa mas malha fechada, e outra que exercite degeneração controlada independentemente da ranhura. Uma falha em requisito diferente não dá crédito ao detector pretendido.

O agente operador deve receber snippets/scripts prontos para as etapas mecânicas frágeis, com checagem de pré-condições, em vez de reconstruí-los da narrativa. A manutenção desses auxiliares é parte da receita específica, não justificativa para criar núcleo genérico, viewer ou MCP novo.
