# Recuperar, salvar, exportar e deixar retomável

O histórico do Blender é útil e **não é garantido**. Esta referência diz exatamente o
que foi medido, em que condição, e o que fazer quando a garantia não existe.

## O que foi medido sobre desfazer e refazer

Blender 5.2.1 LTS, modo background, 07/09/2026.

**Fato 1 — o sistema nasce desligado em background.** Sem nenhum `ed.undo_push` na
sessão, a chamada falha com *"Undo disabled at startup in background-mode (call
`ed.undo_push()` to explicitly initialize the undo-system)"*. Não é ausência do
operador: é o sistema não inicializado.

**Fato 2 — um ponto só não basta.** Com **um** único push na pilha, `ed.undo` deixa
de passar no `poll()` e a mensagem muda para *"poll() failed, context is incorrect"*.
Não há estado anterior ao qual voltar. Com dois pontos, funciona.

**Fato 3 — mutação direta de dados não entra no histórico.** Escrever a malha por
`bm.to_mesh(obj.data)` altera a geometria e **não** registra nada. Medido: depois de
uma limpeza feita assim, `redo` devolvia a peça ao estado anterior à limpeza e a
conferência por assinatura acusava `recuperou: False`. Não era o `redo` que falhava;
era a limpeza que nunca tinha sido registrada.

**Fato 4 — um ponto por operação lógica, não por chamada.** Empilhar um ponto ao fim
da união e outro ao fim da limpeza faz um `undo` parar no meio: a assinatura não bate
com a de antes da operação, e parece falha de recuperação quando foi recuperação pela
metade.

## A regra que sai dos quatro fatos

```python
F.marca_recuperacao("antes de <a operação lógica>")   # 1 ponto ANTES
# ... a operação lógica INTEIRA: união, limpeza, ajustes ...
F.marca_recuperacao("<a operação lógica> concluída")  # 1 ponto DEPOIS
```

As funções `preenche_entre_limites` e `limpa_degeneracoes_na_regiao` aceitam
`marcar_no_historico=True`, mas o padrão é **falso** justamente para você poder
agrupar. Use `True` só quando a chamada for a operação lógica inteira.

## Conferir a recuperação pelo conteúdo

Chamada que retornou não prova recuperação. Compare assinaturas:

```python
a_antes = F.assinatura("Peca")["sha256"]
F.marca_recuperacao("antes")
# ... opera ...
a_depois = F.assinatura("Peca")["sha256"]
F.marca_recuperacao("depois")

F.desfaz_e_confere("Peca", a_antes)    # recuperou: True
F.refaz_e_confere("Peca", a_depois)    # recuperou: True
```

Duas cautelas embutidas nas funções:

- elas consultam `contexto_de_historico()` antes e, se `ed.undo` não estiver
  chamável, **levantam `ErroDePrecondicao` em vez de tentar**. Assim você cai na
  recuperação por arquivo em vez de prometer o que não há;
- o objeto é relido **pelo nome** depois do undo. Referências a objeto e malha podem
  ficar inválidas; guardar o objeto numa variável e reusá-lo depois do undo é erro.

Medido no cenário sintético, variantes `correta` e `ranhura`: `undo` recupera a
assinatura anterior e `redo` a posterior, nos dois casos.

**Alcance:** isso vale para o caminho ensaiado — construção por dados, união
booleana com `EXACT`, limpeza local, tudo em background. Não vale como promessa para
todo operador e todo modo. Em sessão viva com o usuário editando, não fique testando
histórico repetidamente: é destrutivo.

## Quando não há histórico confiável

Salve antes. `Ctrl+Z` não recupera nada depois de fechar a aplicação.

```python
F.salva_cena("<destino acordado>.blend")
```

A função **recusa por padrão sobrescrever o arquivo de origem**. Salvar uma prévia por
cima da entrada é perda de trabalho, e é um caso onde o erro é irreversível. Se
sobrescrever for mesmo o combinado, passe `permitir_sobrescrever_a_origem=True`
explicitamente.

O retorno traz `sha256` do arquivo. Limite declarado no próprio retorno: **hash de
`.blend` prova integridade do arquivo e não separa mudança de geometria de mudança de
câmera, seleção ou iluminação.** Para geometria, use a assinatura.

## Exportar

```python
F.exporta_malha("Peca", "<destino>.stl")
```

MEDIDO no 5.2.1: o operador é `wm.stl_export` com `export_selected_objects=True`. O
nome antigo `export_mesh.stl` **não existe** nesta versão. A função tenta os dois e
registra qual funcionou, para a receita não depender de adivinhação.

O retorno traz `bytes`, `sha256` do arquivo e `assinatura_da_geometria`, que amarra o
artefato entregue à geometria medida. Limite declarado: **exportação bem-sucedida não
prova validade geométrica.** Confira o artefato entregue:

```bash
python verificadores/check_mesh.py --malha <destino>.stl
```

Medido num cubo exportado por este caminho: 12 triângulos, 0 arestas abertas, 0
não-manifold, estanque, 1 componente, `apto_para_booleana: true`.

## Deixar o trabalho retomável

Ver `registro_de_trabalho.md`. O mínimo, para outro agente continuar sem conversar
com você:

- o arquivo salvo e o hash dele;
- a assinatura da geometria, com a cobertura declarada;
- o que foi medido, com que método, com que tolerância e em que pontos;
- o que **não** foi decidido;
- o próximo passo.

## Encerrar a apresentação

Restaure as sobreposições que você alterou e informe em que modo deixou a cena, para
o usuário continuar selecionando. Não encerre a sessão do Blender do usuário para
cumprir prazo. Tempo esgotado do MCP **não prova** que o código parou lá dentro: em
estado incerto, inspecione antes de repetir.

Antes de executar codigo especifico ou entregar uma edicao, consulte o contrato de
`fluxo_interativo.md`: captura anterior real, limites de aceite, identidade da selecao,
recuperacao e verificacao do arquivo exportado.

STL: exporta_malha grava em temporario, valida estrutura binaria e numeros finitos,
e so entao publica. Destino existente e recusado por padrao; sobrescrever=True exige
autorizacao do usuario. Falha preserva o arquivo anterior. Modo e selecao sao restaurados.
Essa validacao nao decide fechamento, colisao ou imprimibilidade: confira o STL reaberto.
