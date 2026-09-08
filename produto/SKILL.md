---
name: modelagem-3d
description: Use quando o pedido envolver criar, inspecionar, editar ou verificar geometria 3D — criar peça paramétrica por código, abrir e inspecionar malha, orientar seleção no Blender, deslocar região delimitada, preencher vão entre limites, conferir malha e junção, desfazer, salvar ou exportar. TRIGGERS (PT) modelar, criar peça, geometria, malha, STL, 3MF, Blender, selecionar face, rampa, preencher vão, região protegida, não-manifold, exportar STL, desfazer no Blender, conferir malha. TRIGGERS (EN) model this part, mesh, select face, fill gap, ramp, non-manifold, export STL, undo in Blender.
---

# Modelagem 3D — receitas para executar e conferir

**Pacote 2.4.0**, com `scripts/bl_ferramentas.py` na **versão 1.5.0**. Os dois
números são independentes: o do pacote muda a cada correção em qualquer arquivo, o da
biblioteca só quando ela muda. Ambos estão em `INVENTARIO.json`, junto do hash de cada
arquivo, e é ali que se confere qual versão está em mãos.

**Onde conferir a versão, e onde não dá.** `bl_ferramentas.confere_versao("1.5.0")` só
roda **dentro do Blender**: o módulo importa `bpy` e `bmesh`, e no Python do hospedeiro
ele morre com `ModuleNotFoundError: No module named 'bmesh'`. Uma sessão limpa bateu
nisso no primeiro passo executável deste documento e teve que decidir sozinha que a
verificação não se aplicava. Então:

| Onde você está | Como conferir |
|---|---|
| dentro do Blender | `bl_ferramentas.confere_versao("1.5.0")`, que recusa em vez de deixar descobrir pelo resultado |
| no Python do hospedeiro (rota de **criar**, verificadores, validação) | leia `versao_de_bl_ferramentas` em `INVENTARIO.json`. A rota de criar não carrega `bl_ferramentas.py`, e um descasamento de versão dela não afeta essa rota |

Este pacote não é doutrina: são receitas com chamadas testadas. Use a referência da
rota, execute o que está escrito e **meça** o resultado. Nenhuma etapa aqui é
concluída por aparência.

## Três regras que valem em todas as rotas

1. **Meça, não presuma.** Ferramenta que devolve "concluído" não prova efeito. Foi
   medido neste ambiente: `transform.translate` com seleção vazia devolve
   `{'CANCELLED'}` sem erro e nada muda; a união booleana devolve sucesso e deixa
   faces de área nula; a exportação de 3MF aceita malha com defeito de forma.
2. **Validade geométrica não é atendimento ao pedido.** Malha fechada pode ter a
   forma errada. São verificações separadas, e as duas têm que aparecer no registro.
3. **Diga o alcance.** Amostragem prova os pontos amostrados. Uma seção prova aquele
   plano. Declare a cobertura junto com o resultado; conclusão sem alcance declarado
   não vale.

## Classificar o pedido antes de agir

Três perguntas, independentes entre si:

| Pergunta | Respostas | Consequência |
|---|---|---|
| **O que fazer** | criar, editar, reconstruir, parametrizar | escolhe a rota |
| **Em que** | sólido, superfície, malha, montagem | escolhe o contrato de geometria |
| **Para quê** | visualização, intercâmbio, montagem, impressão, usinagem | escolhe quais verificações são exigidas |

Não imponha reconstrução nem impressão a todo pedido. Ajuste visual não precisa do
mesmo rigor de peça para fabricação. Se a finalidade não foi dita e muda o que é
exigido, **pergunte**.

Se o pedido usar "borda", "casca" ou "fechado", trate topologia como declaração
separada da representação: superfície pode ser casca **aberta** (borda obrigatória)
ou casca **fechada** sem sólido (borda proibida). Não deduza uma da outra.

## Rotas e onde está cada receita

| Pedido | Referência a carregar |
|---|---|
| criar ou parametrizar peça por código, com verificação | `referencias/criar_e_parametrizar.md` |
| abrir, inspecionar, orientar seleção, ler o que está selecionado | `referencias/inspecionar_e_selecionar.md` |
| deslocar região delimitada; preencher vão entre dois limites | `referencias/editar_localizado.md` |
| conferir malha, junção, região preservada, dimensões | `referencias/verificar.md` |
| desfazer, refazer, salvar, exportar, deixar retomável | `referencias/recuperar_salvar_exportar.md` |
| que ferramenta existe, o que ela exige, o que **não** existe | `referencias/mapa_de_ferramentas.md` |
| como registrar o trabalho para outro agente continuar | `referencias/registro_de_trabalho.md` |
| **escrever o meu próprio script que roda dentro do Blender** | `referencias/mapa_de_ferramentas.md`, seção «O contrato do script que roda DENTRO do Blender» |

Carregue **uma** referência por vez, a da rota em uso. Elas repetem de propósito o
que é crítico, para não obrigar a carregar tudo.

## Antes de editar qualquer coisa de outra pessoa

- Pergunte onde salvar. **Não sobrescreva o arquivo de origem** para gravar uma
  prévia.
- Se houver uma sessão do Blender aberta com trabalho do usuário, não carregue outro
  arquivo nela e não a encerre. Cena com alterações não salvas perde trabalho.
- Trabalhe no objeto atual se for a preferência do usuário; não duplique a peça a
  cada operação sem que ele queira.
- Registre um ponto de recuperação antes de alterar, e confira a recuperação pelo
  **conteúdo**, não por a chamada ter retornado.

## Licença

**MIT**, com o texto completo em `LICENSE`, na raiz deste pacote. Pode usar, copiar, modificar, distribuir e vender, **mantendo o aviso de copyright e o texto da licença**. O pacote contém somente código do autor: nenhuma biblioteca de terceiros e nenhum binário são redistribuídos aqui.

## O que este pacote não faz

Não reconstrói CAD a partir de malha, não seleciona por imagem, não decide folga de
encaixe (não há valor calibrado: isso continua pendente), não mede parede mínima nem
silhueta, e não aprova peça para fabricação. Quando o pedido cair fora, diga qual é o
limite e o que seria necessário — não improvise o trecho difícil.

**E não verifica que um furo é passante.** Isto merece linha própria porque é o
requisito mais comum da rota de criar. Nenhum dos oito tipos de requisito decide
passagem: o tipo `furo` mede **duas seções**, o que é amostragem, e ele mesmo diz isso
no campo `o_que_isto_nao_diz` da própria saída — só que diz **depois** de medir, dentro
do JSON, num requisito que sai `APROVADA`. Ler `furo_A: APROVADA` e concluir "o furo
atravessa" é o erro que esta linha existe para evitar. Se a passagem importa, diga que
ela **não foi verificada** e ofereça o que dá para medir: `euler` e o número de
componentes conexos em `check_mesh.py` (malha fechada, orientação consistente, 1
componente e `euler = −2` implicam dois túneis atravessando o sólido), e o `volume`
comparado ao valor calculado assumindo passagem, que limita o material residual à
tolerância declarada. Isso é dedução a partir de medida, não veredito de verificador, e
tem que ser apresentado como tal.
