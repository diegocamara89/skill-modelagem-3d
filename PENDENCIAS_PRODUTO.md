# Pendências do produto

Lista viva. Cada item diz o que está aberto, o que já foi **medido** sobre ele, e de
quem é a decisão. Item fechado sai daqui e vira linha de evidência na tabela da fase.

Regra que vale enquanto um ensaio de sessão limpa estiver rodando: **não editar
`produto/`**. Alterar o pacote no meio de uma execução foi o achado (a) da primeira
rodada e custou a ela uma execução inteira.

---


## Aberto, e é limite medido do produto

### D2 — não existe requisito que prove "furo passante"

Achado por sessão limpa (`evidencias_finais/SESSAO_LIMPA_D.md`, §4.8), e é o requisito
mais comum da rota de criar.

Nenhum dos oito tipos decide passagem. O tipo `furo` mede **duas seções**, o que é
amostragem, e o próprio verificador admite isso no campo `o_que_isto_nao_diz` — só que
depois de medir, dentro do JSON, num requisito que sai `APROVADA`.

**Já feito:** `produto/SKILL.md` passou a listar isso explicitamente na seção de
limites, com as duas medidas que dão evidência **indireta** (gênero por `euler` com
malha fechada e 1 componente; volume contra o valor calculado assumindo passagem) e com
a instrução de apresentá-las como dedução, não como veredito.

**Falta:** um tipo de requisito `furo_passante` que decida por medida volumétrica — a
coluna do furo comparada ao material remanescente dentro dela. Isso é implementação
nova no verificador, que hoje é **cópia congelada** e cujo comportamento foi
estabilizado com teste. Mexer nele exige refazer a suíte de M0 (11 casos, 30 mutações)
e não cabe numa correção de revisão.

### D3 — `A_CALIBRAR` continua sem número medido

A separação mínima segura entre diâmetro de furo e espessura de parede não tem valor
medido. `referencias/criar_e_parametrizar.md` diz isso com essas palavras e **não**
inventa um número.

O que existe medido: o defeito é a **igualdade** entre duas expressões (4/4 e 5/5
quebram igualmente, 6 arestas não-manifold nos dois); e meio milímetro de diferença, no
par análogo, foi **pior** que a igualdade exata (4 arestas defeituosas contra 2). E a
folga que **funciona** na família entregue: altura de corte `T * 3`, com 0 defeitos em
toda a grade ensaiada.

Fechar isto é uma varredura dedicada com a geometria real do trabalho, não uma escolha
de gabinete.

### D4 — falha ao criar o diretório de saída da varredura sobe como traceback

`verificadores/sweep_params.py` chama `os.makedirs(a.saida)` antes do laço de variantes
e **fora** do tratamento de exceção. Se o caminho de `--saida` não puder ser criado, o
resultado é um `PermissionError` ou `FileNotFoundError` cru, sem JSON, sem `codigo` e
sem `etapa` — ou seja, a separação entre falha de ambiente e reprovação geométrica, que
é o ponto de que essa página mais se orgulha, é contornada nesse caso.

Achado por sessão limpa (§4.4), que mediu as duas variantes da falha. O verificador é
cópia congelada e não foi editado; o que foi feito é o honesto no curto prazo:

- o controle documentado, que **não reproduzia**, foi substituído por um que reproduz
  (diretório ocupando o nome do 3MF de saída), com o resultado medido:
  `E_EXPORT_3MF` na etapa `exportacao`, `n_reprovadas_por_geometria: 0`,
  `etapas_concluidas: ["portao_1_solido", "exportacao_malha"]`;
- o limite ficou escrito na própria página.

Fechar de verdade é mover o `makedirs` para dentro do tratamento, com código próprio —
e refazer a suíte de M0 por causa disso.

### D5 — sete capacidades declaradas seguem sem medidor

`parede_minima`, `folga_entre` e `silhueta` estão declaradas e **não implementadas**, e
saem no relatório como não verificadas com o motivo — o que é o comportamento correto,
não um defeito. Ficam aqui para que a lista de capacidades não seja confundida com lista
de verificadores.

### D6 — a tolerância que decide a forma é a única sem procedência obrigatória

Achado pela sessão limpa E (§4.5). A assimetria é real e é contra a própria doutrina do
produto: `limpa_degeneracoes_na_regiao` **exige** `justificativa_da_tolerancia` como
parâmetro obrigatório — e essa é a tolerância **cosmética**, que só remove face de área
nula. Já `mede_topo_em_pontos`, que é **a única medida que pega ranhura e desnível**,
aceita `tolerancia=0.01` por padrão silencioso, e é assim que os exemplos das
referências a usam.

**Já feito:** `referencias/editar_localizado.md` passou a dizer que o número não tem
procedência, e a ensinar como derivá-lo (maior que o ruído de leitura de altura, medido
entre 1e-6 e 3e-6; menor que o menor desvio que se precisa pegar).

**Falta, e é decisão de projeto:** tornar a justificativa **obrigatória**, como na
limpeza. Isso muda a assinatura de uma função usada pelo ensaio e por duas referências,
e por isso não entrou junto com uma correção de revisão — uma mudança de assinatura no
fim de uma rodada é exatamente o tipo de alteração que invalida a evidência que acabou
de ser gerada.

---

### D7 — os `.pyc` da árvore de trabalho carregam o caminho absoluto do autor

Achado pela sexta revisão, antes de ela parar por limite de uso. Um `.pyc` guarda o
caminho absoluto do arquivo de origem, portanto carrega nome de usuário e estrutura de
pastas. Rodar qualquer script de dentro de `produto/` cria esses arquivos.

**Medido:** **zero** `.pyc` rastreados no git, **zero** no pacote montado. Ou seja: não
houve vazamento, nem na entrega nem no repositório.

**Já feito, porque "declarado" não é "conferido":** um `.gitignore` impede o commit
acidental; o empacotador passou a **contar** bytecode no destino e a reprovar se houver,
em vez de apenas listar `__pycache__` entre os negados; e os 11 arquivos que estavam na
árvore de trabalho foram removidos.

**E um erro meu, ao tratar isto, expôs um buraco que já existia.** Eu criei o
`.gitignore` com `printf ... > .gitignore` depois de concluir que não havia um — e a
conclusão veio de uma saída de terminal que **não provava isso**: a cadeia de comandos
tinha quebrado antes de chegar ao `cat`, e a mensagem "(sem .gitignore)" era o ramo de
erro, não uma medida. O `.gitignore` existente foi sobrescrito, e com ele caíram as
linhas que excluíam **de propósito** `padroes_de_vazamento.json` — o arquivo que nomeia
o projeto privado. Um `git add -A` seguinte commitou as três cópias dele.

Desfeito e conferido: o commit foi revertido, o `.gitignore` original restaurado, os
objetos soltos removidos com `git gc --prune=now`, e o repositório **não tem remoto**,
portanto nada saiu da máquina. `git log --all` não registra nenhuma adição desse
arquivo em nenhum commit, e `git ls-files` não o lista.

O buraco que apareceu: o `.gitignore` original cobria `prototipo/` e
`base_congelada/arquivos/`, e **não** `base_pos_m0/arquivos/`, porque essa pasta nasceu
depois dele. A cópia privada estava lá desde M1, desprotegida, e nunca foi commitada
por acaso. Agora está coberta.

**Fica aberto:** as receitas mandam `sys.dont_write_bytecode = True` antes do import, e
isso resolve para quem seguir a receita. Não há como impedir que um agente que não a
siga crie o arquivo dentro de uma pasta somente-leitura — o que é limite do Python, não
do pacote.

---

## Fechado

### D1 — licença do produto — **FECHADO em 08/09/2026**

**MIT**, decidido pelo autor. `produto/LICENSE` traz o texto completo, com a nota de que o pacote contém somente código dele, que os scripts que importam `bpy` executam **dentro** do Blender sem conter código dele, e o limite da verificação de licença das dependências (uma a uma nas oito da tabela; versão medida, sem verificação individual, nas outras 40).

Com isso o pacote **pode** ser distribuído. O critério C18 de M3 passou a `ATENDIDO`.

### P1 — `check_intent.py` exige `--malha`, e a documentação omitia — **FECHADO**

Três referências documentavam `check_intent.py --requisitos req.json`, e a CLI real
exige `--malha`. Corrigido nas três (`verificar.md`, `criar_e_parametrizar.md`,
`mapa_de_ferramentas.md`), que hoje trazem a forma com `--malha` e a marcam como
obrigatória.

### P2 — a tabela de tolerância por tipo estava errada em `furo` — **FECHADO**

O validador recusava `tol_mm` em `furo` dizendo que o verificador não a lê, e o
verificador lê e **decide** com ela. A tabela era transcrita à mão, com o comentário
"conferido no fonte tipo por tipo".

Fechado de forma a não voltar: `produto/scripts/extrai_tolerancias.py` extrai a tabela
do fonte do verificador, e `produto/scripts/testa_paridade_validador.py` reprova se a
tabela do validador divergir da extraída. Controle positivo medido: restaurando a
tabela errada, o teste acusa `furo` como divergente e o veredito vira `FALHOU`.
