# Verificar: o que cada medida prova, e o que ela não prova

**Após deslocamento localizado**, confira também quem absorveu o movimento:
`sessao_e_edicao_guiada.md`, seção 4, traz `verifica_deslocamento` e seus limites.
Área e ângulos da transição são indicadores condicionais; malha fechada e altura
correta do alvo não bastam. Não reprove uma quina intencional por ângulo alto nem
aprove uma parede colapsada porque seus triângulos não têm área zero.

A regra que organiza tudo aqui: **validade geométrica e atendimento ao pedido são
coisas diferentes**, e nenhuma delas se conclui pela aparência.

## As três famílias, que não se substituem

| Família | Pergunta | Ferramenta | O que NÃO prova |
|---|---|---|---|
| **topológica** | a malha é bem formada? | `mede_malha`, `check_mesh.py` | nada sobre a forma. Malha fechada pode ter a forma errada |
| **de forma** | a superfície está onde foi combinado? | `mede_topo_em_pontos`, `secao_por_plano` | nada sobre validade de malha |
| **de intenção** | atende ao requisito declarado? | `check_intent.py` | nada sobre imprimibilidade ou encaixe |

Uma peça pode passar nas três e ainda assim não servir: nenhuma delas é aprovação
para fabricação.

## Verificação topológica

```python
F.mede_malha("Peca")        # dentro do Blender
```
```bash
python verificadores/check_mesh.py --malha peca.stl     # fora, sobre o artefato entregue
```

As contagens vêm **separadas de propósito**:

| Medida | Por que separada |
|---|---|
| `arestas_abertas` | fronteira do material |
| `arestas_nao_manifold` | aresta com mais de duas faces |
| `arestas_soltas` | aresta sem face |
| `faces_degeneradas` | **área nula**. MEDIDO: a união booleana produz 4 delas sem abrir nenhuma borda. "Sem borda aberta" não é "sem degeneração". **Atenção ao limiar, que difere entre as duas ferramentas:** `bl_ferramentas.mede_malha` usa `1e-9` e devolve o valor usado em `limite_de_area_usado`; `check_mesh.py` usa `1e-12`, fixo no fonte e não reportado. São **três ordens de magnitude** de diferença: uma peça com faces muito pequenas pode ser classificada de forma diferente pelas duas, e a concordância entre elas **não** é confirmação mútua. Numa peça normal as duas medem 0 e a diferença não decide nada — o aviso existe para o caso em que decide |
| `n_componentes_conexos` | quantos corpos há de fato |

Armadilha medida em M0, que vale para qualquer leitor de STL: **STL não compartilha
vértices**. Sem soldar (`merge_vertices`), a adjacência de faces sai vazia e cada
faceta vira uma região isolada. Numa peça de referência a contagem caiu de 32.550
para 5.309 vértices depois de soldar. `check_mesh.py` já solda.

Outra, também de M0: **o status do kernel de malha não é oráculo de validade**. O
construtor solda em silêncio e devolveu `Error.NoError` para uma malha com 99 arestas
não-manifold. Confie nas contagens topológicas, não no status.

## Verificação de forma: é ela que pega ranhura

Nenhuma medida topológica detecta um degrau na junção. A que detecta compara a altura
medida com a **esperada**:

```python
pontos = [[x, y, z_esperado], ...]
r = F.mede_topo_em_pontos("Peca", pontos, tolerancia=0.01)
# r["desvio_maximo_absoluto"], r["todos_dentro_da_tolerancia"], r["n_sem_material"]
```

O esperado vem dos **limites acordados com o usuário**, não do que foi construído.

**Custo, medido.** A função testa cada ponto contra **todas** as faces. Com 100 pontos:

| Faces | Segundos |
|---|---|
| 6 | 0,002 |
| 54 | 0,009 |
| 93.750 | **24,4** |
| 705.894 | **185,7** |

São ~2,6 µs por par ponto-face, e cresce linear no produto. Em peça de poucas centenas
de faces é instantâneo; em malha de centenas de milhares, **conte minutos** e reduza o
número de pontos, ou secione em vez de amostrar.

MEDIDO: rampa construída 0,5 abaixo dos limites acordados → malha fechada, zero
não-manifold, zero degeneradas, região protegida intacta, e desvio de perfil de
exatamente **0,5**. Um defeito, um detector.

Erro de método a evitar, também medido: **não** compare dois pontos vizinhos de cada
lado do limite para achar "degrau". Numa superfície inclinada isso mede a inclinação
— numa rampa de inclinação 0,3, amostras a ±0,01 davam "degrau" de 0,006, puro
artefato.

Inspeção independente, por seção:

```python
F.secao_por_plano("Peca", ponto=[0, 20, 0], normal=[0, 1, 0])
```

Trata aresta coplanar, vértice sobre o plano e ponto duplicado, e declara quantas
faces coplanares ignorou. Prova **aquele plano**.

Armadilha medida em M0, se você seccionar fora do Blender com `shapely`: é preciso
**arredondar as coordenadas dos segmentos para 9 casas**, senão `polygonize` devolve
zero polígonos sem erro nenhum — 646 segmentos, 0 polígonos. E `polygonize` já
subtrai os furos da região de material: classificar furo por aninhamento 2D ingênuo
erra. `secoes.py` resolve os dois casos.

## Preservação: escolher a ferramenta certa

| Situação | Ferramenta | Motivo |
|---|---|---|
| há uma **referência** do estado anterior, em arquivo | **`check_intent.py`, tipo `regiao_intacta`** | é a única **exata**: recorta as duas peças pela caixa e mede o volume da **diferença simétrica**. Zero é zero, não amostra |
| a operação retessela e não há referência em arquivo | `mede_topo_em_pontos` sobre a região | amostragem; o conjunto de vértices muda por retesselação sem a superfície mudar |
| a operação não retessela (deslocamento puro) | `captura_regiao_protegida` + `compara_regiao_protegida` | compara posições **e área**, não índices. Área é o que separa retesselação de face removida |

**Prefira `regiao_intacta` quando puder.** Basta exportar a peça original antes de
editar e passá-la em `--referencia`:

```bash
python verificadores/check_intent.py --malha depois.stl --referencia antes.stl --requisitos req.json
```

```json
{"requisitos": [{"id": "topo_intacto", "tipo": "regiao_intacta",
                 "caixa_min": [0.0, 0.0, 20.0], "caixa_max": [12.0, 26.0, 21.5],
                 "tol_fracao": 1e-9}]}
```

**A tolerância deste tipo é `tol_fracao`, e só ela.** O exemplo anterior usava
`tol_mm3`, que o verificador **não lê** para `regiao_intacta`: o número estava ali sem
participar da decisão. Uma revisão independente apontou. `tol_fracao` é a fração do
volume da caixa que se admite divergir, e o padrão interno é `1e-9`.

Cada tipo tem a sua, e passar a errada é passar um número que não decide nada:

| `tipo` | Tolerância que o verificador lê | Valor que decide se você **não** declarar |
|---|---|---|
| `caixa` | `tol_mm` | 0,05 |
| `distancia_entre_furos` | `tol_mm` | 0,2 |
| `volume` | `tol_mm3` | `max(1,0; 1% do volume esperado)` |
| `interferencia` | `tol_mm3` | 0,0 |
| `furo` | `tol_pos_mm`, **`tol_mm`** (diâmetro), `circularidade_min` | 0,2 · **0,2** · 0,90 |
| `regiao_intacta` | `tol_fracao` | 1e−9 |
| `n_solidos`, `n_furos_no_plano` | **nenhuma**: contagem é exata | — |

**Não declarar não é "sem margem": é aceitar a da terceira coluna.** Uma sessão limpa
teve dois requisitos de furo aprovados por uma tolerância de diâmetro de 0,2 que ela
não escolheu e que não estava escrita em lugar nenhum. Se o número importa, declare-o.

**Atenção ao nome:** em `furo`, a tolerância de diâmetro **entra** como `tol_mm` e
**sai** no relatório como `tol_diam_mm`. São o mesmo número com dois nomes.

`scripts/valida_requisitos.py` confere isso e recusa tolerância que **este tipo** não
lê; `--tipos` lista a tabela, os padrões e os nomes que mudam na saída.

Esta tabela **não é transcrita**: `scripts/extrai_tolerancias.py` a extrai do fonte do
verificador, e `scripts/testa_paridade_validador.py` reprova se a tabela do validador
divergir da extraída. O motivo é concreto: a versão anterior era transcrita à mão, com
o comentário "conferido no fonte tipo por tipo", e estava **errada** em `furo` — o
validador recusava `tol_mm`, dizendo que o verificador não a lê, quando ele lê e
**decide** com ela. O erro sobreviveu a uma rodada inteira de revisão porque estava
protegido por uma afirmação, não por uma medida.

**Códigos de saída**, para quem automatiza: `check_intent.py` sai **1** quando há
requisito reprovado e **0** quando todos passam; `sweep_params.py` sai **1** com
variante reprovada; `valida_requisitos.py` sai **1** em `FORMA_INVALIDA`. E
`scripts/roda_blender.py` sai **1** em qualquer estado diferente de `OK` — mas
**cuidado**: sem `--exigir CAMPO=VALOR`, ele considera `OK` qualquer relatório
legível, inclusive um que diga `veredito_global: FALHOU`.

Medido num ensaio independente: divergência **0,0 mm³** na região preservada, e
**5.616,0 mm³** quando a mesma caixa foi apontada para o vão que **deveria** mudar —
o que prova que o zero anterior era medida, não silêncio.

Aviso sobre o próprio verificador: o cabeçalho do módulo, na linha 21, descreve
`regiao_intacta` como "por amostragem". **Está desatualizado.** A implementação, na
linha 325, diz e faz o contrário, e é ela que vale: *"Não usa amostragem de pontos nem
ponto-dentro-do-sólido. […] recorta as duas peças pela caixa e mede o volume da
diferença simétrica. Zero é zero, não amostra."* O arquivo não foi editado aqui de
propósito: ele é cópia byte a byte da base estabilizada.

Duas coisas que **não** provam preservação, e a segunda foi medida durante a
construção desta receita:

1. contar faces cujos vértices caem numa caixa — triângulo pode atravessar a caixa;
2. comparar um conjunto **vazio** — a captura devolvia zero posições em silêncio e a
   comparação ainda emitia veredito. Hoje as duas funções recusam conjunto vazio.

Contagem de faces igual, ou dimensão externa igual, também não provam preservação.

## Verificação de intenção

```bash
python verificadores/check_intent.py --malha peca.stl --requisitos req.json
```

**`--malha` é obrigatório**, e é ele que define a peça medida. Sem ele a ferramenta
sai com erro de argumento. O arquivo de requisitos pode trazer um campo `peca`, mas
quem manda é `--malha`.

### O formato do arquivo de requisitos

O arquivo é um **objeto** com a chave `requisitos`, nunca uma lista nua. Lista nua
produz erro não tratado, e não `ESPEC_INVALIDA`:

```json
{"requisitos": [
  {"id": "envelope", "tipo": "caixa", "valor": [44.0, 26.0, 21.0], "tol_mm": 0.5},
  {"id": "um_corpo", "tipo": "n_solidos", "valor": 1}
]}
```

**Confira a forma antes de medir.** Passar uma lista nua — a leitura mais natural do
formato — produz um **traceback não tratado** dentro do verificador, e não
`ESPEC_INVALIDA`. O verificador é derivado da base, com alterações registradas em PROVENIENCIA.json; a guarda mora
fora dele:

```bash
python scripts/valida_requisitos.py req.json
python scripts/valida_requisitos.py --tipos     # lista tipos, campos e tolerâncias
```

Ele responde **uma** pergunta: o arquivo está na forma que o verificador espera. Forma
aceitável não diz nada sobre a peça. Medido, com controle positivo: arquivo bem
formado sai `OK`; lista nua, tipo inexistente, campo faltando, identificador repetido,
lista vazia e medida sem tolerância saem `FORMA_INVALIDA` com o motivo. Ele também diz
quais tipos exigem `--referencia`.

Todo requisito precisa de `id` e `tipo`. **Identificadores repetidos são recusados.**
Os tipos disponíveis, com os campos que cada um exige:

| `tipo` | Campos obrigatórios | O que mede |
|---|---|---|
| `caixa` | `valor` com 3 números | dimensões da caixa envolvente |
| `volume` | `valor` | volume; exige malha fechada |
| `n_solidos` | `valor` | quantos corpos há |
| `furo` | `eixo`, `plano`, `posicao` com 2, `diametro` | um furo em posição e diâmetro |
| `n_furos_no_plano` | `eixo`, `plano`, `valor` | quantos furos naquele plano |
| `distancia_entre_furos` | `eixo`, `plano`, `valor` | distância entre dois furos |
| `regiao_intacta` | `caixa_min` com 3, `caixa_max` com 3, `tol_fracao`, e `--referencia` na chamada | ver abaixo: é a medida **exata** de preservação |
| `interferencia` | `entre` com dois caminhos, **ou** `com` com um | dois corpos ocupando o mesmo espaço. `entre` compara duas partes; `com` compara a malha principal com outra |

Tolerâncias aceitas, conforme o tipo: `tol_mm`, `tol_mm3`, `tol_pos_mm`,
`tol_fracao`, `circularidade_min`.

**Tipo de contagem não precisa de tolerância**, e exigir uma seria erro: `n_solidos` e
`n_furos_no_plano` comparam inteiros, e contar três corpos é exato. Medir 30 mm não é.
É a mesma regra do método — igualdade é legítima em contagem inteira e proibida em
medida — e o validador deste pacote a violou na primeira versão, recusando um
requisito que o verificador aceita.

Estados possíveis por requisito, e eles não colapsam. **Esta lista é a do
verificador**, conferida no fonte:

| Estado | Significa |
|---|---|
| `APROVADA` / `REPROVADA` | medido e decidido |
| `NAO_IMPLEMENTADA` | o tipo existe no contrato e **não há medidor** |
| `ESPEC_INVALIDA` | a declaração não é executável |
| `ERRO` | **falha operacional**, com causa própria — não é reprovação geométrica |
| `INDETERMINADA` | não deu para decidir |

`NAO_APLICAVEL` **não** é estado deste verificador: ele vem do mapa de papéis de
`matriz.py`, que é outra ferramenta. Confundir os dois faz dispensa parecer resultado.

`NAO_IMPLEMENTADA` **barra quando o papel é decisivo** e não barra quando é
informativo. Em nenhum dos casos se preenche com valor favorável, zero ou estimativa.

Falha operacional — permissão, disco, dependência ausente — **nunca** vira reprovação
geométrica. Ela tem código e etapa próprios, e a variante não entra na contagem de
reprovadas por geometria.

## Quais verificações são exigidas

Não é uma lista fixa: sai da classificação.

```bash
python verificadores/matriz.py criar solido impressao_fdm
python verificadores/matriz.py criar superficie visualizacao '{"borda":"proibida","estanqueidade":"exigida"}'
```

**O vocabulário é fechado**, e a ferramenta recusa termo fora dele em vez de adivinhar:

| Decisão | Valores aceitos |
|---|---|
| modalidade | `criar`, `editar`, `reconstruir`, `reparar`, `parametrizar` |
| representação | `solido`, `superficie`, `malha`, `montagem` |
| finalidade | `visualizacao`, `intercambio`, `montagem`, `impressao_fdm`, `usinagem` |

Repare em `impressao_fdm`: **`impressao` sozinho é recusado**. Em prosa se fala
"impressão"; no comando, o termo é `impressao_fdm`.

A topologia declarada manda nas dispensas que dependem dela: `superficie` **não**
implica casca aberta, e numa casca fechada sem sólido a estanqueidade é exigida pela
topologia mesmo quando a finalidade sozinha não a pediria.

Verificação dispensada **não é** verificação aprovada.

## Exportação não é verificação

Exportar com sucesso, inclusive em 3MF, não prova validade geométrica. MEDIDO em M0:
na variante com tangência, o escritor de 3MF **aceitou** a malha, e quem reprovou foi
o portão de malha. A ideia de que o formato fechado recusa o que o STL aceita **não
se sustenta** nesta versão da biblioteca.

Confira sempre o artefato entregue, e não a peça que você acha que exportou:

```bash
python verificadores/check_mesh.py --malha entregue.stl
```

## Declarar o alcance, sempre

Toda saída destas ferramentas traz um campo `limite`. Repasse-o. Amostragem prova os
pontos amostrados; uma seção prova aquele plano; uma caixa prova aquela caixa.
Conclusão sem alcance declarado não vale, e "passou em tudo" sem dizer em quê é a
forma mais comum de aprovar sem evidência.
