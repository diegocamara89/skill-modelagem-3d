# Plugin de modelagem 3D — plano enxuto

Versão 3, 07/09/2026. Planejamento interno. Substitui o plano M1–M6 anterior; M0 e seus registros permanecem preservados. A implementação inicial passa a ser M1–M3 abaixo.

## Ponto de partida

M0 registrado como concluído: 11 casos e 30 mutações. Não repetir a estabilização nem extrair todos os protótipos para um núcleo novo. Preservar seus scripts e testes; usar os verificadores que as receitas precisarem.

A pasta `base_congelada/arquivos/` é pré-M0. Antes da primeira alteração de protótipos, guardar cópia pós-M0 de fontes e insumos necessários, ambiente e resultados, em `base_pos_m0/`, sem sobrescrever a anterior. Rodar comandos que escrevem em área derivada da cópia. Congelar uma vez, não criar sistema de versionamento próprio.

Se código necessário já estiver em construção, inspecionar e aproveitar; não apagar trabalho só porque a arquitetura mudou. Retirar obrigações futuras de infraestrutura, não remover código alheio sem avaliar uso.

## M1 — Receitas utilizáveis e teste com agente sem contexto

**Objetivo:** provar que instruções suficientes permitem usar ferramentas existentes. Esta é a próxima tarefa autorizada.

Entregas:

1. `SKILL.md` curto e referências condicionais: criação/parametrização simples, inspeção/seleção, edição localizada, verificação e recuperação/exportação.
2. Modelo de registro por trabalho conforme o desenho: entrada, pedido, operação, resultado, identidade, verificações, pendências e próximo passo.
3. Mapa enxuto de ferramentas disponíveis por receita, incluindo dependências e lacunas concretas. CLI existente e MCP do Blender são caminhos válidos; não criar MCP próprio.
4. Cenários sintéticos para repetir os fluxos. Nenhum exemplo privado.
5. `M1_RESULTADO.md` com evidências, falhas, limites e auxiliares necessários para M2.

Aceite:

- Sessão nova de agente recebe somente instruções distribuíveis, cenário sintético e pedido. Conclui uma criação ou alteração paramétrica simples e uma edição localizada suportada, registrando resultado e limites, sem receber histórico desta conversa. O implementador executar a receita sozinho não substitui esse teste; se a sessão nova não estiver disponível, registrar esse aceite como pendente.
- Seleção real com sobreposições desligadas é reconhecida; seleção vazia não dispara edição. O controle positivo com seleção válida segue. Pedido de orientar sem executar é respeitado.
- Deslocamento sintético com direção e distância conhecidas atende à tolerância e preserva região declarada. Alteração errada é detectada no requisito correspondente, sem crédito por outro erro.
- Preenchimento local é inspecionado na junção. Controle defeituoso com ranhura e malha fechada falha na verificação da intenção. Declarar posições e alcance das seções/amostras; não generalizar além delas.
- Seleção capturada seguida de mudança de geometria é relida antes de editar; o caminho sem mudança funciona. Incluir transformação ou modificador quando relevante à receita.
- Undo e redo recuperam assinaturas geométricas anterior e posterior no caminho ensaiado. A retomada a partir do arquivo salvo e registro permite a outro agente identificar pendências sem inferir aprovação da aparência.
- Mudança manual após medição exige nova verificação antes de entregar. Câmera ou sobreposições não são tratadas como mudança geométrica. O resultado medido se vincula ao artefato entregue, quando houver exportação.

Se a ferramenta existente for suficiente, a receita já atende: não criar auxiliar apenas para preencher M2. Se um script mínimo for indispensável ao teste, implementar só esse trecho, identificando a lacuna e testando-o; isso não autoriza a extração ampla do núcleo.


### Obrigação de ensinar o procedimento

Para cada receita, fornecer:

1. Pré-condições e consultas concretas: objeto, modo, seleção, unidades, transformações e capacidades disponíveis.
2. Sequência executável com chamadas/snippets ou scripts testados, entradas explícitas e saídas esperadas. Não deixar ao agente reconstruir operações críticas a partir de frases genéricas.
3. Tabela de decisão por sintoma/resultado: prosseguir, corrigir, perguntar ou parar. Incluir conexão perdida, seleção invisível, seleção acidental, limites ambíguos, degeneração após união e junção topologicamente válida mas visualmente errada.
4. Recuperação: como registrar undo, reobter referências e verificar a restauração; alternativa de salvamento quando histórico não estiver comprovado.
5. Exemplo sintético completo: gerador/entrada, pedido, passos, verificações independentes, resultado esperado e defeitos plantados. Dimensões escolhidas para o exemplo, nunca extraídas de projeto real.

**Aceite adicional:** executar com o modelo efetivamente previsto para operar o produto, em sessão sem contexto. Registrar modelo/versão, ferramentas, instruções fornecidas, intervenções do autor e resultado por requisito. Se o modelo alvo ainda não estiver definido, essa cobertura permanece pendente; sucesso com modelo mais capaz não a substitui.

O agente pode interpretar o pedido e adaptar parâmetros dentro do domínio da receita. Não pode precisar inventar algoritmo crítico, consultar o histórico privado ou receber código corretivo do autor para o ensaio contar como execução autônoma. Se isso acontecer, registrar a lacuna, atualizar a receita e repetir em sessão limpa, com variante sintética não usada na redação. Pergunta legítima ao usuário para resolver ambiguidade prevista não é intervenção corretiva do autor.

Além do exemplo demonstrado, testar uma variante sintética com dimensões/orientação diferentes dentro do domínio declarado. Critérios e tolerâncias devem ser definidos antes; não redefinir o aceite para acomodar a saída. Cada defeito plantado deve atingir o requisito que pretende testar, com controle positivo correspondente.

O primeiro exemplo usa união local, mas não autoriza preencher qualquer cavidade por caixa ou copiar constantes do teste. A receita precisa declarar a geometria que suporta e como reconhecer quando não se aplica. Trechos de código incluídos devem ser executados no teste; pseudocódigo e instruções ainda não reproduzidas ficam explicitamente rotulados.

Os auxiliares mínimos indispensáveis às receitas entram já em M1. M2 consolida apenas as lacunas restantes; não deixar o operador improvisar um trecho crítico sob a justificativa de que scripts só viriam depois.

## M2 — Auxiliares necessários e verificadores reaproveitados

**Objetivo:** consolidar somente as lacunas e repetições demonstradas em M1.

Entregas: scripts pequenos, entradas/saídas documentadas, dependências e testes. Evitar contratos genéricos; preservar resultados semânticos dos verificadores existentes. Um adaptador de saída pode ser útil, mas não altera a decisão nem transforma ausência em aprovação.

Aceite:

- Cada auxiliar identifica a receita e a lacuna que resolve. Capacidade existente suficiente é usada diretamente.
- Comparar campos semânticos dos verificadores alterados com base pós-M0: estado, medida, tolerância, requisito, motivo, código/etapa e papel. Normalização de campos voláteis é declarada antes; divergência sem explicação bloqueia a alteração.
- Defeito intencional no campo comparado reprova a comparação; execução correta passa. Erro operacional plantado não recebe nome de reprovação geométrica.
- Executar verificações afetadas; antes de concluir mudanças nos protótipos, rodar suítes completas em cópia para verificar regressões. Só rodar novos testes quando justificam capacidade ou risco, não para espelhar implementação.
- Caminhos de entrada não são sobrescritos incidentalmente. Escritas ficam no trabalho autorizado. Testar falha e sucesso no ponto certo de uma operação de escrita.
- Falha de conexão é declarada e o controle conectado funciona. Timeout em mutação externa fica incerto até inspeção; não repetir automaticamente nem encerrar o Blender do usuário.

Não entram: banco de projetos, cache de verificações, árvore de revisões, gerente geral de processos ou servidor MCP próprio. Se M1 não demonstrar lacuna, M2 termina registrando que não há auxiliar novo necessário.

## M3 — Empacotar e testar fora da oficina

**Objetivo:** entregar plugin instalável com receitas e recursos comprovados, sem ambiente implícito da máquina do autor.

Entregas: manifesto compatível com hospedeiro alvo, skill/referências, auxiliares necessários, dependências e versões suportadas, avisos de licença e inventário explícito. Não adicionar servidor ao manifesto se o produto não precisa de servidor próprio.

Aceite:

- Instalar o pacote em ambiente isolado e seguir apenas as instruções documentadas. Executar cenário sintético em sessão sem histórico, com as dependências externas declaradas. Não aceitar venv/caminho pessoal herdado como teste limpo.
- Sem Blender/MCP, uma rota independente funciona e a dependente informa ausência; com as dependências presentes, a rota Blender funciona. Carregar skill não instala nem baixa componentes.
- Inventário do pacote extraído coincide com o permitido. Referências da skill e manifesto resolvem para recursos existentes.
- Pacote sem contaminação conhecida passa; amostra privada de teste plantada em área de ensaio é detectada. Amostras de regressão, inclusive numéricas quando exigidas pelo auditor, ficam fora do pacote. Limitar a conclusão aos padrões e cobertura efetivamente testados.
- Nenhum caminho, geometria, nome, medida ou captura de projeto real integra exemplos ou receitas. Revisar manualmente os novos recursos além da triagem automática.
- Licenças e versões de componentes efetivamente incluídos são identificadas; não redistribuir código externo por ter sido usado via ferramenta. Publicação continua ação separada.

## Regras comuns de aceite

Contagem verde não substitui requisito comprovado. Caso barrado pelo motivo previsto pode ser teste bem-sucedido; erro inesperado invalida o experimento. Toda recusa tem controle positivo. Resultado de uma etapa não prova outra. Registro de ausência, limite ou pendência é obrigatório quando afeta a conclusão.

Os testes deste plano usam somente geometria sintética. Não tocar a cena atual do usuário para testar receitas sem pedido específico. O executor de M1 pode preparar/testar seus cenários em sessão separada e identificada; dependência indisponível vira impedimento explícito, não aprovação.

## Fora do plano inicial

Interface visual própria está retirada. Sistema geral de projetos/revisões, cache, servidor MCP próprio e gerenciador geral de trabalhos ficam adiados até necessidade demonstrada. Não migrar silenciosamente essas obrigações para um auxiliar com outro nome.

Mantêm-se identidade da geometria, registro de alterações, verificações proporcionais e salvamentos recuperáveis. Atualizar ou preencher o registro não exige duplicar toda a peça. Folgas, espessuras, silhueta e outras capacidades ainda sem verificador continuam declaradas como indisponíveis; não expandir a implementação para fechá-las antecipadamente.

## Próxima autorização

Executar M1 deste plano enxuto. Não executar a extração ampla do M1 da versão 2. Entregar evidência e lista de lacunas antes de avançar para M2 ou instalar/publicar o pacote. Este plano é a especificação de implementação; a revisão que o escreveu não executou os novos aceites.
