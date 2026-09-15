<!-- Relatorio de sessao limpa E, preservado no repositorio. Operador: subagente
sem historico deste projeto, modelo claude-opus-5. Pacote sob ensaio: 1.8.0,
montado e nunca executado, hash 6a46d09a. Rota ensaiada: EDICAO no Blender
headless (a sessao D havia percorrido a rota de criar por codigo). Nada aqui foi
editado por mim: os nove achados estao como ele escreveu. -->

# Relatório — rota de EDIÇÃO (preencher vão) com o pacote `pacote_intocado_18`

Sessão limpa, sem histórico do pacote. Blender **headless** apenas
(`--background --factory-startup`, via `scripts/roda_blender.py`). **Não** foi usado
`scripts/mcp_blender.py` nem qualquer contato com `127.0.0.1:9876`: a sessão viva do
usuário não foi tocada.

- Pasta da habilidade (só leitura): `C:\Users\<usuario>\AppData\Local\Temp\pacote_intocado_18`
- Python do hospedeiro: `C:\Users\<usuario>\AppData\Local\Temp\ensaio_isolado_18\venv\Scripts\python.exe`
- Pasta de trabalho (tudo que escrevi): `C:\Users\<usuario>\AppData\Local\Temp\sessao_limpa_E`
- Blender localizado: `C:\Users\<usuario>\AppData\Local\Microsoft\WindowsApps\blender-launcher.exe`
  (5.2.1 LTS), achado pelo alias de execução do Windows.
- `bl_ferramentas` conferida **dentro** do Blender: `confere_versao("1.5.0")` →
  `{"versao": "1.5.0", "confere": true}`. `INVENTARIO.json` declara a mesma versão.

## 0. A peça: minhas dimensões, não as do exemplo

Bloco `bloco_E`, **90 × 30 × 26**, com dois patamares de alturas diferentes separados
por um vão:

| Elemento | Extensão em x | Topo (z) |
|---|---|---|
| base | 0 → 90 | 8 |
| patamar alto | 0 → 25 | **26** |
| vão | 25 → 65 | piso em 8 |
| patamar baixo | 65 → 90 | **17** |

Vão = **40,0**. Queda a vencer = **9,0**. (O exemplo do pacote é 60 × 40 × 10 com vão
de 20 e patamares em 20/14 — nenhum número meu vem dele.)

Volume calculado à mão antes de rodar: `90·30·8 + 25·30·18 + 25·30·9` = **41 850**.
Medido pelo gerador: **41 850,0**.

---

## 1. Comandos, na íntegra, com diretório e código de saída

Diretório corrente de **todos** os comandos executáveis:
`C:\Users\<usuario>\AppData\Local\Temp\sessao_limpa_E`.
Abreviaturas usadas abaixo apenas para caber na linha — nos comandos reais tudo é
caminho absoluto:
`PY = C:\Users\<usuario>\AppData\Local\Temp\ensaio_isolado_18\venv\Scripts\python.exe`,
`PK = C:\Users\<usuario>\AppData\Local\Temp\pacote_intocado_18`,
`WK = C:\Users\<usuario>\AppData\Local\Temp\sessao_limpa_E`.

Antes de qualquer execução houve **8 comandos de leitura** (`cat`/`sed`/`grep`/`find`)
sobre `SKILL.md`, `INVENTARIO.json`, as 6 referências e 4 fontes
(`scripts/bl_ferramentas.py`, `scripts/roda_blender.py`, `cenarios/gera_cenario.py`,
`cenarios/ensaio_preenchimento.py`). Nenhum deles escreveu nada.

Todas as execuções levaram `PYTHONDONTWRITEBYTECODE=1` no ambiente, e o script de
dentro do Blender faz `sys.dont_write_bytecode = True` **antes** de importar
`bl_ferramentas` — precaução para não criar `__pycache__` dentro da pasta da
habilidade (ver §4, item 8).

### C1 — localizar o Blender
```
PYTHONDONTWRITEBYTECODE=1 "PY" "PK\scripts\roda_blender.py" --achar
```
**Saída = 0.** `{"executavel": "...blender-launcher.exe", "como": "alias de execucao do Windows"}`

### C2 — escrever meus parâmetros (`heredoc`, sem execução)
Criou `WK\param_bloco.json`. **Saída = 0.**

### C3 — construir a peça em Blender headless *(primeira execução bem-sucedida)*
```
PYTHONDONTWRITEBYTECODE=1 "PY" "PK\scripts\roda_blender.py" "PK\cenarios\gera_cenario.py" --resultado "WK\saida\cenario.json" --args "WK\param_bloco.json" --passa-resultado
```
**Saída = 0.** `estado: "OK"`, 1,92 s. `medidas`: 20 vértices, 16 faces, 0 abertas,
0 não-manifold, 0 degeneradas, volume **41 850,0**. Gravou `saida\bloco_E.blend`.

### C4 — preencher o vão, variante correta
```
PYTHONDONTWRITEBYTECODE=1 "PY" "PK\scripts\roda_blender.py" "WK\passo_preenche.py" --cena "WK\saida\bloco_E.blend" --resultado "WK\saida\correta.json" --args "WK\cfg_correta.json" --passa-resultado --exigir veredito_global=ATENDIDO
```
**Saída = 0.** `estado: "OK"`, `exigencia.obtido = "ATENDIDO"`, 2,12 s.

### C5 — extrair os números de `correta.json` (script meu, `PY -c`)
**Saída = 1.** `TypeError: 'float' object is not subscriptable`. Causa: eu supus que
`volume_de_material_na_caixa` devolvesse dicionário. Ver §4, item 2. **Não** afetou a
execução no Blender (C4 já tinha terminado); afetou a minha leitura e um trecho do meu
script que só roda no caminho barrado.

### C6 — corrigir `passo_preenche.py` (edição, sem execução)
**Saída = 0.**

### C7 — reextrair os números
**Saída = 0.**

### C8 — CONTROLE NEGATIVO 1 (`limite_b` fora do material)
```
PYTHONDONTWRITEBYTECODE=1 "PY" "PK\scripts\roda_blender.py" "WK\passo_preenche.py" --cena "WK\saida\bloco_E.blend" --resultado "WK\saida\nc1.json" --args "WK\cfg_limite_b_fora.json" --passa-resultado --exigir veredito_global=ATENDIDO
```
**Saída = 1.** `estado: "VEREDITO_NEGATIVO"`,
`obtido = "BARRADO_ANTES_DE_ALTERAR"`. **Era o esperado.**

### C9 — ler as provas do NC1
**Saída = 0.**

### C10 — CONTROLE NEGATIVO 2 (rampa 0,6 abaixo do acordado)
```
PYTHONDONTWRITEBYTECODE=1 "PY" "PK\scripts\roda_blender.py" "WK\passo_preenche.py" --cena "WK\saida\bloco_E.blend" --resultado "WK\saida\nc2.json" --args "WK\cfg_ranhura.json" --passa-resultado --exigir veredito_global=ATENDIDO
```
**Saída = 1.** `estado: "VEREDITO_NEGATIVO"`, `obtido = "FALHOU"`. **Era o esperado.**

### C11 — ler as provas do NC2
**Saída = 0.**

### C12 — conferir a malha do artefato **que está no disco**
```
PYTHONDONTWRITEBYTECODE=1 "PY" "PK\verificadores\check_mesh.py" --malha "WK\saida\correta_depois.stl"
```
**Saída = 0.** Números em §3.

### C13 — conferir a **forma** dos dois arquivos de requisitos
```
PYTHONDONTWRITEBYTECODE=1 "PY" "PK\scripts\valida_requisitos.py" "WK\req_correta.json"
PYTHONDONTWRITEBYTECODE=1 "PY" "PK\scripts\valida_requisitos.py" "WK\req_controle_vao.json"
```
**Saída = 0** nos dois. `estado: "OK"`, `tipos_que_exigem_referencia: ["regiao_intacta"]`.

### C14 — verificar a intenção declarada, com referência em arquivo
```
PYTHONDONTWRITEBYTECODE=1 "PY" "PK\verificadores\check_intent.py" --malha "WK\saida\correta_depois.stl" --referencia "WK\saida\correta_antes.stl" --requisitos "WK\req_correta.json"
```
**Saída = 0.** 5 requisitos, **5 aprovados**, `atende_ao_pedido: true`.

### C15 — CONTROLE do próprio verificador: caixa apontada para o **vão**
```
PYTHONDONTWRITEBYTECODE=1 "PY" "PK\verificadores\check_intent.py" --malha "WK\saida\correta_depois.stl" --referencia "WK\saida\correta_antes.stl" --requisitos "WK\req_controle_vao.json" > saida\intent_controle_vao.json
```
**Saída = 1.** `REPROVADA`, divergência **16 200,0 mm³**. É este número que prova que os
`0,0 mm³` de C14 são medida e não silêncio.

### C16 — os verificadores externos sobre o artefato **ERRADO** (NC2)
```
PYTHONDONTWRITEBYTECODE=1 "PY" "PK\verificadores\check_mesh.py" --malha "WK\saida\nc2_depois.stl" > saida\mesh_nc2.json
PYTHONDONTWRITEBYTECODE=1 "PY" "PK\verificadores\check_intent.py" --malha "WK\saida\nc2_depois.stl" --referencia "WK\saida\nc2_antes.stl" --requisitos "WK\req_correta.json" > saida\intent_nc2.json
```
`check_mesh` **saída = 0** (`"acao": "Pode seguir."`);
`check_intent` **saída = 1** (`volume_com_a_rampa` REPROVADA).

### C17 — provar que não escrevi na pasta da habilidade
```
find "PK" -name "__pycache__" -o -name "*.pyc"            # vazio
find "PK" -type f -printf "%T@ ... %p\n" | sort -n        # 24 arquivos, mtime máx 03:31
PYTHONDONTWRITEBYTECODE=1 "PY" -c "<sha256 de cada entrada de INVENTARIO.json>"
```
**Saída = 0.** `conferidos_ok=23 divergentes=0 faltando=0`. O 24º arquivo é o próprio
`INVENTARIO.json`, que não consta do seu manifesto.

---

## 2. Arquivos que eu criei (todos dentro da pasta de trabalho)

| Caminho completo | O que é |
|---|---|
| `C:\Users\<usuario>\AppData\Local\Temp\sessao_limpa_E\RELATORIO.md` | este relatório |
| `...\sessao_limpa_E\param_bloco.json` | minhas dimensões, entrada de `gera_cenario.py` |
| `...\sessao_limpa_E\passo_preenche.py` | meu script de dentro do Blender: segue `editar_localizado.md` parte 2 |
| `...\sessao_limpa_E\cfg_correta.json` | variante correta |
| `...\sessao_limpa_E\cfg_limite_b_fora.json` | controle negativo 1 |
| `...\sessao_limpa_E\cfg_ranhura.json` | controle negativo 2 |
| `...\sessao_limpa_E\req_correta.json` | 5 requisitos declarados |
| `...\sessao_limpa_E\req_controle_vao.json` | requisito que **tem** que reprovar |
| `...\sessao_limpa_E\saida\cenario.json` | relatório do gerador |
| `...\sessao_limpa_E\saida\bloco_E.blend` | peça antes de editar — sha256 `d1194694…` |
| `...\sessao_limpa_E\saida\correta.json` | relatório completo da variante correta |
| `...\sessao_limpa_E\saida\correta_antes.stl` | 1 884 B — sha256 `f0401e03…` (referência exata) |
| `...\sessao_limpa_E\saida\correta_depois.stl` | 3 884 B — sha256 `5d0c4c39…` (**a entrega**) |
| `...\sessao_limpa_E\saida\correta_depois.blend` | 89 677 B — sha256 `d5240587…` |
| `...\sessao_limpa_E\saida\nc1.json` | relatório do controle 1 |
| `...\sessao_limpa_E\saida\nc1_antes.stl` | 1 884 B — sha256 `f0401e03…` |
| `...\sessao_limpa_E\saida\nc2.json` | relatório do controle 2 |
| `...\sessao_limpa_E\saida\nc2_antes.stl` | 1 884 B — sha256 `f0401e03…` |
| `...\sessao_limpa_E\saida\nc2_depois.stl` | 4 284 B — sha256 `21816d6c…` (peça errada) |
| `...\sessao_limpa_E\saida\nc2_depois.blend` | 89 730 B — sha256 `c7030ed6…` |
| `...\sessao_limpa_E\saida\mesh_nc2.json` | `check_mesh` do artefato errado |
| `...\sessao_limpa_E\saida\intent_nc2.json` | `check_intent` do artefato errado |
| `...\sessao_limpa_E\saida\intent_controle_vao.json` | controle da caixa apontada para o vão |

Os **três** `*_antes.stl` têm o mesmo sha256 `f0401e03…`: as três variantes partiram da
peça idêntica. Isso é o que torna os controles comparáveis.

**Não existe `nc1_depois.stl` nem `nc1_depois.blend`** — e essa ausência é parte da
prova do controle 1: a operação foi barrada antes de alterar a peça, portanto não houve
nada para exportar.

---

## 3. Cada número medido, com tolerância e procedência

### 3.1 Sobreposição e tolerâncias — de onde saíram

| Parâmetro | Valor | Procedência |
|---|---|---|
| `sobreposicao` | **2,0** | um vigésimo do **meu** vão (40,0 / 20). A receita exige o parâmetro *e* `origem_da_sobreposicao`, e diz explicitamente que copiar o 1,0 do exemplo é erro. Derivei do meu vão. |
| tolerância de perfil | **0,01** | **derivada por mim** (a pasta usa 0,01 nos exemplos sem justificar — §4, item 5): duas ordens abaixo do menor detalhe da peça (a sobreposição de 2,0) e três ordens **acima** do ruído de precisão simples que o próprio pacote mediu (1e-6 a 3e-6). |
| tolerância de limpeza | **1e-5** | cinco ordens abaixo do menor detalhe a preservar (2,0) e acima da precisão de coincidência do solver EXACT. Justificativa é **obrigatória** na função. |
| `tolerancia_de_uniao` da seção | **1e-5** (padrão) | do pacote: uma ordem acima do ruído medido (1e-6…3e-6) e abaixo de qualquer detalhe. Conferido no retorno. |
| `tol_mm` do envelope | **0,05** | valor que `verificar.md` declara como padrão do tipo `caixa`; declarei-o explicitamente para não aceitar padrão não escolhido. |
| `tol_mm3` do volume | **5,0** | ~1e-4 do volume esperado; acima do ruído residual do solver que **eu medi** (≈5e-4 na variante oblíqua) e **116× mais apertado** que o padrão não declarado (`max(1; 1% de 58 050)` = 580,5). |
| `tol_fracao` de `regiao_intacta` | **1e-9** | é a única tolerância que este tipo lê (`verificar.md` corrige a versão que usava `tol_mm3`); 1e-9 é também o padrão interno, declarado por escolha. |
| `n_solidos` | sem tolerância | contagem inteira é exata; exigir tolerância aqui seria erro. |

### 3.2 A operação preencheu, e interceptou material nas TRÊS zonas

Medido **em cópia, antes de alterar a peça** (`interseccao_por_zona`):

| Zona | Caixa medida | Volume de material | Calculado à mão |
|---|---|---|---|
| `extremo_do_limite_a` | [23,0,6] → [25,30,26] | **1 200,0** | 2 · 20 · 30 = 1 200 |
| `extremo_do_limite_b` | [65,0,6] → [67,30,17] | **660,0** | 2 · 11 · 30 = 660 |
| `abaixo_do_piso` | [23,0,6] → [67,30,8] | **2 640,0** | 44 · 2 · 30 = 2 640 |

Corroboração aritmética: peça 41 850,0 + ferramenta 20 460,0 − união 58 050,0 =
interseção **4 260,0**; calculado à mão (40 + 80 + 22) · 30 = 4 260. `houve_interseccao: true`.

### 3.3 A superfície liga os dois limites

- **Perfil**: `mede_topo_em_pontos`, tolerância 0,01, contra o perfil que os **limites
  acordados** implicam (26 em x ≤ 25, 17 em x ≥ 65, reta entre eles).
  **99 pontos**, **33 posições distintas em x**, 3 planos de y (3,0 / 15,0 / 27,0).
  **`desvio_maximo_absoluto = 0.0`**, `n_sem_material = 0`,
  `todos_dentro_da_tolerancia = true`.
  Amostragem = grade uniforme de 15 pontos em [25 − 3·2, 65 + 3·2] **mais** pontos
  densos com k **simétrico** `−1,5 −1 −0,5 −0,25 0 +0,25 +0,5 +1 +1,5` em torno de
  **cada** limite. Critério executável conferido: as **duas** costuras, em
  `25 − 2 = 23,0` e `65 + 2 = 67,0`, estão entre os x amostrados (`true` nas duas).
- **Seção independente** (`secao_por_plano`, ponto [0, 15, 0], normal [0,1,0]),
  10 pontos, 10 segmentos, 0 faces coplanares ignoradas,
  `faces_com_mais_de_dois_cruzamentos = 0`: o topo sai
  (0; 26) → (23; 26) → (25; 26) → **segmento único** → (65; 17) → (67; 17) → (90; 17).
  O segmento `[9,6]` liga exatamente (65; 17) a (25; 26): é a prova de que a superfície
  toca os **dois** limites, e de que na zona de sobreposição o topo é **horizontal na
  altura do limite** — nenhum ponto acima de 26 em x < 25.
  **Alcance: prova este plano (y = 15), não a peça.**
- **Volume**: 41 850,0 → **58 050,0**. Diferença 16 200,0 = o trapézio que os limites
  implicam (`(26+17)/2 − 8 = 13,5`; `13,5 · 40 · 30 = 16 200`).

### 3.4 A malha continua fechada e sem defeito topológico

`mede_malha` depois da união e da limpeza:

| Medida | Valor |
|---|---|
| `arestas_abertas` | **0** |
| `arestas_nao_manifold` | **0** |
| `arestas_soltas` | **0** |
| `faces_degeneradas` | **0** |
| `n_componentes_conexos` | **1** |
| faces / vértices | 27 / 40 (eram 16 / 20) |

A união desta peça saiu com **0** degeneradas (coerente com a correção documentada: o
topo horizontal na sobreposição é coplanar e o solver EXACT lida melhor com isso que
com interseção oblíqua). A limpeza local devolveu
`degeneradas_antes: 0, degeneradas_depois: 0, reduziu: false, zerou: true,
abriu_borda: false` — que é exatamente o caso listado na tabela de sintomas
("não havia degeneração: é o resultado correto"). **Não repeti a união.**

Conferido **no artefato do disco**, não na peça que eu achava que exportei
(`check_mesh.py --malha correta_depois.stl`): 76 triângulos, 228 vértices antes de
soldar → **40 depois**, `fechada_watertight: true`, **euler = 2**, 0 arestas abertas,
0 com mais de 2 faces, 0 facetas degeneradas, 0 duplicadas, orientação consistente,
**1 componente**, `volume_mm3 = 58 050,0`, caixa `[90, 30, 26]`,
`apto_para_booleana: true`, `motivos_de_reprovacao: []`.
O volume do disco (58 050,0) bate com o medido na cena (58 050,0), e a assinatura de
geometria do export (`09aeb669…`) bate com a assinatura da peça no momento da entrega.

### 3.5 A região que não devia mudar não mudou

Duas medidas de naturezas diferentes, como manda `verificar.md`:

1. **Exata**, `check_intent.py` tipo `regiao_intacta`, com `correta_antes.stl` em
   `--referencia` (diferença simétrica booleana recortada pela caixa):

| Requisito | Caixa | Peça na caixa | Referência na caixa | Divergência | `tol_fracao` |
|---|---|---|---|---|---|
| `topo_do_patamar_alto_intacto` | [0,0,8]→[22,30,27] | 11 880,0 | 11 880,0 | **0,0 mm³** | 1e-9 |
| `topo_do_patamar_baixo_intacto` | [69,0,8]→[90,30,18] | 5 670,0 | 5 670,0 | **0,0 mm³** | 1e-9 |

2. **Amostragem de altura** (a que é válida depois de booleana, porque a costura
   retessela sem mudar a superfície): `mede_topo_em_pontos` em **51 pontos** sobre o
   topo do patamar alto, incluindo `x = 23,0` (a costura) e `x = 24,0`,
   tolerância 0,01 → `desvio_maximo_absoluto = 0.0` **antes** e **0.0 depois**.

**E o controle que dá sentido aos zeros acima**: a mesma verificação, com a caixa
apontada para o vão ([25,0,8]→[65,30,26]) devolveu
`volume_da_peca_na_caixa = 16 200,0`, `volume_da_referencia_na_caixa = 0,0`,
`volume_de_divergencia = 16 200,0 mm³`, `fracao_divergente = 0,75`, **REPROVADA**,
código de saída 1. Sem esse número, os `0,0 mm³` seriam indistinguíveis de um
verificador mudo.

### 3.6 Requisitos declarados (`check_intent.py`, 5 de 5 aprovados)

| id | tipo | medido | esperado | tolerância |
|---|---|---|---|---|
| `envelope` | `caixa` | [90,0; 30,0; 26,0] | [90,0; 30,0; 26,0] | `tol_mm` 0,05 (desvio 0,0) |
| `um_corpo` | `n_solidos` | 1 | 1 | nenhuma (contagem exata) |
| `volume_com_a_rampa` | `volume` | 58 050,0 mm³ | 58 050,0 mm³ | `tol_mm3` 5,0 (desvio 0,0) |
| `topo_do_patamar_alto_intacto` | `regiao_intacta` | 0,0 mm³ | 0 | `tol_fracao` 1e-9 |
| `topo_do_patamar_baixo_intacto` | `regiao_intacta` | 0,0 mm³ | 0 | `tol_fracao` 1e-9 |

### 3.7 Recuperação, conferida pelo conteúdo

Um ponto de histórico **antes** e **um depois** da operação lógica inteira (união +
limpeza), como manda `recuperar_salvar_exportar.md` — não um por chamada.

- assinatura antes `51a42ee5…`, depois `09aeb669…`
- `contexto_de_historico`: `undo_pollavel: true`
- `desfaz_e_confere(51a42ee5…)` → **`recuperou: true`**
- `refaz_e_confere(09aeb669…)` → **`recuperou: true`**
- depois do redo, `assinatura_agora == assinatura_exportada` → **true**
  (o artefato no disco corresponde ao estado final)
- `salva_cena` → `correta_depois.blend`, `retorno_do_operador: ["FINISHED"]`,
  89 677 B, sha256 `d5240587…`, `havia_arquivo_antes: false` (não sobrescreveu origem)

**Alcance declarado:** vale para este caminho — construção por dados, união EXACT,
limpeza local, tudo em background. Não é promessa para todo operador nem para sessão
viva.

### 3.8 CONTROLE NEGATIVO 1 — barrado **antes** de alterar a peça

Natureza: **pré-condição de interseção**. `limite_b = {"x": 95,0, "z": 17,0}`, isto é,
5 unidades além do fim da peça (x = 90).

`ErroDePrecondicao`, texto integral devolvido:

> o volume de preenchimento nao encontraria material em `['extremo_do_limite_b']`, e a
> receita promete interceptar nos DOIS extremos e abaixo do piso. Nada foi alterado na
> peca: a medida e feita em copia, antes da uniao. Medidas por zona:
> `{'extremo_do_limite_a': 1200.0, 'extremo_do_limite_b': 0.0, 'abaixo_do_piso': 4020.0}`.
> Causa mais comum: limites calculados em coordenada local e usados como se fossem de mundo.

**Por que este controle vale:** o total das três zonas é **5 220,0** — um escalar único
de "houve alguma interseção" teria **aprovado**. O que barra é a zona `b` medida
**separadamente**, em **0,0**.

Prova de que a peça não foi tocada (medida depois da recusa):

| | antes | depois da recusa |
|---|---|---|
| assinatura sha256 | `51a42ee5104bd07465e9…` | `51a42ee5104bd07465e9…` (**idênticas**) |
| volume | 41 850,0 | 41 850,0 |
| faces / vértices | 16 / 20 | 16 / 20 |
| abertas / não-manifold / degeneradas / componentes | 0 / 0 / 0 / 1 | 0 / 0 / 0 / 1 |

E: nenhum `nc1_depois.stl` foi gravado. `roda_blender.py` saiu com **código 1** e
`VEREDITO_NEGATIVO` porque `veredito_global` veio `BARRADO_ANTES_DE_ALTERAR`.
Nada depois do preenchimento foi medido, e o relatório diz isso:
*"o preenchimento NAO foi executado; nada depois dele foi medido. Um resultado de etapa
nao prova outra."*

### 3.9 CONTROLE NEGATIVO 2 — a peça sai errada e a verificação acusa

Natureza **diferente** da anterior: aqui a operação **é executada** e conclui com
sucesso; o defeito é de **forma**. Passei `limite_a.z = 25,4` e `limite_b.z = 16,4`,
0,6 abaixo dos limites acordados (26 e 17), e medi contra o perfil **acordado**.

O que **não** acusou (e é o ponto):

| Detector | Resultado no artefato errado |
|---|---|
| `mede_malha` na cena | 0 abertas, 0 não-manifold, 0 soltas, **0 degeneradas**, 1 componente, 27 faces |
| `check_mesh.py` no `nc2_depois.stl` do disco | `fechada_watertight: true`, euler 2, 0/0/0, 1 componente, `apto_para_booleana: true`, `motivos_de_reprovacao: []`, **`"acao": "Pode seguir."`**, saída 0 |
| `envelope` (`caixa`) | **APROVADA**, [90,0; 30,0; 26,0], desvio 0,0 |
| `um_corpo` (`n_solidos`) | **APROVADA**, 1 |
| `regiao_intacta` nos dois patamares | **APROVADA**, 0,0 mm³ nas duas caixas |
| região protegida por amostragem | **0,0** em 51 pontos |
| as 3 zonas de interseção | todas interceptam (1 164,0 / 624,0 / 2 640,0) |

O que **acusou**:

| Detector | Resultado |
|---|---|
| `mede_topo_em_pontos`, tol 0,01, contra o perfil acordado | **`desvio_maximo_absoluto = 0,6`**, **57 de 99 pontos fora da tolerância**, todos com desvio exatamente **−0,6** (ex.: x=25,5 esperado 25,8875 medido 25,2875; x=28,0 esperado 25,325 medido 24,725) |
| `secao_por_plano` em y = 15 | dois pontos distintos em x = 25: **z = 26,0 e z = 25,4** — o degrau |
| `check_intent.py`, `volume_com_a_rampa` | **REPROVADA**: medido 57 330,0, esperado 58 050,0, **desvio 720,0 mm³**, `tol_mm3` 5,0. Saída **1** |
| meu veredito | `FALHOU`, `falhas: ["perfil_liga_os_dois_limites"]`; `roda_blender` saiu **1** com `VEREDITO_NEGATIVO` |

Volume medido 57 329,99954 contra 57 330 calculado à mão: resíduo de **≈4,6e-4**. Ele
só aparece nesta variante, cujo topo de sobreposição corta o material **obliquamente**;
na variante correta, com topo coplanar, todos os volumes saíram inteiros exatos
(58 050,0 / 1 200,0 / 660,0 / 2 640,0). Isso confirma, por medida, a nota do pacote de
que EXACT lida melhor com faces coplanares coincidentes.

**Nota sobre declarar tolerância**: com o `tol_mm3` padrão **não declarado** (580,5),
este erro de 720 mm³ ainda reprovaria — mas com margem de apenas 1,24×. Com o 5,0 que
declarei, reprova por 144×. É a diferença entre reprovar e reprovar *demonstravelmente*.

---

## 4. Onde a pasta me deixou na mão

Esta seção **não está vazia**. São 9 pontos, todos com arquivo e linha.

**1. As duas receitas mandam inserir um caminho que a própria pasta declara inválido.**
`referencias/editar_localizado.md:23` e `referencias/inspecionar_e_selecionar.md:13`
trazem, literalmente:
```python
import sys; sys.path.insert(0, "<caminho>/produto/scripts")
```
O prefixo `produto/` **não resolve no pacote extraído** — e quem diz isso é o próprio
`INVENTARIO.json`, no campo `nota`: *"A versao anterior gravava 'produto/...', que nao
resolve no pacote extraido"*. O manifesto foi corrigido; os dois trechos de código das
referências **não**. Tive que adivinhar `<raiz do pacote>/scripts`. É o **primeiro
comando executável** das duas rotas de edição e inspeção.

**2. `volume_de_material_na_caixa` devolve um `float` nu, e isso não está escrito em
lugar nenhum.** A função só aparece em `referencias/mapa_de_ferramentas.md:94`,
descrita como "volume **exato** de material dentro de uma caixa", sem assinatura e sem
forma de retorno. Todas as outras funções do pacote devolvem dicionário com campos
declarados; `editar_localizado.md` §5b até discute os volumes por zona, sempre por
dentro do retorno de `preenche_entre_limites`. Escrevi `r["volume_de_material"]` por
analogia e recebi `TypeError: 'float' object is not subscriptable` (comando C5). Tive
que abrir `scripts/bl_ferramentas.py:824-859` para achar `return abs(_volume(copia))`.
**A mensagem de erro não me disse nada sobre o que fazer** — é um `TypeError` do
Python, sem relação com geometria.

**3. Nenhuma referência ensina a escrever o próprio script de dentro do Blender.** As
referências mostram trechos que começam em `import bl_ferramentas as F` e param ali.
Nada diz que o script precisa: (a) ler `sys.argv` depois de `--`; (b) **escrever ele
mesmo** o JSON de resultado; (c) receber o caminho do resultado como **último**
argumento quando se usa `--passa-resultado`; (d) capturar exceções e **gravá-las** no
relatório, porque o lançador desanexa e um erro que só levanta não deixa vestígio no
chamador. Isso é o contrato central da rota headless. Tive que extraí-lo lendo
`cenarios/gera_cenario.py:155-178` e `cenarios/ensaio_preenchimento.py:157-165`.
`referencias/registro_de_trabalho.md` seria o lugar, mas trata só do formato do diário.
`mapa_de_ferramentas.md` documenta o lado de **fora** (as duas bandeiras) e nada do
lado de dentro.

**4. A bandeira `--cena` não é mencionada em nenhuma referência.**
`grep -rn "\-\-cena" referencias/` → **zero ocorrências**.
`recuperar_salvar_exportar.md` manda salvar um `.blend` ("Salve antes") e nunca diz
como reabri-lo numa execução headless seguinte — que é exatamente o que se precisa para
partir da mesma peça em três variantes. `mapa_de_ferramentas.md` mostra a assinatura do
módulo com `cena=None` num comentário, sem dizer que existe a bandeira de linha de
comando correspondente. Achei `--cena` lendo `scripts/roda_blender.py:174`.

**5. A tolerância que decide a FORMA é a única sem procedência.**
`referencias/editar_localizado.md:295` e `referencias/verificar.md:52` usam
`tolerancia=0.01` em `mede_topo_em_pontos` e nunca derivam o número — é também o
padrão da função. Isso contraria a regra que a própria pasta impõe duas vezes:
`verificar.md` diz *"Não declarar não é 'sem margem': é aceitar a da terceira coluna"*,
e `limpa_degeneracoes_na_regiao` **exige** `justificativa_da_tolerancia` como parâmetro
obrigatório. Ou seja: a tolerância da limpeza, que é cosmética, é obrigatória e
justificada; a tolerância do perfil, que é **a única medida que pega ranhura**, vem por
padrão silencioso nos exemplos. Tive que derivar a minha (§3.1) e declará-la eu mesmo.
Além disso, a tabela de tolerâncias de `verificar.md` cobre só os tipos de
`check_intent.py`; `mede_topo_em_pontos` não tem linha nela.

**6. `secao_por_plano` pode devolver poligonal inválida, e nenhuma referência avisa
quando.** Todos os exemplos da pasta usam normal `[0,1,0]`. Eu seccionei também na
costura do limite `a` (ponto [23,0,0], normal [1,0,0]) e recebi
`faces_com_mais_de_dois_cruzamentos: 2`, `n_pontos: 9` com `n_segmentos: 12` e
segmentos repetidos (`[1,7],[1,7]`, `[8,6],[8,6]`), mais um ponto espúrio em
z = 7,36 e outro em x = 23,000002. O campo `limite` do **retorno** avisa que a
poligonal está incompleta quando essa contagem não é zero — a ferramenta é honesta —
mas `grep -rn "faces_com_mais_de_dois_cruzamentos" referencias/` → **zero
ocorrências**. `editar_localizado.md` §3 lista o que o retorno declara
(`pontos_unidos_por_coincidencia`, faces coplanares ignoradas) e **omite exatamente o
campo que invalidou a minha seção**. Descartei essa seção; a que vale é a de normal
`[0,1,0]`, que saiu com a contagem em 0.

**7. `pontos_unidos_por_coincidencia` é indecidível pela documentação.**
`editar_localizado.md` §3 manda conferir esse campo, dizendo que ele traz "quantos
pontos ela uniu". Na minha seção limpa veio `pontos_unidos_por_coincidencia: 10` com
`n_pontos: 10` — igual ao total. Na seção da costura veio **18** com `n_pontos: 9` — o
dobro. Não é possível saber, pela documentação, se o número certo é "igual ao total"
(nada foi descartado) ou "quantas uniões ocorreram" (zero seria o bom). A referência
manda usar o campo como conferência e não diz qual valor é o esperado.

**8. Nada avisa que importar `bl_ferramentas` dentro do Blender grava na pasta da
habilidade.** O pacote se declara somente-leitura em vários lugares (verificadores como
"cópias byte a byte", *"não os edite ali"*), e `criar_e_parametrizar.md` chega a avisar
que os padrões de `--saida`/`--json` de `sweep_params.py` **gravam dentro do pacote** —
aviso muito bem-vindo. Mas nenhuma linha avisa que `sys.path.insert` + `import
bl_ferramentas` faz o Python criar `<pacote>/scripts/__pycache__`, e a receita manda
fazer exatamente isso. Tomei a precaução por conta própria
(`sys.dont_write_bytecode = True` antes do import, mais `PYTHONDONTWRITEBYTECODE=1` no
ambiente do processo pai). **Não testei o que aconteceria sem ela**, porque testar
significaria escrever na pasta.

**9. Um número da tabela de resultados não se sustenta como "resultado" — é parâmetro
da amostragem, e a pasta o apresenta como medida.** `editar_localizado.md` §8 diz *"No
cenário do pacote a amostragem vai de 45 para **99 pontos** com a lista simétrica — 33
posições distintas em x, em 3 planos de y. **Medido**"*. A minha peça, com dimensões
completamente diferentes (vão de 40 em vez de 20, sobreposição 2,0 em vez de 1,0),
produziu **exatamente 99 pontos e 33 posições em x**. Não é coincidência nem
confirmação: 99 = (15 da grade + 18 dos k, menos as coincidências) × 3 planos, ou seja
é consequência aritmética da **receita de amostragem**, invariante às dimensões. Ler
"99 pontos, medido" como evidência sobre a peça é confundir parâmetro com medida — e a
mesma página conta que o número antigo (87) sobreviveu a uma revisão justamente por
isso.

### Coisas que funcionaram exatamente como escrito (para o contraste ter valor)

- `--achar` localizou o `blender-launcher.exe` de primeira, e o alerta sobre
  `WindowsApps\blender.exe` não ser chamável direto poupou o caminho errado.
- `--passa-resultado` e `--exigir CAMPO=VALOR` fizeram o prometido: os dois controles
  negativos saíram com **código 1** e `VEREDITO_NEGATIVO`, e sem `--exigir` teriam
  saído `OK` com código 0.
- `valida_requisitos.py` avisou, antes de qualquer medição, que `regiao_intacta` exige
  `--referencia`.
- A instrução de **exportar a peça antes de editar** transformou "0,0 em 51 pontos" em
  "0,0 mm³ na caixa inteira". Custou um comando, como a página promete.
- A tabela de sintomas acertou o meu caso `reduziu: false` + `zerou: true` ("não havia
  degeneração; **não** repita a união"), e eu não repeti.
- A exigência de `origem_da_sobreposicao` e de `justificativa_da_tolerancia` me forçou
  a derivar números em vez de copiar os do exemplo.
- Todas as `ErroDePrecondicao` que recebi vieram com a medida por zona embutida na
  mensagem, e não com um "falhou" seco.

---

## 5. Quanto tempo, em passos, até a primeira execução bem-sucedida

- **8 comandos de leitura** da pasta (SKILL, inventário, 6 referências, 4 fontes).
- **C1** (`--achar`) → sucesso.
- **C2** (escrever `param_bloco.json`).
- **C3** → **primeira execução bem-sucedida dentro do Blender**: `estado: "OK"`, peça
  com volume 41 850,0.

Ou seja: **3º comando executado, 1ª invocação do Blender, zero tentativas falhas**.

Até o **preenchimento** bem-sucedido: **C4**, também na primeira tentativa, já com
`--exigir veredito_global=ATENDIDO` e código de saída 0.

Houve **uma** falha em todo o trabalho, o **C5**, e ela foi minha leitura do JSON, não
uma execução no Blender — causada pelo item 2 da §4 (tipo de retorno não documentado).
Custou 2 comandos (corrigir + reextrair). Total: **17 comandos executáveis**, 2
consumidos por essa correção.

---

## 6. Declaração sobre a pasta da habilidade

**Não escrevi nada dentro de `C:\Users\<usuario>\AppData\Local\Temp\pacote_intocado_18`**,
nem por acidente, nem `__pycache__`. Provas, no comando C17:

1. `find` por `__pycache__` e `*.pyc` na pasta → **nada**.
2. A pasta tem **24 arquivos**, o mesmo número da primeira listagem, e o `mtime` mais
   recente de todos é **2026-09-08 03:31**, anterior à minha primeira execução (03:40).
3. Recálculo do `sha256` de **todas** as 23 entradas de `INVENTARIO.json`, resolvidas
   contra a raiz do pacote: **`conferidos_ok=23 divergentes=0 faltando=0`**. O 24º
   arquivo é o próprio `INVENTARIO.json`, que não consta do seu manifesto.

Também **não** houve qualquer contato com a sessão viva do Blender do usuário:
`scripts/mcp_blender.py` não foi executado, nenhuma conexão a `127.0.0.1:9876` foi
aberta, e todas as três execuções foram
`blender-launcher.exe --background --factory-startup <cena.blend> --python <script>`,
processos separados, sobre `.blend` criados por mim na pasta de trabalho.

---

## 7. O que NÃO foi verificado

Não é aprovação para fabricação. Fora do que este relatório mediu:

- **imprimibilidade**, parede mínima, silhueta: sem medidor no pacote
  (`NAO_IMPLEMENTADA`; não estimei).
- **folga de encaixe**: `A_CALIBRAR`, sem valor medido.
- A seção prova **um plano** (y = 15). O perfil prova **99 pontos** nas posições
  listadas, em 3 planos de y. `regiao_intacta` prova **as duas caixas declaradas**.
  Nenhuma dessas conclusões se estende à peça inteira.
- A recuperação por `undo`/`redo` foi conferida **neste caminho**, em background. Não é
  promessa para sessão viva.
- **Não decidido**: se o encontro da rampa com o patamar baixo deveria ter algum
  acabamento (arredondamento/chanfro). Construí a ligação plana que os limites
  implicam, sem improvisar acabamento.
