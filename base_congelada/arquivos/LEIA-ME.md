# Protótipos da skill universal de projeto 3D

Estado em 07/09/2026. Nada aqui é arquivo de skill: são as ferramentas em teste, na pasta de trabalho, aguardando aprovação do desenho.

**Decisões tomadas pelo proprietário:** motor de modelagem é build123d. Exemplos são sintéticos.

**Correção de sigilo, 07/09/2026.** A versão anterior deste arquivo afirmava que não havia nenhuma referência ao projeto privado. Isso era **falso**. Uma revisão externa encontrou o nome de um arquivo de referência real, o hash dele e cotas num arquivo de saída, e uma normal e um centroide reais dentro do exemplo de uso de uma ferramenta que **vai ser distribuída**. Os dois foram removidos.

A causa raiz não foi descuido pontual: era empacotar por exclusão. O pacote agora é montado por **lista de permissão**, com auditoria que barra a montagem se encontrar dado do projeto privado em arquivo permitido. **Este arquivo (`LEIA-ME.md`) está na lista de negados**, porque as notas de trabalho abaixo citam medidas de arquivos reais de propósito.

## Por que estas ferramentas existem

O council concluiu que doutrina em texto não corrige cegueira espacial, só corrige desobediência. A ordem foi trocar regra escrita por script determinístico que o agente chama e lê, e validar o primeiro script contra dois casos extremos antes de aceitar qualquer arquitetura.

Toda ferramenta devolve, junto do resultado, o que ela **não** decidiu. É assim que a honestidade sai do prompt e entra no dado.

## Ferramentas

| Script | O que faz | Portão | Estado |
|---|---|---|---|
| `find_datums.py` | Regiões planas coplanares e conectadas: área, normal, centroide, resíduo de planaridade, ângulo com cada eixo | não decide qual é a interface | valida nos 2 casos |
| `align_rigid.py` | Transformação rígida datum sobre datum, com o ângulo relativo em destaque | conta os graus de liberdade que sobraram; nunca espelha | valida em 3 modos |
| `check_mesh.py` | Validade topológica da malha | barra booleana e exportação | valida nos 2 casos |
| `slice_check.py` | Fatiador de verdade em modo headless | o portão real | valida nos 2 sentidos |
| `split_for_volume.py` | Orientação e planos de corte quando a peça estoura o envelope | não escolhe o corte sem a direção de carga | valida no caso 2 |
| `sweep_params.py` | Varre a família de parâmetros por três portões | reprova a família, não a peça | achou 4 defeitos em 6 variantes |
| `tolerance_lookup.py` | Folga de encaixe | recusa cravar número sem cupom medido | valida nos 3 modos |
| `check_intent.py` | Verifica se a geometria atende ao **pedido**, contra requisitos declarados | requisito não verificado não é requisito atendido | pega requisito plantado com erro de 4,25 mm |
| `secoes.py` | Seção de malha em polígonos, com material e furo separados | módulo compartilhado | conferido contra geometria à mão |
| `exemplo_b123d.py` | Modelo paramétrico mínimo que demonstra as seis regras | verifica antes de exportar | limpo nos 3 portões |
| `req_exemplo.json` | Requisitos declarados do exemplo, com um item errado de propósito | dado, não código | — |
| `matriz.py` | Roteia verificações a partir da classificação | não verifica nada, só responde o que verificar | 4 classificações conferidas |
| `casos.py` | Os seis casos de teste da generalidade, toda geometria sintética | cada caso declara o que espera | 6 de 6 passam |
| `roda_casos.py` | Executa os casos e confere roteamento, resultado e extras | reprova por cobrança indevida e por falta | — |
| `mutacoes.py` | Introduz defeitos de propósito e confere que a suíte reprova **no verificador previsto** | erro de execução vira inválido, não crédito | 11 de 11 pegas |
| `empacota.py` | Monta o pacote por lista de permissão e barra vazamento | nada fora da lista viaja | pacote de prova sai limpo |
| `padroes_de_vazamento.json` | Padrões que reconhecem o projeto a proteger | **local, nunca viaja** | — |
| `gera_caso2.py` | Geometria sintética do caso 2 | apoio | — |
| `folgas_publicadas.json` | Faixas de terceiros com rótulo de confiança | dado, não código | — |
| `folgas_medidas.json` | Folgas medidas nesta oficina | **vazio, e vazio é a resposta certa** | — |

## Os dois casos que o council exigiu

**Caso 1, peça-fonte com interface de acoplamento.** O extrator devolve a face inclinada como candidato número 1 por área, marcada como não alinhada a eixo. É o que o processo original deixou passar: alinhou por eixo quando a interface é inclinada.

**Caso 2a, sem peça-fonte.** Modo do zero: nenhum candidato, mais a lista dos datums que precisam sair dos requisitos.

**Caso 2b, geometria do zero, prismática.** Zero regiões inclinadas. Não inventa interface onde não existe.

## Achados de engenharia, todos medidos em 07/09/2026

### Malha e leitura de arquivo

1. **STL não compartilha vértices.** Sem soldar, a adjacência de faces fica vazia e cada faceta vira uma região sozinha. No caso 1 os vértices caem de 32.550 para 5.309 ao soldar, e só então a face de acoplamento aparece inteira.
2. **O `status()` do kernel de malha não é oráculo de validade.** O construtor solda e conserta em silêncio, e devolveu sem erro uma malha com 99 arestas não-manifold. Quem reprova são as contagens topológicas.
3. **O caminho de polígonos do trimesh exige um módulo nativo que não está instalado aqui.** A área de seção foi refeita com segmentos do corte mais polígonos do shapely e regra par-ímpar. Menos dependência binária para uma skill distribuída.
4. **Seção de malha em polígonos tem duas armadilhas, e as duas falham em silêncio.**

   **Nodação.** Os segmentos que saem do corte têm extremos calculados por face, e faces vizinhas produzem coordenadas que diferem nos últimos bits. O polygonize do shapely exige linha nodada: com o dado cru devolve **zero polígonos, sem erro**. Medido: 646 segmentos, zero polígonos. Arredondar para 9 casas decimais resolve, e 9 casas em milímetro não altera cota. Passar por união antes não resolve, porque funde as linhas e devolve um polígono só.

   **Quem é furo.** O polygonize devolve a região de material **já com os furos subtraídos**, e os anéis dos furos como polígonos separados. Logo os dois têm profundidade de aninhamento zero, e classificar furo por aninhamento falha calado. O verificador contava zero furos numa peça com dois. A regra correta compara o contorno externo preenchido: um polígono é furo se o ponto interno dele cai dentro do contorno preenchido de outro e não cai dentro do outro. Isso não depende de módulo nativo.

   **Correção de um número que eu havia publicado errado.** A versão anterior deste documento dizia que o perfil de seção do abrigo era plano, com ganho de 1,000x, e concluía que a área não distinguia o corte. Isso era efeito do defeito acima: o código somava a cavidade como material. Com a seção correta, conferida à mão contra a geometria:

   | medida | valor |
   |---|---|
   | laje do piso | 53.084 mm² |
   | anel da parede | 2.729 mm² |
   | seção num degrau | 6.329 mm² |

   O perfil **não** é plano, e o deslocamento do corte de 150 mm para 136,18 mm o põe sobre um degrau, com 2,3 vezes mais seção na junta. A ferramenta faz trabalho real; a versão anterior não conseguia porque estava medindo errado.

### Modelagem paramétrica

5. **A tolerância de malha é ignorada em silêncio na segunda exportação da mesma forma.** O núcleo guarda a triangulação no objeto. Três exportações com tolerâncias diferentes devolveram 2.508 triângulos idênticos. Construindo a forma do zero a cada vez: 4.980, 2.500, 600 e 392 triângulos, como esperado. Quem trocar tolerância e reusar o objeto vai medir a malha velha.
6. **O escritor de 3MF é um portão de geometria de graça.** Ele recusa o que a exportação de malha aceita, porque o formato exige malha manifold. Serve como confirmação independente do portão topológico.

   **Correção de 07/09/2026, após revisão externa.** A versão anterior deste documento dizia que o escritor de 3MF foi o *único* portão a pegar o defeito descrito abaixo. Isso estava errado, e o erro era meu, não da medição. O portão de malha da varredura **media** as arestas não-manifold e a estanqueidade, e **não as usava na decisão**: aprovava variante com seis arestas não-manifold. Os dados tinham pegado o defeito; a decisão os ignorou. Com o portão corrigido, malha e 3MF reprovam as mesmas quatro variantes. Isto é exatamente o defeito que este projeto existe para evitar, um portão incapaz de revelar o erro que ele guarda, e eu o construí.
7. **Coincidência paramétrica produz contato tangente, e o defeito é a igualdade, não o valor.** Duas encontradas no mesmo exemplo sintético:

   **Topo do furo contra topo da nervura**, com altura 50, diâmetro 5, parede 4:

   | topo do furo | topo da nervura | arestas não-manifold | 3MF |
   |---|---|---|---|
   | 30,0 mm | 30,0 mm | 2 | recusa |
   | 29,5 mm | 30,0 mm | **4** | recusa |
   | 27,5 mm | 30,0 mm | 0 | aceita |

   Deixar meio milímetro de material foi **pior** que a tangência exata.

   **Diâmetro do furo contra espessura da parede que ele atravessa:**

   | caso | arestas não-manifold | 3MF |
   |---|---|---|
   | diâmetro 4, parede 4 | 6 | recusa |
   | diâmetro 5, parede 5 | 6 | recusa |
   | diâmetro 3, parede 4 | 0 | aceita |
   | diâmetro 6, parede 4 | 0 | aceita |

   Reproduz em dois valores absolutos diferentes. O que quebra é o furo tangenciar as duas laterais da parede ao mesmo tempo.

8. **Por isso a varredura da família não é luxo.** O mesmo código saiu limpo num valor de parâmetro e defeituoso no vizinho. Na grade de seis variantes, quatro reprovaram. Uma grade finita testa pontos, não a família: nada é afirmado sobre valores entre os pontos ou fora deles.

### Fatiador em linha de comando

9. **A receita que funciona, na ordem em que os erros apareceram.** Cada tentativa produziu um erro diferente:

   | tentativa | resultado |
   |---|---|
   | perfil do sistema direto | processo incompatível com a impressora |
   | achatar a herança e remover o campo de origem | campo de origem não suportado |
   | trocar a origem para usuário e zerar compatibilidade | falha muda, sem mensagem |
   | **achatar a herança e não tocar em mais nada** | **funciona** |

   Metadados fazem parte da identidade do perfil. Remover qualquer um torna o conjunto incompatível.

10. **O executável é um aplicativo gráfico do Windows.** Não escreve no console em chamada normal, e caminho com espaço é partido na passagem de argumentos. A ferramenta copia tudo para diretório sem espaço e redireciona a saída para arquivo.
11. **O detalhe do erro vai para o log, não para a saída de erro.** E o log é escrito no diretório atual, não no de saída. Rodar com o diretório atual apontado para a área de trabalho resolve, e para de sujar a pasta do projeto.
12. **Sem tela, o fatiador sempre reclama de gráficos e de miniatura.** Quatro linhas de ruído benigno por execução, filtradas por lista.
13. **Códigos de saída observados**, em complemento de dois, com a mensagem do programa sempre igual e inútil:

    | código | visto quando |
    |---|---|
    | 0 | sucesso |
    | −5 | faltava o campo de origem no perfil |
    | −17 | conjunto de perfis incompatível |
    | −50 | peça maior que o envelope |

    O log traduz o −50: nada a fatiar, porque nenhum objeto está inteiramente dentro do volume de impressão.

### Folga de encaixe

14. **O registro de calibração existente cobre qualidade, não dimensão.** Tem temperatura, avanço de pressão, chapa e estado por rolo. Não tem uma única folga de encaixe. A ferramenta lê esse registro para saber o que está calibrado, e mantém um registro próprio de folgas que **começa vazio**.
15. **Há pendência dimensional aberta no registro**, de sobre-extrusão declarada e calibração não concluída. Erro de vazão muda dimensão, então qualquer folga medida antes de fechar isso carrega o erro. A ferramenta avisa e sugere marcar a medição como provisória.
16. **A entrada de exemplo foi apagada.** Usei uma folga de 0,22 mm para demonstrar o ciclo de registro e removi em seguida. Número inventado não fica em registro, nem como exemplo.

## Verificação de intenção: o teste que importa

O verificador foi rodado contra o exemplo paramétrico com nove requisitos declarados, sendo **um deles errado de propósito**: declara um furo em 20,0 mm quando ele está em 15,75 mm.

| Requisito | Resultado |
|---|---|
| dimensões externas | aprovado, medido 60 × 45 × 50 mm |
| corpo único | aprovado |
| dois furos na base | aprovado, contou 2 |
| furo dianteiro em 15,75 | aprovado, centro medido em 15,75, diâmetro 4,999 |
| furo traseiro em 33,75 | aprovado, centro medido em 33,75, diâmetro 4,999 |
| distância entre furos, 18,0 | aprovado, medido 18,0 |
| **furo declarado em 20,0** | **reprovado, erro de posição 4,250 mm** |
| parede mínima | não verificado, tipo não implementado |
| silhueta | não verificado, tipo não implementado |

O erro plantado foi pego com o valor exato. O diâmetro medido de 4,999 contra 5,000 é a aproximação da circunferência por cordas na malha, e não um defeito da peça.

Os dois não implementados aparecem como não verificados, com o motivo. **Requisito não verificado não é requisito atendido**, e a entrega diz isso em vez de calar.

## Resultados de referência

| Peça | Portão de malha | Fatiador | Tempo | Massa |
|---|---|---|---|---|
| Cubo 40 × 30 × 20 | aprovado | aprovado | 1.674 s | 8,86 g |
| Exemplo paramétrico | aprovado | aprovado | 3.737 s | 19,40 g |
| Abrigo de 300 mm | aprovado | **barrado**, estoura a altura | — | — |
| Peça-fonte do caso 1 | **barrado**, 99 arestas não-manifold | não testado | — | — |

O caso 1 barrando é o ponto: foi exatamente sobre essa malha que a operação booleana original foi feita sem reparo.

## Revisão externa de 07/09/2026 e o que ela corrigiu

Um revisor independente leu estes arquivos e apontou seis defeitos de código e cinco conclusões excessivas. Conferi cada um por inspeção direta. **Todos procedem.** Nenhum era falso positivo.

| Defeito | Onde estava | Correção |
|---|---|---|
| Portão de malha aprovava malha que ele próprio media como inválida | decisão da varredura | passou a exigir zero aresta não-manifold e estanqueidade |
| Aprovação do fatiador ignorava os próprios motivos de reprovação | decisão do portão do fatiador | separado em processo concluído, saída gerada e checagens aprovadas; aprovado exige os três |
| Exclusão recursiva do caminho recebido por argumento | preparação da área de trabalho | subpasta exclusiva por execução, com marcador de propriedade; nada é apagado sem o marcador |
| Comentário afirmava preservar precisão dupla, e não preservava | ponte para o kernel de malha | passou a usar a classe de precisão dupla, e o resultado declara qual caminho foi usado |
| Máquina e material ausentes funcionavam como curinga, e o resultado dizia "medido nesta máquina" | consulta de folga | resposta aplicável só com os dois informados e casados; sem isso, aplicabilidade indeterminada |
| Caminho do registro da oficina fixo no código | consulta de folga | virou argumento; a ausência do registro não impede a consulta |

Conclusões excessivas retiradas: inclinação e área não estabelecem função de face; o fator de anisotropia não é universal e agora carrega material e contexto; área de seção é critério geométrico e não conclusão estrutural; fatiar afirma que o fatiador produziu saída naquelas condições; e grade finita testa amostras, não a família.

**A lição que fica.** Script determinístico também produz interpretação errada com confiança. A diferença é que o erro fica no código, onde alguém pode achar. Foi o que aconteceu.

## Os seis casos de generalidade

Executados em 07/09/2026, seis de seis passam. Detalhe e números na seção 8 do `DESENHO.md`.

O que a construção deles ensinou, além de passar:

1. **Interferência é entre partes, não entre o todo e a parte.** O caso 3 reprovou na primeira execução porque eu declarei a interferência da montagem inteira contra um componente dela, e a montagem contém o componente, então sempre acusa. O verificador ganhou a forma `entre`, com dois arquivos, e a forma antiga ficou só para comparar contra a peça principal.
2. **Contar corpos sem soldar vértices dá número absurdo.** O caso 3 reportou **1508 corpos** numa montagem de duas peças, porque a concatenação de dois arquivos não compartilha vértices e a divisão por componentes conta grupos de facetas soltas. Soldar antes de contar devolve 2. O número errado estava no meu próprio relatório, não na verificação.
3. **O caso da superfície tem proteção dupla.** A finalidade visualização dispensa o fatiador e a representação superfície também. Nenhuma mutação de um eixo só reprova esse caso, então ele prova a conjunção e não cada eixo. Isolar a representação exigiu inventar a classificação superfície para impressão.

## Segunda revisão externa, 07/09/2026

Um revisor independente executou a suíte numa cópia isolada, conferiu que nenhum dos 63 arquivos originais foi alterado, e apontou catorze pontos: um de sigilo, dez de integração e três menores. Conferi cada um por inspeção direta. **Todos procedem.**

O padrão comum aos dez pontos de integração é um só: **a ferramenta mede e o executor não usa.** As correções da primeira revisão existiam dentro de cada ferramenta, e a integração entre elas ainda conseguia transformar evidência incompleta em aprovação.

| Achado | Correção |
|---|---|
| Dados do projeto privado em material distribuível | removidos; pacote por lista de permissão com auditoria que barra |
| Verificação obrigatória não executada permitia aprovação | cinco estados por verificação; ausente e erro bloqueiam |
| Executor usava dois campos do portão de malha e descartava o veredito | consome o veredito completo; faces invertidas passavam antes |
| Erro na inspeção do 3MF não virava motivo de reprovação | falha de leitura, ausência de metadados e ausência de G-code viram motivo |
| Exceção em mutação contava como detecção | estado inválido separado; mutação declara onde espera a reprovação |
| Mutação do datum alterava o relatório, não a geometria | passa a mudar a construção, exportar e remedir |
| Caso de reconstrução rotulava constante como medida | o diâmetro sai de medição real da seção; cotas não usadas identificadas |
| Montagem aprovava intercâmbio verificando uma peça só | intercâmbio com os dois componentes; contagem declarada e conferida |
| Furo aprovava área equivalente como se fosse diâmetro e eixo | circularidade entra na decisão; segunda seção confere extensão |
| Classificação de seção errava com ilha de material dentro de cavidade | paridade de profundidade de aninhamento resolve o caso |
| Proposta de corte tratada como partição validada | pedaços são medidos; partição só é validada se todos couberem |
| Registro de folgas contradizia o próprio aviso de bloqueio | pendência aberta invalida aplicabilidade; estado da medição gravado |
| Requisito malformado podia ser aprovado parcialmente | esquema validado antes de medir; malformado reprova |
| Ambiente da oficina fixo no código, dados dentro do pacote | ambiente configurável; medições gravadas fora do pacote |

**A afirmação que eu tinha errado.** Eu havia escrito que a mutação da superfície era pega por reprovação no fatiador. A saída da própria execução mostrava o contrário: o fatiador **aceita** casca aberta, e quem reprova é a estanqueidade.

**Prova de que o bloqueio funciona no caminho real.** Rodando a suíte com `--sem-fatiador`, os dois casos de impressão ficam incompletos e reprovam por falta de evidência, em vez de passar calados.

## Terceira revisão externa, 07/09/2026

Dezesseis achados: um de sigilo parcial, doze P1 e três P2. Conferi cada um por inspeção direta. **Todos procedem.**

O padrão foi o mesmo da segunda revisão, agora um nível acima: as correções existiam dentro de cada ferramenta, e a **integração** entre elas ainda transformava evidência ausente, inválida ou parcial num nome de aprovação.

| Achado | Correção |
|---|---|
| Empacotador copiava para destino existente sem auditar o resultado, e o modo de só auditar era ignorado | exige destino vazio, audita inventário e conteúdo do que ficou, recusa auditar junto com montar, e recusa interseção entre permitidos e negados |
| Auditor não reconhece a classe numérica de vazamento que motivou a correção | passou a dizer "nenhum padrão conhecido encontrado" em vez de "liberado", e a exigir os padrões locais para autorizar publicação |
| Obrigação resolvida por pedaço de texto no identificador aprovava por ausência de nome | obrigação mapeada por **tipo** de requisito, exigindo pelo menos uma evidência válida do tipo |
| Estado devolvido pelo verificador não era validado | valor fora do contrato vira erro |
| Erro operacional na medição virava reprovação, e mutação recebia crédito por falha de execução | estado de erro distinto de ponta a ponta |
| Modalidade de parametrização quebrada: a varredura montava o resultado e nunca o imprimia | passou a imprimir, e o caso 7 exercita o caminho pelo executor real |
| Booleanas de intenção não conferiam o status do kernel | status conferido em cada operando e em cada resultado |
| Segunda seção do furo ignorava a forma | circularidade das duas seções entra na decisão, e a afirmação de continuidade foi retirada |
| Resíduo de planaridade era medido e não decidia | resíduo comparado com a tolerância; o que não passa sai dos candidatos |
| Oráculo do datum não detectava inclinação invertida | comparação entre normais orientadas, mais controle contra o ângulo do gerador |
| Envelope inválido virava partição validada sem nenhum corte | envelope útil tem que ser positivo e finito; partição vazia não é validada |
| Contratos por representação não chegavam aos verificadores | intercâmbio e varredura passaram a ter contrato por representação; casos 8 e 9 provam |
| Folga com estado ausente ou valor não finito podia ser recomendada | validação de finitude e estados explícitos; medição contaminada por pendência não volta a valer |
| Escrita podia sobrescrever a entrada | recusa quando entrada e saída são o mesmo arquivo |
| Portão do fatiador confundia presença de campo com evidência | exige metadados mínimos e G-code não vazio; envelope desconhecido fica desconhecido; herança não resolvida é erro |
| Ambiente e proveniência não reproduzíveis | manifesto de ambiente no pacote, adaptador completo repassado, e hashes de modelo, perfis, saída e executável na evidência |
| Conclusões corrigidas num trecho e mantidas em outro | revisadas: imprimibilidade, tração, acoplamento inclinado, e o acento em "não validado" que classificava como validada |

**O defeito factual mais sutil.** A classificação do estado de calibração procurava a negação **sem acento** e a afirmação por pedaço de texto. Uma linha escrita como não validada, com acento, passava a negação, casava a afirmação e era classificada como **validada**. O registro atual usa texto sem acento, então o erro não aparecia, mas a conclusão estava errada por construção. Agora o texto é normalizado.

## Quarta revisão externa, 07/09/2026

Oito achados: quatro bloqueadores e quatro de contrato. Conferi cada um por inspeção direta. **Todos procedem.** Quarta rodada seguida sem um único falso positivo.

| Achado | Correção |
|---|---|
| Varredura reaproveitava o relatório de outra execução, porque o arquivo temporário usava só o identificador do processo | arquivo exclusivo por chamada, e a identidade de módulo, função e grade é conferida no resultado |
| O relatório do empacotador era gravado depois da auditoria do destino | recusa relatório dentro do destino e recusa nome que colida com arquivo do pacote |
| Envelope com valor presente e inválido virava aprovação | exige finitude, positividade e área com pelo menos três vértices utilizáveis |
| Erro operacional na varredura contava como reprovação geométrica | estado operacional por variante, propagado como erro |
| Identificadores repetidos sobrescreviam evidência no mapa de obrigações | identificador repetido é especificação inválida, e o mapa virou lista |
| Superfície paramétrica ainda era obrigada a ser fechada | os três portões da varredura vêm da representação; caso 10 prova |
| Mutações apagavam diretórios temporários que não provaram ter criado | diretório exclusivo por teste, removido pelo próprio gerenciador |
| Campo de autorização contradizia a conclusão cautelosa | o campo foi removido; a ferramenta declara que não emite autorização de publicação |

**Duas falhas nos meus próprios oráculos novos**, achadas ao rodá-los. A comparação da mensagem do empacotador dependia de caixa alta. E o julgamento das mutações invalidava o experimento quando o erro era a consequência esperada do defeito plantado. Erro esperado e erro de infraestrutura passaram a ser declarados separadamente.

## Ambiente

| Pacote | Versão |
|---|---|
| build123d | 0.11.1 |
| núcleo geométrico | 7.9.3.1.1 |
| escritor de 3MF | 2.5.0 |
| trimesh | 5.0.0 |
| manifold3d | 3.5.2 |
| shapely | 2.1.2 |
| fatiador | OrcaSlicer 2.4.2 |

**Ausentes e que nenhum script pode exigir:** `rtree`, `matplotlib`, `fast_simplification`.

A pesquisa mostrou que pacote de modelagem por código já chegou quebrado ao repositório público por causa de versão frouxa do núcleo geométrico, e que atualizar o núcleo no lugar quebra o ambiente. A skill precisa travar versão exata e nunca atualizar sobre a instalação existente.
