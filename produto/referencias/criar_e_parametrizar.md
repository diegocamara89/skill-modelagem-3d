# Criar e parametrizar geometria simples

Rota para: "faça uma peça assim", "gere essa família de tamanhos", sem exigir
reconstrução de nada nem impressão.

Duas ferramentas possíveis, e a escolha não é de gosto:

| Backend | Quando |
|---|---|
| **build123d** (código, sólido) | a peça é descrita por parâmetros e operações; você quer sólido analítico, STEP e varredura de família |
| **Blender** | a peça já existe como malha, ou o trabalho é de edição; ver `editar_localizado.md` |

Esta referência trata do primeiro caso.

## Passo 1 — escrever a peça como função de parâmetros

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
   a mesma altura da parede produz faces coincidentes e o resultado degenera.
2. **Nada de constante mágica.** Se um valor precisa existir, ele é parâmetro ou sai
   de outro parâmetro.

## Passo 2 — varrer a família, não uma amostra

O mesmo código sai limpo num valor e defeituoso no vizinho. Isso não é hipótese: é o
achado mais reusável deste projeto.

**Coincidência paramétrica gera contato tangente, e o defeito é a IGUALDADE entre
duas expressões, não o valor.** Medido — e leia a coluna da direita antes de usar
qualquer número daqui:

| Diâmetro do furo | Espessura da parede | Arestas não-manifold | Em que código |
|---|---|---|---|
| 4 | 4 | **6** | corte com altura **igual** à parede |
| 5 | 5 | **6** | idem |
| 3 | 4 | 0 | idem |
| 6 | 4 | 0 | idem |

Repare: 4/4 e 5/5 quebram igualmente. O valor não importa; a igualdade importa.

**Esta tabela não reproduz com o `familia_placa` que acompanha o pacote, e isso é
deliberado.** Ela mede o corte com altura igual à parede; a função entregue atravessa
com `T * 3`, justamente para não cair nisso. Rodando a igualdade na função entregue —
`--grade "T=4,5;d=4,5"` — dá **4 variantes, 4 aprovadas, 0 arestas não-manifold, 0
abertas**. Uma sessão limpa gastou um comando para descobrir isso e quase deixou de
usar `d=8` sem motivo. Ou seja: a tabela é o registro do defeito que a folga resolve,
**não** um aviso sobre o código atual. Se você escrever sua própria família, é aí que
ela volta a valer.

E não adianta trocar por `d != parede`: 4,0 e 4,5 são diferentes, e a única medição
de meio milímetro que existe, no par análogo, deu **4 arestas defeituosas contra 2 da
igualdade exata** — ou seja, foi **pior**. **A separação mínima segura é
`A_CALIBRAR`: não há número medido, e este documento não é lugar de inventar um.**
Ela sai de varredura com a geometria real. O que existe medido é a folga que
**funciona** na família entregue: altura de corte `T * 3`, com 0 defeitos em toda a
grade ensaiada.

Varra:

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
variável na linha de comando. Uma revisão independente apontou que documentar só a
forma POSIX obriga o operador a improvisar justamente o caminho de importação de que a
receita depende.

Medido nessa grade: 4 variantes, **4 aprovadas**, 0 reprovadas por geometria, 0 erros
operacionais.

**`--saida` e `--json` são resolvidos contra o diretório de execução, e o padrão de
`--saida` é relativo (`varredura`).** Como a receita manda executar de dentro do
pacote, seguir os exemplos ao pé da letra **grava dentro da pasta da habilidade**. Uma
sessão limpa criou `<pacote>/varredura/` com dois arquivos assim, sondando o `--help`.
Use **caminho absoluto** nos dois, apontando para a sua pasta de trabalho. Os exemplos
acima usam caminho curto para caber na linha; num trabalho de verdade, escreva o
caminho inteiro.

Cada variante passa por três portões:

| Portão | O que exige |
|---|---|
| 1. sólido | contagem de corpos declarada e volume positivo — o contrato vem da **representação** |
| 2. malha | zero arestas abertas, zero não-manifold, zero degeneradas, orientação consistente, estanque |
| 3. formato fechado | o escritor de 3MF aceita |

**Declare a representação, mesmo no caso simples.** `--representacao` e `--n-solidos`
são opcionais na linha de comando e valem `solido` e `1` quando omitidos — que é
exatamente o caso dos exemplos desta página, e por isso eles funcionam sem declarar
nada. Uma sessão limpa teve que adivinhar isso. Escrever
`--representacao solido --n-solidos 1` torna o contrato explícito, e é o que se deve
fazer quando o número de corpos importa: se a sua família produzir 2 corpos e você não
declarar, o portão 1 **reprova** com `n_solidos_esperado: 1`, e a reprovação é
correta.

O portão 1 muda com a representação declarada: `superficie` exige faces e **zero**
sólidos; `montagem` exige a contagem declarada de corpos. Para superfície, a borda é
declarada, não deduzida: `--borda obrigatoria|proibida|indiferente`.

## Passo 3 — separar falha operacional de reprovação geométrica

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

Nota medida, que contraria uma crença comum: o escritor de 3MF **não** é portão de
graça. Na variante com tangência ele **aceitou** a malha, e quem reprovou foi o
portão de malha.

## Passo 4 — declarar o que a peça tem que atender

A varredura prova que a geometria é bem formada. Ela **não** prova que a peça é a
pedida. Para isso, declare requisitos e verifique:

```json
{"requisitos": [
   {"id": "envelope", "tipo": "caixa", "valor": [80.0, 50.0, 6.0], "tol_mm": 0.5},
   {"id": "um_corpo", "tipo": "n_solidos", "valor": 1},
   {"id": "dois_furos", "tipo": "n_furos_no_plano", "eixo": "z", "plano": 3.0,
    "valor": 2}
 ]}
```

**Cuidado com o nome do requisito contra o que ele mede.** A versao anterior deste
exemplo declarava `{"id": "dois_furos", "tipo": "n_solidos", "valor": 1}`. O nome diz
furos e o tipo conta **corpos desconexos**: uma placa macica, sem furo nenhum, tem um
corpo e passaria. Uma revisao independente pegou isso. Quem conta furos e
`n_furos_no_plano`, e ele precisa do plano onde medir — aqui `z = 3,0`, no meio da
espessura de 6.

```bash
python verificadores/check_intent.py --malha peca.stl --requisitos req.json
```

Requisitos com o mesmo identificador são recusados; um requisito sem medidor sai como
`NAO_IMPLEMENTADA`, que barra quando o papel é decisivo.

## Passo 5 — só então exportar

```python
from build123d import export_stl, export_step
export_stl(peca, "peca.stl", tolerance=0.01, angular_tolerance=0.1)
export_step(peca, "peca.step")
```

Armadilha medida em M0: **reexportar a MESMA forma com outra tolerância devolve a
malha em cache**, com a contagem de triângulos idêntica, sem aviso nenhum. O kernel
guarda a triangulação. Se a tolerância importa, construa do zero.

Confira o artefato entregue, e não a peça que você acha que exportou:

```bash
python verificadores/check_mesh.py --malha peca.stl
```

## Decisão por sintoma

| Sintoma | Diagnóstico | Ação |
|---|---|---|
| uma variante da grade quebra e as vizinhas não | provável coincidência paramétrica | procure a **igualdade** entre expressões, não o valor |
| malha com arestas não-manifold e você não mudou nada | corte com altura igual à parede | atravesse com folga; a folga é parâmetro, não constante |
| a varredura devolve erro operacional | ambiente, não geometria | corrija o ambiente; **não** conte como reprovação |
| tolerância de malha "não faz efeito" | triangulação em cache | construa do zero em vez de reexportar |
| pedem folga de encaixe | não há valor calibrado | diga que é `A_CALIBRAR` e o que seria preciso medir |
| pedem parede mínima ou silhueta | sem medidor | `NAO_IMPLEMENTADA`, não estime |

## Exemplo sintético completo

Gerador: `cenarios/familia_exemplo.py`, que acompanha o pacote. **Nada aqui
depende de arquivo fora dele.**

```powershell
$env:PYTHONPATH = "cenarios"
python verificadores/sweep_params.py --modulo familia_exemplo --funcao familia_placa --grade "L=70,80;d=4,5" --saida saida --json varredura.json
```

Em bash, a forma equivalente é `PYTHONPATH=cenarios python ...` numa linha.

Esperado, **medido**: `n_variantes: 4`, `n_aprovadas: 4`,
`n_reprovadas_por_geometria: 0`, `n_com_erro_operacional: 0`.

Defeito plantado, para conferir que o detector está vivo: grade `"L=80;d=5,40"`.
Com `d=40` num comprimento 80 os furos alcançam as bordas e o vizinho.

**Medido:** 2 variantes, 1 aprovada, **1 reprovada por geometria**, **0 erros
operacionais**; a variante `d=40` sai com **3 arestas não-manifold** e **0 arestas
abertas**. Ela reprova onde deve, e a reprovação não foi confundida com falha de
ambiente.

O mesmo arquivo traz `familia_suporte_em_L`, para exercitar a rota com outra
topologia de parâmetros.

Controle de erro operacional, que tem que ficar **separado**. **O controle que esta
página trazia antes não reproduzia:** ela mandava apontar `--saida` para um caminho sem
permissão de escrita, e o que acontece é um traceback cru de `os.makedirs`
(`PermissionError` ou `FileNotFoundError`), sem JSON, sem `codigo` e sem `etapa` — a
criação do diretório de saída acontece **antes** do laço e fora do tratamento de
exceção. Uma sessão limpa mediu isso duas vezes. Ou seja: a separação de que esta
página mais se orgulha era contornada precisamente pela falha que ela mandava usar
para testá-la.

O controle que **reproduz** deixa o diretório criável e faz falhar a *escrita*: crie,
dentro de `--saida`, um **diretório** com o nome exato do 3MF da primeira variante.

```powershell
$T = "C:\caminho\da\sua\pasta\controle"
New-Item -ItemType Directory -Force "$T\saida\v_L70_d4.3mf" | Out-Null
$env:PYTHONPATH = "cenarios"
python verificadores/sweep_params.py --modulo familia_exemplo --funcao familia_placa --grade "L=70,80;d=4,5" --saida "$T\saida" --json "$T\rel.json"
```

**Medido:** código de saída 1, `n_aprovadas: 3`, **`n_reprovadas_por_geometria: 0`**,
`n_com_erro_operacional: 1`, e o erro traz `codigo: "E_EXPORT_3MF"`, `etapa:
"exportacao"`, a causa *"o caminho de saida … esta ocupado por um diretorio"* e
`etapas_concluidas: ["portao_1_solido", "exportacao_malha"]` — que é a prova de que a
injeção atingiu a etapa pretendida, e não uma anterior.

Limite conhecido, e ele fica aqui em vez de ser corrigido no verificador porque o
verificador é cópia congelada com comportamento estabilizado por teste: **falha na
criação do diretório de saída sobe como traceback**, não como erro operacional
classificado. Se o seu `--saida` não puder ser criado, você recebe um traceback de
`os.makedirs` e nenhum JSON. Confira o caminho antes de varrer.
