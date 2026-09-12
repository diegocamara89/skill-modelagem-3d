# Fluxo interativo: selecionar, operar, conferir

1. Identifique a sessao e objeto ativos. Distingua Blender vivo de processo headless:
   mudar um arquivo em background nao muda o que o usuario ve no Blender aberto.
2. Oriente a selecao quando faltar alvo: objeto ativo, Tab para Edit Mode; teclas
   1/2/3 da fileira superior escolhem vertices/arestas/faces (numpad controla vistas).
   Clique no elemento. Alt+A limpa a selecao. Shift+clique adiciona ou retira.
   Confirme o modo e a contagem lida; uma tecla pressionada nao comprova selecao.
3. Para solido com arestas sobrepostas: Z > Solid, habilite Overlays pelo botao de dois circulos no cabecalho e o modo
   de edicao. Alt+Z alterna X-Ray para enxergar/selecionar atraves; isso tambem pode
   selecionar o verso. Confira visualmente. Keymap pode ter sido personalizado.
4. Leia somente a receita da operacao. Fixe eixo ou plano e valor, e interprete
   a selecao como indicacao do usuario. Nao amplie para toda a malha silenciosamente.
5. Execute UMA chamada pronta. Movimento altera vertices existentes; extrusao cria
   geometria; alinhamento projeta; preenchimento cria superficie. Escolha pelo pedido.
6. Confira resposta e efeito. Resultado numerico nao certifica parede adjacente,
   colisao ou intencao. Quando isso importa, use a verificacao correspondente.
7. Mostre a mudanca na mesma sessao. Captura temporaria destacada deve ser identificada
   como marcacao, nao incorporada ao modelo sem querer. Responda brevemente.

Timeout nao autoriza repetir: a operacao pode ter ocorrido. Inspecione antes.
Ctrl+Z imediato e Ctrl+Shift+Z foram testados para as novas operacoes. Nao use Undo
global automatico depois de outras acoes: ele pode desfazer trabalho alheio.
A chamada de mover tem historico proprio limitado; as outras nao prometem isso.

Escopo comprovado: geometrias sinteticas simples, Blender 5.2.1 LTS, chamadas
prontas usadas por executor sem historico. Isso nao prova desempenho em qualquer
STL, em malha densa ou no projeto privado do usuario. Nao imponha ensaio complexo
para ajuste simples; escale a verificacao conforme o risco real e a finalidade.

## Contrato curto de execucao e conferencia

Use a chamada pronta quando ela cobre a construcao solicitada. Se nao cobre, diga
qual condicao falta e reutilize transporte e auxiliares existentes no codigo especifico.
Nao force uma operacao simples a preservar encontros que ela nao preserva.

As CLIs prontas exigem --captura para escrever. Obtenha o token em
capturar_selecao.py (ou no preview/inspecao da ferramenta). Ele vincula processo,
objeto, coordenadas, conectividade e selecao; a conferencia ocorre na mesma chamada
antes da escrita. captura_depois pode alimentar a proxima chamada. Token desatualizado
exige nova inspecao do alvo, nao retry cego. Nao precisa escrever um verificador de
identidade para essas CLIs. Codigo especifico fora delas deve aplicar a mesma guarda.

Fixe limites numericos para as medidas decisivas antes de executar. Concluida exige
todos esses limites satisfeitos e nenhuma falha pendente. Medidas informativas nao
viram aprovacao. Compare com captura anterior real e imutavel, em memoria ou arquivo;
subtrair o delta do resultado e uma reconstrucao hipotetica, nao evidencia do antes.
Verifique os vertices do alvo e a regiao protegida relevante. Area igual sozinha nao
prova movimento rigido. Defeito preexistente precisa de comparacao antes/depois:
ter existido antes nao prova que nao piorou. Limites de piora devem ser declarados.

Extrusao, alinhamento, preenchimento e arredondamento guardam uma copia temporaria
da malha e conferem a recuperacao geometrica apos falha. Os estados distinguem:
- RECUSADO: operacao nao iniciada por precondicao.
- FALHA_SEM_ALTERACAO_LIQUIDA: estado final confere com o anterior; pode ter havido escrita intermediaria.
- FALHA_RESTAURADA: recuperacao executada e conferida.
- FALHA_COM_ALTERACAO ou INDETERMINADO: inspecionar; nao declarar recuperado nem repetir.
A garantia cobre geometria e selecao da malha, nao materiais/animacao nem operacoes
arbitrarias. Movimento conserva seu historico proprio de coordenadas. Para scripts
especificos, prepare recuperacao e limites antes de escrever; nao use Undo global
para desfazer trabalho concorrente. Na sessao headless nao se promete Undo nativo.

## BMesh, datablock e visibilidade sao verificacoes distintas

Em Edit Mode, leia a geometria de edicao por bmesh.from_edit_mesh. Depois da edicao,
atualize normais e use bmesh.update_edit_mesh com parametros adequados a mudanca de
topologia. Para consultar obj.data.vertices atualizado, sincronize explicitamente
com obj.update_from_editmode() antes da leitura. Essa sincronizacao nao substitui a
medicao contra o alvo e a captura anterior. Fora de Edit Mode use os dados adequados
ao objeto, considerando modificadores quando existirem.

Divergencia entre BMesh e obj.data nao prova viewport parado nem perda ao salvar.
Concordancia entre eles tambem nao prova atendimento ao pedido. Nao memorize regras
como 'nunca medir pela BMesh'. Identifique a janela/sessao, solicite redesenho e confira
captura posterior no mesmo enquadramento quando houver duvida visual. tag_redraw e
uma solicitacao, nao prova de exibicao. Sem essa evidencia, informe que a geometria
foi medida mas a exibicao ainda nao foi confirmada; nao culpe o viewport por inferencia.

Referencias tecnicas: https://docs.blender.org/api/5.2/bmesh.html e
https://docs.blender.org/api/5.2/bpy.types.Object.html#bpy.types.Object.update_from_editmode

## Entrega para impressao

Quando o pedido incluir imprimir/testar, exporte a geometria atual do objeto correto
para destino combinado, sem substituir silenciosamente um arquivo anterior. Confira
o STL reaberto: escala/dimensoes, correspondencia com a origem exportada, fechamento,
orientacao e componentes segundo a finalidade. Verificacao local nao cobre a malha
inteira. Entregue caminho absoluto e pendencias; exportado nao significa aprovado
para impressao. Nao repare automaticamente regioes fora do pedido.
