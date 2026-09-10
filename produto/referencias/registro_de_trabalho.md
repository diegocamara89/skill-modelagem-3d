# Registro por trabalho

Uma pasta por trabalho, **fora da instalação do plugin**. Um arquivo de registro
legível, acrescentado a cada alteração relevante. Não é banco de dados, não é árvore
de versões, e não exige copiar a peça a cada comando.

O objetivo é concreto: **outro agente, sem esta conversa, tem que conseguir continuar
o trabalho e saber o que ainda não foi decidido** — sem inferir aprovação pela
aparência.

## Estrutura da pasta

```
<trabalho>/
  registro.md            entradas em ordem, nunca apagadas
  entrada/               o que chegou (ou o caminho de origem, se não for copiar)
  saida/                 o que foi produzido: .blend, .stl, relatórios
  medidas/               JSON das verificações, como saíram das ferramentas
```

## Uma entrada por alteração relevante

Acrescente; **não reescreva o histórico**. Modelo:

```markdown
## 003 — preencher o vão entre os dois patamares
data: 2026-09-07 23:40
operacao_id: 003

### Pedido
"ligar os dois patamares com uma rampa, sem mexer no patamar de cima"
finalidade: visualizacao        unidades: milímetros (escala de cena 1.0)

### Entrada e alvo
arquivo: entrada/peca.blend    sha256: 4f1a…  (integridade do ARQUIVO)
objeto: Peca
assinatura da geometria: 9c22…  cobertura: todos os vértices e faces, mundo, 6 casas
seleção capturada: faces [10]  centros em mundo: [[10.0, 20.0, 20.0]]
  (índices valem SÓ para esta geometria capturada)

### Operação e parâmetros
receita: editar_localizado.md, parte 2
limites: a={x:20, z:20}  b={x:40, z:14}   faixa y: 0 a 40   base z: 10
sobreposição: 1.0 — origem: um vigésimo do vão medido de 20. Em planta alcança a
  região protegida e a retessela, o que é esperado; em altura o topo é horizontal na
  altura do limite e não a ultrapassa. O que se verifica é a altura.
região protegida: x 0 a 19, z 20        tolerância de perfil: 0.01
solver: EXACT

### Resultado
saida/peca_v3.blend    sha256: b71e…
assinatura da geometria depois: e05d…
ponto recuperável: undo push "preenchimento do vão concluído, com limpeza"

### Verificações
| verificação | método | resultado | alcance |
|---|---|---|---|
| topologia | mede_malha | 0 abertas, 0 não-manifold, 0 degeneradas (4 antes da limpeza) | objeto inteiro |
| perfil da junção | mede_topo_em_pontos, tol 0.01 | desvio máx 0.0 | 99 pontos, 33 posições em x, y = 4, 20, 36, com adensamento em limite ∓ ov |
| região protegida | mede_topo_em_pontos, tol 0.01 | desvio máx 0.0 | 18 pontos, x 1 a 18 |
| recuperação | undo/redo por assinatura | recuperou nos dois sentidos | este caminho, em background |
medidas/003_*.json guarda a saída completa das ferramentas.

### Pendências e próximo passo
- não verificado: imprimibilidade, folga de encaixe (A_CALIBRAR), parede mínima
- não decidido: se o patamar baixo deve ser arredondado na saída da rampa
- próximo passo: confirmar com o autor o acabamento da saída da rampa
```

## Identidade: o que registrar, e por quê

**Nome de arquivo não é identidade.**

| O que | Como identificar | O que isso prova |
|---|---|---|
| arquivo entregue | `sha256` dos bytes | integridade **do arquivo** |
| geometria na cena | `F.assinatura(...)`: coordenadas **e** conectividade, com cobertura e arredondamento declarados | que a geometria é aquela |
| seleção | índices **mais** centros em mundo | índice só vale para a geometria capturada |
| operação | um identificador simples e sequencial | ordem e referência cruzada |

Hash de `.blend` **não** distingue mudança de geometria de mudança de câmera,
seleção ou iluminação. Se o registro só tiver o hash do arquivo, ele não sabe se a
peça mudou.

Registre também a **cobertura** da assinatura. "Assinatura igual" de uma cobertura
parcial não é "peça igual".

## Quando um resultado anterior deixa de valer

Releia o estado antes de editar ou de afirmar validade. O resultado anterior fica
inaplicável, e tem que ser **medido de novo**, se:

- houve alteração manual depois da medição;
- houve undo ou redo;
- os requisitos ou as referências mudaram;
- a medição foi feita sobre outra geometria, outro objeto ou outro artefato.

**Não há cache de medições nesta entrega.** Execute as verificações pertinentes ao
resultado que será entregue. Não atribua a uma peça atual a aprovação de outra
geometria — foi assim que evidência velha recebeu nome de aprovação em rodadas
anteriores deste projeto.

Câmera, iluminação e enquadramento **não** são alteração geométrica. Não trate uma
imagem diferente como peça diferente, nem o contrário.

## O que nunca entra no registro de um trabalho distribuível

Nada de projeto de cliente: nomes, medidas, arquivos, capturas, logs ou caminhos.
Exemplos e cenários de teste usam **apenas geometria sintética**, com dimensões
escolhidas para o exemplo.

## Registro mínimo aceitável

Se o trabalho for pequeno, o registro pode ser curto — mas estes cinco campos não
podem faltar, porque são os que permitem continuar:

1. pedido e finalidade;
2. identidade da entrada e da saída;
3. o que foi medido, com método, tolerância e **alcance**;
4. o que ficou **não decidido**;
5. o ponto recuperável e o próximo passo.
