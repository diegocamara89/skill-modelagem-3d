# Dependências, versões e licenças

Levantado em 08/09/2026, das versões **efetivamente instaladas** nesta máquina, por
`importlib.metadata`. Não é lista de intenção: é o que rodou.

## O que o pacote redistribui

**Somente código do autor.** Os quatro auxiliares em `produto/scripts/`, os geradores
e ensaios em `produto/cenarios/`, as referências em `produto/referencias/`, e as cinco
cópias byte a byte dos verificadores estabilizados em M0, em `produto/verificadores/`,
que também são código do autor.

Nenhuma biblioteca de terceiros é incluída. Elas são **dependências declaradas**, que
o usuário instala. Usar uma ferramenta não é motivo para redistribuir o código dela.

## Dependências do Python do hospedeiro

| Pacote | Versão medida | Licença | Quem precisa |
|---|---|---|---|
| `trimesh` | 5.0.0 | MIT | `check_mesh.py`, `check_intent.py`, `secoes.py`, `sweep_params.py` |
| `numpy` | 2.2.6 | BSD 3-Clause | os mesmos |
| `manifold3d` | 3.5.2 | Apache-2.0 | `check_mesh.py`, `check_intent.py` |
| `shapely` | 2.1.2 | BSD 3-Clause | `secoes.py` |
| `build123d` | 0.11.1 | Apache-2.0 | `sweep_params.py`, `cenarios/familia_exemplo.py` |
| `cadquery-ocp-novtk` | 7.9.3.1.1 | Apache-2.0 | vem com `build123d`; é o kernel geométrico |
| `lib3mf` | 2.5.0 | BSD | escritor de 3MF, usado pelo terceiro portão da varredura |
| `scipy` | 1.16.3 | BSD 3-Clause | dependência transitiva |

**Ausentes, e nunca exigidas:** `rtree`, `matplotlib`, `fast_simplification`. Se algo
parecer precisar delas, é defeito da receita.

## Sete são pedidas; a oitava é transitiva. Instalar traz 48 pacotes

**A classificação da tabela acima estava errada, e a quinta revisão apontou.** O
comando medido pede **sete**: `trimesh`, `numpy`, `manifold3d`, `shapely`,
`build123d`, `lib3mf` e `scipy`. `cadquery-ocp-novtk` **não** está no comando — ela
entra por transitividade do `build123d`, que é exatamente o que a coluna "quem
precisa" já dizia dela, e ainda assim ela foi contada entre as diretas.

Isto foi medido, não estimado, e a versão anterior deste documento omitia: num `venv`
criado do zero, `pip install` das **sete** pedidas instala **48 pacotes**. A lista
completa, com versão de cada um, está em `evidencias_finais/AMBIENTE_ISOLADO.json`,
campo `dependencias.instalados_pelo_ensaio` — junto do `pip list` de antes, que traz
só `pip 24.3.1`, o que é o que torna a diferença conferível.

Os outros **41** vêm por transitividade, a maioria de `build123d` — incluindo
`cadquery-ocp-novtk` e `cadquery-ocp-proxy`:

`anytree` 2.13.0, `asttokens` 3.0.2, `cadquery-ocp-proxy` 7.9.3.1.1, `certifi` 2026.7.22, `charset-normalizer` 3.5.1, `cloudpickle` 3.1.2, `colorama` 0.4.6, `executing` 2.2.1, `ezdxf` 1.4.4, `fonttools` 4.64.0, `idna` 3.19, `ipython` 9.17.1, `ipython_pygments_lexers` 1.1.1, `jedi` 0.20.0, `joblib` 1.6.0, `matplotlib-inline` 0.2.2, `mpmath` 1.3.0, `narwhals` 2.25.0, `ocp_gordon` 0.2.2, `ocpsvg` 0.6.0, `parso` 0.8.7, `prompt_toolkit` 3.0.53, `psutil` 7.2.2, `pure_eval` 0.2.3, `pygments` 2.21.0, `pyparsing` 3.3.2, `requests` 2.34.2, `scikit-learn` 1.9.0, `stack-data` 0.6.3, `svgelements` 1.9.6, `svgpathtools` 1.8.0, `svgwrite` 1.4.3, `sympy` 1.14.0, `threadpoolctl` 3.6.0, `traitlets` 5.16.1, `trianglesolver` 1.2, `typing_extensions` 4.16.0, `urllib3` 2.7.0, `wcwidth` 0.8.3, `webcolors` 24.8.0

**Limite declarado, e ele importa:** a licença foi identificada **uma a uma** apenas
para as oito da tabela. Para as outras 40 eu tenho versão medida e **não**
tenho verificação individual de licença. Isso não afeta o que o pacote redistribui —
que continua sendo somente código do autor, nenhum binário e nenhuma biblioteca — mas
afeta o que um operador instala na máquina dele, e por isso está escrito aqui em vez
de ficar implícito num "oito dependências".

A conferência que sustenta este parágrafo saiu do próprio instrumento depois de ele
ser corrigido: a primeira versão gravava a lista de pacotes **truncada** em 1500
caracteres, o JSON não carregava, e a comparação respondia "0 instalados" sobre lista
nenhuma — o mesmo defeito da auditoria que extraiu zero padrões e reportou zero
achados.

`matriz.py` e `scripts/roda_blender.py`, `scripts/mcp_blender.py` e
`scripts/valida_requisitos.py` rodam **só com a biblioteca padrão**. É por isso que a
rota independente continua útil sem Blender e sem as bibliotecas de malha.

## Dependência externa: Blender

| | |
|---|---|
| Versão medida | **5.2.1 LTS**, Python interno 3.13.13 |
| Instalação medida | Microsoft Store |
| Licença do Blender | **GPL** |
| Redistribuído? | **Não.** É pré-requisito que o usuário instala |
| Complemento MCP | comunitário, instalado pelo usuário; **não** redistribuído |

## Uma questão de licença que é decisão do autor, não minha

`produto/scripts/bl_ferramentas.py` e os arquivos de `produto/cenarios/` **importam
`bpy`** e rodam **dentro** do processo do Blender.

O fato relevante: a Blender Foundation sustenta publicamente que script que usa a API
Python do Blender é obra derivada do Blender e, ao ser **distribuído**, precisa ser
compatível com GPL. Essa é a posição deles; não é consenso universal e há discussão
sobre onde termina a fronteira entre uso e derivação.

**Não estou concluindo a licença deste produto.** Registro o fato porque ele afeta
diretamente a decisão de vender o pacote, e porque neste projeto eu já afirmei uma
premissa de licença errada uma vez, sobre outro material, e a revisão externa me
corrigiu. Não vou repetir o padrão.

Três caminhos possíveis, e a escolha é do autor, com assessoria:

1. **distribuir a parte que toca `bpy` sob licença compatível com GPL**, mantendo
   proprietário o que não importa `bpy` — hoje isso seria `roda_blender.py`,
   `mcp_blender.py`, `valida_requisitos.py`, os cinco verificadores e todas as
   referências, que juntos são a maior parte do valor;
2. **não distribuir os arquivos que importam `bpy`**, e documentar as chamadas para o
   usuário colar, o que degrada a receita justamente no ponto que o plano manda
   entregar pronto;
3. **distribuir tudo sob licença compatível com GPL**, tratando o pacote como obra
   derivada.

Enquanto a decisão não existir, o pacote fica **local**. Publicação é ação separada e
não está autorizada por nenhuma etapa deste plano.

## Como conferir este levantamento

```bash
python -c "import importlib.metadata as md; [print(a, md.version(a)) for a in ('trimesh','numpy','manifold3d','shapely','build123d','cadquery-ocp-novtk','lib3mf','scipy')]"
python produto/scripts/roda_blender.py --achar
```

E, para a versão do Blender, um script que imprima `bpy.app.version_string` pelo
contrato de arquivo de resultado descrito em `mapa_de_ferramentas.md`.
