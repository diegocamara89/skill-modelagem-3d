# Editar região delimitada: deslocar e preencher entre limites

Para apenas mover rigidamente uma seleção já definida, use a rota curta
`mover_selecao.md`. Reutilize a ferramenta pronta, sem gerar outra implementação.

Duas operações, com o mesmo cuidado: **a operação retornar não prova que ela fez
efeito**, e efeito não prova que o efeito é o pedido.

Antes de começar, leia `inspecionar_e_selecionar.md`. Sem o diagnóstico, os critérios
de seleção saem no sistema de coordenadas errado.

---

# Parte 1 — Deslocar uma região delimitada

**Se o pedido é alterar a forma de uma borda/patamar e conservar seus encontros,
comece em `sessao_e_edicao_guiada.md`.** A translação abaixo é uma operação rígida
de um conjunto já definido, não uma estratégia para escolher esse conjunto. Meça
também as faces incidentes que absorvem o deslocamento; elas podem esticar, dobrar
ou inverter enquanto a altura do alvo e a topologia global continuam corretas.

## Pré-condições

- objeto em Edit Mode;
- seleção **contada**, não presumida;
- vetor de deslocamento em unidades da cena, com direção e distância acordadas;
- ponto de recuperação registrado.

## Sequência executável

```python
# dentro do Blender. O caminho e relativo a RAIZ DO PACOTE, sem prefixo `produto/`:
# esse prefixo existe apenas na arvore de desenvolvimento e NAO resolve no pacote
# extraido — o proprio INVENTARIO.json diz isso, e estas duas linhas ficaram para
# tras quando o manifesto foi corrigido.
import sys
sys.dont_write_bytecode = True          # nao criar __pycache__ dentro do pacote
sys.path.insert(0, r"<raiz do pacote>\scripts")
import bl_ferramentas as F
```

```python
F.entra_em_edicao("Peca", "face")
sel = F.seleciona_faces_por_caixa_de_mundo("Peca", minimo=[...], maximo=[...])
# sel["faces_marcadas"] > 0, senão já levantou ErroDePrecondicao

F.marca_recuperacao("antes de deslocar a região")
r = F.desloca_selecao("Peca", [0.0, 0.0, 2.0])
```

O que conferir no retorno de `desloca_selecao`, e **por que não basta olhar um só**:

| Campo | Significado | Se estiver errado |
|---|---|---|
| `vertices_selecionados_antes` | contagem lida antes de operar | zero → a função barra, e é isso que se quer |
| `retorno_do_operador` | `FINISHED` ou `CANCELLED` | `CANCELLED` com seleção não vazia: investigue, não repita |
| `geometria_mudou` | assinatura antes ≠ depois | **`FINISHED` com `geometria_mudou` falso é o sinal de que algo está errado** |

MEDIDO, e é um defeito que eu mesmo produzi e corrigi durante a construção desta
receita: se a assinatura for lida de `obj.data` enquanto o objeto está em Edit Mode,
ela compara **duas leituras da mesma cópia velha** e reporta "não mudou" mesmo com o
deslocamento aplicado. `F.assinatura` agora lê a malha viva em Edit Mode e declara a
fonte no campo `fonte_da_leitura`. Se você escrever sua própria comparação, faça o
mesmo.

Confirme também a medida externa, que é independente da assinatura:

```python
F.diagnostico("Peca")["objeto"]["dimensions_mundo"]
```

No cenário sintético, subir 2 unidades o topo do patamar alto leva a altura de
`20.0` para `22.0`. Medido.

## Controles obrigatórios

- **negativo**: com a seleção limpa (`F.limpa_selecao`), `desloca_selecao` tem que
  levantar `ErroDePrecondicao`. Sem esse controle, um "nada aconteceu" silencioso
  passaria por sucesso.
- **positivo**: com seleção válida, `geometria_mudou` verdadeiro e o alvo muda pelo
  vetor pedido. Dimensão externa só é oráculo quando a região define esse extremo.
  Na edição de forma, complete com a transição e a região protegida, como na rota guiada.

---

# Parte 2 — Preencher um vão entre dois limites

## Quando esta receita se aplica, e quando não

Ela liga **dois** limites por uma superfície **plana**, ao longo de um eixo, com
seção constante no eixo transversal, num objeto **alinhado aos eixos de mundo**.

Fora do domínio, e a função **recusa** em vez de improvisar:

| Situação | O que acontece | Alternativa |
|---|---|---|
| objeto girado | `ErroDePrecondicao` dizendo qual eixo está fora | aplicar a rotação (Object ▸ Apply ▸ Rotation), ou usar outra receita |
| superfície curva, ou mais de dois limites | fora do escopo | pare e diga o limite |
| sobreposição zero | `ErroDePrecondicao` | ver abaixo por quê |

MEDIDO: com o objeto girado 30° em z, a seleção por caixa de mundo já não encontra a
face alvo, e o preenchimento recusa com a lista de alternativas. Nada depois disso é
medido, e o relatório diz isso explicitamente.

## O procedimento, passo a passo

### 1. Capturar o estado e os limites

Leia a seleção viva e o estado da geometria. Obtenha escala de unidade e
transformação, e converta tudo para um sistema comum **antes** de comparar
distâncias. Sincronize os dados ao sair de Edit Mode.

### 2. Identificar os dois limites e a faixa de ligação

A seleção é **indicação**, não inferência automática de intenção. Determine:

- `limite_a = {"x": ..., "z": ...}` e `limite_b = {"x": ..., "z": ...}` em mundo;
- a faixa transversal `y_de`, `y_ate`;
- `z_da_base`, abaixo do piso do vão;
- a **região protegida**, que é o que não pode mudar.

Confirme com o usuário **somente** os limites ainda ambíguos.

### 3. Examinar uma seção antes de construir

```python
F.secao_por_plano("Peca", ponto=[0, 20, 0], normal=[0, 1, 0])
```

A função trata aresta coplanar ao plano, vértice exatamente no plano e ponto
coincidente. Ela devolve os pontos unidos por proximidade, os segmentos, a contagem de
faces coplanares ignoradas, **quantos pontos ela uniu**, e declara que prova **aquele
plano**, não a peça.

**Sobre o limiar de união, que já esteve errado.** Os pontos vêm de interpolação sobre
coordenada de precisão simples, cujo ruído foi medido entre **1e-6 e 3e-6**. A versão
anterior unia arredondando a **7 casas** — mais fino que o próprio ruído. Medido numa
varredura de 33 planos: **4 deles devolviam 20 pontos em vez de 10**, cada ponto em
duplicata, com y em 9,999999 e 10,000002. Quem contasse pontos de seção para decidir
tiraria conclusão errada.

O padrão agora é `tolerancia_de_uniao=1e-5`, uma ordem **acima** do ruído medido e
abaixo de qualquer detalhe dos cenários.

**Dois campos do retorno são oráculo, e a versão anterior desta página mandava
conferi-los sem dizer qual é o valor esperado** — o que é pedir conferência e negar o
critério:

| Campo | Valor saudável | O que outro valor significa |
|---|---|---|
| `pontos_unidos_por_coincidencia` | **igual a `n_pontos`** | numa poligonal fechada, cada ponto é alcançado por **duas** faces vizinhas, então o segundo encontro de cada ponto é uma união. Valor **menor** que `n_pontos` indica seção aberta; **maior** indica face cortada em mais de dois pontos |
| `faces_com_mais_de_dois_cruzamentos` | **0** | a poligonal está **incompleta**: uma face não convexa foi cortada em mais de dois pontos e o par escolhido é arbitrário. O campo `limite` do retorno também avisa. **Descarte a seção** e secione em outro plano |

Medido numa sessão limpa independente: seccionando na costura de um limite (normal
`[1,0,0]`), o retorno trouxe `faces_com_mais_de_dois_cruzamentos: 2`, `n_pontos: 9`,
`n_segmentos: 12` com segmentos repetidos e um ponto espúrio — e a mesma peça,
seccionada com normal `[0,1,0]`, deu contagem **0** e um segmento único ligando os dois
limites. Ou seja: o plano importa, e o campo diz quando não dá para confiar.

### 4. Escolher a sobreposição — e de onde ela sai

O volume tem que **interceptar o material** nas duas junções e abaixo do piso. Volume
que apenas encosta produz contato tangente.

**Não existe constante universal para isso.** A função exige o parâmetro
`sobreposicao` **e** o parâmetro `origem_da_sobreposicao`, que registra de onde o
número saiu. Sem justificativa, ela recusa.

No cenário sintético a sobreposição foi derivada como **um vigésimo do comprimento do
vão**: 1,0 unidade num vão de 20; e 1,5 num vão de 30, na variante de outra medida.
**Copiar o número deste exemplo é erro**: derive do seu vão.

**A sobreposição é aplicada nos DOIS extremos e também para baixo.** O prisma vai de
`limite_a.x − ov` até `limite_b.x + ov`, e a base desce a `z_da_base − ov`. Não há
sobreposição por extremidade: é um valor só, simétrico.

**Correção de um critério que, como estava escrito, não era satisfazível.** A versão
anterior pedia uma sobreposição "pequena o bastante para não alcançar a região
protegida". Isso é impossível por construção: qualquer valor positivo **entra em
planta** na região protegida — é justamente assim que ele intercepta o material. Um
ensaio independente apontou a contradição, depois de tentar contorná-la
reparametrizando os limites e produzir uma prateleira de 0,296 abaixo do perfil
acordado.

O critério correto é sobre **altura**, não sobre planta:

- em planta, a sobreposição **alcança** a região protegida e **retessela** a face de
  topo dela. Isso é esperado, e aparece como uma aresta de costura em
  `limite − ov`;
- em altura, o topo da sobreposição é **horizontal na altura do limite**, portanto
  coplanar com a superfície protegida e **sem ultrapassá-la**;
- o que se verifica, então, é que a **altura** da região protegida não mudou, e que o
  z máximo da peça não subiu. Retesselação sem mudança de altura **não é** violação
  da preservação.

Por isso a região protegida se verifica por **amostragem de altura**, não por conjunto
de posições de vértices: o conjunto muda pela costura, e a superfície não.

### 5. Construir e unir

```python
r = F.preenche_entre_limites(
        "Peca",
        limite_a={"x": 20.0, "z": 20.0},
        limite_b={"x": 40.0, "z": 14.0},
        y_de=0.0, y_ate=40.0,
        z_da_base=10.0,
        sobreposicao=1.0,
        origem_da_sobreposicao="um vigésimo do vão medido de 20; o topo da sobreposição é horizontal na altura de cada limite, portanto não ultrapassa a superfície protegida",
        solver="EXACT")
```

A superfície superior é **horizontal na altura de cada limite dentro da zona de
sobreposição** e inclinada apenas **entre** os limites.

Isto é uma correção, e vale contar por que: a primeira versão prolongava a
**inclinação** para dentro do material. MEDIDO: com inclinação −0,3 e sobreposição
1,0, o topo do volume chegava a **z = 20,3** em x = 19, ou seja, subia **0,3 acima da
superfície que se prometeu preservar**. Uma saliência, exatamente sobre a região
protegida.

Pior: a medição de perfil **não pegou**, porque a grade uniforme caía em x = 17,
18,86 e 20,71 e passava por cima do trecho entre 19 e 20. **Quem revelou foi a
seção** (`secao_por_plano`), que mostrou dois pontos distintos em x = 19: z = 20,0 e
z = 20,3. Daí duas consequências obrigatórias: o topo virou horizontal na
sobreposição, e a amostragem de perfil passou a incluir **pontos densos na vizinhança
de cada limite**, não só uma grade que cobre o vão.

E uma previsão minha que a medição derrubou: eu esperava que a coplanaridade do topo
horizontal com o material criasse degeneração. Ela criou **menos**: 33 faces com 4
degeneradas antes, 27 faces com **zero** degeneradas depois. O solver `EXACT` lida
melhor com faces coplanares coincidentes do que com interseção oblíqua.

### 5b. A sobreposição serviu? Meça, não confie no parâmetro

Passar um número positivo em `sobreposicao` não garante que o volume tocou o material.
Se os limites estiverem no lugar errado, o prisma flutua e a união apenas cola dois
sólidos separados — **sem erro nenhum**.

A verificação vem em duas partes, e a primeira é a que decide.

**`interseccao_por_zona`, medida ANTES de alterar a peça.** As três regiões que o
prisma tem que encontrar com material são medidas **separadamente**, por interseção
booleana numa **cópia**: a sobreposição do limite a, a do limite b, e a faixa abaixo do
piso. Se qualquer uma delas vier vazia, a função **recusa e não altera nada**.

Isto corrige dois defeitos que uma revisão independente apontou juntos: a medida
anterior era um **único escalar** de volume, que prova "alguma" interseção — interseção
só com a base passava —, e ela era feita **depois** da união, então a falha deixava um
corpo flutuante grudado na peça e a receita mandava revisar coordenadas sem desfazer
nada.

Medido, na peça do cenário: `extremo_do_limite_a` = 440,0, `extremo_do_limite_b` =
200,0, `abaixo_do_piso` = 880,0 — os três exatos, iguais a `11×1×40`, `5×1×40` e
`22×1×40`. E no controle parcial, com o limite b colocado além da peça:
`extremo_do_limite_b` = **0,0** com os outros dois em 440,0 e 1.640,0. Um escalar único
teria aprovado esse caso, porque o total é 2.080.

**`interseccao_com_o_material`, aritmética, como corroboração.** A união de dois
sólidos que se interceptam tem volume **menor** que a soma dos dois.

```
interseccao_medida = volume_da_peca + volume_do_preenchimento − volume_da_uniao
```

| Variante medida | Peça | Preenchimento | Soma | União | Interseção |
|---|---|---|---|---|---|
| `correta` | 35.200 | 7.040 | 42.240 | 40.800 | **1.440** |
| `flutuante` | 35.200 | 5.280 | 40.480 | 40.480 | **0,0** |

`houve_interseccao: false` significa que **não há junção**. Medir perfil ali seria
medir coisa nenhuma, e a receita para e diz isso. A causa mais comum é a mesma do erro
de seleção: limites calculados em coordenada **local** e usados como se fossem de
mundo.

Sobre o solver: `EXACT` foi o usado e medido. Isso vale para este domínio; não é
solução universal. Em falha, a função devolve `ErroDePrecondicao` com a mensagem do
solver, sem deixar o modificador pendurado no objeto.

### 6. Medir degeneração e limpar **localmente**

MEDIDO: a união produz faces de área nula **sem abrir nenhuma borda**. Isto é:
"malha fechada" não detecta o problema; a contagem própria detecta. No cenário
corrigido a união sai com zero degeneradas, mas **repetir a mesma união** — o que
acontece quando um agente reexecuta a operação depois de um tempo esgotado sem
inspecionar — produz **5 faces degeneradas**, e é aí que a limpeza é necessária.

```python
F.mede_malha("Peca")   # arestas_abertas, arestas_nao_manifold, faces_degeneradas — separados

F.limpa_degeneracoes_na_regiao(
    "Peca",
    minimo=[18.0, -0.001, 8.0], maximo=[42.0, 40.001, 22.0],
    tolerancia=1e-5,
    justificativa_da_tolerancia="quatro ordens de grandeza abaixo do menor detalhe (a sobreposição de 1,0) e acima da precisão de coincidência do solver")
```

A limpeza é **restrita à caixa** e a tolerância é obrigatória com justificativa,
porque tem que ser menor que o menor detalhe a preservar. Limpeza global apaga
detalhe que se queria manter.

Confira no retorno: `degeneradas_antes`, `degeneradas_depois`, `zerou` e
`abriu_borda`. **Se `abriu_borda` for verdadeiro, a limpeza piorou a peça** — recuse
a conclusão e volte pelo histórico.

Medido na variante de aplicação duplicada: **5 → 0**, sem abrir borda, faces 39 →
34. E a forma não muda: o perfil continua com desvio 0,0. Um defeito topológico com a
forma certa, que é o oposto do caso da ranhura.

### 7. Marcar **uma** vez o fim da operação lógica

```python
F.marca_recuperacao("preenchimento do vão concluído, com limpeza")
```

Por que aqui e não dentro de cada função: ver `recuperar_salvar_exportar.md`. Em
resumo, dois pontos empilhados fazem um `undo` parar no meio do caminho, e a
conferência acusa "não recuperou" quando o que houve foi recuperar metade.

### 8. Verificar o pedido — e é aqui que a ranhura aparece

Nenhuma medida topológica pega ranhura. A medida que pega é a **altura do material
comparada ao perfil acordado**:

```python
pontos = [[x, y, z_esperado_naquele_x], ...]     # o perfil que os LIMITES implicam
F.mede_topo_em_pontos("Peca", pontos, tolerancia=0.01)
```

O perfil esperado vem dos **limites combinados com o usuário**, não do que foi
construído. É por isso que ele detecta uma rampa construída baixa demais.

**A tolerância é a única desta rota sem procedência, e isto é assimetria reconhecida.**
`limpa_degeneracoes_na_regiao` **exige** `justificativa_da_tolerancia` como parâmetro
obrigatório — e essa é a tolerância cosmética. Esta aqui, que é **a única medida que
pega ranhura**, tem padrão silencioso `0.01`. Uma sessão limpa apontou a inversão. Até
que ela seja fechada (ver `PENDENCIAS_PRODUTO.md`, D6), **derive o seu número e
declare-o no registro do trabalho**: ele tem que ser maior que o ruído da leitura de
altura, que sai de coordenada de precisão simples e foi medido entre 1e-6 e 3e-6, e
**menor** que o menor desvio que você precisa pegar — numa ranhura de 0,5, qualquer
valor entre 1e-5 e 0,1 serve, e 0,01 é uma escolha confortável no meio, não uma
constante da natureza.

MEDIDO, e é o controle negativo desta receita: com a rampa 0,5 abaixo dos limites
acordados, a peça fica **fechada, sem não-manifold e sem degeneração**, a região
protegida fica intacta, e **só** o perfil reprova, com desvio de exatamente 0,5 em
todos os pontos do trecho da rampa. Um defeito, um detector.

**Onde amostrar.** Uma grade uniforme sobre o vão não cobre a junção, e foi assim que
uma saliência de 0,3 escapou. Amostre a grade **mais** pontos densos em torno de cada
limite, em frações da sobreposição.

A lista de `k` tem que ser **simétrica**, e isto é uma correção: a versão anterior
prescrevia `k` em `−1, −0,75, −0,5, −0,25, 0, +0,25, +0,5`, que é assimétrica. Uma
sessão limpa independente seguiu a receita ao pé da letra e mediu a consequência:
"para dentro do material" tem **sinal oposto** em cada limite, então `k = −1` acerta a
costura do limite `a`, em `xa − ov`, e **nada** na lista alcança a costura do limite
`b`, que fica em `xb + ov`. Com `ov = 1,2`, o maior x amostrado foi 48,6 e a costura
estava em 49,2: **nunca medida**. É o mesmo tipo de furo de cobertura que deixou passar
a saliência de 0,3.

Use `k` em `−1,5, −1, −0,5, −0,25, 0, +0,25, +0,5, +1, +1,5` em torno de **cada**
limite, ou espelhe a lista por limite. As duas costuras ficam em `limite ∓ ov`, e as
duas precisam de ponto.

Com a lista simétrica a amostragem sai em **99 pontos**: 33 posições distintas em x,
em 3 planos de y.

**Esse 99 é parâmetro da amostragem, não medida da peça** — e a distinção não é
pedantismo. Uma sessão limpa independente construiu uma peça com dimensões
completamente diferentes (vão de 40 em vez de 20, sobreposição 2,0 em vez de 1,0) e
obteve **exatamente** 99 pontos e 33 posições em x. Não foi confirmação de nada: o
número é consequência aritmética da receita de amostragem (a grade mais os `k` de cada
limite, menos as coincidências, vezes 3 planos), e é **invariante às dimensões**. Ler
"99 pontos" como evidência sobre a peça é confundir parâmetro com medida.

O que **é** medida é o desvio: 0,0 nesses 99 pontos, na peça do pacote, e 0,0 nos 99
pontos da peça da sessão limpa. E vale dizer por que o número já mudou uma vez: a
versão anterior deste texto dizia 87, contagem da lista **assimétrica**; ao corrigir a
lista eu deixei o número antigo, e uma revisão independente pegou. O que importa é a
densidade perto do limite, e que as duas costuras, em `limite − ov` e `limite + ov`,
estejam entre os pontos — o ensaio **exige** isso como critério executável.

Aviso de método: **não** meça o "degrau" comparando dois pontos vizinhos de cada lado
do limite. Numa superfície inclinada isso mede a inclinação. Medido: numa rampa de
inclinação 0,3, amostras a ±0,01 produziam um "degrau" de 0,006 que era artefato do
próprio método. Compare sempre com o **esperado**.

### 9. Conferir a região protegida

Três ferramentas, e escolher errado dá resposta errada:

| Ferramenta | Use quando | Natureza |
|---|---|---|
| **`check_intent.py`, tipo `regiao_intacta`** | você exportou a peça **antes** de editar e pode passá-la em `--referencia` | **exata**: recorta as duas peças pela caixa e mede o volume da diferença simétrica |
| `mede_topo_em_pontos` sobre a região | houve booleana e não há referência em arquivo | amostragem: prova os pontos amostrados |
| `captura_regiao_protegida` + `compara_regiao_protegida` | a operação **não** retessela, por exemplo um deslocamento puro | conjunto de posições **e área**; depois de booleana acusaria retesselação como alteração. Devolve `veredito`: `PRESERVADA` só com as duas medidas iguais; `ALTERADA` se a área mudar, ainda que o conjunto de posições seja idêntico; `INDETERMINADO` se a captura vier de versão que não media área |

**Exporte a peça antes de editar.** Custa um comando e transforma "0,0 em 45 pontos"
em "0,0 mm³ na caixa inteira". Medido num ensaio independente: `regiao_intacta`
devolveu **0,0 mm³** de divergência na região preservada e **5.616,0 mm³** quando a
caixa foi apontada para o vão que deveria mudar — o segundo número é o que prova que o
primeiro é medida e não silêncio. Ver `verificar.md` para o formato do requisito.

A comparação por posições agora **recusa** capturar ou comparar conjunto vazio. Isso
também foi um defeito meu durante a construção: a captura devolvia zero posições em
silêncio e a comparação ainda emitia veredito.

Medido no cenário correto: 18 pontos amostrados na superfície protegida, desvio
máximo **0.0** antes e depois.

### 10. Recuperar, salvar, entregar

Ver `recuperar_salvar_exportar.md`.

## Decisão por sintoma

| Sintoma | Diagnóstico | Ação |
|---|---|---|
| união "concluiu" mas a peça está estranha | meça perfil e degeneração separadamente | topologia limpa + perfil fora = forma errada, não defeito de malha |
| faces de área nula depois da união | esperado; conte-as | limpeza **local** com tolerância justificada, depois meça de novo |
| a limpeza abriu borda | tolerância grande demais para a peça | reduza, recupere pelo histórico, refaça |
| perfil com desvio constante em todo o trecho | os limites usados não são os acordados | reveja `limite_a`/`limite_b`, não a tolerância |
| limpeza devolve `reduziu: false` com `zerou: true` | **não havia degeneração**: é o resultado correto, não falha | siga em frente. **Não** repita a união: repetir é o que cria as 5 faces degeneradas da variante `duplicado` |
| aresta nova na face de topo protegida, em `limite − ov` | costura da sobreposição, esperada | confira **altura**, não contagem de vértices |
| perfil com `sem_material` em alguns pontos | o volume não cobre aquela faixa | reveja `y_de`/`y_ate` e a sobreposição |
| `houve_interseccao` falso | os limites não estão sobre material | quase sempre coordenada local usada como mundo; releia o diagnóstico |
| recusa nomeando uma zona sem material | aquela extremidade, ou o piso, não tem material onde o prisma passaria | **a peça não foi alterada**: a medida é em cópia, antes da união. Corrija o limite daquela ponta |
| região protegida acusa diferença após booleana | provavelmente retesselação | use amostragem de altura, não conjunto de posições |
| recusa por objeto girado | fora do domínio | aplicar rotação ou outra receita; **não** improvise |

## Exemplo sintético completo, com defeitos plantados

`cenarios/ensaio_preenchimento.py` executa o procedimento inteiro em três variantes.


> **Rodado assim, nesta máquina, em 08/09/2026.** O comando abaixo é uma linha só, de
> propósito: `\` no fim da linha é continuação de shell POSIX e **não** funciona no
> PowerShell, e `/tmp` não existe no Windows. O `--passa-resultado` entrega o caminho
> de `--resultado` ao script como último argumento, então ele é escrito **num lugar
> só** — antes era preciso repeti-lo dentro do arquivo de parâmetros, e duas grafias
> que divergissem davam `SEM_RESULTADO` com o arquivo existindo em outra pasta.

`cfg.json`: só a variante — o destino vem do `--passa-resultado`. O vocabulário é
**fechado** (`correta`, `ranhura`, `tangente`, `duplicado`, `flutuante`, `parcial`);
nome fora dele é recusado e a recusa é **gravada** no relatório como
`ESPEC_INVALIDA`, porque o lançador do Blender desanexa e um erro que só levanta não
deixa vestígio nenhum no chamador.

```json
{"variante": "correta"}
```

```powershell
python scripts/roda_blender.py cenarios/ensaio_preenchimento.py --resultado saida/ensaio.json --args cfg.json --passa-resultado --exigir veredito_global=ATENDIDO
```

Medido com esse comando: `"estado": "OK"`, `exigencia.obtido = "ATENDIDO"`,
`passos_com_estado_inesperado` vazio. Sem `--exigir`, um ensaio que **falhou** sairia
como OK com código de saída zero — o auxiliar só sabe dizer se o arquivo é legível.

`cenario` no `cfg.json` continua aceito, para ensaiar outras medidas
(`{"variante": "correta", "cenario": {"comprimento": 96.0, ...}}`).

Resultados **medidos**, e é assim que se sabe que cada detector faz o seu serviço:

| Variante | Topologia | Perfil | Protegida | Onde barra |
|---|---|---|---|---|
| `correta` | 0 aberta, 0 não-manifold, **0** degeneradas, 27 faces | desvio máx **0.0** em **99** pontos | desvio **0.0** em 18 pontos | não barra |
| `ranhura` | 0, 0, 0 — **limpa** | desvio máx **0.5**, fora da tolerância | 0.0, intacta | **só no perfil** |
| `duplicado` | **5 → 0** degeneradas, 39 → 34 faces | 0.0, **forma certa** | 0.0, intacta | **só na degeneração** |
| `flutuante` | não medida | não medida | não medida | **na medida de interseção**, antes de medir junção |
| `tangente` | não medida | não medida | não medida | **na pré-condição**, antes da união |
| outra medida (96×24×6, vão 30) | 0 degeneradas | 0.0 | 0.0 | não barra |
| girada 30° | não medida | não medida | não medida | **na pré-condição** de domínio |

As linhas `ranhura` e `duplicado` são o par que importa: **forma errada com topologia
limpa** e **topologia suja com a forma certa**. Nenhum dos dois detectores cobre o
outro caso, e é por isso que as medidas são separadas.

Nas variantes barradas, o relatório registra: *"o preenchimento não foi executado;
nada depois dele foi medido. Um resultado de etapa não prova outra."*

Antes de executar codigo especifico ou entregar uma edicao, consulte o contrato de
`fluxo_interativo.md`: captura anterior real, limites de aceite, identidade da selecao,
recuperacao e verificacao do arquivo exportado.
