<!-- Relatorio de sessao limpa, preservado no repositorio porque uma revisao
independente apontou que o relatorio da sessao anterior existia apenas no
transcrito de uma conversa, e portanto nao era auditavel. Operador do ensaio:
subagente sem historico deste projeto, modelo claude-opus-5. Pacote sob ensaio:
1.6.0. Nada aqui foi editado por mim: os achados estao como ele escreveu,
inclusive os que me contradizem. -->

# Relatório — placa 80 × 50 × 8 com dois furos passantes D=10

**Pasta da habilidade (só leitura):** `C:\Users\marce\AppData\Local\Temp\ensaio_isolado_16\pacote_1.6.0`
**Interpretador usado (todos os comandos):** `C:\Users\marce\AppData\Local\Temp\ensaio_isolado_16\venv\Scripts\python.exe`
**Pasta de trabalho:** `C:\Users\marce\AppData\Local\Temp\sessao_limpa_D`
**Shell:** Git Bash (POSIX). **Data:** 08/09/2026.

**Blender:** nenhum Blender foi executado, nem headless. O `SKILL.md` roteia
"criar ou parametrizar peça por código, com verificação" para
`referencias/criar_e_parametrizar.md`, e essa referência usa **build123d no Python
do hospedeiro** — ela diz explicitamente que Blender só entra quando a peça já
existe como malha. Portanto nada nesta tarefa chegou perto do socket
`127.0.0.1:9876` nem de `scripts/mcp_blender.py`. A sessão aberta do usuário não
foi tocada.

---

## 1. Comandos executados, na íntegra

Notação: `[dir]` é o diretório de execução. `PKG` =
`C:/Users/marce/AppData/Local/Temp/ensaio_isolado_16/pacote_1.6.0`,
`W` = `C:/Users/marce/AppData/Local/Temp/sessao_limpa_D`,
`PY` = `C:/Users/marce/AppData/Local/Temp/ensaio_isolado_16/venv/Scripts/python.exe`.

| # | dir | comando | saída |
|---|---|---|---|
| 1 | qualquer | `ls -la "PKG"` | 0 |
| 2 | qualquer | `ls -la "W"` | 1 (pasta ainda não existia) |
| 3 | qualquer | `cat "PKG/SKILL.md"` | 0 |
| 4 | PKG | `find . -type f \| sort` | 0 |
| 5 | qualquer | `mkdir -p "W"` | 0 |
| 6 | qualquer | `cat "PKG/INVENTARIO.json"` | 0 |
| 7 | qualquer | `cat "PKG/referencias/criar_e_parametrizar.md"` | 0 |
| 8 | qualquer | `cat "PKG/referencias/verificar.md"` | 0 |
| 9 | qualquer | `cat "PKG/cenarios/familia_exemplo.py"` ; `cat "PKG/verificadores/PROVENIENCIA.json"` | 0 |
| 10 | PKG | `PY -c "<confere sha256 de cada entrada de INVENTARIO.json>"` → `total 22 divergentes 0` | 0 |
| 11 | PKG | `PY scripts/valida_requisitos.py --tipos` | 0 |
| 12 | PKG | `PY verificadores/matriz.py criar solido intercambio` | 0 |
| 13 | PKG | `PY verificadores/sweep_params.py --help` | 0 |
| 14 | PKG | `PYTHONPATH="W" PY verificadores/sweep_params.py --modulo peca_placa --funcao placa_dois_furos --grade "T=8;d=10" --representacao solido --n-solidos 1 --saida "W/saida" --json "W/varredura.json"` | **0** |
| 15 | W | `PY exporta.py` | 0 |
| 16 | PKG | `PY scripts/valida_requisitos.py "W/req.json"` | 0 (`OK`, 7 requisitos) |
| 17 | PKG | `PY verificadores/check_intent.py --malha "W/saida/peca.stl" --requisitos "W/req.json"` | **0** (7/7 APROVADA) |
| 18 | PKG | `PY verificadores/check_mesh.py --malha "W/saida/peca.stl"` | 0 |
| 19 | PKG | `PY scripts/valida_requisitos.py "W/req_controle_negativo.json"` | 0 (`OK`, 7 requisitos) |
| 20 | PKG | `PY verificadores/check_intent.py --malha "W/saida/peca.stl" --requisitos "W/req_controle_negativo.json" > "W/saida/intent_cn.json"` | **1** (6 REPROVADA, 1 APROVADA) |
| 21 | PKG | `grep -n "tol_diam_mm" verificadores/check_intent.py scripts/valida_requisitos.py referencias/*.md` | 0 |
| 22 | PKG | `PY verificadores/check_intent.py --malha "W/saida/peca.stl" --requisitos "W/req_lista_nua.json"` | **1** (traceback `AttributeError`) |
| 23 | PKG | `sed -n '215,262p' verificadores/check_intent.py` | 0 |
| 24 | PKG | `PY scripts/valida_requisitos.py "W/req_probe_tolmm.json"` | **1** (`FORMA_INVALIDA`) |
| 25 | PKG | `PY verificadores/check_intent.py --malha "W/saida/peca.stl" --requisitos "W/req_probe_tolmm.json"` | **1** (REPROVADA por `tol_diam_mm: 0.001`) |
| 26 | PKG | `PYTHONPATH="W" PY verificadores/sweep_params.py --modulo peca_placa --funcao placa_dois_furos --grade "T=8;d=8,10,12,40" --representacao solido --n-solidos 1 --saida "W/saida/familia" --json "W/varredura_familia.json"` | **1** (1 de 4 reprovada) |
| 27 | PKG | `PYTHONPATH="scripts" PY -c "import bl_ferramentas as F; print(F.confere_versao('1.5.0'))"` | **1** (`ModuleNotFoundError: No module named 'bmesh'`) |
| 28 | PKG | `PYTHONPATH=cenarios PY verificadores/sweep_params.py --modulo familia_exemplo --funcao familia_placa --grade "L=70,80;d=4,5" --saida "W/saida/doc_a" --json "W/saida/doc_a.json"` | 0 (4/4 aprovadas) |
| 29 | PKG | idem com `--grade "L=80;d=5,40" --saida "W/saida/doc_b" --json "W/saida/doc_b.json"` | **1** (1 de 2 reprovada) |
| 30 | PKG | idem com `--grade "T=4,5;d=4,5" --saida "W/saida/doc_c" --json "W/saida/doc_c.json"` | 0 (4/4 aprovadas) |
| 31 | PKG | `PYTHONPATH="W" PY verificadores/sweep_params.py ... --saida "Z:/sem_permissao" --json "W/saida/erro_op.json"` | **1** (`FileNotFoundError [WinError 3]`, traceback) |
| 32 | PKG | `PYTHONPATH="W" PY verificadores/sweep_params.py ... --saida "C:/Windows/System32/sem_permissao_ensaio" --json "W/saida/erro_op2.json"` | **1** (`PermissionError [WinError 5]`, traceback) |
| 33 | PKG | `sed -n '272,290p' verificadores/sweep_params.py` | 0 |
| 34 | PKG | `PYTHONPATH="W" PY verificadores/sweep_params.py --modulo peca_placa --funcao placa_dois_furos --grade "T=8;d=10"` (sem `--saida`) | 0 — **e isto gravou dentro do pacote**, ver §4.6 |
| 35 | PKG | `grep -n 'saida' verificadores/sweep_params.py` | 2 (grep sem match na 2ª parte do comando composto) |
| 36 | — | `ls -la "PKG/varredura"` | 0 (confirma a gravação indevida) |
| 37 | PKG | `rm -rf varredura` + reconferência dos 22 hashes → `divergentes 0 de 22` | 0 |
| 38 | PKG | `ls -la cenarios cenarios/__pycache__` | 0 |
| 39 | PKG | `rm -rf cenarios/__pycache__` | **bloqueado pelo classificador de permissões** — ver §4.6 |

---

## 2. Arquivos criados

Todos dentro da pasta de trabalho, exceto o incidente registrado em §4.6.

| Caminho completo | O que é |
|---|---|
| `C:\Users\marce\AppData\Local\Temp\sessao_limpa_D\peca_placa.py` | a peça como função de parâmetros (`placa_dois_furos`) |
| `C:\Users\marce\AppData\Local\Temp\sessao_limpa_D\exporta.py` | exportação STL + STEP, construindo do zero |
| `C:\Users\marce\AppData\Local\Temp\sessao_limpa_D\req.json` | requisitos declarados (7) |
| `C:\Users\marce\AppData\Local\Temp\sessao_limpa_D\req_controle_negativo.json` | controle negativo (6 errados + 1 certo) |
| `C:\Users\marce\AppData\Local\Temp\sessao_limpa_D\req_lista_nua.json` | sonda da armadilha documentada (lista nua) |
| `C:\Users\marce\AppData\Local\Temp\sessao_limpa_D\req_probe_tolmm.json` | sonda de `tol_mm` no tipo `furo` |
| `C:\Users\marce\AppData\Local\Temp\sessao_limpa_D\saida\peca.stl` | **artefato entregue** (51.484 bytes, 1.028 triângulos) |
| `C:\Users\marce\AppData\Local\Temp\sessao_limpa_D\saida\peca.step` | sólido analítico (22.565 bytes) |
| `C:\Users\marce\AppData\Local\Temp\sessao_limpa_D\saida\v_T8_d10.stl` / `.3mf` | variante da varredura (portão 3) |
| `C:\Users\marce\AppData\Local\Temp\sessao_limpa_D\varredura.json` | relatório da varredura da peça pedida |
| `C:\Users\marce\AppData\Local\Temp\sessao_limpa_D\varredura_familia.json` | varredura de família `d=8,10,12,40` |
| `C:\Users\marce\AppData\Local\Temp\sessao_limpa_D\saida\intent_cn.json` | saída do controle negativo |
| `C:\Users\marce\AppData\Local\Temp\sessao_limpa_D\saida\forma_cn.json` | validação de forma do controle negativo |
| `C:\Users\marce\AppData\Local\Temp\sessao_limpa_D\saida\familia\v_T8_d{8,10,12,40}.stl/.3mf` | 8 arquivos da varredura de família |
| `C:\Users\marce\AppData\Local\Temp\sessao_limpa_D\saida\doc_a{,.json}`, `doc_b{,.json}`, `doc_c{,.json}` | reprodução dos exemplos da própria referência (14 arquivos + 3 JSON) |
| `C:\Users\marce\AppData\Local\Temp\sessao_limpa_D\__pycache__\peca_placa.cpython-312.pyc` | gerado pelo Python |
| `C:\Users\marce\AppData\Local\Temp\sessao_limpa_D\RELATORIO.md` | este relatório |

### A peça

```python
def placa_dois_furos(L=80.0, P=50.0, T=8.0, d=10.0,
                     x1=20.0, y1=25.0, x2=60.0, y2=25.0):
    from build123d import Align, Box, Cylinder, Pos
    corpo = Box(L, P, T, align=(Align.MIN, Align.MIN, Align.MIN))
    furos = [Pos(x, y, T / 2) * Cylinder(d / 2, T * 3)
             for (x, y) in ((x1, y1), (x2, y2))]
    return corpo - furos
```

Duas decisões, ambas da referência: origem em `Align.MIN` nos três eixos, para que
a placa ocupe 0..80 × 0..50 × 0..8 e as posições dos furos sejam **literalmente**
(20, 25) e (60, 25) no mesmo sistema em que o pedido foi escrito; e cilindro de
altura `T*3`, nunca `T`, para atravessar com folga em vez de gerar faces
coincidentes.

### Classificação (passo obrigatório do método)

`matriz.py criar solido intercambio` → exigidas `geometria_nao_vazia`, `intencao`,
`reabre_em_cad`, todas DECISIVAS; dispensadas `malha_estanque`,
`zero_nao_manifold`, `portao_do_fatiador`, `envelope_e_particao`,
`folga_calibrada`, `orientacao_anisotropia`. Medi as dispensadas de todo modo
(`check_mesh`), e registro que **verificação dispensada não é verificação
aprovada**.

---

## 3. Resultado, requisito por requisito

### 3.1 Portões geométricos (`sweep_params.py`, comando 14)

Grade `T=8;d=10` — 1 variante. `n_variantes: 1`, `n_aprovadas: 1`,
`n_reprovadas_por_geometria: 0`, `n_com_erro_operacional: 0`.

| Portão | Medido | Veredito |
|---|---|---|
| 1 — sólido | `n_solidos` = 1 (esperado 1), `volume_mm3` = 30743,363 > 0 | **APROVADA** |
| 2 — malha | 1.028 triângulos; `arestas_abertas` 0; `arestas_com_mais_de_2_faces` 0; `facetas_degeneradas` 0; `fechada_watertight` true; `orientacao_consistente` true | **APROVADA** |
| 3 — 3MF | escritor aceitou, 13.638 bytes | **APROVADA** |

**Alcance:** os pontos desta grade, com tolerância de malha linear 0,01 mm e
angular 0,1 rad. Nada é afirmado sobre valores intermediários nem sobre
imprimibilidade.

### 3.2 Intenção (`check_intent.py --requisitos req.json`, comando 17)

`atende_ao_pedido: true` — 7 aprovados, 0 reprovados, 0 não verificados, saída 0.
Forma do arquivo conferida antes por `valida_requisitos.py` → `OK`.

| id | tipo | esperado | **medido** | tolerância | veredito |
|---|---|---|---|---|---|
| `envelope_80x50x8` | `caixa` | [80,0; 50,0; 8,0] | **[80,0; 50,0; 8,0]**, maior desvio **0,0 mm** | `tol_mm` = 0,5 | **APROVADA** |
| `um_corpo_so` | `n_solidos` | 1 | **1** | nenhuma (contagem exata) | **APROVADA** |
| `dois_furos_em_z4` | `n_furos_no_plano` z @ 4,0 | 2 | **2** | nenhuma (contagem exata) | **APROVADA** |
| `furo_A_20_25_d10` | `furo` z @ 4,0 | (20;25), D=10 | centro **(20,0; 25,0)**, erro de posição **0,0 mm**; D equiv. **9,9979 mm**, erro **0,0021 mm**; circularidade **0,9998** | `tol_pos_mm` 0,5; `circularidade_min` 0,90; `tol_diam_mm` **0,2 (padrão não declarado — §4.3)** | **APROVADA** |
| `furo_B_60_25_d10` | `furo` z @ 4,0 | (60;25), D=10 | centro **(60,0; 25,0)**, erro **0,0 mm**; D equiv. **9,9979 mm**, erro **0,0021 mm**; circularidade **0,9998** | idem | **APROVADA** |
| `distancia_entre_furos_40` | `distancia_entre_furos` z @ 4,0 | 40,0 mm | **40,0 mm**, desvio **0,0 mm** | `tol_mm` = 0,5 | **APROVADA** |
| `volume_analitico` | `volume` | 30743,363 mm³ (= 80·50·8 − 2·π·5²·8) | **30743,884 mm³**, desvio **0,521 mm³** | `tol_mm3` = 20,0 | **APROVADA** |

Cada `furo` foi conferido em duas seções (z = 4,0 e z = 3,6; deslocamento −0,4 mm
escolhido pelo próprio verificador): desvio de centro 0,0 mm, desvio de diâmetro
0,0 mm, circularidade da segunda seção 0,9998.

### 3.3 Artefato entregue (`check_mesh.py`, comando 18)

Conferido no `peca.stl` que está no disco, não na peça que eu acho que exportei.

`triangulos` 1028 · `vertices_antes_de_soldar` 3084 → `depois_de_soldar` 512 ·
`fechada_watertight` true · `euler` **−2** · `arestas_abertas` 0 ·
`arestas_com_mais_de_2_faces` 0 · `facetas_degeneradas` 0 ·
`facetas_duplicadas` 0 · `orientacao_consistente` true ·
`n_componentes_conexos` 1 · `volume_mm3` 30743,884 · `caixa_mm` [80,0; 50,0; 8,0] ·
`motivos_de_reprovacao` [] · `acao` "Pode seguir."

### 3.4 O requisito "passante": o que eu consigo provar e o que não

O verificador é honesto ao ponto de se limitar. A saída do tipo `furo` diz, com
essas palavras, que duas seções são **amostragem** e "conferir as duas pontas
também não prova furo passante", e que a verificação volumétrica que provaria
passagem "não está implementada aqui". A tabela de tipos de `verificar.md` **não
oferece nenhum tipo** que prove passagem. Então:

- **Não** existe requisito declarável, nesta pasta, cujo veredito seja "o furo
  atravessa". Registro isso como limite, não como aprovação.
- Duas evidências indiretas, que são **minha dedução** e não veredito de
  verificador, e por isso vão separadas:
  1. `euler = −2` com malha fechada, orientação consistente e **1** componente
     conexo ⇒ gênero 2 ⇒ exatamente **dois túneis** atravessando o sólido. Furo
     cego é reentrância e não altera o gênero (ficaria `euler = 2`).
  2. `volume` medido 30743,884 mm³ contra 30743,363 mm³ calculado **assumindo os
     dois furos passantes**, desvio 0,521 mm³. Com `tol_mm3` 20,0, isso limita
     qualquer material residual dentro das duas colunas de furo a < 20 mm³, ou seja
     uma membrana média de espessura < 0,25 mm num furo. Não é zero, e eu não vou
     escrever que é.

**Veredito da parte (b):** os 7 requisitos declarados foram **APROVADOS**, com os
números da tabela §3.2, e os 3 portões geométricos passaram. Isso é evidência
geométrica e de intenção declarada. **Não** é aprovação para fabricação, **não**
prova imprimibilidade, e **não** prova por si só que os furos são passantes — só
os requisitos que eu escrevi foram verificados.

### 3.5 Varredura de família (comando 26), como controle adicional

Grade `T=8;d=8,10,12,40`: `n_variantes` 4, `n_aprovadas` 3,
`n_reprovadas_por_geometria` **1**, `n_com_erro_operacional` 0, saída 1.
A variante `d=40` reprovou nos portões 1 e 2 (`arestas_com_mais_de_2_faces` **3**,
`arestas_abertas` 0) e **o escritor de 3MF a aceitou** — confirmando a nota da
referência de que 3MF não é portão de graça. As variantes `d=8, 10, 12` passaram.

---

## 3.6 (c) Controle negativo

Arquivo: `req_controle_negativo.json`. Forma conferida primeiro
(`valida_requisitos.py` → `OK`, 7 requisitos): o controle não passa por erro de
forma, passa por **medição**. Dentro dele coloquei 6 requisitos que a peça
deliberadamente não atende e **1 que ela atende**, para que o verificador tenha
que discriminar em vez de reprovar em bloco.

`check_intent.py` → `atende_ao_pedido: **false**`, 1 aprovado, **6 REPROVADOS**,
0 não verificados, **código de saída 1**.

| id | tipo | declarado (errado de propósito) | **medido** | desvio | tolerância | veredito |
|---|---|---|---|---|---|---|
| `CN_espessura_6_errada` | `caixa` | [80; 50; **6,0**] | [80,0; 50,0; **8,0**] | **2,0 mm** | `tol_mm` 0,5 | **REPROVADA** |
| `CN_tres_furos_errado` | `n_furos_no_plano` z @ 4,0 | **3** | **2** | — | nenhuma | **REPROVADA** |
| `CN_furo_d6_errado` | `furo` z @ 4,0 (20;25) | D = **6,0** | D equiv. **9,9979** | **3,9979 mm** | `tol_diam_mm` 0,2 | **REPROVADA** |
| `CN_furo_fora_de_posicao` | `furo` z @ 4,0 | (**40,0**; 25,0), D=10 | mais próximo em **(20,0; 25,0)** | **20,0 mm** | `tol_pos_mm` 0,5 | **REPROVADA** |
| `CN_distancia_30_errada` | `distancia_entre_furos` | **30,0 mm** | **40,0 mm** | **10,0 mm** | `tol_mm` 0,5 | **REPROVADA** |
| `CN_dois_corpos_errado` | `n_solidos` | **2** | **1** | — | nenhuma | **REPROVADA** |
| `CP_um_corpo_certo` (controle positivo embutido) | `n_solidos` | 1 | **1** | — | nenhuma | **APROVADA** |

Veredito literal do verificador: *"1 aprovados, 6 REPROVADOS, 0 nao verificados."*
Os quatro medidores usados na aprovação (`caixa`, `n_furos_no_plano`, `furo`,
`distancia_entre_furos`, `n_solidos`) reprovaram quando apontados para o número
errado, e o mesmo medidor (`n_solidos`) aprovou e reprovou no mesmo arquivo
conforme o valor declarado. O zero de reprovações do §3.2 foi medição, não
silêncio.

**Controle extra (sonda de precisão):** `req_probe_tolmm.json` apertou a
tolerância de diâmetro para 0,001 mm. O erro real de 0,0021 mm passou a reprovar
(`tol_diam_mm: 0.001` → REPROVADA). Ou seja, o medidor de diâmetro tem resolução
de fato, e o "APROVADA" do §3.2 vem da tolerância, não de indiferença.

---

## 4. Onde a pasta me deixou na mão

Esta seção **não** está vazia. São 9 achados, cada um com arquivo e linha.

Antes, o crédito devido: o `INVENTARIO.json` fecha (22 arquivos, **0**
divergentes), a rota estava clara no `SKILL.md`, e os dois exemplos numéricos da
referência reproduziram **exatamente** o que ela promete — comandos 28 e 29:
`L=70,80;d=4,5` → 4 variantes, 4 aprovadas, 0 reprovadas, 0 erros operacionais; e
o defeito plantado `L=80;d=5,40` → 2 variantes, 1 aprovada, **1 reprovada por
geometria, 3 arestas não-manifold, 0 arestas abertas**, 0 erros operacionais. A
armadilha da lista nua (`verificar.md`) também é verdadeira e reproduz o
traceback prometido (comando 22). Isso é raro e vale dizer.

### 4.1 O primeiro passo acionável do `SKILL.md` não roda no interpretador da rota

`SKILL.md`, linhas 8–13, manda: *"Confira com
`bl_ferramentas.confere_versao("1.5.0")`, que recusa em vez de deixar descobrir
pelo resultado."* É a primeira instrução executável do documento e não diz **onde**
rodar. No venv indicado ela morre:

```
File "...\pacote_1.6.0\scripts\bl_ferramentas.py", line 30, in <module>
    import bmesh
ModuleNotFoundError: No module named 'bmesh'
```

`bl_ferramentas.py` só existe dentro do Blender (`bpy`/`bmesh`). Ou seja: **a
salvaguarda contra confusão de versão é inexecutável exatamente na rota de criar**,
que roda 100% no Python do hospedeiro. Tive que decidir sozinho que essa
verificação não se aplicava aqui e seguir sem ela. `SKILL.md` deveria dizer "só
dentro do Blender".

### 4.2 O descasamento de versão é anunciado e não é resolvido

`SKILL.md` linha 8: *"Pacote 1.6.0. As referências descrevem
`scripts/bl_ferramentas.py` versão 1.5.0. Se as duas não baterem, releia a
referência da versão carregada."* `INVENTARIO.json` confirma os dois números
(`"versao_do_pacote": "1.6.0"`, `"versao_de_bl_ferramentas": "1.5.0"`). Nada, em
lugar nenhum, diz **o que mudou** entre 1.5.0 e 1.6.0. A instrução "releia a
referência da versão carregada" é impossível de cumprir: existe uma referência só.
Adivinhei que o descasamento não afetava a rota build123d — porque essa rota nem
toca em `bl_ferramentas.py` — mas isso foi dedução minha, não informação da pasta.

### 4.3 **O achado grave:** `valida_requisitos.py` recusa uma tolerância que `check_intent.py` lê e usa para decidir

`verificar.md` traz a tabela "Tolerância que o verificador lê", e para `tipo: furo`
lista **`tol_pos_mm`, `circularidade_min`**. `scripts/valida_requisitos.py --tipos`
repete exatamente isso. E `verificar.md` afirma:
*"`scripts/valida_requisitos.py` confere isso e recusa tolerância que seria
ignorada."*

Só que `verificadores/check_intent.py`, **linha 218**:

```python
tol_d = float(r.get("tol_mm", 0.2))
```

`furo` **lê `tol_mm`** como tolerância de diâmetro, e decide com ela (linha 248:
`ok = bool(erro_pos <= tol_pos and erro_d <= tol_d and ...)`).

Medido, comandos 24 e 25, no mesmo arquivo de requisitos:

- `valida_requisitos.py` → `FORMA_INVALIDA`, saída 1, com o motivo:
  *"requisitos[0] de tipo 'furo' traz ['tol_mm'], que o verificador NAO le para
  este tipo. […] Tolerancia ignorada e numero que nao decide nada."*
- `check_intent.py` no mesmo arquivo → leu, reportou `"tol_diam_mm": 0.001` e
  **REPROVOU** o requisito por um erro de diâmetro de 0,0021 mm.

Três consequências práticas, e todas me custaram tempo:

1. A guarda **mente** sobre o verificador, e mente com a frase mais confiante do
   documento.
2. A tolerância de diâmetro do tipo `furo` é, pelo caminho sancionado,
   **indeclarável**: se você a declara, a guarda barra; se não declara, ela vale
   silenciosamente **0,2 mm** — um número que não aparece em `verificar.md`, nem em
   `criar_e_parametrizar.md`, nem em `--tipos`. Meus dois requisitos de furo do
   §3.2 foram decididos por uma tolerância que eu não escolhi.
3. O campo de saída chama-se `tol_diam_mm` (linha 257) e o campo de **entrada**
   chama-se `tol_mm`. `grep -n "tol_diam_mm"` na pasta inteira dá **uma** linha, a
   257, e nenhuma nas referências. Precisei abrir `check_intent.py` e ler as linhas
   215–262 para descobrir de onde vinha o `0.2` que apareceu no meu relatório de
   aprovação.

Ironia registrada: `verificar.md` gasta um parágrafo se parabenizando por uma
revisão ter pegado esta **mesma classe** de defeito em `regiao_intacta`
(`tol_mm3` declarado e não lido). A classe sobreviveu em `furo`, invertida.

### 4.4 O controle de erro operacional documentado não reproduz — ele estoura em traceback

`criar_e_parametrizar.md`, último parágrafo: *"Controle de erro operacional, que
tem que ficar separado: aponte a saída para um caminho sem permissão de escrita. O
resultado tem que ser `E_EXPORT_3MF` na etapa `exportacao`, com
`n_reprovadas_por_geometria: 0`."*

Não é o que acontece. `verificadores/sweep_params.py`, **linha 279**:

```python
os.makedirs(a.saida, exist_ok=True)
```

roda **antes** do laço de variantes e **fora** de qualquer `try/except` (o
tratamento de exceção só começa na linha 288). Medido duas vezes:

- `--saida "C:/Windows/System32/sem_permissao_ensaio"` (comando 32) →
  `PermissionError: [WinError 5] Acesso negado`, traceback cru, saída 1.
- `--saida "Z:/sem_permissao"` (comando 31) →
  `FileNotFoundError: [WinError 3]`, traceback cru, saída 1.

Em nenhum dos dois há JSON, `codigo`, `etapa`, `erros_operacionais` nem
`n_reprovadas_por_geometria`. A separação entre falha de ambiente e reprovação
geométrica — a coisa de que a referência mais se orgulha, com dois parágrafos e uma
tabela — **é contornada precisamente pela falha que a referência manda usar para
testá-la**. E a mensagem de erro não diz nada sobre o que fazer: é um traceback de
`os.makedirs`.

### 4.5 A tabela de "coincidência paramétrica" não reproduz com o código que a pasta entrega

`criar_e_parametrizar.md`, Passo 2, apresenta como **medição** ("Isso não é
hipótese: é o achado mais reusável deste projeto. […] Medido:") a tabela
diâmetro/parede: 4/4 → **6** arestas não-manifold, 5/5 → **6**, 3/4 → 0, 6/4 → 0.

Rodei a igualdade na função da própria pasta (comando 30):
`--modulo familia_exemplo --funcao familia_placa --grade "T=4,5;d=4,5"` →
`T4_d4`, `T4_d5`, `T5_d4`, `T5_d5`, **todas as 4 aprovadas**, 0 arestas
não-manifold, 0 abertas. Também na minha peça (comando 26), `d=8` com `T=8`
passou limpo.

A explicação óbvia é que a tabela mede uma versão **anterior** do código, sem a
folga `T*3` que a mesma página manda usar — mas a página não diz isso, e o
parágrafo seguinte constrói toda uma doutrina (`A_CALIBRAR`, "a igualdade importa,
não o valor") sobre um número que não é reproduzível com os artefatos entregues.
Gastei um comando para descobrir que o aviso não se aplica ao código do pacote. Se
eu tivesse acreditado nele, teria evitado `d=8` sem motivo.

### 4.6 O `--saida` padrão grava **dentro da pasta só-leitura**, e os exemplos da referência também

`verificadores/sweep_params.py`, **linha 262**:

```python
ap.add_argument("--saida", default="varredura")
```

Caminho **relativo**, resolvido contra o diretório de execução. E a própria
referência manda executar de dentro do pacote (`python verificadores/sweep_params.py
...`) com `--saida saida`, também relativo — de modo que **seguir o exemplo da
referência ao pé da letra cria `pacote_1.6.0/saida/` dentro da pasta só-leitura**.
Nenhuma linha das referências avisa disso nem sugere caminho absoluto.

Eu bati nisso: o comando 34, sondando o `--saida` opcional do `--help`, criou
`C:\Users\marce\AppData\Local\Temp\ensaio_isolado_16\pacote_1.6.0\varredura\` com
`v_T8_d10.stl` e `v_T8_d10.3mf`. **Isso violou a regra de não escrever na pasta da
habilidade e a falha é minha, não da pasta** — mas o padrão relativo é o que fez
uma sonda inofensiva virar escrita indevida. Removi o diretório (comando 37) e
reconferi o `INVENTARIO.json`: **0 divergentes de 22**, nenhum arquivo inventariado
alterado.

Resta um resíduo que **não consegui remover**: ao importar `familia_exemplo`, o
Python gerou
`...\pacote_1.6.0\cenarios\__pycache__\familia_exemplo.cpython-312.pyc`. O
`rm -rf` desse diretório foi **bloqueado pelo classificador de permissões**
(comando 39). Registro para o operador decidir. Contexto: o pacote já era
distribuído com `__pycache__` em `scripts/` e `verificadores/`, e nenhum arquivo do
inventário mudou. Todos os meus comandos posteriores usaram `--saida` e `--json`
**absolutos**, apontando para a pasta de trabalho.

### 4.7 Portão 1 exige uma declaração que o exemplo da referência não faz

`criar_e_parametrizar.md`, Passo 2, tabela dos portões: *"1. sólido — contagem de
corpos declarada e volume positivo — o contrato vem da **representação**"*. Mas os
dois comandos de exemplo da mesma página (bloco PowerShell e bloco bash) **não
passam** `--representacao` nem `--n-solidos`. `--help` mostra os dois como
opcionais, sem revelar o padrão. Tive que adivinhar que
`--representacao solido --n-solidos 1` era a declaração correta para "um corpo".
A página explica quando `montagem` e `superficie` precisam de declaração extra, e
nunca diz o que acontece com `solido` sem declaração nenhuma — o caso do próprio
exemplo dela.

### 4.8 Nenhum tipo de requisito prova "furo passante", e nada avisa isso antes

O pedido era de furos **passantes**. `verificar.md` tem uma tabela de 8 tipos e
uma tabela de três famílias de verificação, e nenhuma das duas menciona que
passagem não é verificável. Só descobri depois de rodar: a mensagem
`o_que_isto_nao_diz` do tipo `furo` (`check_intent.py`, linhas 259–262) admite que
duas seções são amostragem e que "conferir as duas pontas também não prova furo
passante", e que a verificação volumétrica "não está implementada aqui". É a
resposta certa, no lugar errado: aparece **depois** da medição, dentro do JSON, num
requisito que saiu **APROVADA**. Um agente apressado leria `furo_A: APROVADA` e
declararia o furo passante. A seção "O que este pacote não faz" do `SKILL.md` lista
folga de encaixe, parede mínima e silhueta — e **não** lista passagem de furo, que
é o requisito mais comum desta rota. Tive que construir a evidência indireta do
§3.4 por conta própria.

### 4.9 Duas coisas menores que a documentação deveria dizer

- **Códigos de saída não são documentados em lugar nenhum.** `check_intent.py`
  sai **1** quando há reprovação (comando 20) e **0** quando tudo aprova;
  `sweep_params.py` sai **1** com variante reprovada (comandos 26 e 29);
  `valida_requisitos.py` sai **1** em `FORMA_INVALIDA` (comando 24). Isso é
  exatamente o que se quer para automação, é comportamento bom, e não está escrito
  em nenhuma referência — descobri lendo os códigos de retorno.
- **`--saida` produz STL e 3MF, mas o STL da varredura não é o artefato final.**
  A referência passa do Passo 2 (varredura, que já grava `v_*.stl`) para o Passo 5
  (`export_stl` manual) sem dizer que são arquivos diferentes com o mesmo
  conteúdo, nem qual deles é "o entregue". Escrevi `exporta.py` por conta própria
  porque `check_intent.py` precisa de um `--malha` e a referência não indica qual
  caminho usar. (Confirmei depois: `saida/peca.stl` e `saida/v_T8_d10.stl` têm os
  mesmos 51.484 bytes.)

---

## 5. Quanto tempo até a primeira execução bem-sucedida

Contando por passos de comando, e sem esconder que a pasta se portou bem no
caminho principal:

- **Passos 1 a 9 — leitura, sem execução de ferramenta.** Listar a pasta, ler
  `SKILL.md`, `INVENTARIO.json`, `criar_e_parametrizar.md`, `verificar.md`,
  `familia_exemplo.py` e `PROVENIENCIA.json`.
- **Passo 10 — primeira execução bem-sucedida de qualquer coisa:** a conferência
  dos 22 hashes do `INVENTARIO.json` (`divergentes 0`), na **primeira tentativa**.
  No mesmo passo, `valida_requisitos.py --tipos` também rodou de primeira.
- **Passo 14 — primeira execução bem-sucedida de geometria:** a peça pedida
  passou nos três portões na **primeira tentativa**, sem nenhuma tentativa
  frustrada antes. Foram 5 idas ao shell de leitura + 1 arquivo escrito
  (`peca_placa.py`) antes disso.
- **Passo 17 — primeira verificação de intenção:** 7/7 APROVADA, também de
  primeira, com a forma pré-conferida no passo 16.

**Zero retentativas no caminho principal.** Todos os erros deste relatório
(passos 22, 24–25, 27, 31–32, 34) foram **sondas deliberadas** feitas depois de a
peça já estar construída e verificada — controles negativos e testes das
afirmações da própria documentação. A pasta me levou de zero a peça verificada em
uma passada. Onde ela falhou foi em me contar a verdade sobre as tolerâncias que
usa para decidir (§4.3), sobre o seu próprio controle de erro operacional (§4.4) e
sobre o que os seus vereditos não provam (§4.8).
