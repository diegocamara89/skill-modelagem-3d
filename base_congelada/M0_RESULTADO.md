# M0 — resultado da execução

Executado em 07/09/2026. Seis correções, cada uma com aceite observável próprio, e cada
aceite com **controle positivo**: sem ele, uma ferramenta que recusasse tudo satisfaria a
lista de recusas sozinha.

## Linha de base

Antes de tocar em qualquer arquivo: **cópia congelada** de 25 arquivos (16 scripts, dados
e geometrias sintéticas) em `base_congelada/arquivos/`, com `hashes.json` para conferir a
integridade da cópia. Hash identifica conteúdo e não recupera conteúdo — o ponto de
retorno é a cópia, não o hash.

Linha de base medida antes das correções: **10 de 10 casos**, **24 de 24 mutações**.

## Resultado depois das seis correções

| Suíte | Antes | Depois |
|---|---|---|
| Casos de generalidade | 10 de 10 | **11 de 11** |
| Mutações | 24 de 24 | **30 de 30** |
| Auditoria do empacotador | limpo | limpo, 0 achados de vazamento |

Comparação campo a campo contra a linha de base, nos 10 casos originais: **uma única
diferença**, e ela é a mudança pretendida — o caso 10 passou a ter a verificação
`topologia` com estado `APROVADA`, onde antes ela não existia. Todo o resto idêntico,
incluindo estado por verificação e string de resultado. Nenhuma das 24 mutações
pré-existentes mudou de estado.

## As seis correções

### M0.1 Identidade de caminho no empacotador
A proteção comparava **texto** com prefixo e caixa, e só rodava quando `--destino` estava
presente. Agora resolve identidade física (`realpath` + `normcase`, com `samefile` quando
os dois lados existem, e o **ancestral existente** para alvo ainda inexistente dentro de
uma junção), vale em todos os modos, e recusa com código estável: `E_CAMINHO_NO_DESTINO`,
`E_CAMINHO_SOBRE_ENTRADA`, `E_CAMINHO_NOME_DE_PACOTE`.

Aceite: 3 recusas — incluindo **junção real** criada com `mklink /J`, porque variação de
caixa não demonstra identidade física — e **2 aceitações**, mais hash de toda entrada
idêntico antes e depois dos cinco testes.

### M0.2 Falha de escrita do formato fechado
**O achado que derrubou a minha própria classificação.** Eu escrevi um classificador cuja
regra era "família `OSError` vem do sistema, qualquer outra exceção é recusa do formato,
portanto geométrica" — e declarei no comentário onde ela poderia errar. O aceite mediu e
ela errou: com o alvo ocupado, o escritor de 3MF **não** levanta `OSError`. Levanta
`lib3mf.Lib3MF.ELib3MFException` com `error_code` **5**, que a própria biblioteca chama de
`GENERICEXCEPTION`, com o texto "The specified file could not be created".

Ou seja: o código numérico da biblioteca **não separa** falha de E/S de recusa de formato,
e separar pela frase seria o defeito que M0.3 corrige. A correção não interpreta a
biblioteca: **mede o próprio caminho de saída**, antes de chamar o escritor e de novo
depois de uma falha. Impedimento de sistema nunca chega a virar evidência de geometria.

Aceite: **três** casos, não dois — falha operacional (`E_EXPORT_3MF`, etapa `exportacao`),
reprovação geométrica, e **controle positivo** (a mesma geometria válida com escrita
permitida exporta e aprova). Mais a prova de que a injeção atingiu a etapa certa: o alvo
`.3mf` é ocupado por um diretório, o que deixa a exportação de malha funcionando, e
`etapas_concluidas` mostra `exportacao_malha` concluída antes da falha.

**Medição colateral que corrige uma afirmação antiga:** na variante com tangência, o
escritor de 3MF **aprovou** (`portao_3: true`) e quem reprovou foi o portão de malha. A
alegação de que o 3MF é portão de graça não se sustenta nesta versão da biblioteca.

### M0.3 Oráculo de erro esperado com causa
O julgamento conferia **em qual verificador** o erro apareceu, e não a causa. Agora a
mutação declara `errar_em` com **código esperado** e **evidência plantada**, e causa
divergente no mesmo lugar dá `INVALIDO`, não crédito.

Também tornei o tempo limite testável (`SKILL3D_TEMPO_LIMITE_S`, padrão 900): um caminho
que só se exercita esperando 900 segundos não está verificado. Par discriminante medido:
tempo esgotado no verificador previsto → `INVALIDO` com `codigos_encontrados: []`; exceção
plantada de verdade → `PEGOU` com `E_CONSTRUCAO` e a marca confirmada.

E a colisão de nome no empacotador passou a exigir o motivo, não apenas código de saída
diferente de zero, que qualquer falha satisfaz.

### M0.4 Área de impressão
Três pontos colineares têm extensão positiva nos dois eixos e área **zero**, e passavam.
Agora há área por soma de produtos cruzados e teste de polígono simples.

**Achado do próprio aceite:** o primeiro polígono autointersectante que escrevi era
simétrico, e a soma de produtos cruzados **cancela** — ele era pego pelo teste de área, e
o teste de autointersecção nunca era exercitado. Troquei por um assimétrico, com área
8.000 mm² e cruzamento entre as arestas 0 e 2. Sem isso, o teste de autointersecção teria
recebido crédito sem nunca ter rodado.

O resultado passa a declarar **o que ele compara**: caixa envolvente contra caixa
envolvente, que para mesa não retangular não prova contenção.

### M0.5 Topologia separada da representação
A regra antiga fazia de `superficie` sinônimo de casca aberta. Agora a topologia é
**declarada** (`borda`, `orientacao`, `componentes`, `estanqueidade`), validada contra
contrato, e é ela que decide as dispensas que dependem de borda. Declaração inválida é
erro, nunca o valor mais parecido.

Novo verificador `topologia`, com medida por requisito e `NAO_IMPLEMENTADA` para requisito
declarado sem medidor. Nova medida em `check_mesh.py`: `n_componentes_conexos`. Caso 11
novo: **casca fechada sem sólido**, borda proibida, onde a estanqueidade é exigida pela
topologia declarada e não pela finalidade.

Um "extra" do runner carregava a mesma dedução falsa — presença de malha implicando casca
aberta — e foi corrigido para seguir a borda declarada.

Aceite: inverter a declaração reprova, em **três camadas** — no verificador de topologia
para a casca aberta, para a casca fechada, e no portão de malha do executor da varredura.

### M0.6 Papel da métrica
A matriz era binária: ou a verificação barrava, ou não era feita. Faltava o meio.
Três papéis agora: `DECISIVA`, `INFORMATIVA`, `NAO_APLICAVEL`, declaráveis por caso e
validados contra contrato. Declarar papel para verificação fora do roteamento é erro.

`NAO_IMPLEMENTADA` entrou no contrato de estados, e o **bloqueio é qualificado pelo
papel**: decisiva barra, informativa não, e nenhuma das duas preenche com valor favorável.

**Correção de uma promessa maior que a evidência.** A versão anterior deste aceite
prometia inverter o resultado do *caso* trocando o papel de uma métrica. É falso: a mesma
malha com duas arestas não-manifold também reprova em outras verificações de impressão.
O aceite agora tem três pares:

1. geometria com 2 arestas não-manifold: a medida é **2 nos dois papéis**, a métrica entra
   nos motivos só em decisiva, e o estado de **todas** as outras verificações é registrado
   e **idêntico** nas duas execuções (medido: zero divergências);
2. **controle de agregação** — dois cubos fechados disjuntos, limpos em tudo exceto na
   contagem de componentes: informativa **aprova e entrega**, decisiva **reprova**. Este é
   o par que prova o efeito na entrega;
3. medidor ausente por papel: decisiva barra como `NAO_IMPLEMENTADA`, informativa não
   barra, e nenhuma das duas inventa medida.

Para expressar o par 2 foi preciso generalizar o vocabulário de expectativa: existia
`aprovado` e um único caso especial de folga, sem forma de declarar "reprovado exatamente
nesta verificação". Agora existe `{"barrado_em": [...]}`.

## O que continua aberto

Sete capacidades declaradas como não implementadas (amostra de regressão de sigilo
numérico, requisitos não geométricos por contexto, geometria de junta, silhueta contra
imagem, declaração inconsistente com geometria, `parede_minima`, `folga_entre`), o teste
de instalação limpa, as oito decisões comerciais, e o limiar `A_CALIBRAR` de separação —
que agora tem ferramenta para ser medido e ainda não foi medido.
