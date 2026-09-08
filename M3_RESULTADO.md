# M3 — resultado

Executado em 08/09/2026. Pacote **2.2.0**, `bl_ferramentas` **1.5.0**.

**Hash do pacote final:** `723a6a32194a16b10bfcae1fe9e8c1b7d745371b8974205d81456ce1eb2e15e8`
— sha256 sobre nome e conteúdo de cada um dos **25** arquivos do pacote, em ordem
determinística, medido em pacote recém-montado e **nunca executado**. O ensaio da rota
Blender no venv isolado recomputou o hash do pacote que ele **executou** e chegou ao
mesmo valor (`evidencias_finais/AMBIENTE_ISOLADO.json`,
`hash_do_pacote_executado`).

**A evidência deste documento foi regerada sobre estes bytes.** A segunda revisão
independente apontou, com razão, que a evidência anterior tinha sido produzida em
1.2.0 e 1.3.0 e que o pacote mudara depois. `evidencias_finais/` contém os relatórios
das nove execuções sobre 1.5.0, com a versão estampada em cada um, mais o hash do
pacote e os dois relatórios de revisão.

## O que é a entrega

Um diretório de 22 arquivos, montado por **lista de permissão explícita**, com
`INVENTARIO.json` trazendo o hash de cada um. Instalação é copiar o diretório; não há
instalador, não há download no carregamento, e o pacote não pressupõe nada do ambiente
do autor além das dependências declaradas.

| Parte | Conteúdo |
|---|---|
| entrada | `SKILL.md`, com as três regras, a classificação e o roteamento |
| referências | 7 arquivos condicionais, uma por rota |
| auxiliares | 4 scripts, cada um com a lacuna medida que o justifica |
| verificadores | 5 cópias **byte a byte** da base pós-M0, com `PROVENIENCIA.json` |
| cenários | gerador sintético, ensaio com 8 variantes, e duas famílias paramétricas |

## Aceite de M3

| ID | Critério | Método | Evidência | Observado | Estado |
|---|---|---|---|---|---|
| C1 | instalar o pacote em ambiente isolado e seguir apenas as instruções documentadas | `venv` criado do zero, com **só** as dependências declaradas, e **controle negativo de isolamento** antes de instalar | `evidencias_finais/AMBIENTE_ISOLADO.json` | pacote **2.1.0** montado em destino recém-criado; venv novo em `…\ensaio_isolado_21\venv`; `import numpy` no venv vazio devolve **código 1**, o que prova que ele não vê os pacotes do hospedeiro; instalação das **7** declaradas, que trazem **48** pacotes no total, com `cadquery-ocp-novtk 7.9.3.1.1` entrando como transitiva do `build123d`, como documentado — a lista completa, antes e depois, está no mesmo arquivo. O JSON traz, por passo, o comando exato, o diretório, o código de saída e a saída | **ATENDIDO** |
| C2 | executar cenário sintético em sessão sem histórico, com as dependências externas declaradas | subagente sem histórico, **modelo `claude-opus-5`**, **cinco** rodadas, as duas últimas sobre o pacote **montado**, e cobrindo as duas rotas do produto | **`evidencias_finais/SESSAO_LIMPA_D.md`** (rodada D, preservada no repositório); rodadas A a C nos relatórios de fase | rodada D, sobre 1.6.0: **7 de 7 requisitos APROVADA** com os números medidos, varredura 1/1 aprovada, malha estanque, e controle negativo reprovando 6 de 7 propositais. **9 achados, 1 grave.** Rodada **E** (`SESSAO_LIMPA_E.md`), sobre 1.8.0 e pela rota de **edição**, que a D não havia percorrido: preencheu o vão de uma peça própria com sobreposição **derivada**, provou a ligação dos dois limites com desvio **0,0**, a preservação com **0,0 mm³** contra **16.200 mm³** na caixa de controle, e os dois controles negativos saindo com código 1; **não escreveu nada** na pasta da habilidade. Mais **9 lacunas**. A terceira revisão apontou que o relatório da sessão C existia só no transcrito de uma conversa e não era auditável; os dois últimos estão no repositório, com hash em `HASHES.json`, e **não foram editados por mim**. Rodada **F** (`SESSAO_LIMPA_F.md`), sobre **2.0.0**, fechou a lacuna que E havia aberto: com a tarefa de **escrever o próprio script** de dentro do Blender, passou **na primeira tentativa**, provou o retorno nos dois sentidos e não escreveu nada na pasta. Mais **7** lacunas | **ATENDIDO** |
| C3 | não aceitar venv nem caminho pessoal herdado como teste limpo | comparação registrada entre o interpretador do hospedeiro e o do venv, com `sys.executable`, `sys.prefix`, `sys.base_prefix` e `sys.path` de cada um | `evidencias_finais/AMBIENTE_ISOLADO.json`, campos `hospedeiro`, `venv` e `passos[venv_identidade]` | hospedeiro em `…\Programs\Python\Python312`; venv em `…\ensaio_isolado_21\venv`, com `base_prefix` apontando para o hospedeiro e `prefix` para si mesmo. Todas as rotas rodaram com `cwd` = raiz do pacote, e o JSON registra o diretório de cada passo. A versão anterior desta linha dizia apenas *«as rotas rodaram»*, o que não é registro: não permitia reconstituir qual interpretador rodou nem onde | **ATENDIDO** |
| C4 | sem Blender, uma rota independente funciona e a dependente informa a ausência | `BLENDER_EXE` para caminho inexistente, com os dois lados medidos no venv isolado | `evidencias_finais/SEM_BLENDER.json` | dependente: código **1** nas duas chamadas, mensagem **nomeando `BLENDER_EXE`**, e o arquivo de resultado **não foi escrito** — o que é a prova de que ninguém leu resultado velho. Independentes: **6 de 6** com código 0 (`check_mesh` sobre o STL entregue, `matriz`, `valida_requisitos`, o teste de paridade, e a importação de `check_intent` e `sweep_params`). A versão anterior desta linha dizia apenas *«execução registrada»* | **ATENDIDO** |
| C5 | com as dependências presentes, a rota do Blender funciona | ensaio inteiro disparado **do pacote montado**, com o Python do venv isolado como lançador | `evidencias_finais/AMBIENTE_ISOLADO.json`, campo `rota_blender` | **VEREDITO ATENDIDO, 21 critérios, 0 falhos, 0 passos com estado inesperado**, em cenário inédito 52 × 28 × 7; o relatório registra `versao_ferramentas 1.5.0` e `Blender 5.2.1 LTS`, e o hash do pacote executado é o mesmo do entregue. A quarta revisão apontou que a evidência anterior citava `versao_ferramentas 1.4.0`, e 1.5.0 mudou justamente booleana, salvamento e oráculos. Precisão: o interpretador de dentro do Blender é o interno dele, não o do venv — o que isto prova é a rota sobre os **bytes** do pacote | **ATENDIDO** |
| C6 | carregar a skill não instala nem baixa componentes | leitura | `produto/SKILL.md` e as referências | nenhum comando de instalação em nenhum arquivo do pacote; as dependências são declaradas em `mapa_de_ferramentas.md` como pré-requisito | **ATENDIDO** |
| C7 | inventário do pacote extraído coincide com o permitido, e o **manifesto resolve** | auditoria do destino, que **consome o manifesto** | `evidencias_finais/empacotamento.json` e `AMBIENTE_ISOLADO.json`, campo `conferencia_do_manifesto` | **24** arquivos, nada sobrando, nada faltando; o manifesto resolve na **raiz do pacote extraído**: **23** declarados, 0 não resolvem, 0 divergem, e nada no pacote fora do manifesto. Conferido duas vezes: pelo próprio empacotador e, de fora, sobre a pasta montada | **ATENDIDO** |
| C8 | referências da skill e manifesto resolvem para recursos existentes | varredura de todos os caminhos citados | auditoria descrita em `M1_RESULTADO.md` | **nenhum** caminho citado nas referências deixa de existir no pacote | **ATENDIDO** |
| C9 | pacote sem contaminação conhecida passa | auditoria da árvore real | `evidencias_finais/empacotamento.json` | **24** permitidos, 5 padrões, **0 achados**, e o controle positivo da varredura **casando** (1 padrão) | **ATENDIDO** |
| C10 | amostra privada plantada em área de ensaio é **detectada** | contaminação plantada numa **cópia** | `evidencias_finais/empacotamento.json`, campo `controle_da_varredura` | o controle positivo plantado fora do pacote **casa** (`varredura_funciona: true`, 1 padrão), o que prova que a varredura encontra quando há; sobre a árvore do produto, 0 achados. Numa rodada anterior, com contaminação plantada em cópia, foram 2 achados nomeando padrão e trecho, e a montagem foi recusada | **ATENDIDO** |
| C11 | amostras de regressão ficam fora do pacote | lista de negados e inventário | `empacota_produto.py`, `produto/INVENTARIO.json` | `padroes_de_vazamento.json`, `base_congelada/`, `base_pos_m0/`, `evidencias_m1/`, `cenas_de_teste/`, `prototipo/` e todos os relatórios de fase estão **fora**; nada disso aparece no inventário | **ATENDIDO** |
| C12 | nenhum caminho, geometria, nome, medida ou captura de projeto real integra exemplos ou receitas | varredura automática **mais** revisão manual dos recursos novos | auditoria e leitura | toda dimensão dos cenários foi escolhida para o exemplo; os quatro cenários das sessões limpas (50 × 30 × 8, 44 × 26 × 21, 72 × 34 × 25, 40 × 22 × 4) são sintéticos e nenhum vem de projeto real | **ATENDIDO** |
| C13 | licenças e versões dos componentes efetivamente incluídos são identificadas | `pip list` **antes e depois** num venv criado do zero, e a diferença | `DEPENDENCIAS_E_LICENCAS.md`, `evidencias_finais/AMBIENTE_ISOLADO.json` campo `dependencias` | oito dependências **diretas** com versão medida e licença, e o documento passou a dizer o que omitia: instalar as oito traz **48 pacotes**, sendo **40 transitivos** (a maioria de `build123d`), todos com versão medida e **sem** verificação individual de licença — limite declarado, não glosado. **Nenhuma redistribuída**: o pacote contém somente código do autor. O achado é do próprio instrumento, depois de corrigido: a primeira versão gravava o `pip list` truncado, o JSON não carregava, e a conferência respondia *«0 instalados»* sobre lista nenhuma | **ATENDIDO** |
| C14 | não redistribuir código externo por ter sido usado via ferramenta | inventário | `produto/INVENTARIO.json` | o pacote contém **somente** código do autor. Nenhuma biblioteca de terceiros, nenhum binário | **ATENDIDO** |
| C15 | dados do trabalho fora da instalação | modelo de registro | `produto/referencias/registro_de_trabalho.md` | uma pasta por trabalho, **fora** da instalação, com entrada, saída, medidas e pendências | **ATENDIDO** |
| C16 | hash do pacote final | cálculo determinístico sobre pacote **recém-montado e nunca executado** | `evidencias_finais/hash_do_pacote.txt` | `723a6a32194a16b10bfcae1fe9e8c1b7d745371b8974205d81456ce1eb2e15e8`, sobre **25** arquivos, no pacote **2.2.0**. Sobre 2.1.0 ele era **igual** ao hash do pacote executado pelo ensaio da rota Blender; 2.2.0 difere de 2.1.0 apenas por `LICENSE`, `SKILL.md` e `INVENTARIO.json` ao hash do pacote que o ensaio da rota Blender executou. Uma medição anterior deu 31 arquivos: rodar um script de dentro do pacote cria `__pycache__`, e o hash passava a incluir arquivos que não fazem parte da entrega | **ATENDIDO** |
| C17 | revisão independente sobre este mesmo pacote | `codex exec`, somente leitura, cinco passadas | `evidencias_finais/revisao_1_codex.txt` a `revisao_5_codex.txt` | **cinco** revisões, **todas `BLOQUEIA`**: 10, 10, 12, 6 e 5 achados. **Todos os 43 corrigidos**, com o que foi medido em cada correção, e cada rodada regenerou a evidência — o que invalida a passada anterior e é a razão de haver uma seguinte. A quarta apontou defeito **na correção da terceira**. **Não houve passada sobre 2.2.0**, que é o estado atual: foram **seis** tentativas, cinco concluídas — todas `BLOQUEIA`, com 10, 10, 12, 6 e 5 achados — e a sexta **não concluiu**, porque a conta do Codex bateu no limite de uso (`evidencias_finais/revisao_6_codex_interrompida.txt` guarda o que ela alcançou antes de parar, inclusive um achado válido sobre os `.pyc` da árvore de trabalho, já tratado). Usar o Codex não é critério bloqueante deste projeto, e por isso a tentativa fica registrada em vez de omitida | **PENDENTE** |
| C19 | o validador de requisitos **espelha** o verificador congelado | comparação das duas respostas na mesma entrada, com o verificador importado | `produto/scripts/testa_paridade_validador.py`, `evidencias_finais/paridade_do_validador.json` | **339 casos**: 324 `ESPELHO_OK`, 15 `EXTRA_DECLARADO`, **0 falhas**. Com divergência plantada, o teste acusa dos dois lados: 1 `FALHA_PERMISSIVO` ao aceitar eixo `W`, 16 `FALHA_ESTRITO` ao recusar número escrito como texto — e volta a 0 ao despatchar. O validador anterior **anunciava** espelhar e aceitava `NaN`, tolerância negativa, caixa invertida, eixo fora do vocabulário e `entre` com um caminho | **ATENDIDO** |
| C20 | destino de pacote reprovado não continua existindo | manifesto adulterado de propósito numa cópia da origem | `evidencias_finais/AMBIENTE_ISOLADO.json`, campo `controle_do_empacotador` | com um hash trocado por zeros, o empacotador devolve **código 1** e a pasta de destino **não existe** depois. Antes ela ficava no disco, e um ensaio desta própria rodada chegou a rodar dentro de um pacote reprovado sem notar | **ATENDIDO** |
| C21 | relatório com veredito negativo reprova no invocador | `--exigir CAMPO=VALOR` em `roda_blender.py` | `evidencias_finais/ensaio_nome_invalido.json` | relatório que traz `veredito_global: ESPEC_INVALIDA` sai como `VEREDITO_NEGATIVO`, com código de saída não zero; **sem** a bandeira, o mesmo relatório saía como `OK` e código **zero** — legível estava sendo tratado como aprovado | **ATENDIDO** |
| C22 | a tabela de tolerância por tipo é **extraída**, não transcrita | `scripts/extrai_tolerancias.py` lê o fonte do verificador; o teste de paridade compara | `evidencias_finais/tolerancia_extraida.json`, `paridade_do_validador.json` | a tabela transcrita estava **errada** em `furo`, que lê `tol_mm` como tolerância de diâmetro e **decide** com ela: o validador recusava um número decisivo e a referência garantia o contrário. Extração e tabela agora coincidem nos 8 tipos; restaurando a tabela errada, o teste acusa `furo` e o veredito vira `FALHOU`. O erro sobreviveu a uma rodada inteira de revisão porque estava protegido pela lista de *extras*, ou seja, por uma afirmação minha | **ATENDIDO** |
| C23 | o padrão de tolerância que decide quando ninguém declara está escrito | extração do valor padrão de cada leitura | `referencias/verificar.md`, `valida_requisitos.py --tipos` | os oito tipos com o valor que decide na omissão (`caixa` 0,05; `furo` 0,2 / 0,2 / 0,90; `distancia_entre_furos` 0,2; `regiao_intacta` 1e−9; `interferencia` 0,0; `volume` max(1,0; 1%)). Uma sessão limpa teve dois requisitos aprovados por uma tolerância de 0,2 que ela não escolheu e que não estava escrita em lugar nenhum | **ATENDIDO** |
| C24 | o controle de erro operacional documentado **reproduz** | execução do controle exatamente como documentado | `PENDENCIAS_PRODUTO.md` D4, `referencias/criar_e_parametrizar.md` | o controle anterior (`--saida` sem permissão) dava traceback cru de `os.makedirs`, sem JSON e sem código, porque a criação do diretório está fora do tratamento. O novo controle (diretório ocupando o nome do 3MF) foi medido: código 1, `E_EXPORT_3MF` na etapa `exportacao`, **`n_reprovadas_por_geometria: 0`**, 3 aprovadas, e `etapas_concluidas: [portao_1_solido, exportacao_malha]`, que prova que a injeção atingiu a etapa pretendida | **ATENDIDO** |
| C25 | número documentado como medição corresponde ao código entregue | reexecução da tabela de coincidência paramétrica sobre a família do pacote | `referencias/criar_e_parametrizar.md` | a tabela 4/4 → 6 arestas não-manifold **não reproduz** com o `familia_placa` entregue, que atravessa com `T * 3`: medido `T=4,5;d=4,5` → **4 variantes, 4 aprovadas, 0 não-manifold**. A página passou a dizer em que código a tabela vale e que ela é o registro do defeito que a folga resolve, não um aviso sobre o código atual | **ATENDIDO** |
| C26 | a passagem de furo é declarada como **não verificável** antes de alguém confiar num APROVADA | leitura dos oito tipos e da seção de limites | `produto/SKILL.md`, `PENDENCIAS_PRODUTO.md` D2 | nenhum tipo decide passagem; o verificador admitia isso **dentro** do JSON de um requisito `APROVADA`, depois de medir. A seção de limites do `SKILL.md` passou a listar isso com as duas medidas de evidência **indireta** e a instrução de apresentá-las como dedução | **ATENDIDO** |
| C27 | barrar **não** é resposta certa onde a operação tinha que executar | controle mutante que injeta `ErroDePrecondicao` no preenchimento da variante `correta` | `evidencias_finais/controle_injeta_precondicao.json` | o ensaio termina **FALHOU**, com o critério `preenchimento_NAO_devia_barrar_nesta_variante`, e o invocador devolve `VEREDITO_NEGATIVO`. Antes, `feito is None` caía no ramo de *«barrou corretamente»* para **qualquer** variante: uma booleana que devolvesse `CANCELLED` na `correta` viraria pré-condição e o ensaio poderia sair `ATENDIDO`. O defeito estava na correção da revisão anterior | **ATENDIDO** |
| C28 | a `ranhura` prova executavelmente que **só** o perfil reprova | critério sobre a topologia medida **antes** da limpeza | `evidencias_finais/ensaio_ranhura.json`, critério `ranhura_nasce_com_topologia_limpa` | zero borda aberta, zero não-manifold e zero degenerada **antes** de limpar. A medição existia e nenhum predicado a usava: uma ranhura que também sujasse a topologia seria limpa e receberia o mesmo crédito. A evidência media zero por acaso; o oráculo não exigia | **ATENDIDO** |
| C29 | os controles de seleção conferem o **motivo**, não só o estado | critério sobre o texto da mensagem e sobre a assinatura | `evidencias_finais/ensaio_correta.json`, critérios `caixa_vazia_barra_PELO_MOTIVO_certo`, `selecao_vazia_barra_PELO_MOTIVO_certo` e `os_dois_controles_nao_alteraram_a_peca` | as mensagens contêm *«nao contem nenhuma face»* e *«nenhum vertice selecionado»*, e a assinatura é idêntica à de antes dos dois controles. A própria referência já contava o episódio em que um controle passou barrando por Object Mode, **sem** exercitar a guarda — e o critério aceitava isso de novo | **ATENDIDO** |
| C30 | o **valor** padrão de tolerância também tem oráculo | comparação dos padrões extraídos do fonte com a tabela declarada, mais controle mutante | `evidencias_finais/paridade_do_validador.json`, campo `padroes_divergentes` | os oito tipos coincidem em nome **e** valor. O critério achou uma divergência real na primeira execução: o padrão de `volume` estava escrito como prosa (*«1% do volume esperado»*) e o fonte diz `max(1.0, 0.01 * esp)` — prosa não é comparável com nada. Controle mutante: trocando o padrão de `furo` de 0,2 para 0,5, o teste acusa e o veredito vira `FALHOU` | **ATENDIDO** |
| C31 | o caminho de importação das receitas resolve no **pacote extraído** | leitura das duas rotas de edição e inspeção | `referencias/editar_localizado.md`, `referencias/inspecionar_e_selecionar.md` | as duas mandavam `sys.path.insert(0, "<caminho>/produto/scripts")`, e o prefixo `produto/` **não resolve** no pacote extraído — o próprio `INVENTARIO.json` diz isso no campo `nota`, porque o manifesto foi corrigido e estes dois trechos ficaram para trás. Era o **primeiro comando executável** das duas rotas. Agora é `<raiz do pacote>\\scripts`, com `sys.dont_write_bytecode = True` antes do import | **ATENDIDO** |
| C32 | o contrato do script que roda **dentro** do Blender está escrito | leitura das referências | `referencias/mapa_de_ferramentas.md` | nenhuma referência ensinava as quatro obrigações do script de dentro — ler `sys.argv` depois de `--`, receber o resultado como último argumento, **gravar** o relatório, e capturar exceção **gravando-a**. Uma sessão limpa extraiu o contrato lendo o código dos cenários. É o contrato central da rota headless, e agora está na página, com o exemplo completo | **ATENDIDO** |
| C33 | os campos que são oráculo dizem qual é o valor esperado | leitura da seção de seção por plano | `referencias/editar_localizado.md` | a página mandava conferir `pontos_unidos_por_coincidencia` sem dizer qual valor é bom, e **não citava** `faces_com_mais_de_dois_cruzamentos`, que é o campo que invalidou uma seção de sessão limpa. Agora há tabela: união saudável é **igual a `n_pontos`** (cada ponto é alcançado por duas faces vizinhas) e cruzamentos ambíguos têm que ser **0**, com o que cada desvio significa | **ATENDIDO** |
| C34 | parâmetro de amostragem não é apresentado como medida da peça | reexecução em peça de outras dimensões | `referencias/editar_localizado.md`, `evidencias_finais/SESSAO_LIMPA_E.md` §4.9 | a página dizia *«99 pontos. Medido»*. Uma sessão limpa com vão de 40 (contra 20) e sobreposição 2,0 (contra 1,0) obteve **exatamente** 99 pontos: o número é consequência aritmética da receita de amostragem e **invariante às dimensões**. A página passou a dizer isso, e a separar o que é medida — o desvio 0,0 — do que é parâmetro. É a mesma classe do 87 que sobreviveu a uma revisão | **ATENDIDO** |
| C35 | o caminho do resultado é entregue por bandeira **nomeada**, não por posição | controle com **dois** argumentos do chamador | `evidencias_finais/CONTRATO_DO_RESULTADO.json` | com `args=[param, segundo]`, o script grava no destino pedido e o **segundo argumento fica intacto** (mesmo sha256 antes e depois). Antes, `--passa-resultado` acrescentava o caminho por posição e os cenários liam `argv[1]`: com dois argumentos, o script gravava **sobre o segundo argumento do chamador** e o chamador esperava outro arquivo. Toda a evidência usava exatamente um argumento, portanto **não discriminava o erro** | **ATENDIDO** |
| C36 | o gerador cumpre o contrato que a referência diz que ele exemplifica | injeção de falha real de escrita | `evidencias_finais/CONTRATO_DO_RESULTADO.json` | com `saida_blend` apontando para caminho ocupado por diretório, `gera_cenario.py` grava `veredito_global: "ERRO"` com tipo, mensagem e traceback, e o invocador devolve `VEREDITO_NEGATIVO`. Antes ele era **apresentado** como exemplo completo do contrato e não capturava exceção nem emitia veredito — um erro nele não deixava vestígio nenhum. Registro do caminho: a primeira tentativa deste controle usou parâmetros geométricos impossíveis e **o gerador concluiu**; defeito não exercitado não vale como controle, e por isso a injeção passou a ser de escrita | **ATENDIDO** |
| C37 | evidência de critério aponta para os bytes atuais, ou diz por que não | varredura de todas as referências de evidência em M1 | `M1_RESULTADO.md`, `evidencias_finais/IDENTIDADE_DAS_FUNCOES_DE_A1.json` | as referências a `evidencias_m1/` caíram de **15 para 2**. A única linha de aceite que continua lá é **A1**, que exige instância **gráfica** do Blender e não pode ser regerada em segundo plano; o que sustenta a linha é a identidade medida do código: `estado_das_sobreposicoes` e `diagnostico` são byte a byte idênticas nos **9** commits que tocaram `bl_ferramentas.py`. O arquivo declara o que o argumento **não** cobre | **ATENDIDO** |
| C38 | a ajuda de linha de comando ensina o contrato **vigente** | leitura do `--help` contra o código | `produto/scripts/roda_blender.py` | o texto de `--passa-resultado` continuava ensinando o contrato **posicional**, que o comentário logo acima declarava removido — e era o contrato que quebra com dois argumentos. Quem fizesse o movimento mais natural, rodar `--help` primeiro, escreveria um script que sobrescreve o próprio segundo argumento. A ajuda agora nomeia a bandeira real e diz por que ela é nomeada | **ATENDIDO** |
| C39 | a afirmação sobre o código de saída do lançador corresponde ao medido | 8 modos de execução, remedidos do zero | `evidencias_finais/CODIGO_DE_SAIDA_DO_LANCADOR.json` | a página e o auxiliar diziam que o código «é 0 mesmo quando o Blender falha». **Errado como escrito**, e uma sessão limpa contestou com três medidas próprias. Remedido em oito modos: `sys.exit(N)` **propaga** (0, 1, 2); exceção não tratada, erro de sintaxe, import inexistente e erro de API do Blender devolvem **todos 0**; e stdout vem **vazio nos oito**. Ou seja: código não zero é sinal confiável de falha, código zero não é sinal de nada, e o contrato de arquivo continua necessário — por um motivo mais estreito do que o documentado. Texto corrigido nos três lugares | **ATENDIDO** |
| C40 | o caminho de falha mais comum não é o mais lento | medição do tempo de espera | `produto/scripts/roda_blender.py`, campo `segundos_de_espera_pelo_arquivo` | `SEM_RESULTADO` — script que não gravou — consumia o tempo-limite **inteiro** com o processo já morto: **300 s** medidos por uma sessão limpa num erro decidido no primeiro segundo. Agora a espera desiste 5 s depois de o processo sair. Medido depois da correção: **7 s** | **ATENDIDO** |
| C41 | capacidade existente é encontrável pelo índice | leitura da tabela de rotas e do mapa | `produto/SKILL.md`, `produto/referencias/mapa_de_ferramentas.md` | três coisas existiam e não eram achadas: o contrato do script de dentro (documentado, mas sem linha na tabela de rotas — a sessão F reconstruiu o contrato lendo o fonte **antes** de descobrir a página), o modo de importar `bl_ferramentas` de um script que vive **fora** do pacote, e a caixa envolvente em **mundo**, que `diagnostico` já devolve e que a sessão reescreveu por não encontrar. Nenhuma exigiu código novo; todas exigiam sinalização | **ATENDIDO** |
| C42 | limiares diferentes para a mesma medida são declarados | comparação dos dois medidores de face degenerada | `produto/referencias/verificar.md` | `bl_ferramentas.mede_malha` usa `1e-9` e devolve o valor usado; `check_mesh.py` usa `1e-12`, fixo e não reportado. São **três ordens de magnitude**, e a referência listava as duas como a mesma medida — de modo que a concordância entre elas parecia confirmação mútua. Agora está escrito, com o alcance: em peça normal as duas medem 0 e a diferença não decide nada | **ATENDIDO** |
| C18 | licença do produto decidida | decisão do autor, registrada em 08/09/2026 | `produto/LICENSE`, `produto/SKILL.md` seção «Licença» | **MIT**, com o texto completo em `LICENSE` na raiz do pacote, no manifesto e na lista de permissão do empacotador. Permite usar, copiar, modificar, distribuir e vender **mantendo o aviso de copyright e o texto da licença**. O `LICENSE` também registra que o pacote contém somente código do autor, que os scripts que importam `bpy` executam **dentro** do Blender sem conter código dele, e o limite da verificação de licença das dependências | **ATENDIDO** |

## Segunda revisão independente, e os dez achados dela

Executada sobre `REVISAO_FINAL_CONTEXTO.md`, somente leitura. Veredito: **BLOQUEIA**,
com dez achados. Conferi cada um por inspeção direta: **todos procedentes**. Relatório
integral em `evidencias_finais/revisao_2_codex.txt`.

| # | Achado | Como foi corrigido, e o que foi medido |
|---|---|---|
| 1 | **o pacote final não era o exercitado pela evidência**: os ensaios de M3 registravam `bl_ferramentas 1.2.0` e o produto já estava adiante | `evidencias_finais/` foi **regerada** sobre os bytes de 1.5.0, com `bl_ferramentas 1.4.0` estampado em cada relatório e o hash do pacote no `HASHES.json` |
| 2 | **o ensaio gravava `OK` por ausência de exceção**, e `esperado` era só texto: um passo que mediu `todos_dentro_da_tolerancia: false` saía como OK, e o resumo dizia "só os controles barrando" sobre resultado errado | o ensaio passou a **julgar**, com predicado executável por critério, veredito global e a regra de que exceção no predicado é `INDETERMINADO`, nunca aprovação. **18 critérios** no caminho completo, 9 nas variantes barradas, 5 na girada. E ele pegou um defeito na primeira execução: ver abaixo |
| 3 | a correção da amostragem simétrica deixou **87** no texto, e o código passou a produzir **99** | corrigido em três lugares, e o ensaio agora **exige** como critério que as costuras em `limite ∓ ov` estejam entre os pontos |
| 4 | a **justificativa falsa** de sobreposição sobrevivia no cenário distribuído e no modelo de registro — e é campo de **procedência**, que fica gravado na evidência | trocada nos dois pelo critério de **altura**; nenhuma ocorrência restou |
| 5 | `tolerancia_de_uniao` **não unia por proximidade**: arredondar casas não é distância, e `0,999994` com `1,000001` distam 7e-6, cabem em 1e-5 e caíam em chaves diferentes | união por **distância real**, com grade espacial e consulta das 27 células vizinhas, extraída para função testável. Quatro controles: dentro da mesma célula une; **atravessando a fronteira** une; 2e-5 não une; 4e-5 atravessando não une |
| 6 | contagem **fracionária** passava: `valor: 1.9` virava `1` por `int()` e aprovava | o validador exige inteiro não negativo em tipo de contagem. Controles: fracionário barra, negativo barra, inteiro passa, float inteiro passa |
| 7 | as **booleanas centrais** ainda inferiam sucesso por ausência de exceção — o mesmo padrão já corrigido na exportação | as duas exigem `FINISHED` **e** que o modificador tenha saído do objeto; sem isso, `CANCELLED` faria a aritmética declarar como interseção todo o volume da ferramenta |
| 8 | `PYTHONPATH=... comando` é **POSIX** e o ambiente medido é Windows: o operador teria de improvisar o caminho de importação | documentada a forma **PowerShell** ao lado da POSIX, nos dois lugares |
| 9 | os caminhos do manifesto **não resolviam** no pacote extraído: o inventário gravava `produto/...` e a conferência passava por remover o prefixo, validando uma lista paralela | caminhos relativos à **raiz do pacote**, e o empacotador passou a **consumir o manifesto** em vez de conferir a lista paralela. Medido no pacote montado: 21 declarados, **0 não resolvem, 0 divergem** |
| 10 | A4 aprovava **metade** do critério: media a dimensão externa e não comparava nenhuma região não selecionada | o ensaio passou a medir o topo do patamar **baixo**, fora da seleção, antes e depois do deslocamento, e a exigir que a altura restaure |

**O critério novo pegou um defeito meu na primeira execução**, e vale registrar porque é
a prova de que ele serve: minha primeira correção do achado 10 reselecionava pela caixa
da altura **original**; depois de subir 2, aquela caixa não encontra face alguma, a
seleção fica vazia, o deslocamento de volta é barrado e a peça segue **2 unidades mais
alta** pelo resto do ensaio. Os critérios de perfil e de superfície protegida
reprovaram na hora. Sem eles, o ensaio teria reportado "todos os passos OK".

E um achado colateral que derrubou outra afirmação minha: a variante `duplicado`
**produz** face não convexa cortada em mais de dois pontos — 2 delas, com 12 pontos e
apenas 10 segmentos. Eu havia escrito que essa contagem era 0 em todos os cenários.
Corrigido em `LACUNAS_PARA_M2.md` e `M2_RESULTADO.md`, e o critério da variante passou a
**exigir o aviso** em vez de exigir zero.

## Os pontos que ficam pendentes, e por quê

`bl_ferramentas.py` e os arquivos de `cenarios/` **importam `bpy`** e rodam dentro do
processo do Blender, que é GPL. A Blender Foundation sustenta publicamente que script
que usa a API Python deles é obra derivada e, ao ser **distribuído**, precisa ser
compatível com GPL.

**Não estou concluindo a licença deste produto.** Registro o fato, as três saídas
possíveis e a recomendação de assessoria, em `DEPENDENCIAS_E_LICENCAS.md`. Neste
projeto eu já afirmei uma premissa de licença errada uma vez, sobre outro material, e
a revisão externa me corrigiu; não repito o padrão.

Consequência prática: **o pacote fica local**. Publicação é ação separada e não está
autorizada por nenhuma etapa deste plano.

**E o segundo pendente, C17.** Quatro revisões independentes, **todas com
`BLOQUEIA`**: 10, 10, 12 e 6 achados, os 38 corrigidos e medidos. Em paralelo, cinco
sessões limpas acharam mais 18 defeitos.

**A estrutura disto merece ser dita sem enfeite, porque ela é o resultado.** Cada
rodada de correção regenera a evidência que a rodada anterior examinou, e por isso
invalida a própria revisão que a motivou; então sempre falta uma passada sobre o estado
atual. Não é um detalhe de processo: a quarta revisão encontrou um defeito **na correção
da terceira** — o ramo que tratava "barrou" como sucesso em variante que tinha que
executar — e a sessão limpa D encontrou um defeito que **sobreviveu a uma revisão
inteira** porque estava protegido por uma lista de exceções que eu próprio havia
declarado. Duas vezes, o erro estava na correção.

O padrão que se repete é um só, e vale mais do que a contagem de achados: **eu fecho os
exemplos medidos e deixo o contrato aberto.** Foi assim na união de pontos por distância
(arredondei o índice duas vezes), na tabela de tolerância por tipo (transcrevi e errei
em `furo`), no julgador do ensaio (aceitava estado inesperado em passo que nenhum
predicado cobria) e no padrão de tolerância (comparava nomes e não valores). A resposta
que funcionou, sempre, foi a mesma: trocar afirmação minha por oráculo executável —
extrair a tabela do fonte em vez de transcrevê-la, comparar as duas respostas na mesma
entrada em vez de conferir o fonte tipo por tipo, plantar o defeito e exigir que o teste
falhe.

Pelo critério deste projeto — mudança posterior invalida a parte afetada da revisão —
**C17 fica PENDENTE sobre 2.2.0**, e é o que falta para o pacote poder ser chamado de
revisado. Registro isso em vez de declarar conclusão: as quatro revisões mostraram que
exatamente esse atalho produz aprovação sem evidência.

## Capacidades comprovadas, e os limites

**Comprovado**, com número e alcance declarado:

- criar e parametrizar peça simples por código, com varredura de família pelos três
  portões e separação entre falha operacional e reprovação geométrica;
- inspecionar malha, orientar seleção, e reconhecer seleção real com sobreposições
  desligadas;
- deslocar região delimitada, com controle negativo de seleção vazia e positivo de
  efeito medido;
- preencher vão entre dois limites, com as **três** interseções medidas antes de
  alterar a peça, limpeza local de degenerações e verificação de perfil contra o
  esperado;
- desfazer e refazer conferidos por assinatura, no caminho ensaiado;
- salvar e exportar com hash, recusando sobrescrever a origem, exigindo `FINISHED` do
  operador e vinculando artefato à geometria medida;
- conferir o artefato entregue com verificadores independentes;
- orientar na sessão viva por cliente somente-leitura, com falha de conexão declarada.

**Não comprovado, e o pacote diz isso em vez de aprovar por silêncio:** aptidão para
fabricação. Para `impressao_fdm`, `matriz.py` lista dez verificações **todas
decisivas** e quatro não têm medidor aqui. Continuam sem medidor: folga de encaixe
(`A_CALIBRAR`, **sem número medido**), parede mínima, folga entre peças, silhueta
contra imagem, geometria de junta, declaração inconsistente com a geometria,
reconstrução de CAD a partir de malha, seleção por imagem.

**Fora do domínio da receita de preenchimento, com recusa explícita:** objeto girado,
superfície curva, mais de dois limites.

## Como instalar e usar

1. copiar o diretório do pacote para onde a skill é lida;
2. garantir o Python do hospedeiro com: `trimesh`, `numpy`, `manifold3d`, `shapely`,
   `build123d`, `lib3mf` — versões em `DEPENDENCIAS_E_LICENCAS.md`;
3. para as rotas de Blender, ter o Blender instalado. Conferir com
   `python scripts/roda_blender.py --achar`;
4. conferir a integridade com os hashes de `INVENTARIO.json` e a versão com
   `bl_ferramentas.confere_versao(...)`;
5. começar por `SKILL.md`, que roteia para a referência da rota.

Sem Blender, as rotas independentes continuam úteis e a dependente informa o que
falta.
