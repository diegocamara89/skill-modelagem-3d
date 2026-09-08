# Plugin de modelagem 3D — desenho enxuto

Versão 3, 07/09/2026. Planejamento interno, fora do inventário comercial.

Esta versão substitui a arquitetura de produto da versão 2. O método de `DESENHO.md` permanece como referência: modalidade, representação e finalidade independentes; validade geométrica distinta de atendimento ao pedido; conclusões limitadas ao que foi medido. Isso não obriga implementar todas as capacidades previstas naquele documento. Protótipos e registros de M0 permanecem preservados.

## 1. Produto

Receitas para um agente sem histórico interpretar um pedido de modelagem, escolher ferramentas existentes, executar, verificar e permitir continuação do trabalho. O plugin empacota instruções, referências condicionais e os auxiliares que tiverem utilidade demonstrada.

O produto é geral: criação, edição, reconstrução e parametrização são rotas possíveis, não sinônimos. A primeira entrega cobre um subconjunto explícito e não se anuncia como editor universal.

**Reaproveitar primeiro.** Blender fornece seleção, edição, viewport e histórico; seu MCP existente fornece a conexão. Bibliotecas CAD, scripts de verificação e fatiador existentes são usados conforme o pedido. O agente conversa no hospedeiro. Não criar segundo modelo dentro das ferramentas.

## 2. O que entra e o que sai

| Manter agora | Adiar ou retirar |
|---|---|
| Receitas, diagnóstico e tratamento de ambiguidades reais | Interface visual própria e painéis: retirados |
| Verificadores existentes necessários às receitas | Extração integral dos protótipos para núcleo novo: retirada do plano inicial |
| Registro por trabalho e identidade da geometria verificada | Banco de projetos, árvore de revisões, cache automático: adiados |
| Histórico nativo e salvamentos recuperáveis | Gerenciador geral de trabalhos: adiado |
| CLI dos scripts quando útil | Servidor MCP próprio e proxy do Blender: fora do plano inicial |
| Dependências e limites declarados | Contratos genéricos para todas as operações futuras: adiados |

Criar código somente se uma receita precisar de capacidade que a ferramenta existente não forneça adequadamente, ou se um procedimento repetido justificar um auxiliar determinístico. Documentar a lacuna e seu teste; não construir infraestrutura antecipadamente.

## 3. Receitas e organização

Entrada curta em `SKILL.md`: finalidade, como classificar o pedido, rotas suportadas e referências a carregar. Detalhes ficam em referências condicionais. O histórico de revisões adversariais não acompanha cada pedido do agente.

Primeiras rotas:

- Criar ou parametrizar geometria simples com backend existente, parâmetros explícitos e verificações pertinentes; sem exigir reconstrução ou impressão.
- Abrir e inspecionar um modelo no Blender; orientar seleção e visualização.
- Editar região selecionada: deslocamento delimitado e preenchimento local entre limites identificados; conferir região protegida e junção.
- Conferir, desfazer/refazer, salvar ou exportar e preparar retomada por outro agente.

`REFERENCIA_BLENDER_EDICAO_GUIADA.md` é o material inicial da receita de Blender. Reescrevê-la para distribuição sem contexto privado. Seleção por imagem, reconstrução automática de CAD a partir de STL e edição arbitrária de qualquer malha não são capacidades implícitas.

Uma receita informa: quando usar, insumos necessários, ferramenta reaproveitada, como identificar o alvo, ação, verificação, recuperação e limites. Não exigir o mesmo checklist para um ajuste visual e uma peça para fabricação.


### Profundidade operacional das receitas

Entrada curta não significa procedimento superficial. Cada receita precisa ensinar os passos críticos a um agente menos capaz, sem exigir que reinvente o raciocínio geométrico do autor. A referência condicional contém pré-condições, consultas exatas, interpretação dos resultados, sequência executável, parâmetros/unidades, decisões, condições de parada, recuperação e exemplo sintético com resultado esperado.

Expressões como "criar rampa", "corrigir malha" ou "validar resultado" não são instruções suficientes. Explicar como obter limites da geometria, escolher a operação suportada, medir o resultado e distinguir falhas. Trechos repetitivos ou frágeis devem vir prontos e testados quando forem necessários para cumprir a receita, sem criar infraestrutura genérica.

Separar três estados de conhecimento: observado no experimento local, reproduzido em cenário sintético, e ainda não testado. Incluir as falhas intermediárias e a recuperação, não só o caminho feliz. A referência Blender registra as lições; o M1 deve convertê-las em receitas executáveis, não apresentá-las como scripts universais já implementados.

## 4. Registro simples e identidade

Uma pasta por trabalho, fora da instalação. Usar um registro legível (Markdown com campos estruturados ou JSON documentado); não construir banco de dados. Guardar:

- pedido, finalidade e unidades;
- entrada e objeto-alvo, seleção capturada e identidade do estado relevante;
- operação e parâmetros, regiões protegidas e tolerâncias;
- resultado salvo e verificações com resultado, método, limites e identidade do que mediram;
- pendências, ponto recuperável e próximo passo.

Acrescentar uma entrada por alteração relevante, sem apagar o histórico anterior. Um identificador simples de operação é suficiente; não exige árvore de versões ou cópia de objeto a cada comando.

**Identidade não é nome de arquivo.** Para arquivo entregue, calcular hash dos bytes. Para edição na cena, identificar objeto, coordenadas/conectividade, transformação e dependências geométricas usadas pela operação, incluindo modificadores relevantes. Registrar cobertura da assinatura. Índices de faces só valem para a geometria capturada. Se não for possível identificar o estado relevante, não reutilizar resultados: medir novamente sobre um artefato capturado.

Hash de `.blend` prova integridade do arquivo, não distingue sozinho mudança de geometria de mudança de câmera. Seleção, iluminação e enquadramento não devem ser confundidos com alteração geométrica.

Antes de editar ou afirmar validade, reler o estado. Alteração manual, undo/redo, requisitos ou referências diferentes tornam o resultado anterior inaplicável até nova conferência. **Não há cache de medições nesta entrega:** executar as verificações pertinentes ao resultado que será entregue. Não atribuir a uma peça atual a aprovação de outra geometria.

## 5. Edição guiada e recuperação

Consultar o modo e a seleção real antes de orientar. Na instalação ensaiada, Shift + Alt + Z alterna sobreposições; confirmar o mapa ativo em outras instalações. Sólido + Edit Mode + sobreposições mostra arestas sobre superfícies. Em STL, selecionar um triângulo não equivale a selecionar toda uma superfície funcional.

Quando faltarem direção ou destino, resolver a ambiguidade antes de editar. Excluir seleção acidental conforme o usuário indicar. Preservar unidades, posição e escala; não centralizar referência e candidato separadamente.

Editar o objeto atual é permitido. Usar undo/redo nativo com registro adequado das operações por script; testar o caminho usado, sem presumir que toda mutação Python entra no histórico. Reobter referências depois de undo/redo. Respeitar a preferência do usuário sobre cópias; manter salvamento recuperável em momentos acordados. Ctrl+Z não substitui recuperação após fechar a aplicação.

Durante a operação, combinar uma pausa breve na edição manual. Revalidar o alvo e verificar o resultado; isso não é promessa de bloqueio transacional. Timeout do MCP não prova que o código parou no Blender. Em estado incerto, inspecionar antes de repetir. Não encerrar a sessão do usuário para cumprir um prazo.

## 6. Verificação proporcional e resultado honesto

Reaproveitar os verificadores estabilizados em M0. Não reescrever seus resultados ou agregação apenas para padronizar nomes. Preservar distinção entre falha operacional, requisito reprovado, não implementado, não aplicável e indeterminado; manter os papéis decisivo e informativo. Ausência de medidor não produz número favorável.

Conferir o pedido: deslocamento dentro da tolerância, região protegida preservada, junção sem ranhura no alcance efetivamente medido. Malha fechada pode ter forma errada; imagem bonita não prova precisão. Verificações topológicas, componentes, degenerações e dimensões entram quando pertinentes. Exportação bem-sucedida, inclusive 3MF, não prova validade geométrica.

Relatar separadamente o que foi editado, verificado e não decidido. Amostragem não prova toda a superfície. A aprovação para fabricação ou encaixe não deriva apenas da aparência. Não introduzir valor universal de folga ou de separação por conveniência; `A_CALIBRAR` continua pendente.

## 7. Distribuição e limites

Empacotar só instruções e auxiliares necessários. Ferramentas externas são dependências identificadas, não código automaticamente incluído. Sem instalação ou downloads ao carregar a skill. Sem Blender, as rotas independentes continuam úteis; a rota que depende dele explica o que falta.

Testes e exemplos distribuídos usam apenas geometria sintética. Nada do projeto privado que motivou o experimento — nomes, medidas, arquivos, capturas, logs ou caminhos — integra o pacote. Planos internos, bases congeladas e históricos não entram por inclusão recursiva.

Confirmar licenças das versões efetivamente distribuídas. Não copiar CADAM nesta entrega. Manter inventário explícito, auditoria com controles positivos/negativos e teste de instalação limpa. Triagem sem achados não é autorização de publicação ou garantia de ausência de qualquer dado privado.

Permanecem não implementadas as capacidades já abertas no método (por exemplo, parede mínima, folga entre peças e silhueta), salvo entrega específica com teste próprio. Não ampliar o plano para fechá-las por antecipação.

## 8. Evidência disponível

O executor de M0 registrou 11 casos e 30 mutações; isso é base dos verificadores, não prova do produto inteiro. O experimento Blender demonstrou leitura de seleção, edição localizada, captura visual e undo/redo com conferência geométrica naquele caminho. A prova de que a receita funciona com agente sem contexto e em instalação limpa faz parte das próximas entregas. Nenhuma dessas provas exige reconstruir a infraestrutura existente.
