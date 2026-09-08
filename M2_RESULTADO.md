# M2 — resultado

Executado em 08/09/2026. Ambiente igual ao de M1: Blender **5.2.1 LTS**, Python
interno **3.13.13**, Windows 11.

> **Estado final:** pacote **1.5.0**, `bl_ferramentas` **1.4.0**, hash
> `a965ed25…`. A evidência que sustenta as tabelas deste documento foi **regerada sobre
> esses bytes** e vive em `evidencias_finais/`, depois que a segunda revisão
> independente apontou que a anterior era de uma versão já superada. Os oito ensaios
> mais o do venv isolado saem com **VEREDITO ATENDIDO** e critérios executáveis.

## O desfecho, dito antes dos detalhes

**M2 não acrescenta auxiliar novo.** Os quatro auxiliares que o produto tem entraram
em M1, e entraram lá por obrigação do próprio plano: *"os auxiliares mínimos
indispensáveis às receitas entram já em M1"*. O que M2 faz é o que o plano reserva
para ele — consolidar o que M1 demonstrou, comparar contra a base pós-M0 e provar
regressão — mais o fechamento de uma lacuna que a revisão independente classificou
como obrigação de M1, não de M2.

O plano prevê este desfecho: *"Se M1 não demonstrar lacuna, M2 termina registrando que
não há auxiliar novo necessário."* Não havia lacuna nova a fechar, e nada foi criado
para preencher a fase.

## Os quatro auxiliares, cada um com a receita e a lacuna que resolve

| Auxiliar | Receita que o chama | Lacuna, medida |
|---|---|---|
| `scripts/roda_blender.py` | todas as que entram no Blender | o executável da Store **não roda direto** (acesso negado) e o launcher **desanexa**, devolvendo código 0 e stdout vazio mesmo em falha. Sem isto, "rodou" seria inferido de um silêncio |
| `scripts/bl_ferramentas.py` | inspecionar, editar, verificar, recuperar | cada função cobre uma etapa que erra em silêncio: coordenada local contra critério de mundo, seleção vazia devolvendo `CANCELLED`, undo desligado em background, mutação direta fora do histórico, união deixando face de área nula |
| `scripts/valida_requisitos.py` | verificar intenção | a forma natural do JSON — lista nua — produz **traceback não tratado** dentro do verificador, em vez de `ESPEC_INVALIDA`. O verificador é cópia congelada e não pode ser editado, então a guarda mora fora dele |
| `scripts/mcp_blender.py` | orientar na sessão viva do usuário | a referência descrevia o protocolo do socket e o pacote **não trazia cliente**, obrigando o agente a escrever leitura incremental de JSON em socket. A revisão independente apontou que isso é trecho mecânico frágil, que o plano proíbe deixar para o operador |

Capacidade existente e suficiente foi usada **direto**, sem invólucro: os cinco
verificadores de M0 acompanham o pacote como **cópias byte a byte**, e nenhuma linha
deles foi reescrita.

## Aceite de M2

| ID | Critério | Método | Evidência | Observado | Estado |
|---|---|---|---|---|---|
| B1 | cada auxiliar identifica a receita e a lacuna que resolve | leitura do cabeçalho de cada um | os quatro arquivos em `produto/scripts/` | todos abrem com "POR QUE ESTE ARQUIVO EXISTE" e o fato medido atrás | **ATENDIDO** |
| B2 | capacidade existente suficiente é usada diretamente | inventário | `produto/verificadores/PROVENIENCIA.json` | cinco verificadores em cópia byte a byte; hashes conferidos na criação e reconferidos pela sessão limpa | **ATENDIDO** |
| B3 | comparar campos semânticos dos verificadores **alterados** com a base pós-M0 | `git diff` e comparação de saída | histórico do repositório; `evidencias_m1/suite_m0_*.json` | **nenhum verificador foi alterado**: `git diff c9cf867 HEAD -- prototipo/` é vazio. As cópias produzem saída **idêntica em todos os campos** ao original, em três malhas de 12, 196 e 2.496 triângulos | **ATENDIDO** |
| B4 | defeito intencional no campo comparado reprova; execução correta passa | variantes do ensaio | `evidencias_m1/ensaio_*.json` | `ranhura` reprova **só** no perfil; `duplicado` mede **5** degeneradas com forma certa; `parcial` e `flutuante` barram no preflight; `correta` e a de outra medida passam | **ATENDIDO** |
| B5 | erro operacional plantado não recebe nome de reprovação geométrica | M0.2, reexercitado na rota de criar | `base_congelada/M0_RESULTADO.md`; `evidencias_m1/familia_defeito_plantado.json` | falha de escrita sai como `E_EXPORT_3MF` na etapa `exportacao`, com `n_reprovadas_por_geometria: 0`; e o defeito **geométrico** plantado sai com `n_reprovadas_por_geometria: 1` e `n_com_erro_operacional: 0` | **ATENDIDO** |
| B6 | executar verificações afetadas; suítes completas em cópia antes de concluir mudança nos protótipos | execução fresca comparada campo a campo | `evidencias_m1/suite_m0_casos.json`, `suite_m0_mutacoes.json` | 11 casos e 30 mutações, **zero divergências** contra `base_pos_m0/`. Nenhuma mutação nova, nenhum estado alterado | **ATENDIDO** |
| B7 | caminhos de entrada não são sobrescritos incidentalmente | leitura e teste | `produto/scripts/bl_ferramentas.py` | `salva_cena` **recusa** sobrescrever o arquivo de origem por padrão; `exporta_malha` remove o destino antes e recusa se não puder, para não devolver o hash de um artefato antigo | **ATENDIDO** |
| B8 | testar falha e sucesso no ponto certo de uma operação de escrita | M0.2, com prova de etapa | `base_congelada/M0_RESULTADO.md` | três casos: falha operacional na escrita do formato fechado, reprovação geométrica, e **controle positivo** que exporta e aprova. A injeção atinge a escrita do 3MF, com a exportação de malha **concluída** antes | **ATENDIDO** |
| B9 | falha de conexão é declarada e o controle conectado funciona | `scripts/mcp_blender.py`, cinco estados medidos | execução registrada em M1_RESULTADO e neste documento | `OK` conectado por leitura (cena com 8 objetos); `SEM_SERVIDOR` em porta sem servidor; `TEMPO_ESGOTADO` contra servidor que aceita e cala; `ESCRITA_BARRADA` por padrão, e `OK` com permissão explícita; `PARAMS_ILEGIVEIS` | **ATENDIDO** |
| B10 | tempo esgotado em mutação externa fica incerto até inspeção; não repetir automaticamente nem encerrar o Blender do usuário | contrato do cliente e das receitas | `produto/scripts/mcp_blender.py`; `produto/referencias/mapa_de_ferramentas.md` | o estado `TEMPO_ESGOTADO` carrega, no próprio retorno, que **não prova** que o código parou dentro do Blender; não há repetição automática em lugar nenhum do pacote | **ATENDIDO** |
| B11 | nenhum comportamento alterado sem justificativa e teste | histórico do repositório | commits de M1 e M2 | cada alteração de comportamento em `bl_ferramentas.py` tem comentário no código com o fato medido atrás, e teste correspondente. `VERSAO` sobe quando o comportamento muda | **ATENDIDO** |

## O que não entrou, e por quê

Nada de banco de projetos, cache de verificações, árvore de revisões, gerente de
processos ou servidor MCP próprio. Isso não é omissão: é a exclusão declarada no
desenho, e a revisão independente **não** pediu nenhum deles — os dez achados dela
foram todos sobre evidência, contrato e afirmação sem medida.

Duas lacunas de M1 foram deliberadamente **não** implementadas, e ficam declaradas:

- **índice espacial para `mede_topo_em_pontos`.** O custo foi medido, não estimado:
  ~2,6 µs por par ponto-face, linear no produto. Com 100 pontos, 93.750 faces levam
  **24,4 s** e 705.894 levam **185,7 s**. As peças que as receitas suportam não chegam
  nesse tamanho, e a referência orienta seccionar em vez de amostrar quando chegarem.
  Otimizar sem necessidade demonstrada seria infraestrutura antecipada;
- **poligonal completa para face não convexa** em `secao_por_plano`. Aqui houve
  **correção de uma afirmação minha**: eu havia escrito que a contagem foi 0 em todos
  os cenários. O ensaio julgador mostrou que **não**: a variante `duplicado` produz
  **2** faces cortadas em mais de dois pontos, com 12 pontos e apenas 10 segmentos. A
  lacuna **está** demonstrada. Ela não foi implementada nesta entrega por escopo, e o
  limite fica declarado no próprio retorno — o ensaio agora **exige** esse aviso
  naquela variante, em vez de exigir zero.

## Capacidades que continuam indisponíveis

Sem medidor, e **não** ampliadas para fechar por antecipação: folga de encaixe, que
continua `A_CALIBRAR` **sem número medido**; parede mínima; folga entre peças;
silhueta contra imagem; geometria de junta; declaração inconsistente com a geometria;
reconstrução de CAD a partir de malha; seleção por imagem.

A consequência prática, que a segunda sessão limpa demonstrou por conta própria: para
finalidade `impressao_fdm`, `matriz.py` lista dez verificações **todas decisivas**, e
quatro delas não têm medidor neste pacote. **Portanto o pacote não aprova peça para
impressão**, e diz isso em vez de aprovar por silêncio.
