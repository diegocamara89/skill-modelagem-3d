# Inspecionar e orientar seleção

Para sessão aberta, use primeiro `scripts/sessao_blender.py --diagnosticar`:
`referencias/sessao_e_edicao_guiada.md` documenta o retorno e o próximo passo.
Flags persistidas de objetos ocultos não são a seleção viva do operador.

Rota para: abrir um modelo, entender o que está selecionado, orientar o usuário a
selecionar, e transformar "essa região aí" num alvo com coordenadas.

## Pré-condições, e como consultá-las

Nunca oriente nem edite antes de ler o estado. **A aparência engana em três pontos
diferentes**, todos medidos.

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
d = F.diagnostico("NomeDoObjeto")   # ou sem argumento, para o objeto ativo
```

O que olhar no retorno, e por quê:

| Campo | Por que importa |
|---|---|
| `modo` | leitura de seleção só é confiável em `EDIT_MESH` |
| `selecao_viva.fonte` | em Edit Mode vem de `bmesh.from_edit_mesh`, que é a seleção **real**. `obj.data` está desatualizado |
| `objeto.matriz_mundo_e_identidade` | se falso, coordenada local ≠ coordenada de mundo, e todo critério precisa converter |
| `objeto.caixa_mundo_min/max` | é contra esta caixa que você monta qualquer critério de seleção |
| `objeto.modificadores` | modificador visível muda o que se vê sem mudar a malha base |
| `escala_de_unidade` | relacione a escala da cena às unidades do pedido antes de comparar distâncias |
| `sobreposicoes.disponivel` | em headless é `false` porque **não existe interface**. Ausência não é "desligadas" |

## O erro que mais custa: coordenada local contra critério de mundo

MEDIDO em 07/09/2026. Cubo de aresta 20 posicionado em z=10 ocupa **0 a 20 no mundo**
e **−10 a +10 no local**. O critério "faces com centro acima de z=15":

| Como foi calculado | Faces selecionadas |
|---|---|
| `f.calc_center_median().z > 15` | **0** |
| `(obj.matrix_world @ f.calc_center_median()).z > 15` | **1** |

E o pior: com zero faces, a edição seguinte **não acusa erro**. `transform.translate`
devolve `{'CANCELLED'}` e a geometria fica intacta — o que se parece com sucesso em
qualquer registro que só observe exceção.

Use a função pronta, que já converte e **conta depois de marcar**:

```python
F.entra_em_edicao("Peca", modo_de_selecao="face")
r = F.seleciona_faces_por_caixa_de_mundo(
        "Peca",
        minimo=[0.0, 0.0, 19.999],      # coordenadas de MUNDO
        maximo=[20.0, 40.0, 20.001],
        criterio="centro")              # ou "todos"
# r["faces_marcadas"] é contagem lida na própria bmesh, não intenção
```

Ela **levanta `ErroDePrecondicao` quando nada foi selecionado**, e a mensagem traz a
caixa real do objeto em mundo, para você corrigir o critério.

Escolha do critério:

- `"centro"` — o centro da face está na caixa. Bom para "pegue a face de cima".
- `"todos"` — **todos** os vértices da face estão na caixa. Use quando a caixa
  delimita uma região protegida: triângulo pode atravessar a caixa com o centro
  dentro dela, e aí "está dentro" seria falso.

## Quando o usuário diz que o clique não funcionou

Não conclua que falhou. Conte a seleção:

```python
F.diagnostico("Peca")["selecao_viva"]["faces_selecionadas"]
```

| Contagem | Diagnóstico | Ação |
|---|---|---|
| > 0 | há seleção, o destaque é que está invisível | ensine o controle de sobreposições, não repita o clique |
| 0, em Object Mode | a leitura foi feita no lugar errado | entre em Edit Mode e releia |
| 0, em Edit Mode | não há seleção mesmo | oriente a seleção |

Orientação de interface, confirmada no mapa de teclas desta instalação, **5.2.1 LTS**:

- Mantenha o mouse **sobre a área 3D** ao usar atalhos.
- `Tab` alterna Object Mode e Edit Mode quando o contexto permite.
- `Z` abre o menu de sombreamento; escolha **Sólido**.
- `Shift + Alt + Z` alterna sobreposições. Confirmado consultando
  `wm.context_toggle` com `data_path=space_data.overlay.show_overlays` no keymap
  ativo. **Reconfirme em mapa personalizado.**
- Alternativa visual: o botão **Mostrar sobreposições**, dois círculos sobrepostos,
  na barra da área 3D. O ícone alterna; a seta ao lado abre as opções.
- Sólido + Edit Mode + sobreposições ligadas mostra superfícies preenchidas com as
  arestas de edição por cima. **Wireframe não é necessário** para isso.
- Em seleção de malha, `3` da **fileira superior** seleciona faces. Não confunda com
  o teclado numérico.
- Clique seleciona uma face; `Shift + clique` acrescenta; `B` seleciona por caixa.
  Explique o efeito de **X-Ray**, que faz a seleção alcançar superfícies ocultas.
- Em STL, **uma face costuma ser um triângulo**, não a superfície funcional inteira.

Depois de apresentar algo ao usuário, **restaure as sobreposições** e informe em que
modo você deixou a cena.

## Seleção capturada envelhece — e o envelhecimento é silencioso

`le_selecao` devolve os índices **e** a assinatura do estado em que eles foram lidos.
Índice de face só tem sentido naquela geometria: booleana, limpeza, undo — qualquer
coisa que retessele renumera tudo.

O perigo não é o índice deixar de existir. É ele **continuar existindo apontando para
outra face**. MEDIDO: numa peça de 16 faces a seleção capturou a face de índice 10;
depois de uma união a peça passou a ter 27 faces, e o índice 10 **ainda existe** —
editar por ele atingiria outra superfície sem erro nenhum e com resultado plausível.

Confira antes de editar por uma captura:

```python
captura = F.le_selecao("Peca")
# ... alguma coisa acontece ...
F.confere_selecao_capturada("Peca", captura)   # levanta ErroDePrecondicao se mudou
```

Medido, com os dois controles:

| Situação | Resultado |
|---|---|
| nada mudou desde a captura | passa, e as duas assinaturas são idênticas |
| houve união entre a captura e o uso | **barra**, comparando as assinaturas e dizendo que os índices não valem |

Sem o primeiro caso, uma função que recusasse sempre satisfaria o segundo.

Depois de undo ou redo, **releia também as referências a objeto e malha**: guardar o
objeto numa variável e reusá-lo depois é erro; releia pelo nome.

## Da seleção ao pedido

Uma seleção ampla **não** fornece direção, origem e destino. Antes de editar:

1. Leia a seleção e os centros em mundo: `F.le_selecao("Peca")`.
2. Localize os limites e as superfícies adjacentes. Meça, não estime pela imagem.
3. Distinga borda aberta, rebaixo, ranhura e mero efeito de sombreamento. Uma seção
   resolve: `F.secao_por_plano("Peca", ponto=[0,20,0], normal=[0,1,0])`.
4. Confirme **somente as ambiguidades materiais**, uma vez. Não repita confirmação já
   respondida.
5. Se o usuário indicar que algo entrou por acidente na seleção, exclua **aquilo** e
   respeite a resposta. Não edite tudo o que foi selecionado automaticamente.

Não infira que uma região é dispensável porque parece pequena ou feia.

## Decisão por sintoma

| Sintoma | Verifique | Ação |
|---|---|---|
| "não selecionou nada" | contagem na bmesh | há seleção invisível → ensine sobreposições |
| seleção inclui superfície lateral | centros em mundo de cada face | pergunte só sobre essa exclusão |
| critério de caixa não pega nada | `caixa_mundo_min/max` do diagnóstico | corrija a caixa; **não** relaxe a tolerância até "pegar alguma coisa" |
| objeto com rotação | `matriz_mundo_e_identidade` falso | critérios de mundo alinhados aos eixos não servem; ver o limite em `editar_localizado.md` |
| modificador na lista | `objeto.modificadores` | o que se vê pode não ser a malha base; decida com o usuário se aplica antes |
| conexão do MCP muda | `get_scene_info` | reconecte; **não** reinstale por inferência |

## Exemplo sintético completo

> **Os números abaixo são desta cena de exemplo, não da sua.** Copiar a caixa daqui
> para outra peça costuma selecionar **zero faces**; copiar o índice de face costuma
> "funcionar" por coincidência e selecionar a face errada. Num ensaio independente, o
> topo do degrau alto de uma peça 44 × 26 × 21 era **também** o índice 10 — a
> coincidência premiaria quem copiasse o índice. Sempre derive a caixa do
> `diagnostico` da **sua** peça.

Gerador: `cenarios/gera_cenario.py` (bloco 60 × 40 × 10 com patamar alto em z=20 de
x=0 a 20, patamar baixo em z=14 de x=40 a 60, vão entre eles).


> **Rodado assim, nesta máquina, em 08/09/2026.** O comando abaixo é uma linha só, de
> propósito: `\` no fim da linha é continuação de shell POSIX e **não** funciona no
> PowerShell, e `/tmp` não existe no Windows. O `--passa-resultado` entrega o caminho
> de `--resultado` ao script como último argumento, então ele é escrito **num lugar
> só** — antes era preciso repeti-lo dentro do arquivo de parâmetros, e duas grafias
> que divergissem davam `SEM_RESULTADO` com o arquivo existindo em outra pasta.

`param.json`, no diretório onde você vai rodar (só o que muda em relação ao padrão;
`{}` também serve):

```json
{"nome": "peca_de_ensaio"}
```

```powershell
python scripts/roda_blender.py cenarios/gera_cenario.py --resultado saida/cenario.json --args param.json --passa-resultado
```

Resultado esperado, **medido** com esse comando: `"estado": "OK"` no auxiliar e, em
`saida/cenario.json`, `medidas` = 20 vértices, 16 faces, 0 arestas abertas, 0
não-manifold, 0 degeneradas, volume 35200. O `gabarito.objeto` é `peca_de_ensaio`.

`estado: "OK"` significa apenas que o script escreveu um relatório legível. Para o
auxiliar **reprovar** um relatório que se declara ruim, acrescente
`--exigir CAMPO=VALOR` — sem isso, um relatório com veredito negativo sai como OK e
com código de saída zero.

Selecionar o topo do patamar alto com a caixa de mundo
`[−0.001, −0.001, 19.999] … [20.001, 40.001, 20.001]` deve dar **1 face**, índice 10.

Controle negativo: a caixa `[1000,1000,1000] … [1001,1001,1001]` deve **barrar** com
`ErroDePrecondicao`, e nada deve ser editado.

**Este controle só é válido em Edit Mode, e é preciso conferir a MENSAGEM.** Um ensaio
independente executou-o em Object Mode: ele barrou, mas com *"a selecao de faces exige
Edit Mode"* — ou seja, **passou sem ter testado a guarda de seleção vazia**. Crédito
por defeito não exercitado é o erro que estes controles existem para evitar, e o
próprio controle caiu nele.

Chame `F.entra_em_edicao(...)` antes, e exija que a mensagem contenha *"nao contem
nenhuma face"*. Só assim o controle prova o que diz provar.
