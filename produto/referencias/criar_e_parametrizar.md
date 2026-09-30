# Criar e parametrizar geometria simples

Rota para: "faça uma peça assim", "gere essa família de tamanhos", sem exigir
reconstrução de nada nem impressão. Esta referência trata de criar por código. Se a
peça já existe como malha, ou o trabalho é de edição, use o Blender: ver
`editar_localizado.md`.

## Rota manifold3d (padrão do dono)

Peça funcional para impressão sai de um gerador Python com **manifold3d** (sólidos e booleanas),
**numpy** e **trimesh** (exportação e medidas). Um arquivo `gera.py` por projeto, com as cotas em
constantes no topo e uma função por peça; `pecas()` devolve `[(nome, Manifold)]` e o montador
grava STL ou 3MF.

**Construir**

- Perfil 2D em `mf.CrossSection` (retângulo, `circle(r, n)`, polígono) e `Manifold.extrude`.
  Para extrudar em outro eixo, `transform` com matriz 3×4 de **determinante +1**: com −1 a malha
  sai de dentro para fora e a booleana seguinte erra sem aviso.
- Círculo com `n` explícito (96 a 128 para furo ou encaixe); o padrão faceta e muda a folga.
- Várias peças somadas ou subtraídas de uma vez: `batch_boolean(lista, OpType.Add)`.

**Booleana sem face coincidente**

- Todo cortador passa **0,1 mm além** da face que atravessa (`z0 - 0,1`, `y1 + 0,5`). Face
  coincidente deixa lasca de área zero ou parede de espessura nula.
- Peça somada a outra entra na outra (raiz de 0,5 a 1 mm), e não só encosta.

**Da malha do manifold3d para o arquivo**

- Converta e confira como o fatiador vai ver: junte vértices (`merge_vertices`) e exija malha
  fechada **e** sem face de área < 1e-10. Se falhar, `m.simplify(1e-5)` e tente de novo (até 4
  vezes; a função `robusto()` dos geradores faz isso). Sem vértices soldados o fatiador fecha
  furos: ver `projetar_para_imprimir.md`, seção 11.
- Orientação de impressão depois, na malha do trimesh: rotação (`rotation_matrix`) e translação
  para `bounds[0] = 0`. Modele sempre na posição de uso.

**Conferir antes de entregar**

- Interferência entre peças montadas: volume de `a ^ b` na posição de uso. Zero é encaixe sem
  interferência; aperto proposital aparece como volume positivo e deve bater com o calculado.
- `verificadores/check_mesh.py` em cada STL, e as quatro vistas de `render_de_conferencia.md`.
- 3MF com várias placas, configuração do fatiador e conferência no G-code: skill `bambu-a1`,
  `references/operacao.md`.

## Rota build123d (quando precisar de STEP/CAD)

Use quando a peça é descrita por parâmetros e operações e você quer sólido analítico,
STEP e varredura de família.

### Escrever a peça como função de parâmetros

Uma função que devolve o sólido, com **todos** os parâmetros nomeados e com padrão.
O pacote traz duas prontas em `cenarios/familia_exemplo.py`; esta é a primeira
(dimensões escolhidas para o exemplo):

```python
def familia_placa(L=80.0, P=50.0, T=6.0, d=5.0):
    """Placa com dois furos de fixação."""
    from build123d import Align, Box, Cylinder, Pos
    corpo = Box(L, P, T, align=(Align.CENTER, Align.CENTER, Align.MIN))
    furos = [Pos(x, 0, 0) * Cylinder(d / 2, T * 3) for x in (-L / 4, L / 4)]
    return corpo - furos
```

Duas regras que evitam a maior parte dos defeitos desta rota:

1. **Atravesse de verdade.** O cilindro do furo tem altura `T * 3`, não `T`. Corte com
   a mesma altura da parede produz faces coincidentes e o resultado pode degenerar
   (ver "Booleana e ida e volta por STL").
2. **Nada de constante mágica.** Se um valor precisa existir, ele é parâmetro ou sai
   de outro parâmetro.

### Varrer a família, não uma amostra

O mesmo código sai limpo num valor e defeituoso no vizinho: varra a grade, não uma
amostra. O defeito de coincidência paramétrica (a IGUALDADE entre duas expressões, não
o valor) está medido em "Booleana e ida e volta por STL".

A varredura importa o seu módulo pelo nome, então o diretório dele tem que estar no
caminho de importação. **A sintaxe difere por shell**, e o ambiente medido deste
pacote é Windows:

```powershell
# PowerShell, que e o shell do ambiente medido
$env:PYTHONPATH = "cenarios"
python verificadores/sweep_params.py --modulo familia_exemplo --funcao familia_placa --grade "L=70,80;d=4,5" --saida saida --json varredura.json
```

```bash
# bash, Git Bash ou POSIX
PYTHONPATH=cenarios python verificadores/sweep_params.py \
       --modulo familia_exemplo --funcao familia_placa \
       --grade "L=70,80;d=4,5" --saida saida --json varredura.json
```

`PYTHONPATH=... comando` **não** funciona em PowerShell: lá não existe prefixo de
variável na linha de comando.

Medido nessa grade: 4 variantes, **4 aprovadas**, 0 reprovadas por geometria, 0 erros
operacionais.

**`--saida` e `--json` são resolvidos contra o diretório de execução, e o padrão de
`--saida` é relativo (`varredura`).** Como a receita manda executar de dentro do
pacote, seguir os exemplos ao pé da letra **grava dentro da pasta da habilidade**.
Use **caminho absoluto** nos dois, apontando para a sua pasta de trabalho. Os exemplos
acima usam caminho curto para caber na linha; num trabalho de verdade, escreva o
caminho inteiro.

Cada variante passa por três portões:

| Portão | O que exige |
|---|---|
| 1. sólido | contagem de corpos declarada e volume positivo — o contrato vem da **representação** |
| 2. malha | zero arestas abertas, zero não-manifold, zero degeneradas, orientação consistente, estanque |
| 3. formato fechado | o escritor de 3MF aceita (não é portão de graça: ver `verificar.md`, "Exportação não é verificação") |

**Declare a representação, mesmo no caso simples.** `--representacao` e `--n-solidos`
são opcionais na linha de comando e valem `solido` e `1` quando omitidos — que é
exatamente o caso dos exemplos desta página. Escrever
`--representacao solido --n-solidos 1` torna o contrato explícito, e é o que se deve
fazer quando o número de corpos importa: se a sua família produzir 2 corpos e você não
declarar, o portão 1 **reprova** com `n_solidos_esperado: 1`, e a reprovação é
correta.

O portão 1 muda com a representação declarada: `superficie` exige faces e **zero**
sólidos; `montagem` exige a contagem declarada de corpos. Para superfície, a borda é
declarada, não deduzida: `--borda obrigatoria|proibida|indiferente`.

### Falha operacional separada de reprovação geométrica

Isto vem pronto e é o motivo de a varredura ser confiável. No relatório:

| Campo | Significado |
|---|---|
| `n_aprovadas` | passaram nos três portões |
| `n_reprovadas_por_geometria` | a geometria é ruim |
| `n_com_erro_operacional` | **não foram avaliadas**: permissão, disco, dependência |
| `erros_operacionais[].codigo` / `.etapa` | onde parou, com código estável |

Falha de escrita **nunca** entra na contagem de reprovadas por geometria. Se você
escrever sua própria varredura, replique isso: sem essa separação, um problema de
ambiente vira evidência sobre a peça.

### Exportar para medir e declarar o que a peça tem que atender

Exporte **antes de medir**, e trate esta exportação como intermediária: os `v_*.stl`
que a varredura grava são das **variantes**, não do `peca_para_medir.stl` do comando de
medida.

```python
from build123d import export_stl
export_stl(peca, "peca_para_medir.stl", tolerance=0.01, angular_tolerance=0.1)
```

A varredura prova que a geometria é bem formada. Ela **não** prova que a peça é a
pedida. Para isso, declare requisitos e verifique **contra o arquivo que você acabou
de exportar**:

```json
{"requisitos": [
   {"id": "envelope", "tipo": "caixa", "valor": [80.0, 50.0, 6.0], "tol_mm": 0.5},
   {"id": "um_corpo", "tipo": "n_solidos", "valor": 1},
   {"id": "dois_furos", "tipo": "n_furos_no_plano", "eixo": "z", "plano": 3.0,
    "valor": 2}
 ]}
```

O nome do requisito tem de bater com o que o tipo mede: quem conta furos é
`n_furos_no_plano`, que precisa do plano onde medir — aqui `z = 3,0`, no meio da
espessura de 6. Formato, tolerâncias, estados (`NAO_IMPLEMENTADA` barra quando o papel
é decisivo) e a guarda `valida_requisitos.py`: `verificar.md`.

```bash
python verificadores/check_intent.py --malha peca_para_medir.stl --requisitos req.json
```

### Exportação final

A anterior existe para **medir**. Esta é a que você entrega, e vale re-exportar com o
nome final depois de os requisitos passarem — inclusive porque o formato de intercâmbio
pode ser outro:

```python
from build123d import export_stl, export_step
export_stl(peca, "peca.stl", tolerance=0.01, angular_tolerance=0.1)
export_step(peca, "peca.step")
```

Confira o artefato entregue, e não a peça que você acha que exportou:

```bash
python verificadores/check_mesh.py --malha peca.stl
```

### Armadilhas do build123d

| Sintoma | Causa | O que fazer |
|---|---|---|
| rosca por `sweep` + `Helix`: `is_valid` verdadeiro e o STL com centenas de arestas abertas; recorte da hélice derruba o kernel | varredura helicoidal no OCC | filete em malha + manifold3d: `projetar_para_imprimir.md`, seção 3 |
| revolve de um setor (menos de 360°) sai com volume negativo e não funde | a face do perfil tem normal oposta ao giro (−Y para giro positivo em Z) | oriente o perfil pelo sentido do giro e confira `face.normal_at()` |
| setores revolvidos em separado e fundidos saem inválidos | cilindros coincidentes entre os setores | revolva 360° uma vez e **recorte** os setores; cortadores com raios que passam das faces da peça |
| extrusão "para cima" de um `Polygon` vai para baixo | a normal do polígono segue a ordem dos pontos (o `convex_hull` do shapely a inverte) | passe `dir=(0, 0, ±1)` explícito em todo `extrude` de polígono vindo de outra biblioteca, e confira por corte em várias alturas |
| `extrude(..., taper=…)` sai alargando em vez de afunilar | o sinal do `taper` é relativo à direção da extrusão | extruda a partir da face aberta, na direção do fundo, com `taper` positivo; meça a área em 3 cortes |

## Booleana e ida e volta por STL

**Coincidência paramétrica gera contato tangente, e o defeito é a IGUALDADE entre
duas expressões, não o valor.** Medido com corte de altura **igual** à parede:

| Diâmetro do furo | Espessura da parede | Arestas não-manifold |
|---|---|---|
| 4 | 4 | **6** |
| 5 | 5 | **6** |
| 3 | 4 | 0 |
| 6 | 4 | 0 |

4/4 e 5/5 quebram igualmente: o valor não importa; a igualdade importa. Esta tabela
**não reproduz com o `familia_placa` que acompanha o pacote**, e isso é deliberado: ela
mede o corte com altura igual à parede, e a função entregue atravessa com `T * 3`.
Rodando a igualdade na função entregue — `--grade "T=4,5;d=4,5"` — dá **4 variantes, 4
aprovadas, 0 arestas não-manifold, 0 abertas**. A tabela é o registro do defeito que a
folga resolve, não um aviso sobre o código atual; numa família sua, ela volta a valer.

Trocar por `d != parede` não resolve: 4,0 e 4,5 são diferentes, e a única medição de
meio milímetro que existe, no par análogo, deu **4 arestas defeituosas contra 2 da
igualdade exata** — **pior**. **A separação mínima segura é `A_CALIBRAR`: não há número
medido, e este documento não é lugar de inventar um.** Ela sai de varredura com a
geometria real. O que existe medido é a folga que **funciona** na família entregue:
altura de corte `T * 3`, com 0 defeitos em toda a grade ensaiada.

**A igualdade de altura não implica degeneração.** Placa 30 × 20 × 4 com corte
cilíndrico de altura 4, ambos `Align.MIN` em Z, mediu **zero** não-manifold e zero
degeneradas: o que produz o defeito é a coincidência de **faces**, que depende do
alinhamento e não só do número. Com os dois começando em z=0 e a mesma altura, as
faces de topo e de base coincidem em par e o kernel resolve; foi com outro alinhamento
que as 6 arestas foram medidas. Diagnostique pela medida, não pelo padrão do código.

Setores revolvidos em separado e fundidos (cilindros coincidentes entre setores) têm a
mesma raiz, faces coincidentes: ver "Armadilhas do build123d".

**Malha, fora do kernel:**

- **`manifold3d` não resolve auto-interseção.** `trimesh.boolean.union([m])` com uma malha
  só devolve a mesma malha: mover vértices para dentro do próprio sólido não muda o volume
  (175,485 cm³ antes e depois). O que ele faz bem é unir **sólidos separados**; quando
  fragmenta, o maior componente costuma ser o correto.
- **Resultado de booleana não sobrevive à ida e volta por STL** (euler −138 → −79, arestas
  não-manifold). Encadeie em memória; entre etapas, `.npy` de vértices e faces.
- **Recortar antes de engrossar.** Depois de engrossado, `slice_plane(cap=True)` deixa borda
  aberta (35 a 332 arestas). Recortando a malha limpa e engrossando dentro do cupom, sai
  fechado.
- Se a peça final precisa de uma booleana já feita numa versão antiga, prefira
  `transplante_de_deslocamento.md` a refazê-la na versão engrossada.

**Ida e volta por STL:**

- **Reexportar a MESMA forma com outra tolerância devolve a malha em cache**, com a
  contagem de triângulos idêntica, sem aviso nenhum: o kernel guarda a triangulação.
  Se a tolerância importa, construa do zero.
- **STL não compartilha vértices**: ao reler, solde (`merge_vertices`) antes de contar
  topologia. `check_mesh.py` já solda (números em `verificar.md`).
- O status do kernel de malha não é oráculo de validade; confie nas contagens
  topológicas (`verificar.md`).
- Exportar com sucesso, inclusive em 3MF, não prova validade geométrica; confira o
  artefato entregue com `check_mesh.py`.

## Decisão por sintoma

| Sintoma | Diagnóstico | Ação |
|---|---|---|
| uma variante da grade quebra e as vizinhas não | provável coincidência paramétrica | procure a **igualdade** entre expressões, não o valor |
| malha com arestas não-manifold e você não mudou nada | **pode ser** corte com altura igual à parede, e há outras causas | atravesse com folga; a folga é parâmetro, não constante (ver "Booleana e ida e volta por STL") |
| a varredura devolve erro operacional | ambiente, não geometria | corrija o ambiente; **não** conte como reprovação |
| tolerância de malha "não faz efeito" | triangulação em cache | construa do zero em vez de reexportar |
| pedem folga de encaixe | há valores calibrados, cada um com as suas condições | `projetar_para_imprimir.md`, seção 1; fora das condições, `A_CALIBRAR`: diga o que seria preciso medir |

## Exemplo sintético completo

Gerador: `cenarios/familia_exemplo.py`, que acompanha o pacote. **Nada aqui
depende de arquivo fora dele.**

Varredura da seção "Varrer a família": `n_variantes: 4`, `n_aprovadas: 4`,
`n_reprovadas_por_geometria: 0`, `n_com_erro_operacional: 0` (medido).

Defeito plantado, para conferir que o detector está vivo: `--grade "L=80;d=5,40"`.
Com `d=40` num comprimento 80 os furos alcançam as bordas e o vizinho.

**Medido:** 2 variantes, 1 aprovada, **1 reprovada por geometria**, **0 erros
operacionais**; a variante `d=40` sai com **3 arestas não-manifold** e **0 arestas
abertas**. Ela reprova onde deve, e a reprovação não foi confundida com falha de
ambiente.

O mesmo arquivo traz `familia_suporte_em_L`, para exercitar a rota com outra
topologia de parâmetros.

**Controle de erro operacional**, que tem que ficar **separado**. Apontar `--saida`
para um caminho sem permissão de escrita **não serve**: a criação do diretório de
saída acontece **antes** do laço e fora do tratamento de exceção, e o resultado é um
traceback cru de `os.makedirs` (`PermissionError` ou `FileNotFoundError`), sem JSON,
sem `codigo` e sem `etapa`. O controle que **reproduz** deixa o diretório criável e
faz falhar a *escrita*: crie, dentro de `--saida`, um **diretório** com o nome exato do
3MF da primeira variante.

```powershell
$T = "C:\caminho\da\sua\pasta\controle"
New-Item -ItemType Directory -Force "$T\saida\v_L70_d4.3mf" | Out-Null
$env:PYTHONPATH = "cenarios"
```

E rode a varredura da grade `"L=70,80;d=4,5"` com `--saida "$T\saida"` e
`--json "$T\rel.json"`.

**Medido:** código de saída 1, `n_aprovadas: 3`, **`n_reprovadas_por_geometria: 0`**,
`n_com_erro_operacional: 1`, e o erro traz `codigo: "E_EXPORT_3MF"`, `etapa:
"exportacao"`, a causa *"o caminho de saida … esta ocupado por um diretorio"* e
`etapas_concluidas: ["portao_1_solido", "exportacao_malha"]` — que é a prova de que a
injeção atingiu a etapa pretendida, e não uma anterior.

Limite conhecido: **falha na criação do diretório de saída sobe como traceback**, não
como erro operacional classificado. Se o seu `--saida` não puder ser criado, você
recebe um traceback de `os.makedirs` e nenhum JSON. Confira o caminho antes de varrer.

## Regras de impressão (folga, espessura mínima, feição delicada, rosca, negativos, gravação)

Estão reunidas em `projetar_para_imprimir.md`, a referência de projetar para imprimir.
