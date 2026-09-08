# M1 — resultado

Executado em 07–08/09/2026, sobre o plano enxuto versão 3. Ambiente medido: Blender
**5.2.1 LTS** (Microsoft Store), Python **3.13.13**, Windows 11.

Caminhos completos neste documento são relativos a
`C:\Users\marce\OneDrive\Documentos\Modelagem 3D\06_skill_universal\`.

> **Estado final:** pacote **2.4.0**, `bl_ferramentas` **1.5.0**, hash
> `6fc1727d…`, medido em pacote recém-montado e nunca executado. Os ensaios foram
> executados sobre os bytes de **código** de 2.3.0 (`435d7bb5…`), que são idênticos
> aos de 2.4.0: a diferença entre as duas versões é `SKILL.md` e
> `criar_e_parametrizar.md`, texto. Dizer «idêntico ao hash executado» sem esse
> delta foi um achado da validação adversarial, e a regra agora é declará-lo aqui. A evidência que sustenta as tabelas deste documento foi **regerada sobre
> esses bytes** e vive em `evidencias_finais/`, depois que a segunda revisão
> independente apontou que a anterior era de uma versão já superada. Os oito ensaios
> mais o do venv isolado saem com **VEREDITO ATENDIDO** e critérios executáveis.

## Ponto de partida preservado

`base_congelada/arquivos/` é **pré-M0** e não foi tocada. Antes de qualquer alteração,
`base_pos_m0/` recebeu a cópia pós-M0: 27 arquivos, 16 scripts, mais
`pos_m0_casos.json` e `pos_m0_mutacoes.json`, com `hashes.json` para conferir a
integridade da cópia.

**`prototipo/` está intacto.** `git diff c9cf867 HEAD -- prototipo/` devolve vazio:
nenhum verificador de M0 foi alterado em M1, portanto não há regressão possível vinda
desta fase. Os 11 casos e 30 mutações continuam válidos como estavam.

## O que foi entregue

| Entrega | Caminho | Tamanho |
|---|---|---|
| entrada curta da skill | `produto/SKILL.md` | 3 regras, classificação, roteamento |
| referências condicionais | `produto/referencias/*.md` | 7 arquivos |
| auxiliares dentro do Blender | `produto/scripts/bl_ferramentas.py` | ~1.070 linhas, 20 funções públicas |
| invocador fora do Blender | `produto/scripts/roda_blender.py` | ~180 linhas |
| gerador de cenário sintético | `produto/cenarios/gera_cenario.py` | paramétrico |
| ensaio com variantes e controles | `produto/cenarios/ensaio_preenchimento.py` | 5 variantes |
| modelo de registro por trabalho | `produto/referencias/registro_de_trabalho.md` | com exemplo preenchido |
| mapa de ferramentas e lacunas | `produto/referencias/mapa_de_ferramentas.md` | inclui o que **não** existe |

Dependências dos scripts: **somente biblioteca padrão** mais `bpy`, `bmesh` e
`mathutils`, que vêm com o Blender. Nenhuma dependência do ambiente do autor.

## Tabela de aceite

| ID | Critério | Método | Evidência | Observado | Estado |
|---|---|---|---|---|---|
| A1 | seleção real com sobreposições desligadas é reconhecida | instância gráfica própria, `estado_das_sobreposicoes` + `diagnostico` | `evidencias_m1/overlay_sobreposicoes.json` **mais** `evidencias_finais/IDENTIDADE_DAS_FUNCOES_DE_A1.json` | com `show_overlays: false`, o diagnóstico lê **1 face selecionada** e reporta o estado da sobreposição. **Esta é a única evidência de M1 que não foi regerada**, e a razão é medida: ela exige instância **gráfica** do Blender, e em segundo plano não há viewport para consultar. O que sustenta a linha é a identidade do código que produziu o número: `estado_das_sobreposicoes` e `diagnostico` são **byte a byte idênticas** nos **9** commits que tocaram `bl_ferramentas.py`, conferido commit por commit no arquivo citado. Isso prova que o medidor é o mesmo; **não** substitui uma nova medição, e o próprio arquivo diz o que o argumento não cobre | **ATENDIDO** |
| A2 | seleção vazia não dispara edição | controle negativo no ensaio | `evidencias_finais/ensaio_*.json`, passo `controle_negativo_deslocar_selecao_vazia` | `PRECONDICAO` em todas as variantes | **ATENDIDO** |
| A3 | controle positivo com seleção válida segue | ensaio | passo `controle_positivo_deslocamento` | `FINISHED`, `geometria_mudou: true`, altura 20,0 → 22,0 | **ATENDIDO** |
| A4 | deslocamento com direção e distância conhecidas atende à tolerância e preserva região declarada | medida externa independente | `diagnostico.objeto.dimensions_mundo` | subir 2,0 leva z de 20,0 a 22,0 exatos | **ATENDIDO** |
| A5 | alteração errada é detectada no requisito correspondente, sem crédito por outro erro | variantes `ranhura` e `duplicado` | `evidencias_finais/ensaio_ranhura.json`, `evidencias_finais/ensaio_duplicado.json` | ranhura: **só** o perfil reprova (desvio 0,5), topologia limpa. duplicado: **só** a degeneração (5 faces), perfil 0,0 | **ATENDIDO** |
| A6 | preenchimento local é inspecionado na junção | `mede_topo_em_pontos` + `secao_por_plano` | `evidencias_finais/ensaio_correta.json` | **99** pontos, desvio máximo **0,0**; seção com 10 pontos e 10 segmentos. Eram 87 até a lista de amostragem ficar simétrica, que é o que passou a cobrir a costura em `xb + ov` | **ATENDIDO** |
| A7 | controle defeituoso com ranhura e malha fechada falha na verificação da intenção | variante `ranhura` | `evidencias_finais/ensaio_ranhura.json` | malha 0/0/0, região protegida intacta, perfil **0,5** fora | **ATENDIDO** |
| A8 | declarar posições e alcance das seções e amostras | campo `limite` em toda saída | qualquer relatório de ensaio | posições em y e x listadas; alcance declarado por medida | **ATENDIDO** |
| A9 | seleção capturada seguida de mudança de geometria é relida antes de editar | `confere_selecao_capturada`, par discriminante | `evidencias_finais/captura_envelhecida.json` | sem mudança: passa. Depois da união (16 → 27 faces): **barra**, e o índice 10 ainda existiria | **ATENDIDO** |
| A10 | o caminho sem mudança funciona | mesmo par, controle positivo | `evidencias_finais/captura_envelhecida.json` | assinaturas idênticas, passa | **ATENDIDO** |
| A11 | incluir transformação ou modificador quando relevante | `diagnostico` | qualquer ensaio | reporta `matriz_mundo_e_identidade`, `location`, `scale`, `rotation_euler`, `modificadores` | **ATENDIDO** |
| A12 | undo e redo recuperam as assinaturas anterior e posterior no caminho ensaiado | `desfaz_e_confere` / `refaz_e_confere` | `evidencias_finais/ensaio_correta.json`, `evidencias_finais/ensaio_ranhura.json`, `ensaio_duplicado.json` | `recuperou: true` nos dois sentidos, nas três variantes | **ATENDIDO** |
| A13 | retomada a partir do arquivo salvo e registro permite a outro agente identificar pendências | `salva_cena` + `exporta_malha` + modelo de registro | `evidencias_finais/entrega_peca.*`, `evidencias_finais/entrega_tamanhos.json`, `produto/referencias/registro_de_trabalho.md` | medido com `bl_ferramentas` **1.5.0**, no pacote 1.6.0, e os bytes da biblioteca e do gerador **não mudaram** desde então (o que separa 1.6.0 de 1.9.0 são referências e o `SKILL.md`): `.blend` **95.086** bytes (sha256 `e2a38aed…`); `.stl` **3.884** bytes (sha256 `57b9582b…`) com assinatura da geometria `ed373565…`. Os 93.598 / 3.684 da versão anterior desta tabela eram de uma construção que já não existe | **ATENDIDO** |
| A14 | mudança manual após medição exige nova verificação antes de entregar | regra + mecanismo | `registro_de_trabalho.md`, `confere_selecao_capturada` | assinatura muda → resultado anterior inaplicável; não há cache de medições | **ATENDIDO** |
| A15 | câmera ou sobreposições não são tratadas como mudança geométrica | separação assinatura × hash de arquivo | `salva_cena.limite` | declarado no próprio retorno da função | **ATENDIDO** |
| A16 | o resultado medido se vincula ao artefato entregue | `exporta_malha` devolve hash do arquivo **e** assinatura da geometria | `evidencias_finais/ensaio_entrega.json`, `evidencias_finais/entrega_peca.stl` e `evidencias_finais/check_mesh_do_stl.json` | STL entregue pela construção **atual**, medido pelo `check_mesh.py` do pacote extraído: 76 triângulos, 0 abertas, 0 não-manifold, 0 degeneradas, estanque, 1 componente, volume **40.800,0** idêntico ao medido na cena; operador devolveu `FINISHED` | **ATENDIDO** |
| A17 | pedido de orientar sem executar é respeitado | segunda sessão limpa, pedido 1 explicitamente sem alterar nada | relatório da segunda rodada | descreveu a peça com números e ensinou a seleção; **hash da origem idêntico** antes e depois (`9c682c33…`, 94.683 bytes, mesmo mtime); nenhum `salva_cena`, nenhum `exporta_malha` | **ATENDIDO** |
| A18 | sessão nova de agente conclui criação/alteração simples com as instruções distribuíveis | **cinco** subagentes sem histórico, cada um sobre os bytes de uma versão do pacote, e as duas últimas cobrindo as **duas** rotas | **quarta rodada preservada em `evidencias_finais/SESSAO_LIMPA_D.md`**; as três anteriores, nos relatórios de rodada | rodada D, sobre o pacote **1.6.0**: peça 80 × 50 × 8 com dois furos, **7 de 7 requisitos APROVADA** (caixa 80,0/50,0/8,0 desvio 0,0; furos com erro de posição 0,0 e diâmetro 9,9979; distância 40,0 desvio 0,0; volume desvio 0,521 mm³), 1 de 1 variante aprovada na varredura, malha 1028 triângulos, 0 abertas, 0 não-manifold, estanque; e o **controle negativo dela** reprovou 6 de 7 requisitos errados de propósito, com o certo aprovado no mesmo arquivo. Primeira execução bem-sucedida **de primeira**, zero retentativas no caminho principal. Ela achou **nove** defeitos, um deles grave — todos tratados, ver M3. **Rodada E**, sobre 1.8.0 e pela rota de **edição**: peça própria 90 × 30 × 26 com vão de 40, sobreposição **2,0 derivada do vão dela** e não copiada do exemplo; perfil com desvio máximo **0,0** em 99 pontos; volume 41.850 → **58.050**, exatamente o trapézio implicado; região preservada **0,0 mm³**, e a mesma caixa apontada ao vão devolvendo **16.200 mm³** REPROVADA, o que prova que o zero é medida. Dois controles negativos de naturezas diferentes, ambos com código 1. Primeira execução bem-sucedida no **3º comando**. Ela **não escreveu nada** na pasta da habilidade — 24 arquivos, 23 hashes conferidos, 0 divergentes — e achou mais **nove** lacunas. **Rodada F**, sobre **2.0.0**, com a tarefa de **escrever o próprio script** que roda dentro do Blender — que é a lacuna que E havia apontado como a mais séria da documentação: ela **passou na primeira tentativa**, em 14 passos, provou o retorno nos **dois** sentidos (sucesso com código 0; falha deliberada com código 1, `VEREDITO_NEGATIVO` e traceback gravado), confirmou que os **dois** argumentos dela ficaram intactos, e mediu o artefato do disco com 4 de 4 requisitos `APROVADA`. Não escreveu nada na pasta: 23 de 23 hashes conferidos, zero extras, zero `__pycache__`. Achou mais **sete** lacunas, duas delas contestando afirmações medidas do próprio pacote | **ATENDIDO** |
| A19 | variante sintética com dimensões diferentes dentro do domínio | `variante_outra_medida` | `evidencias_finais/ensaio_variante_outra_medida.json` | 96 × 24 × 6, vão 30, sobreposição derivada 1,5: perfil 0,0, protegida 0,0, undo/redo ok | **ATENDIDO** |
| A20 | a receita declara a geometria que suporta e reconhece quando não se aplica | `variante_girada` | `evidencias_finais/ensaio_variante_girada.json` | girada 30°: seleção por caixa já barra, e o preenchimento recusa nomeando o eixo e as alternativas | **ATENDIDO** |
| A21 | criar ou parametrizar geometria simples com verificação | `sweep_params.py` sobre família sintética | `evidencias_finais/rota_criar_varredura.json` | grade `L=70,80;d=4,5`: 4 variantes, 4 aprovadas, 0 reprovadas por geometria, 0 erros operacionais | **ATENDIDO** |
| A22 | rota independente funciona sem Blender; a dependente informa a ausência | `BLENDER_EXE` apontando para caminho inexistente | execução registrada | dependente: informa o motivo, sai com código 1. Independente: `check_mesh.py` roda normalmente | **ATENDIDO** |
| A23 | nenhum padrão conhecido de dado privado no produto | varredura contra os padrões locais, **com controle positivo plantado** | `evidencias_finais/empacotamento.json` | **5 padrões, 22 arquivos, 0 achados**, e o controle plantado fora do pacote **casou**, provando que a varredura encontra quando há. Conclusão limitada: ausência dos padrões testados, na cobertura testada — **não** prova ausência de qualquer dado privado | **ATENDIDO** |

## Achados medidos que a construção produziu

Estes não estavam nos documentos de entrada. Saíram de rodar as coisas.

### Sobre invocar o Blender

1. O executável da Microsoft Store em `Program Files\WindowsApps` **não roda direto**:
   "Acesso negado", tanto pelo shell quanto pelo Python. O caminho é o alias
   `blender-launcher.exe`.
2. O launcher **desanexa** e devolve **código 0 com stdout vazio**, mesmo quando o
   Blender falha. Ler stdout não funciona e o código de saída não informa nada. Por
   isso o contrato virou "o script escreve um arquivo de resultado".

### Sobre a API

3. `calc_center_median()` é coordenada **local**. Cubo de aresta 20 em z=10: critério
   "acima de z=15" seleciona **1** face em mundo e **0** em local. E com zero faces a
   edição devolve `{'CANCELLED'}` sem erro.
4. `wm.stl_export` é o operador desta versão. `export_mesh.stl` **não existe mais**.
5. Em background o undo **nasce desligado**, e a mensagem é
   *"Undo disabled at startup in background-mode"*. Com **um único** ponto na pilha,
   a mensagem muda para *"poll() failed, context is incorrect"*. São duas falhas
   distintas: sistema não inicializado, e nada a que voltar.
6. `bm.to_mesh(obj.data)` é mutação direta de dados e **não entra no histórico**.
   Medido: depois de uma limpeza feita assim, `redo` desfazia a limpeza e a
   conferência acusava `recuperou: False` — não era o redo que falhava.
7. Um ponto de histórico **por operação lógica**, não por chamada: dois pontos
   empilhados fazem um `undo` parar no meio, e a assinatura acusa "não recuperou"
   quando houve recuperação pela metade.

### Sobre a operação booleana

8. A união produz faces de área nula **sem abrir nenhuma borda**. "Malha fechada" não
   detecta; a contagem própria detecta.
9. Previsão minha derrubada pela medição: eu esperava que um topo **coplanar** com o
   material produzisse mais degeneração que um topo **oblíquo**. Produziu menos — 33
   faces com 4 degeneradas contra 27 faces com **zero**. O solver `EXACT` lida melhor
   com faces coplanares coincidentes.

## Quatro defeitos meus, achados por medição e corrigidos

Registro-os porque são a evidência de que os controles funcionam, e porque três deles
são exatamente a classe de defeito que este projeto existe para evitar.

| Defeito | Como apareceu | Correção |
|---|---|---|
| assinatura lida de `obj.data` em Edit Mode comparava **duas leituras da mesma cópia velha** e reportava "não mudou" com o deslocamento aplicado | `retorno=FINISHED` com `geometria_mudou=False` | `assinatura` lê a malha viva em Edit Mode e declara `fonte_da_leitura` |
| captura de região protegida devolvia conjunto **vazio** em silêncio e a comparação **ainda emitia veredito** | `antes=0 agora=4` e mesmo assim um resultado | as duas funções recusam conjunto vazio |
| medir "degrau" por dois pontos vizinhos numa rampa media a **inclinação** | 0,006 de degrau numa peça correta, puro artefato | comparar sempre com o perfil **esperado**, no mesmo x |
| o volume de preenchimento prolongava a inclinação para dentro do material e subia **0,3 acima da superfície protegida** | **a seção** mostrou dois pontos em x=19: z=20,0 e z=20,3. A amostragem uniforme de perfil passou por cima do trecho | topo horizontal na zona de sobreposição, **e** amostragem densa na vizinhança de cada limite (45 → 87 → **99** pontos, o último salto ao tornar a lista simétrica) |

O quarto é o mais instrutivo: o defeito existia, havia um detector para ele, e a
**amostragem** o escondeu. Foi uma segunda ferramenta, olhando de outro jeito, que o
revelou.

## Discriminação das variantes

| Variante | Topologia | Perfil | Protegida | Onde barra |
|---|---|---|---|---|
| `correta` | 0 aberta, 0 não-manifold, **0** degeneradas, 27 faces | 0,0 em **99** pontos | 0,0 em 18 pontos | não barra |
| `ranhura` | 0, 0, 0 — limpa | **0,5**, fora | 0,0 | **só no perfil** |
| `duplicado` | **5 → 0** degeneradas, 39 → 34 faces | 0,0 | 0,0 | **só na degeneração** |
| `tangente` | não medida | não medida | não medida | **pré-condição**, antes da união |
| `variante_outra_medida` | 0 degeneradas | 0,0 | 0,0 | não barra |
| `variante_girada` | não medida | não medida | não medida | **pré-condição** de domínio |

`ranhura` e `duplicado` são o par que importa: **forma errada com topologia limpa** e
**topologia suja com a forma certa**. Nenhum detector cobre o caso do outro.

Nas variantes barradas o relatório registra: *"o preenchimento não foi executado; nada
depois dele foi medido. Um resultado de etapa não prova outra."*

## Ensaio com agente sem contexto

Modelo operador: **o mesmo modelo implementador, em subagente sem histórico deste
projeto** — foi a definição dada pelo autor. O subagente recebeu apenas: o caminho de
`produto/`, o cenário sintético em `.blend` e o pedido em linguagem de usuário.
Instrução explícita de usar somente o que está em `produto/`, e de não tocar na sessão
viva do Blender.

### Primeira rodada — piloto, e por que não conta como aceite

Cenário: 50 × 30 × 8, vão de x=18 a 32, alturas 18 e 12. Dimensões inéditas em relação
às usadas na redação das receitas.

**Resultado da tarefa: concluída e correta.** Rampa de (18, 18) a (32, 12), largura
total 30. Volume 19.560 → 22.500, acréscimo de **2.940,0** contra o valor analítico
`(10+4)/2 × 14 × 30 = 2.940,0` **exato**. Topologia final 0/0/0/0 com 27 faces. Perfil:
**102 pontos, desvio máximo 0,0**. Região protegida: 36 pontos, 0,0 antes e depois.
Três seções idênticas. Undo e redo recuperaram as duas assinaturas. STL entregue:
76 triângulos, estanque, 1 componente, volume 22.500,0, `apto_para_booleana: true`.
Origem intacta, hash inalterado.

Ele foi além do pedido em duas coisas que valem registro: rodou um **controle negativo
do próprio detector de perfil**, deslocando o esperado em +0,5 e confirmando que
102 de 102 pontos reprovavam — ou seja, provou que o "aprovado" não era medida inerte;
e derivou a sobreposição pela regra da referência (0,7 = 14/20) verificando os dois
sentidos, para baixo e para os lados.

**Mas esta rodada não conta como aceite, por culpa minha.** Eu editava `produto/`
enquanto ela corria. `bl_ferramentas.py` mudou às 00:02:06 e `editar_localizado.md` às
00:02:50, depois de ele ter lido os dois. O comportamento de `preenche_entre_limites`
passou de perfil de 4 pontos para 6 no meio do caminho, e `VERSAO` continuou `"1.0.0"`.
Ele leu uma referência e executou outro código, e **perdeu uma execução inteira**. O
aceite exige bytes identificados; esta rodada vale como piloto.

### Segunda rodada — a que vale como aceite

Cenário: **44 x 26 x 21**, vão de x=12 a 30 (comprimento 18), topos em z=21 e z=13.
Dimensões inéditas nas duas rodadas anteriores. Pacote na versão **1.1.0**, com os
bytes de `INVENTARIO.json` congelados **antes** do início e não tocados durante.

**Pedido 1 — orientar sem executar.** Descreveu a peça com números medidos, a forma
por seção em dois planos, e ensinou os dois caminhos de seleção, à mão e por código.
**Prova de que nada mudou:** hash `9c682c33…`, 94.683 bytes e o **mesmo mtime** antes
e depois. Só passos de leitura; nenhum `salva_cena`, nenhum `exporta_malha`. E rodou o
controle negativo da caixa vazia **em Edit Mode**, obtendo a mensagem certa, o que
confirma que a correção do achado (d) da primeira rodada funcionou.

**Pedido 2 — executar.** Rampa de (12, 21) a (30, 13), largura total 26.

| Medida | Valor |
|---|---|
| sobreposição | **0,9**, derivada de 18/20 pela regra da referência, e **não** copiada do exemplo, que usa 1,0 |
| interseção com o material | **1.024,92**, maior que zero, portanto houve interpenetração |
| material acrescentado | **5.616,0**, conferindo com a seção trapezoidal 18 x ((21-5)+(13-5))/2 x 26 |
| topologia | 0 abertas, 0 não-manifold, 0 soltas, **0 degeneradas**; 16 para 27 faces |
| perfil | **123 pontos** em 3 planos, com adensamento em torno de cada limite; desvio máximo **0,0** |
| região protegida, por amostragem | 45 pontos, desvio **0,0** |
| região protegida, **exata** | `regiao_intacta`: divergência **0,0 mm3** na faixa de z alto e em toda a coluna do degrau |
| envoltória | 0 a 44 / 0 a 26 / 0 a 21, **inalterada** |
| histórico | undo e redo recuperaram as duas assinaturas |
| STL entregue | 76 triângulos, estanque, euler 2, 1 componente, volume 19.240,0 idêntico ao medido na cena |
| reprodutibilidade | duas execuções independentes deram a **mesma** assinatura `d4ce3b6e…`, e reabrir o `.blend` salvo devolve essa assinatura |

Três coisas que ela fez sem eu pedir, e que fortalecem o aceite:

1. **usou o instrumento mais forte, que eu não havia citado.** Encontrou, lendo o
   fonte, o tipo `regiao_intacta` do `check_intent.py`, que mede preservação por
   **diferença simétrica booleana exata** em vez de amostragem, e obteve 0,0 mm3;
2. **rodou três controles negativos próprios**, incluindo `regiao_intacta` apontado
   para o **vão**, que devolveu **5.616,0 mm3**. É esse número que prova que o 0,0
   anterior era medida, e não silêncio;
3. **recusou aprovar para impressão.** Consultou `matriz.py editar solido
   impressao_fdm`, viu 10 verificações todas decisivas e constatou que quatro não têm
   medidor no pacote. Concluiu que não pode aprovar por **ausência de ferramenta**, e
   disse isso. É exatamente o comportamento que o método exige.

### Os seis achados da segunda rodada, todos válidos e corrigidos

| # | Achado | Correção |
|---|---|---|
| 7.1 | `check_intent.py` exige `--malha` e a documentação omitia | corrigido em três referências |
| 7.2 | o esquema do arquivo de requisitos **não estava documentado**, e a forma natural do JSON, uma lista nua, produz **traceback não tratado** em vez de `ESPEC_INVALIDA` | esquema completo documentado, com os oito tipos, campos e tolerâncias; mais `scripts/valida_requisitos.py`, que confere a forma antes da chamada. O verificador **não** foi editado: é cópia byte a byte |
| 7.3 | a tabela de estados de `check_intent.py` estava errada nos **dois** sentidos: listava `NAO_APLICAVEL`, que não existe lá, e omitia `ERRO` | tabela conferida no fonte e corrigida, com a nota de que `NAO_APLICAVEL` vem de `matriz.py` |
| 7.4 | `regiao_intacta` não era citada na rota que mais precisa dela | passou a ser a **primeira** das três opções de preservação, com comando e requisito de exemplo |
| 7.5 | o exemplo de inspeção usava números de **outra** cena sem avisar, e o índice 10 coincidia entre as duas peças | aviso: copiar a caixa seleciona zero faces, e copiar o índice "funciona" por coincidência |
| 7.6 | o vocabulário fechado das três decisões não estava escrito, e `impressao_fdm` aparecia como "impressão" em prosa | tabela dos valores aceitos, com o aviso sobre `impressao` |

Achado colateral, do fonte: o **cabeçalho** de `check_intent.py`, linha 21, descreve
`regiao_intacta` como "por amostragem", e a implementação na linha 325 diz e faz o
contrário, corretamente. A discrepância está registrada na referência; o arquivo não
foi editado, porque é cópia congelada.

E um defeito **do meu próprio validador**, achado pelo meu próprio teste: ele exigia
tolerância em `n_solidos`, que é contagem exata, e assim **recusava um requisito que o
verificador aceita**. Corrigido com isenção para tipos de contagem. É a mesma regra do
método: igualdade é legítima em contagem inteira e proibida em medida.

### Os seis achados da primeira rodada, todos válidos

| # | Achado | Correção |
|---|---|---|
| a | o pacote mudou no meio da execução e `VERSAO` não mudou; nada permitia detectar | `VERSAO` = 1.1.0, muda quando o **comportamento** muda; `confere_versao(esperada)` recusa cedo; `SKILL.md` declara a versão; `INVENTARIO.json` congela os hashes |
| b | a receita não avisava que a sobreposição é aplicada nos **dois** extremos, que é a raiz do problema da saliência | avisa, e explica |
| c | o critério "sobreposição pequena o bastante para não alcançar a região protegida" **não é satisfazível**: qualquer valor positivo alcança em planta, e é assim que ele intercepta | o critério passa a ser sobre **altura**; em planta ela alcança e **retessela**, e isso é esperado |
| d | um controle negativo **passava testando outra coisa**: em Object Mode a caixa vazia barrava com "exige Edit Mode", sem exercitar a guarda de seleção vazia | o controle exige Edit Mode e conferência da **mensagem** |
| e | as verificações que o pacote manda executar em imperativo **não estavam no pacote** | `produto/verificadores/` com cópias byte a byte da base pós-M0, conferidas por hash, mais `PROVENIENCIA.json`; o mapa separa incluído de não incluído, com motivo |
| f | a tabela de sintomas não cobria "limpeza devolveu 0 → 0", que é correto e pode ser lido como falha | linha acrescentada, avisando que repetir a união é o que cria as 5 degeneradas |

O achado (d) merece nota: é **exatamente** a classe de defeito que este projeto
persegue — crédito por defeito não exercitado — encontrada dentro do material que a
combate.

Ao corrigir (e) eu introduzi outro defeito, também registrado: a substituição em massa
de caminhos criou a afirmação falsa de que `familia_placa` vive em `gera_cenario.py`, e
o exemplo apontava para `casos.py`, que não está no pacote. Corrigido com
`produto/cenarios/familia_exemplo.py`, próprio do pacote, medido de dentro dele: grade
limpa 4 de 4; defeito plantado `d=40` em `L=80` reprova **por geometria**, com 3
arestas não-manifold e 0 erros operacionais.

## Revisão independente, e os dez achados

Executada via Codex, somente leitura, sobre `REVISAO_M1_CONTEXTO.md`. Veredito:
**BLOQUEIA**, com dez achados. Conferi cada um por inspeção direta do fonte:
**todos procedentes**. Relatório integral preservado em
`evidencias_finais/revisao_1_codex.txt`.

| # | Achado | Como foi corrigido |
|---|---|---|
| 1 | **A16 estava aprovado com a geometria defeituosa anterior**: volume 40.806 contra 40.800 da construção corrigida, e os 6 mm³ de diferença são exatamente a saliência antiga, `0,5 × 1,0 × 0,3 × 40` | reexecutado: **40.800,0**, 76 triângulos, estanque, 1 componente. Evidência substituída |
| 2 | A17 e A18 exercitaram 1.1.0 com 19 arquivos, e o produto já era outro | terceira sessão limpa contra o inventário **1.3.0**, com o modelo operador registrado |
| 3 | as evidências citadas viviam em pasta temporária e **não eram auditáveis** | `evidencias_m1/` preserva os JSONs, os artefatos e o próprio relatório da revisão, com hash de cada um |
| 4 | a receita de criar tinha requisito **chamado** `dois_furos` com tipo `n_solidos`, que conta **corpos** | medido: numa placa **maciça, sem furo nenhum**, o requisito defeituoso **APROVA**. O corrigido, `n_furos_no_plano`, **REPROVA** a mesma placa e aprova a que tem os dois furos |
| 5 | `regiao_intacta` lê **somente** `tol_fracao`, e a referência documentava `tol_mm3`: número com nome de tolerância que **não participava da decisão** | tabela de tolerância por tipo; e o validador passou a conferir tolerância **por tipo**, exigir `entre`/`com` em `interferencia`, e recusar tolerância que seria ignorada |
| 6 | `exporta_malha` marcava sucesso por **ausência de exceção** — o mesmo defeito que a receita documenta para `transform.translate`, deixado dentro da própria exportação | exige `FINISHED`, remove arquivo anterior antes de exportar, recusa arquivo vazio, e avisa quando há modificador ativo, porque a assinatura não cobre o resultado dele |
| 7 | a interseção era **um escalar** e provava "alguma" interseção; e o mapa prometia contagem de componentes que o retorno não trazia | as **três** zonas medidas separadamente, em cópia, por booleana: **440,0 / 200,0 / 880,0**, iguais a `11×1×40`, `5×1×40`, `22×1×40`. Nova variante `parcial`: `extremo_do_limite_b` = **0,0** com as outras em 440 e 1.640 — caso que o escalar aprovava, porque o total é 2.080. E `mede_malha` passou a contar componentes |
| 8 | a união era aplicada **antes** da medida, e a falha deixava corpo flutuante grudado na peça | a medida virou **preflight**: recusa antes de alterar qualquer coisa, e a mensagem nomeia a zona sem material |
| 9 | a rota da sessão viva exigia o agente **escrever o cliente de socket** | `produto/scripts/mcp_blender.py`, somente leitura por padrão, com sete estados nomeados. Cinco medidos com controle: `OK` conectado, `SEM_SERVIDOR`, `TEMPO_ESGOTADO`, `ESCRITA_BARRADA` (e `OK` com permissão explícita), `PARAMS_ILEGIVEIS` |
| 10 | A23 auditava 15 arquivos e o pacote já tinha mais | reauditado sobre os 22, **com controle positivo plantado** |

O achado 10 rendeu a melhor lição da rodada. Ao reescrever a auditoria, minha extração
de padrões devolveu **zero padrões**, porque o arquivo local guarda pares
`[regex, descrição]` e eu filtrei só strings. A varredura reportou **"0 achados"
sobre padrão nenhum** — e foi o **controle positivo** que acusou, marcando
`varredura_funciona: false`. Sem ele, eu teria registrado uma aprovação vazia. É
exatamente o argumento que este projeto defende, aplicado contra mim.

Também vale registrar o que a revisão **não** fez: não recomendou ampliar o produto.
Os dez achados são todos sobre evidência, contrato e afirmação sem medida — nenhum
pede viewer, servidor próprio, cache ou banco.

## Lacunas concretas para M2

Detalhadas em `LACUNAS_PARA_M2.md`. Resumo:

- **L1, cliente do socket do MCP**, com estados de falha nomeados. Lacuna real: a
  referência descreve o protocolo e o pacote não traz cliente, então o agente tem que
  escrever um. E o aceite de M2 pede que falha de conexão seja **declarada**.
- **L2**, já corrigida em M1: a documentação de `check_intent.py`.
- **L3**, convertida de suspeita em **fato medido**: `mede_topo_em_pontos` custa cerca
  de 2,6 microssegundos por par ponto-face, linear no produto. Com 100 pontos, 93.750
  faces levam 24,4 s e 705.894 levam 185,7 s. Documentado, com a orientação de
  seccionar em vez de amostrar em malha grande. Índice espacial **não** foi
  implementado: as peças que as receitas suportam não chegam nesse tamanho, e otimizar
  sem necessidade demonstrada seria infraestrutura antecipada.
- **L4**, face não convexa cortada em mais de dois pontos: contagem sempre **0** nos
  cenários medidos. Sem lacuna demonstrada, o limite fica declarado e nada é
  implementado.
- **L5**, atendida já em M1 por ser indispensável à receita:
  `scripts/valida_requisitos.py`.

## O que permanece indisponível

Sem medidor, e **não** foi ampliado para fechar por antecipação: folga de encaixe
(`A_CALIBRAR`, sem número medido), parede mínima, folga entre peças, silhueta contra
imagem, geometria de junta, declaração inconsistente com a geometria, reconstrução de
CAD a partir de malha, seleção por imagem.

Fora do domínio da receita de preenchimento, com recusa explícita: objeto girado,
superfície curva, mais de dois limites.
