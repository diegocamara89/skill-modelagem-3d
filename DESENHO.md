# Desenho da skill de projeto 3D

Versão 2, de 07/09/2026. Substitui a versão 1, que era uma espinha única de sete etapas com viés de impressão.

A versão 1 tratava todo projeto como reconstrução de peça para impressão. Isso vinha de um caso real de fracasso e ficou indexado nele. Duas revisões independentes apontaram o mesmo problema por caminhos diferentes: a arquitetura estava confundindo modalidade, representação e finalidade num único caminho obrigatório.

Esta versão separa as três.

---

## 1. As três decisões

Toda tarefa de modelagem responde três perguntas independentes. Elas não se implicam.

### Decisão A: o que fazer com a geometria

| Modalidade | Significa |
|---|---|
| `criar` | não existe geometria de partida |
| `editar` | alterar uma região preservando o resto |
| `reconstruir` | refazer a partir de referência, com informação incompleta |
| `reparar` | consertar arquivo problemático sem redesenhar |
| `parametrizar` | transformar geometria fixa em família controlada |

### Decisão B: em que representação trabalhar

| Representação | Quando |
|---|---|
| `solido` | cota importa, encaixe importa, alguém vai editar depois |
| `superficie` | casca sem espessura, forma visual, painel |
| `malha` | dado de escaneamento, forma orgânica, reparo, booleana que não pode falhar |
| `montagem` | mais de um corpo com posição relativa e movimento |

### Decisão C: para que serve o resultado

| Finalidade | Significa |
|---|---|
| `visualizacao` | render, imagem, apresentação |
| `intercambio` | entregar geometria para outra pessoa ou outro programa |
| `montagem` | conferir posição, folga e interferência entre partes |
| `impressao_fdm` | vai para a impressora de filamento |
| `usinagem` | vai para máquina subtrativa |

**A regra que faz a separação valer:** as três decisões escolhem quais módulos e quais verificações são acionados. Nada mais. Uma superfície decorativa para render não aciona folga calibrada, malha estanque, direção de carga nem fatiador. Uma peça de encaixe para impressão aciona todos.

A modalidade `reconstruir` deixa de ser o eixo da skill e passa a ser uma das cinco. A finalidade `impressao_fdm` deixa de ser o caminho único e passa a ser uma das cinco.

---

## 2. O núcleo, que roda sempre

Sete passos, curtos, independentes de modalidade, representação e finalidade.

1. **Classificar.** Responder as três decisões. Se o pedido não determina alguma, escolher o padrão razoável e dizer qual foi.
2. **Perguntas de bloqueio.** De três a cinco, e elas dependem da classificação. Só entra aqui o que, sem resposta, torna o trabalho impossível ou inseguro. Nada de questionário longo.
3. **Declarar a representação do problema.** O que está sendo feito, quais referências são autoridade, e qual requisito invalida a geometria se estiver errado. Este artefato é curto e confirmável, e existe para tornar a omissão detectável.
4. **Preservar as entradas.** Nenhuma referência é modificada. Hash de cada entrada registrado antes de qualquer operação.
5. **Executar.** Com o módulo da representação escolhida.
6. **Verificar.** Dois eixos, descritos na seção 4: a geometria é válida, e a geometria atende ao pedido. O nível exigido vem da finalidade.
7. **Entregar.** Fonte editável, resultados e evidências, com a proveniência da seção 5.

**O que o núcleo não faz:** não decide função de face, não crava folga, não conclui resistência, não afirma que algo vai encaixar. Isso é seção 6.

---

## 3. Os módulos, acionados pela classificação

| Módulo | Acionado por | Conteúdo |
|---|---|---|
| CAD paramétrico | representação `solido` | build123d, referências geométricas, operações, parâmetros, varredura de família |
| Malha e superfície | representação `malha` ou `superficie` | validade topológica, reparo, booleana de malha, precisão declarada |
| Edição e reconstrução | modalidade `editar`, `reconstruir` ou `reparar` | importação, extração de datums, alinhamento rígido, regiões protegidas, comparação com referência |
| Montagens | representação `montagem` | componentes, posicionamento, interferência, folga entre partes |
| Fabricação FDM | finalidade `impressao_fdm` | orientação, envelope, partição, fatiador, materiais, anisotropia |
| Usinagem | finalidade `usinagem` | intercâmbio, acesso de ferramenta, cota crítica |
| Adaptador de oficina | ambiente local | caminhos, perfis do fatiador, registro de calibração da máquina, folgas medidas |

**O adaptador é a parte que não viaja.** Perfis do fatiador, registro de filamentos e folgas medidas são desta oficina. A ausência do adaptador reduz o que a skill pode afirmar, e não impede modelagem. Quem instalar a skill em outra máquina começa sem adaptador e a skill diz isso, em vez de usar número de outra pessoa como se fosse seu.

---

## 4. Verificação, em dois eixos

Este é o ponto onde a versão 1 estava mais fraca. Ela verificava validade e quase não verificava intenção.

### Eixo 1: validade

A geometria é bem formada. Sólido existe, volume positivo, malha sem aresta aberta, orientação consistente, precisão declarada.

### Eixo 2: intenção

A geometria atende ao pedido. **Uma peça pode estar fechada, fatiar bem e ter o furo no lugar errado.** Nenhuma verificação de validade pega isso.

A intenção é verificada contra requisitos declarados. Cada requisito carrega o seu próprio método de verificação, ou é marcado como não verificável automaticamente, e nesse caso a entrega diz que ele não foi verificado.

Tipos de requisito com verificação mecânica:

| Tipo | O que confere |
|---|---|
| `caixa` | dimensões externas, com tolerância |
| `volume` | volume, com tolerância |
| `n_solidos` | quantidade de corpos |
| `furo` | existência, posição, diâmetro e eixo |
| `n_furos_no_plano` | quantidade de furos numa face |
| `distancia` | entre duas referências declaradas |
| `parede_minima` | espessura mínima numa região |
| `regiao_intacta` | uma região não mudou em relação à referência |
| `interferencia` | dois corpos não ocupam o mesmo espaço |
| `folga_entre` | folga entre dois corpos, contra valor calibrado |
| `silhueta` | comparação com imagem de referência |

Requisito sem verificação declarada **não é ignorado**: aparece na entrega na lista de não verificados.

### A matriz de nível por finalidade

Isto é o mecanismo que impede a impressão de contaminar todo projeto.

| Verificação | visualizacao | intercambio | montagem | impressao_fdm | usinagem |
|---|---|---|---|---|---|
| intenção contra requisitos | sim | sim | sim | sim | sim |
| sólido existe, volume positivo | sim | sim | sim | sim | sim |
| malha estanque | não | não | não | sim | não se aplica |
| zero aresta não-manifold | não | não | não | sim | não se aplica |
| portão do fatiador | não | não | não | sim | não |
| envelope e partição | não | não | não | sim | sim |
| folga calibrada | não | não | sim | sim, se houver encaixe | sim |
| orientação e anisotropia | não | não | não | sim | não |
| intercâmbio reabre em CAD | não | sim | sim | não | sim |

---

## 5. Proveniência da entrega

Quatro níveis, e o primeiro é o que permite alterar o projeto depois.

| Nível | O que é |
|---|---|
| Fonte editável | código, parâmetros, versões travadas, entradas com hash |
| Resultado CAD | intercâmbio exportado daquela execução |
| Resultado de malha | derivado do resultado CAD, com tolerância declarada |
| Evidências | verificações amarradas aos hashes dos três acima |

A versão 1 chamava o intercâmbio de fonte da verdade. Isso estava errado para um fluxo de modelagem por código: promover o intercâmbio a fonte perde a capacidade de alterar o projeto. O intercâmbio é o resultado autoritativo de uma execução, e o código é a fonte.

---

## 6. As zonas de não afirme

A skill não emite estas afirmações, em nenhuma modalidade.

- **Função de face.** Área, inclinação e planaridade são propriedades geométricas. Qual região é assento, apoio ou acabamento vem dos requisitos.
- **Encaixe físico.** Nada encaixa até alguém imprimir e testar. A skill pode dizer que reproduziu a forma de um arquivo que já encaixou, e nada além disso.
- **Folga sem cupom.** Faixa publicada é ponto de partida do cupom, não valor de projeto. Duas fontes de qualidade discordam em uma categoria inteira.
- **Resistência.** A união entre camadas é mais fraca que o material no plano, e a razão medida em alguns materiais ficou em torno de metade. Isso não é constante universal e não substitui avaliação estrutural.
- **Norma que não foi obtida.** Se a skill não leu a norma, ela diz que não leu, em vez de citar valor de segunda mão.
- **Segurança para ser vivo, contato com alimento ou uso sob carga.** Fora de escopo, e dito como fora de escopo.
- **Validade de família a partir de grade finita.** Grade testa pontos. Nada é afirmado sobre os valores entre eles.

---

## 7. Ferramentas

Sete existem e estão validadas. Uma é nova nesta versão.

| Ferramenta | Módulo | Estado |
|---|---|---|
| `find_datums.py` | edição e reconstrução | validada |
| `align_rigid.py` | edição e reconstrução | validada |
| `check_mesh.py` | malha e superfície | validada |
| `sweep_params.py` | CAD paramétrico | validada |
| `split_for_volume.py` | fabricação FDM | validada |
| `slice_check.py` | fabricação FDM | validada |
| `tolerance_lookup.py` | adaptador de oficina | validada |
| `check_intent.py` | núcleo, eixo 2 | **nova** |

Toda ferramenta devolve, junto do resultado, o que ela não decidiu. Toda ferramenta que reprova devolve o motivo em texto que o operador entende.

**Regra que a revisão de 07/09/2026 tornou obrigatória:** se a ferramenta mede uma métrica, a decisão dela usa essa métrica. Construí um portão que media arestas não-manifold e não as usava para reprovar. Métrica medida e não usada é pior que métrica ausente, porque produz aprovação com aparência de rigor.

---

## 8. Casos de teste da generalidade

A versão 1 foi testada só em sólido para impressão, que é justamente o viés a remover. A arquitetura não é chamada de geral antes de passar nestes seis.

Construídos e executados em 07/09/2026. **Seis de seis passam.** Toda geometria é sintética, gerada por `casos.py`.

| Caso | Classificação | Exigidas / dispensadas | Resultado |
|---|---|---|---|
| 1. Peça dimensional do zero | criar, sólido, impressão | 8 / 1 | aprovado, fatiador com código 0 |
| 2. Edição localizada | editar, sólido, intercâmbio | 5 / 6 | aprovado, região preservada com divergência zero |
| 3. Montagem com dois corpos | criar, montagem, montagem | 6 / 5 | **barrado na folga, como esperado** |
| 4. Superfície aberta para render | criar, superfície, visualização | 2 / 7 | aprovado, e a malha **não** é fechada |
| 5. Reconstrução incompleta | reconstruir, sólido, impressão | 10 / 1 | aprovado, datum inclinado preservado com erro de 0,0° |
| 6. Projeto simples | criar, sólido, visualização | 2 / 7 | aprovado em 0,02 s, sem fatiador |
| 7. Família paramétrica | parametrizar, sólido, impressão | 9 / 2 | aprovado, seis variantes varridas |
| 8. Superfície em intercâmbio | criar, superfície, intercâmbio | 3 / 8 | aprovado, zero sólidos e uma face |
| 9. Montagem paramétrica | parametrizar, montagem, montagem | 7 / 4 | barrado na folga, como esperado |
| 10. Superfície paramétrica | parametrizar, superfície, visualização | 3 / 8 | aprovado, e a malha é aberta |

O caso 10 entrou depois da quarta revisão, que apontou que a representação mudava apenas o **primeiro** portão da varredura: o segundo continuava exigindo estanqueidade e o terceiro sempre escrevia o formato que exige malha fechada, então superfície aberta legítima reprovava sempre. Agora os três portões vêm da representação, e para superfície o portão do formato fechado é declarado como não aplicável em vez de reprovar.

Os casos 7, 8 e 9 entraram depois da terceira revisão externa, que apontou três combinações legítimas de classificação que o código não suportava. A modalidade de parametrização estava **quebrada na comunicação com o executor**: a ferramenta montava o resultado estruturado e nunca o imprimia, então toda varredura devolvia falta de saída, e nenhum dos seis casos anteriores exercitava esse caminho. Superfície em intercâmbio reprovava porque a verificação exigia sólido, e uma casca correta tem zero sólidos. E montagem paramétrica reprovava porque a varredura exigia exatamente um sólido em qualquer caso.

O contrato de intercâmbio agora vem da representação. Para sólido e montagem é a contagem de sólidos declarada. Para superfície é presença de faces com zero sólidos, porque contar zero sólidos sozinho não seria evidência de que a casca existe.

O caso 5 mede de verdade: o diâmetro do furo sai de uma seção da referência, medido em 7,9985 mm contra 8,0 nominal. A primeira versão desse caso rotulava uma **constante do gerador** como medida, e a verificação de proveniência, que só conferia existência de rótulo, aprovava um rótulo inventado. O caso agora também identifica as cotas registradas e **não usadas** na construção, que eram três.

O caso 3 entrega um intercâmbio com os **dois** componentes e declara quantos espera encontrar ao reabrir. A primeira versão entregava o arquivo de um componente só, e a verificação aprovava por achar algum sólido.

**O caso 3 é barrado de propósito.** Ele declara um encaixe deslizante, e não existe folga medida em cupom para aquela máquina e material. O resultado esperado é bloqueio, não aprovação. Um caso que só sabe passar não testa a honestidade do mecanismo.

**O caso 5 é o mais direto contra o fracasso de origem.** A referência sintética tem um assento inclinado a 17,0°. O extrator recuperou 17,0°, a reconstrução usou esse ângulo relativo em vez de um eixo, e o assento reconstruído ficou com erro de 0,0°. Oito cotas foram registradas e **cinco** entram na construção. As três restantes aparecem no resultado como registradas e não usadas, porque cota registrada e não usada é ruído no rastro de proveniência. A versão anterior deste documento dizia oito usadas, e estava errada.

O oráculo do datum também mudou. Comparar apenas o ângulo com o eixo vertical descarta o sentido da inclinação e o azimute: uma reconstrução com a inclinação **invertida** conservava o mesmo ângulo, a mesma caixa e o mesmo número de corpos, e o erro dava zero. Agora a comparação é entre as normais orientadas, e há um controle independente que confronta a leitura do extrator com o ângulo conhecido do gerador, para que duas leituras erradas pelo mesmo método não concordem entre si e passem.

### Teste de mutação

Suíte que só sabe passar não testa nada. **Vinte e quatro** defeitos foram introduzidos de propósito, um por vez. **Vinte e quatro de vinte e quatro foram pegos, e cada um no verificador que a mutação previu.**

O experimento tem três estados, não dois. **Pegou** exige reprovação exatamente onde a mutação previu. **Escapou** é passar apesar do defeito, ou reprovar em lugar diferente. **Inválido** é erro de execução, e não conta como detecção, porque o experimento não mediu nada.

| Mutação | Onde a reprovação foi exigida |
|---|---|
| finalidade visualização passa a exigir o fatiador | caso 6, cobrança indevida no roteamento |
| superfície para impressão perde a dispensa de representação | caso 4b, reprovação na estanqueidade |
| finalidade impressão deixa de exigir o fatiador | caso 1, falta no roteamento |
| verificador obrigatório retirado do registro | caso 1, bloqueio por evidência ausente |
| caixa declarada com 2 mm de erro | caso 1, na intenção |
| furo central declarado 3 mm fora | caso 1, na intenção |
| abertura quadrada com a mesma área e o mesmo centro do furo | caso 1c, na intenção, pela forma |
| reconstrução alinhada por eixo, com a geometria realmente mudada | caso 5b, no extra do datum |
| região editada declarada como intacta | caso 2, na intenção e na região |
| intercâmbio da montagem com um componente só | caso 3b, na contagem ao reabrir |
| partição deslocada que estoura o envelope | caso 1b, na partição |
| verificador devolve estado fora do contrato | caso 1, erro por estado inválido |
| requisito de preservação com identificador neutro | caso 2, na obrigação de preservação |
| caso sem nenhum requisito de preservação | caso 2, bloqueio por ausência de evidência |
| reconstrução com a inclinação invertida | caso 5c, na comparação de normais |
| destino de pacote previamente contaminado | o empacotador recusa e não copia nada |
| perfil de máquina sem envelope | envelope fica desconhecido, não aprovado |
| medição de folga sem estado explícito | não conta como definitiva |
| grade com variante geometricamente inválida | caso 7b, na varredura |
| varredura reaproveitando evidência de execução anterior | erro, e a identidade da execução é conferida |
| erro operacional em variante da varredura | erro, e não reprovação geométrica |
| relatório gravado dentro do destino do pacote | o empacotador recusa antes de copiar |
| perfil com envelope de valor inválido | o envelope não vira aprovação |
| dois requisitos com o mesmo identificador | especificação inválida, e a obrigação vira erro |

**Um refinamento do próprio julgamento das mutações.** Antes, qualquer erro de verificação invalidava o experimento, inclusive quando o erro era a **consequência esperada** do defeito plantado. Erro esperado e erro de infraestrutura são coisas diferentes, e agora a mutação declara onde espera erro. Só o erro imprevisto invalida.

**Correção de uma afirmação errada.** A versão anterior deste documento dizia que a mutação da superfície era pega **por reprovação no fatiador**. Isso era falso, e a saída da própria execução mostrava. Medido: sem a dispensa de representação, o fatiador **aceita** a casca aberta e não reprova. Quem reprova são a estanqueidade, a orientação e o não-manifold. A mutação agora exige a reprovação na estanqueidade, que é o mecanismo real.

**Achado que a mutação revelou.** O caso 4 tem proteção **dupla**: a finalidade visualização já dispensa o fatiador, e a representação superfície também. Nenhuma mutação de um eixo só o reprova, então o caso 4 sozinho prova a conjunção e não cada eixo isoladamente. Para isolar a representação foi preciso a classificação superfície declarada para impressão, onde a finalidade exigiria o fatiador e só a representação dispensa. É o caso 6 que prova a separação por finalidade, e o caso 4b que prova a separação por representação.

### Quatro brechas que sobreviveram até a quarta rodada

Todas tinham a mesma forma das anteriores, mas um passo mais fundo: **evidência antiga, inválida ou de outra origem recebia um nome de aprovação.**

A varredura gravava o resultado num arquivo nomeado só pelo identificador do processo, e o reaproveitava. Uma varredura aprovada criava o arquivo, a seguinte falhava antes de gravar outro, e a leitura de reserva devolvia a aprovação **anterior**. Agora o arquivo é exclusivo por chamada e a identidade da execução, com módulo, função e grade, é conferida no que voltou.

O relatório do empacotador era gravado **depois** da auditoria do destino. Apontado para dentro do pacote, criava arquivo não permitido depois de conferir o inventário; apontado para um nome de código, sobrescrevia o que já havia sido auditado. Agora as duas situações são recusadas antes de qualquer cópia.

O envelope aceitava valor **presente e inválido**. Altura não finita passava pela conversão e a comparação com ela é sempre falsa; área com um ponto só dava largura zero e o teste de planta era pulado. Nada ficava marcado como desconhecido, então o resultado dizia que a peça cabe, com a lista de problemas vazia. A correção anterior tratava só a **ausência** de dimensão.

E erro operacional na varredura entrava na contagem de reprovações como se fosse reprovação geométrica. Agora cada variante carrega estado operacional próprio, e o executor devolve erro em vez de reprovação.

### O contrato tipado de resultado

Esta é a correção central da terceira revisão. O padrão dos defeitos era sempre o mesmo, com dez rostos: **evidência ausente, inválida ou parcial recebia um nome de aprovação.**

Cada verificação devolve um estado do contrato, e o estado devolvido é **validado**: valor fora do contrato vira erro em vez de passar por nenhuma lista. Cada obrigação do roteamento é satisfeita por um **tipo** de requisito, e exige pelo menos uma evidência válida daquele tipo. Antes, a obrigação era resolvida filtrando identificadores por pedaço de texto, então um requisito de preservação com identificador neutro reprovava e a obrigação aparecia aprovada, e remover o requisito por completo também aprovava, porque a lista filtrada ficava vazia. Identificador identifica requisito; não é linguagem de classificação.

Erro operacional é distinto de rejeição geométrica de ponta a ponta. Antes, uma exceção na medição virava requisito não verificado, indistinguível de tipo sem medidor, e uma mutação que só exigia reprovação podia receber crédito por falha de dependência.

### Cinco estados por verificação, não dois

Aprovada, reprovada, ausente, erro e não aplicável são coisas diferentes. A versão anterior do executor decidia só por reprovações e deixava as não executadas de fora, então **um verificador ausente não impedia a aprovação do caso**. Agora verificação obrigatória sem resultado válido bloqueia, e não aplicável só vale se o caso a declarou.

Isso é demonstrável: rodando a suíte sem o fatiador, os dois casos de impressão ficam **incompletos** e reprovam por falta de evidência, em vez de passar calados. Quem instalar a skill sem fatiador roda o subconjunto independente de máquina e é informado de quais casos ficaram sem verificar.

### Sigilo do material distribuível

O pacote é montado por **lista de permissão** explícita, com auditoria que barra a montagem se encontrar dado do projeto privado do autor em arquivo permitido.

A primeira tentativa empacotava por exclusão, e uma revisão externa encontrou o nome de um arquivo de referência real, o hash dele, cotas, e uma normal e um centroide reais dentro do exemplo de uso de uma **ferramenta**, que é material distribuído. Empacotar por exclusão publica tudo o que caiu na pasta, incluindo saída de execução contra arquivo real.

Os padrões que reconhecem o projeto a proteger ficam num arquivo **local**, fora do pacote, porque publicar o auditor com eles dentro seria o próprio vazamento que ele existe para impedir. Sem esse arquivo, o auditor cai para padrões genéricos e declara que caiu, e não autoriza publicação.

**O que a auditoria afirma, e o que ela não afirma.** Ela afirma que nenhum **padrão conhecido** foi encontrado nos arquivos permitidos. Isso não é prova de ausência de dado privado. O auditor só acha o que os padrões descrevem, e conjuntos numéricos como normais, centroides e cotas não têm padrão textual: reintroduzir só esses números num exemplo com nomes genéricos passaria. Fechar essa lacuna exige amostras de regressão mantidas fora do pacote, e isso ainda não foi construído.

A terceira revisão também achou três brechas na entrega: o modo de somente auditar era declarado e nunca consultado, então auditar junto com montar ainda copiava; as listas de permitidos e negados nunca eram confrontadas, o que tornava a promessa de negação inexequível; e o destino era criado e recebia os permitidos por cima, sem exigir pasta vazia nem auditar o resultado, então um arquivo privado de um pacote anterior continuava lá e a execução ainda declarava pacote limpo. Agora a montagem exige destino vazio, audita o inventário e o conteúdo do que ficou, e reprova depois de copiar se algo sobrar.

### Contrato de ambiente

O pacote passou a carregar um manifesto com as versões exercitadas do interpretador, do motor de modelagem, do núcleo geométrico e das bibliotecas de malha, mais as regras de instalação e o que fazer sem o fatiador. Ele diz também o que **não** foi feito: nada foi testado numa instalação limpa, e todos os resultados registrados usaram as dependências já presentes na máquina de desenvolvimento.

A evidência do fatiador agora carrega os hashes do modelo, dos perfis achatados, do artefato de saída e do próprio executável, porque a limpeza remove a área de trabalho e sem isso uma aprovação não pode ser amarrada aos bytes entregues.

---

## 9. O que ainda não está resolvido

Dito como pendência, não como detalhe.

- **Requisito não geométrico que invalida geometria.** Segurança, toxicidade, ventilação e higienização não são pegos por nenhum script. O desenho os trata por micro-listas acionadas por contexto, e isso ainda não foi construído nem testado.
- **Geometria de junta para peça partida.** A partição propõe onde cortar e não gera macho, fêmea ou pino, porque a folga sai de cupom medido e o registro de folgas está vazio.
- **Verificação de silhueta contra imagem.** Está na lista de tipos de requisito e ainda não tem implementação nesta versão.
- **Detecção de declaração inconsistente.** Quando o que o operador declara contradiz o que a geometria mostra, isso deveria ser detectado e apontado. É validação cruzada, não questionário, e não existe ainda.
