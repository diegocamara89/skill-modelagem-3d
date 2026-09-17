# Render de conferência: o portão visual antes de entregar

Rota para: **toda geometria criada ou visivelmente alterada**, antes de dizer que está
pronta. Quatro vistas ortográficas, conferidas por quem entrega.

Ferramenta: `scripts/render_conferencia.py`, versão **1.0.0**. Roda **dentro do
Blender**, pelo contrato `executar(config)` de `scripts/executa_com_relatorio.py`, ou
por `renderizar(config)` na sessão viva.

Origem da doutrina: `skills/cad/references/snapshot-review.md` de
[earthtojake/text-to-cad](https://github.com/earthtojake/text-to-cad) (MIT). A política,
o pacote de quatro vistas e a regra do "diagnóstico, não veredito" vêm de lá. O código
aqui é próprio: o renderizador de lá é Chromium headless sobre documento STEP, que não
serve para malha em sessão do Blender.

## A política

**Obrigatório.** Verificador determinístico ter passado **não é motivo para pular.**
Malha fechada, euler certo e requisito `APROVADA` não provam que a peça tem a forma
pedida — isso é a regra 2 da SKILL.md, e o render existe justamente para o outro lado
dela.

Só se pula em caso nomeado, **e o motivo vai no relatório**:

| Pode pular | Por quê |
|---|---|
| exportação ou conversão de formato sem mudar geometria | não há forma nova para conferir |
| alteração que comprovadamente não muda geometria visível | idem, e a comprovação vai junto |
| tarefa só de inspeção ou medição, que não cria nem altera nada | não há entrega de forma |
| falha antes de existir artefato válido | não há o que renderizar |

Fora desses, sem render conferido não se declara pronto.

**Não fique em laço de render.** Renderize de novo só quando um reparo mudou a
geometria visível, ou quando um achado específico precisa de confirmação.

## As quatro vistas, e por que são essas

| Vista | Direção (do centro para a câmera) | O que ela existe para pegar |
|---|---|---|
| `iso` | (1, −1, 0.8) | forma geral, topo e duas laterais |
| `iso_oposto` | (−1, 1, −0.8) | base e as duas laterais restantes |
| `topo` | (0, 0, 1) | padrão, simetria, posição de furo em planta |
| `frente` | (0, −1, 0) | perfil, altura, degrau, ressalto |

`iso_oposto` é a **negação exata** de `iso`, e essa escolha é a razão de ser do par:
toda face cuja normal não seja perpendicular a essa direção aparece em **uma das duas**.
Cobertura por construção, não por suspeita — não é preciso desconfiar da base para
que a base seja conferida.

**Medido neste pacote, em 17/09/2026.** Uma peça com bolso raso e furo cego **só na
face de baixo** saiu como um bloco perfeitamente liso na `iso`, sem nenhum vestígio
dos dois defeitos, e mostrou os dois com clareza na `iso_oposto`. Uma vista isométrica
sozinha teria aprovado a peça.

Quando uma imagem basta e quando não: uma `iso` resolve peça simples e estática. Use
as quatro quando o erro semântico é plausível — montagem ou mais de um corpo, furos em
faces ou eixos diferentes, casca, cavidade, furo cego ou recinto fechado, nervura,
ressalto, aba ou padrão repetido, reparo depois de falha booleana, e sempre que
"parecer o objeto pedido" faz parte da tarefa.

## Chamada

```python
{"objeto": "NOME_REAL_DO_OBJETO",
 "pasta": "CAMINHO_ABSOLUTO_DA_PASTA_DE_SAIDA",
 "prefixo": "peca",
 "resolucao": [1024, 768],
 "vistas": ["iso", "iso_oposto", "topo", "frente"],
 "margem": 0.12}
```

`objeto` ou `objetos` nomeia o alvo; sem nenhum dos dois, entram todos os MESH visíveis
da cena. `pasta` é obrigatória. Os arquivos saem como `<prefixo>_<vista>.png`.

Nome de objeto dos exemplos **não identifica o objeto do usuário**. Pegue o nome real
antes de chamar.

## O que o relatório traz, e o que fazer com cada campo

| Campo | O que ele é |
|---|---|
| `fracao_silhueta` | fração de pixels com alfa > 0, ou seja, a silhueta **medida** |
| `vistas_praticamente_vazias` | vistas com silhueta abaixo de 0,1% — imagem vazia na prática |
| `bbox_extensao_mundo` | extensão da caixa envolvente em X, Y, Z, no mundo |
| `atualizado_de_edit_mode` | objetos em que foi preciso chamar `update_from_editmode()` |
| `ortho_scale_mm` | largura de mundo que a imagem cobre, por vista |
| `sha256` e `bytes` | identidade do arquivo que você conferiu |
| `cena_do_usuario_alterada` | sempre `false`; ver abaixo |

`vistas_praticamente_vazias` não vazio é **falha de conferência, não peça aprovada**:
enquadramento errado, objeto oculto, malha sem face. Resolva antes de olhar as imagens.

O fundo é transparente de propósito. Com alfa zero no fundo, a silhueta é medida e não
estimada — um PNG em branco não consegue se passar por render bom.

## Três armadilhas medidas

**1. Em EDIT_MESH o datablock está atrasado.** O render sairia da malha **anterior**, e
o defeito que você acabou de introduzir não apareceria. O script chama
`obj.update_from_editmode()` antes de medir e renderizar, e diz que chamou em
`atualizado_de_edit_mode`. Se você escrever outro renderizador, repita isso.

**2. A cena do usuário não é tocada.** Todo o render acontece numa cena temporária,
criada e removida ali mesmo; os objetos são apenas **vinculados**, nunca copiados nem
movidos. Motor, resolução, câmera e caminho de saída do usuário ficam como estavam.
Conferido no teste: mesma contagem de cenas, mesmos objetos, nenhuma câmera órfã,
motor e `filepath` idênticos antes e depois.

**3. A vista de baixo sai escura — e isso NÃO é o problema.** Vale registrar porque a
suposição óbvia está errada, e foi derrubada por medida em 17/09/2026, na vista de
baixo da peça de teste com defeito:

| Modo de luz | brilho mín. | brilho médio | contraste |
|---|---|---|---|
| `STUDIO` | 0,058 | 0,367 | 0,148 |
| `MATCAP` | 0,039 | 0,341 | 0,159 |

`MATCAP` é **levemente mais escuro**, não mais claro. `use_world_space_lighting = False`
também não muda nada no render — testado. E abaixo de 0,15 de brilho ficam apenas
0,2–0,4% da silhueta: bolso raso e furo cego na face de baixo **aparecem nos dois
modos**. O que revelava o defeito nunca foi o brilho; foi **olhar a face certa**.

O script usa `MATCAP` porque ele ilumina no espaço da câmera e as quatro vistas recebem
a luz do mesmo jeito — consistência entre vistas, não correção de escuridão. Mais
`show_cavity`, que realça quina, vinco e faceta sem depender da direção da luz.

Se um dia a escuridão realmente atrapalhar numa peça sua, a saída não é trocar a luz:
é acrescentar a vista que olha aquela face de frente.

## O limite, que é o mais importante desta página

**Imagem é diagnóstico, não veredito.** Nenhuma alegação se sustenta em "está certo na
imagem". Toda suspeita levantada aqui vira **medida** antes de virar afirmação:

| Na imagem | A medida que decide |
|---|---|
| padrão de furos parece assimétrico | meça os centros e compare as distâncias |
| tampa ou peça filha parece deslocada | confira a matriz e a folga de montagem |
| nervura ou ressalto parece solto | conte componentes conexos e confira a junção |
| cavidade ou furo cego parece errado | seção no plano, depois profundidade e parede |
| parede parece fina | meça a parede; a imagem não mede espessura |

E o render **não prova**: dimensão, parede, folga, passagem de furo, malha fechada,
orientação de normal nem aptidão para fabricação. Isso continua sendo dos verificadores,
em `referencias/verificar.md`, e a passagem de furo continua **não verificada** por
nenhum deles.

No registro do trabalho entram os quatro PNGs — ou o motivo declarado do skip — e quais
verificações determinísticas sustentam cada achado visual.
