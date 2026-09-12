# Deslocar faces selecionadas na sessão aberta

Use quando a seleção já identifica a região e o pedido é uma translação rígida. A ferramenta move os vértices das faces selecionadas; faces vizinhas que compartilham esses vértices acompanham a mudança. Não promete conservar ângulos dessas paredes, preencher vãos ou reconstruir transições.

Não escreva um script para cada distância. Execute a ferramenta pronta no Python do hospedeiro, com o caminho absoluto real da instalação:

```powershell
python "<raiz do pacote>/scripts/mover_selecao.py" --acao mover --porta <porta confirmada> --objeto "Peca" --eixo Z --distancia-mm 1
python "<raiz do pacote>/scripts/mover_selecao.py" --acao mover --porta <porta confirmada> --objeto "Peca" --eixo Z --distancia-mm -0.3
python "<raiz do pacote>/scripts/mover_selecao.py" --acao desfazer --porta <porta confirmada> --objeto "Peca"
```

O eixo é global; a distância está em milímetros. Informe o nome do objeto confirmado pelo diagnóstico, não um nome presumido. A porta é obrigatória: use a conexão confirmada para a sessão pretendida. Em ensaio isolado, use a porta fornecida pelo avaliador, nunca a da cena de trabalho.

A seleção deve estar em Edit Mode num único objeto. Confira a resposta de cada chamada antes da próxima. Timeout não autoriza repetir a edição: consulte o estado primeiro. Se houver recusa, resolva a pré-condição indicada sem trocar de método silenciosamente.

Mostre a viewport ao usuário após a edição usando a captura existente do MCP. Medidas de deslocamento não substituem a inspeção das faces vizinhas. Se o pedido exigir prolongamento ou reconstrução de conexão, use a rota de edição guiada; não tente obter esse efeito mudando pesos para encaixar nesta operação.

Código novo só se a ferramenta não cobrir a operação pedida: identifique essa lacuna antes. O invólucro, transporte, unidades e contexto da operação pronta não devem ser reescritos pelo agente.

`desfazer` e `refazer` desta CLI restauram as coordenadas registradas pela ferramenta, como uma nova operação no Undo do Blender. Não são comandos para desfazer qualquer ação da sessão. Se a geometria mudar fora da sequência, recusam a restauração. O histórico fica somente na memória da sessão; não sobrevive à reabertura. Ctrl+Z continua sendo o histórico nativo e pode invalidar essa sequência.
