# Chamadas prontas: uma seleção, um objeto, uma operação

Rota para o Blender **aberto**, quando o pedido é uma operação simples sobre **um** objeto
em Edit Mode: mover, expandir, extrudar, alinhar, preencher ou arredondar. As três rotas
convivem e cada uma tem o seu domínio:

| Rota | Quando |
|---|---|
| `edicao_por_letras.md` | o operador aponta com letras; vários objetos em edição; cena em metros |
| **esta** (`*_selecao.py`) | um só objeto em edição; a operação pronta cobre o pedido; cena em **mm** |
| `sessao_e_edicao_guiada.md` | deformação delimitada com alvo, transição e região protegida |

No fluxo "A + Tab em tudo" (vários objetos em edição) as chamadas prontas recusam: use as
letras.

## Regras comuns (valem para as seis operações)

**Pré-condições de todas as chamadas:** objeto ativo nomeado (nome real, vindo do
diagnóstico da sessão; nunca copiar nome de exemplo), Edit Mode, malha exclusiva sem
modificadores nem shape keys, unidades METRIC com escala de cena em mm.

**Fluxo.**
1. Identifique sessão e objeto ativos. Blender vivo não é processo headless: mudar um
   arquivo em background não muda o que o usuário vê no Blender aberto.
2. Oriente a seleção se faltar alvo: objeto ativo, `Tab` para Edit Mode; teclas `1`/`2`/`3`
   da fileira superior escolhem vértices/arestas/faces (o numpad controla vistas); clique no
   elemento; `Alt+A` limpa; `Shift+clique` soma ou retira. Confirme modo e contagem lidos:
   tecla pressionada não comprova seleção.
3. Sólido com arestas sobrepostas: `Z` > Solid, Overlays ligados (botão de dois círculos no
   cabeçalho) e Edit Mode. `Alt+Z` liga o X-Ray, que enxerga e seleciona através, inclusive o
   verso. O keymap pode ter sido personalizado.
4. Leia só a receita da operação. Fixe eixo ou plano e valor; trate a seleção como indicação
   do usuário, sem ampliar para a malha toda em silêncio.
5. Execute **uma** chamada pronta. Mover altera vértices existentes; extrudar cria
   geometria; alinhar projeta; preencher cria superfície. Escolha pelo pedido.
6. Confira resposta e efeito. Resultado numérico não certifica parede adjacente, colisão nem
   intenção: quando isso importa, use a verificação correspondente.
7. Mostre a mudança na mesma sessão. Captura temporária destacada é marcação, não entra no
   modelo. Responda brevemente.

Se a chamada pronta não cobre a construção pedida, diga qual condição falta e reutilize
transporte e auxiliares existentes; não force uma operação simples a preservar encontros
que ela não preserva.

**Captura e TOKEN.** As CLIs exigem `--captura` para escrever. O TOKEN é o campo `captura`
de:

```
python scripts/capturar_selecao.py --porta PORTA --objeto NOME
```

(ou do preview/inspeção da própria ferramenta). Ele vincula processo, objeto, coordenadas,
conectividade e seleção; a conferência ocorre na mesma chamada, antes da escrita. O
`captura_depois` do resultado alimenta a próxima chamada se o alvo continua correto.
Token desatualizado exige nova inspeção do alvo, não repetição às cegas nem recaptura
automática para contornar uma seleção que mudou. Não precisa escrever verificador de
identidade para essas CLIs; código específico fora delas deve aplicar a mesma guarda.
Substitua `NOME`, `PORTA` e `TOKEN` por valores reais; não use a porta de outra sessão.

**Limites antes de executar.** Fixe limites numéricos para as medidas decisivas antes de
rodar. "Concluída" exige todos satisfeitos e nenhuma falha pendente; medida informativa não
vira aprovação. Compare com uma captura anterior real e imutável (memória ou arquivo):
subtrair o delta do resultado é reconstrução hipotética, não evidência do antes. Verifique os
vértices do alvo e a região protegida relevante; área igual não prova movimento rígido.
Defeito preexistente pede comparação antes/depois, com limite de piora declarado.
Escale a verificação ao risco: nada de ensaio complexo para ajuste simples. O escopo
comprovado destas chamadas são geometrias sintéticas simples; isso não prova desempenho em
qualquer STL, em malha densa ou em projeto real.

**Estados.** Extrudar, alinhar, preencher e arredondar guardam uma cópia temporária da
malha e conferem a recuperação geométrica após falha:

- `RECUSADO`: operação não iniciada, por precondição.
- `FALHA_SEM_ALTERACAO_LIQUIDA`: estado final confere com o anterior; pode ter havido escrita
  intermediária.
- `FALHA_RESTAURADA`: recuperação executada e conferida.
- `FALHA_COM_ALTERACAO` ou `INDETERMINADO`: inspecionar; não declarar recuperado nem repetir.

A garantia cobre geometria e seleção da malha, não materiais, animação nem operações
arbitrárias. Em script específico, prepare recuperação e limites antes de escrever.

**Undo.** Ctrl+Z imediato e Ctrl+Shift+Z valem para as operações novas (mover tem histórico
próprio, abaixo). Não use Undo global automático depois de outras ações: pode desfazer
trabalho alheio. Na sessão headless não se promete Undo nativo.

**Timeout não autoriza repetir.** A operação pode ter ocorrido: inspecione antes.

## Mover faces em eixo global

Translação rígida da união dos vértices das faces selecionadas. Faces adjacentes acompanham
os vértices compartilhados; a forma delas não é certificada. Exige distância finita diferente
de zero, em mm. Se o pedido exige reconstruir encontros, use edição guiada.

```
python scripts/mover_selecao.py --acao inspecionar --porta PORTA --objeto NOME
python scripts/mover_selecao.py --acao mover --porta PORTA --objeto NOME --eixo Z --distancia-mm 1 --captura TOKEN
```

O TOKEN é o campo `captura` da inspeção; a escrita exige que sessão, geometria e seleção
ainda correspondam a ela. Para desfazer/refazer **desta** ferramenta: `--acao desfazer` ou
`--acao refazer` com `--captura` atual. O histórico próprio restaura coordenadas e recusa
geometria externa alterada; não é o histórico geral do Blender, nem de materiais ou animação.
Não gere código novo para trocar a distância.

`DESLOCAMENTO_VERIFICADO` mede o deslocamento do alvo e a preservação dos outros vértices.
**Não certifica** colisão, espessura, qualidade adjacente nem fabricação; confira o viewport
se houver dúvida de exibição. `INDETERMINADO` exige inspeção antes de repetir; falha com
estado final igual retorna `FALHA_SEM_ALTERACAO_LIQUIDA`, o que não prova que nenhuma escrita
foi tentada.

## Expandir a partir de uma face

Para quando o usuário marcou **uma** face e pediu a região conectada ou a superfície plana
que a contém. Exige exatamente uma face visível selecionada; com várias, peça uma face
inicial ou mantenha a seleção manual.

```powershell
python "<raiz>/scripts/selecionar_regiao.py" --porta <porta confirmada> --objeto "NOME" --modo conectada
python "<raiz>/scripts/selecionar_regiao.py" --porta <porta confirmada> --objeto "NOME" --modo conectada --aplicar --captura TOKEN
```

A primeira chamada calcula o conjunto sem mudar a seleção e retorna a captura (o TOKEN da
segunda); se geometria ou seleção mudarem, refaça o preview. `captura_depois` identifica a
seleção expandida. Conectividade = faces ligadas por arestas, **independente do ângulo**:
pode selecionar a casca inteira de um sólido. Faces ocultas bloqueiam a expansão; objetos e
ilhas separados não entram.

Para limitar ao plano da face inicial: `--modo plano --angulo-graus <tolerância angular>
--distancia-mm <tolerância de plano>`. As duas tolerâncias vêm do pedido/precisão requerida,
não de valor universal. A distância compara todos os vértices ao plano inicial e a normal à
normal inicial: não acumula pequenas inclinações ao longo da malha. Requer unidades métricas.

Confira as faces retornadas e mostre a captura atual. Seleção errada: restaure/reselecione a
face inicial antes de repetir; a expansão não altera coordenadas nem topologia. **Não
promete** identificar a região funcional do objeto nem detectar marcação acidental por
intenção.

## Extrudar faces selecionadas

Cria volume novo a partir de **um** conjunto conectado de faces planas, na normal global, com
distância positiva em mm. Para apenas deslocar vértices existentes, use mover. A tolerância
de plano é um limite computacional declarado, não folga de impressão; não a adivinhe.

```
python scripts/extrudar_selecao.py --porta PORTA --objeto NOME --distancia-mm DISTANCIA --tolerancia-plano-mm TOLERANCIA --captura TOKEN
```

Não precisa escrever código Blender (usa `extrude_face_region` nativo). A operação aparece na
cena conectada e entra no Undo nativo. `EXTRUSAO_MEDIDA` confirma a altura na normal e os
vértices preexistentes preservados. **Não certifica** colisão, auto-interseção, espessura nem
fabricação: inspecione a forma.

## Alinhar seleção a um plano

Projeção ortogonal dos vértices das faces selecionadas num plano global. **Não** é rotação
rígida nem preserva paredes adjacentes. O usuário/contexto fornece ponto GLOBAL em mm, normal
(não nula) e deslocamento máximo (positivo); sem cotas ou referências, não deduza o plano
pela imagem.

```
python scripts/alinhar_selecao.py --porta PORTA --objeto NOME --ponto-mm X Y Z --normal NX NY NZ --maximo-mm LIMITE --captura TOKEN
```

Recusa antes de alterar se algum vértice excederia o limite. `ALINHAMENTO_MEDIDO` mede o
resíduo ao plano e os vértices não selecionados preservados. Colisão, forma das faces
adjacentes e fabricação **continuam não verificadas**.

## Preencher ou ligar bordas

Cria SUPERFÍCIE, não promete volume fechado. Modo `contorno`: um único loop fechado, plano e
estritamente convexo. Modo `ponte`: duas arestas paralelas separadas, com uma face entre
elas. Não serve para remendar qualquer buraco nem reconstruir encontros de sólidos. Exige
seleção de ARESTAS visíveis, soltas ou na borda (nunca internas), e tolerância
computacional de planaridade em mm.

```
python scripts/preencher_selecao.py --porta PORTA --objeto NOME --modo ponte --tolerancia-mm TOLERANCIA --captura TOKEN
```

Troque `ponte` por `contorno` para fechar o loop. `SUPERFICIE_CRIADA` confirma uma face com
os vértices delimitados e preservados. Volume fechado, colisão, orientação global e
fabricação **não foram verificados**.

## Arredondar uma quina

Domínio: UMA aresta convexa manifold de 90 graus, malha exclusiva, escala uniforme positiva
sem cisalhamento, seleção de ARESTAS. Não serve para vários cantos nem ângulos diferentes.

```
python scripts/arredondar_selecao.py --porta PORTA --objeto NOME --raio-mm RAIO --segmentos NUMERO --captura TOKEN
```

Raio positivo, segmentos inteiros de 2 a 64; o raio fica abaixo da metade da menor aresta
incidente, com margem numérica de 0.00001 mm. Usa bevel nativo com perfil circular 0.5.
`PERFIL_MEDIDO` confirma erro radial <= 0.00001 mm nos vértices do perfil e arestas manifold.
**Não mede** o erro da aproximação facetada entre os vértices (mais segmentos reduzem a
faceta), nem colisão, auto-interseção ou fabricação. A distância OFFSET só equivale a raio
neste domínio de quina de 90 graus.
