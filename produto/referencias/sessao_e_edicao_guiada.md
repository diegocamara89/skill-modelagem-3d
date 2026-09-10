# Blender aberto: diagnosticar, interpretar e editar a forma

Use para “suba esta borda”, “corrija este desnivel”, “este lado deve acompanhar
aquele”. Leia esta rota **antes** de escolher vertices ou chamar translação.
`scripts/edicao_guiada.py` é uma biblioteca adicional, versão 1.0.0; não substitui
os verificadores existentes. O agente ainda precisa identificar a feição.

## 1. Entrada única na sessão

No Python do hospedeiro, usando o caminho real da instalação:

```powershell
python "<raiz do pacote>/scripts/sessao_blender.py" --diagnosticar
```

Este comando usa o cliente MCP já existente e envia **somente código fixo de
consulta**. Não muda modo, seleção ou geometria. O sinalizador técnico
`permitir_escrita=True` é necessário porque o transporte classifica qualquer
`execute_code` como potencial escrita; não constitui autorização para editar.
Para operações solicitadas pelo usuário, aproveite a autorização já dada dentro
desse escopo. Não peça novamente por causa do nome desse sinalizador.

| Retorno | Próximo passo |
|---|---|
| `SEM_SERVIDOR` | verificar complemento/conexão; não reinstalar por tentativa |
| `TEMPO_ESGOTADO` | não repetir uma edição; primeiro conferir o estado alcançado |
| `DIAGNOSTICO_AUSENTE` | inspecionar resposta do complemento; não tratar conexão como execução |
| `SEM_SELECAO_VIVA` / `SELECAO_VAZIA` | identificar objeto ativo e orientar marcação quando necessária |
| `MULTIPLOS_OBJETOS_EM_EDICAO` | escolher pelo pedido; contagem maior não decide o alvo |
| `INDICACAO_DISPONIVEL` | interpretar a feição, não mover imediatamente os índices |

`flags_fora_de_edicao` são dados antigos/persistidos, inclusive de objetos ocultos.
Nunca eleja o alvo pela maior contagem. As faces/vertices em `em_edicao` vêm da
`bmesh` viva. Índices valem apenas para a captura correspondente. Escala sem unidade
definida sai como desconhecida: não transforme unidades em mm por suposição.

Dentro do Blender:

```python
import sys
sys.dont_write_bytecode = True
sys.path.insert(0, r"<raiz do pacote>/scripts")
import edicao_guiada as G
d = G.diagnostica()
```

Se a biblioteca já estava carregada e a instalação mudou, recarregue-a explicitamente
com `importlib.reload(G)` antes de capturar qualquer estado. Não misture capturas
de versões diferentes.

Se for preciso entrar em edição por script, `G.entra_em_edicao(nome)` fornece
contexto explícito com `temp_override`, confere `poll` e o modo alcançado. Não troca
o modo de outro objeto silenciosamente. Falha de contexto pede diagnóstico; não
implica que “o MCP não suporta o operador”. Se necessário, oriente Tab com o cursor
no viewport e o objeto ativo. Para sólido com arestas, use Solid + Edit Mode +
Overlays; X-Ray muda o que pode ser selecionado. Veja `inspecionar_e_selecionar.md`.

## 2. Transformar a indicação em plano geométrico

Uma marcação parcial, assimétrica ou com triângulos desconexos pode apontar uma
feição contínua. Diferencie a intenção da seleção com esta sequência:

1. Relacione a marcação com seção/perfil, normais e superfícies adjacentes.
2. Delimite **alvo** (efeito integral), **transição** (onde a forma pode mudar) e
   **protegido** (onde não pode). Simetria só se pedida ou confirmada pela geometria;
   não a deduza de uma seleção imperfeita.
3. Decida o encontro desejado: manter quina, prolongar plano, refazer arredondamento
   ou deformar suavemente. Uma região curva não se torna plana só porque é mais fácil.
4. Mostre uma prévia da delimitação se houver ambiguidade material. Pergunte apenas
   o que realmente não pode ser inferido; preserve as respostas já recebidas.

| Geometria/intenção | Estratégia |
|---|---|
| conjunto independente ou encontro que aceita deformação das faces incidentes | translação delimitada; conferir essas faces |
| mudança suave permitida numa faixa delimitada | pesos explícitos na faixa, com amplitude e região limitadas |
| plano, parede de espessura definida, quina ou raio que precisam permanecer exatos | reconstrução local/paramétrica; não “alisar” para esconder defeito |
| alvo ou encontro ainda desconhecido | inspecionar/obter decisão antes de construir |

Translação parcial pode esticar, dobrar ou inverter faces na fronteira; **não cria
sempre um degrau**. Uma faixa de transição em parede vertical também não garante
resultado correto. Não propague por cadeia de vizinhos, número de passos ou distância
geodésica sem delimitação espacial e geométrica: pode alcançar quase a peça inteira.
O pacote não escolhe nem calibra automaticamente esses limites.

### Escolher método e evidência sem adaptar o pedido à ferramenta

Antes de construir, registre brevemente: efeito pedido; referências preservadas;
região que pode mudar; método; medidas capazes de revelar uma construção errada.
Não é um formulário para toda ação simples: é a decisão necessária quando a forma
ou a correspondência entre antes/depois pode mudar.

- **Cota explícita versus forma existente:** se não coincidem, informe ambos e a
  definição da medida. Para ângulo, nomeie planos/eixos, orientação e se é ângulo
  interno, entre normais ou relativo a um eixo. Para distância, nomeie os extremos
  e o sistema de coordenadas. Resíduo de ajuste pequeno não resolve qual referência
  o usuário queria. Não troque o valor pedido pelo existente sem resolver a ambiguidade.
- **Escolha geométrica:** quando a feição exige nova aresta, novo encontro ou remoção
  de fileiras, considere reconstrução da região. Não traduza a posteriori cada
  deslocamento em pesos só para passar em `verifica_deslocamento`. Conformidade aos
  pesos prova execução desse plano, não que o plano produz a feição solicitada.
- **Escolha do medidor:** correspondência por índice serve quando ela é preservada.
  Retriangulação requer comparação de superfície/perfis em referências estáveis.
  Ausência de um auxiliar pronto não torna a geometria impossível: use uma medição
  adequada e registre seu alcance; se ela não puder ser implementada, declare esse
  impedimento específico, sem substituir silenciosamente a operação.

| Operação | Evidência apropriada | Evidência insuficiente |
|---|---|---|
| deslocamento com conectividade preservada | deslocamento do alvo, protegido, encontros e perfil independente dos pesos | reproduzir os pesos que a própria tentativa escolheu |
| reconstrução/retriangulação local | limites da região, superfícies de referência, seções comuns antes/depois, encontro e topologia resultante | comparação de índices ou contagem igual de faces |
| criação paramétrica | cotas/geometria do artefato exportado e domínio de parâmetros ensaiado | dizer “exato por construção” sem medir o resultado |
| correção estética | comparação em condições iguais e defeito localizado correspondente | malha fechada ou imagem com outra luz/câmera |

### Manter a região de medição comparável

Determine a região a partir da referência **antes** da tentativa. Caixa fixa pode
perder uma superfície deslocada; faixa de inclinação pode selecionar outras faces
depois da edição. Nesses casos, mudança de área/ângulo pode ser mudança da amostra.
Registre membros ou regra de correspondência e cobertura, incluindo as faces que
entram/saem. Se a região se move, transporte a referência explicitamente ou compare
em uma região comum que contenha o efeito inteiro. Se não há correspondência,
não apresente diferenças como degradação ou melhora da mesma superfície.

Fatias por proximidade de vértices não são seções geométricas: um plano pode
atravessar faces sem passar perto de qualquer vértice. Use interseção com faces;
se a seção falhar, não conclua que a superfície está ausente. Inferência de colisão
ou inversão exige evidência correspondente, não apenas caixas/alturas sobrepostas.

Se o verificador expande a faixa para vizinhos, derive os limites para **essa mesma
zona medida**, antes da execução. Um limite de área de outra seleção não é válido.
Defeito preexistente pede diagnóstico separado: tolerância não precisa aceitar toda
imperfeição original, mas também não pode ignorar o domínio medido.

### Diante de reprovação

1. Verifique se falhou a geometria, a cobertura da medida ou a especificação do teste.
2. Se o teste estiver errado, corrija-o a partir da referência e reaplique **também
   ao estado anterior e a um controle defeituoso**. Preserve o registro da correção.
   Não afrouxe limites apenas porque a tentativa falhou.
3. Se o método produzir o defeito, mude o método; não repita a mesma deformação com
   limiares sucessivos sem nova hipótese verificável.
4. Escolhas rotineiras de implementação dentro do pedido já autorizado não exigem
   nova permissão só porque alteram a topologia. Pergunte se muda a forma pretendida,
   a região protegida, o escopo ou se há ambiguidade material.

Trocar Blender por CAD paramétrico (ou o inverso) exige um benefício concreto:
que feição será criada melhor, como preservar/integrar o restante, que conversão
pode perder informação e como validar a exportação. Não atribua precisão ou ausência
de defeitos ao nome do software. Se a ferramenta atual suporta o reparo local, não
migre apenas porque a primeira estratégia falhou.

## 3. Executar uma prévia com recuperação

Capture a marcação antes de sair de Edit Mode; sincronize ao sair. Salvar a marcação
não salva outros trabalhos da cena. Nunca recarregue outro .blend na sessão do
usuário só porque os índices foram gravados.

Se foi solicitada cópia, use `G.copia_para_previa(nome, novo_nome)` em Object Mode.
Ela copia objeto e malha, preservando vínculos de materiais. Os materiais continuam
compartilhados: mudar o datablock do material muda ambas. Se o usuário quer editar o
objeto atual, não multiplique cópias a cada ajuste; registre recuperação adequada.

`G.captura(nome)` inclui coordenadas de mundo, conectividade e escala no hash.
Materiais são informados separadamente. Modificadores/câmera não estão no hash.

Para uma deformação que **já foi escolhida e delimitada**, em Object Mode:

```python
antes = G.captura(nome)
plano = {
    "assinatura_antes": antes["sha256"],
    "alvo": indices_do_alvo,
    "transicao": pares_indice_peso,   # pesos estritamente entre 0 e 1
    "vetor": deslocamento_em_mundo,
}
previa = G.desloca_com_pesos(nome, plano)
```

Todos os demais vértices são protegidos. O auxiliar recusa índices repetidos,
assinatura antiga, pesos inválidos, malha compartilhada, modificadores e shape keys.
Não altera a conectividade, não usa seleção implícita nem operador de transformação
dependente de viewport. Retorna **PREVIA_NAO_VALIDADA**, não aprovação. Não aplique
novamente sobre a prévia usando os mesmos índices/captura: recapture e reavalie.

## 4. Conferir o alvo E quem absorveu o deslocamento

```python
r = G.verifica_deslocamento(antes, previa["depois"], plano,
                           tolerancia=tolerancia_medida,
                           limites_transicao=limites_justificados)
```

As faces incidentes a pesos diferentes entram automaticamente na medição da
transição, inclusive quando a translação rígida não declarou pesos intermediários.
Uma camada de faces vizinhas por aresta entra na zona medida para verificar as dobras
nos encontros com alvo e protegido; a lista completa é devolvida no resultado.
O verificador mede erro do alvo/protegido e área, qualidade de triângulo e ângulo
entre faces adjacentes da transição. `limites_transicao` exige `area_min`, `area_max`,
`angulo_max_graus`, `qualidade_min`. Sem limites ele retorna **INDETERMINADA**.
Não use os próprios valores da saída para escolher limites que a façam passar.

Área e ângulos são **indicadores condicionais**, não aprovação estética universal.
Quina intencional pode ter ângulo alto; levantar uma parede pode aumentar a área.
Defina limites pelo perfil/encontro desejado e comparação anterior, em unidades da
cena. Não copie limiares de uma peça privada nem confunda mm com unidades sem escala.
Qualidade = área/perímetro² por triângulo; o equilátero tem sqrt(3)/36. Uma face
estreita não é necessariamente degenerada ou defeituosa.

`MEDIDAS_CONFORMES` vale somente para o contrato fornecido. Complete a entrega com:

- seções atravessando **cada encontro**, mais amostras no alvo e no protegido;
- controle de topologia, auto-interseção quando houver ferramenta adequada e
  preservação dos detalhes que importam à finalidade;
- comparação visual em mesma câmera, projeção, escala, material, luz e sobreposições.

Raios medem a superfície atingida, não a feição pretendida. Para diferenças
antes/depois, mantenha origem, direção e correspondência da superfície; descarte
oclusões e múltiplas interseções ambíguas. Centros de face evitam alguns acertos em
arestas, mas não resolvem oclusão. Imagem `offscreen` não é necessariamente o viewport
do usuário. Não identifique feição só por cor de seleção.

Meça a mesma vizinhança antes/depois. “Já existia no original” não dispensa conferir
se piorou, nem invalida pedido de repará-la. Compare o outro lado somente quando ele
for uma referência válida. Retesselação perde correspondência por índice: este
verificador recusa essa comparação; use comparação de superfície/seção apropriada.

## 5. Erros e exemplo executável sem improvisar o invólucro

Para headless, escreva `def executar(config): ...; return resultado_dict` num arquivo.
Use o invólucro pronto, que captura sintaxe, importação, configuração e exceção da
operação com traceback. Não precisa recriar `com_traceback.py`:

```powershell
python "<raiz do pacote>/scripts/trabalho_blender.py" --script "<raiz do pacote>/cenarios/exemplo_edicao_guiada.py" --resultado "<pasta de trabalho>/resultado.json"
```

Para parâmetros, acrescente `--config "<pasta de trabalho>/config.json"`, por exemplo
com `{"altura": 1.5}`. `trabalho_blender` reutiliza `roda_blender`, sempre em processo
headless separado, e encaminha corretamente os argumentos nomeados do invólucro.

O exemplo completo cria apenas uma superfície sintética aberta em headless. Não é
peça fabricável nem reconstrutor automático. `CONCLUIDA` é estado operacional;
abra `resultado.estado` e as medidas. Se for REPROVADA/INDETERMINADA, não entregue
como aprovada. Timeout, encerramento forçado e falha de disco podem impedir o JSON;
nesses casos, ausência de relatório é impedimento, nunca sucesso.

Os testes reproduzíveis da oficina estão em `tests/test_edicao_guiada_blender.py`
e `tests/test_contratos_guiados.py`, fora do pacote instalado. Todo cenário é sintético.
