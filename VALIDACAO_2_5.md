# Edição guiada — entrega 2.5.0

10/09/2026. Receitas e auxiliares para interpretar indicação, delimitar alvo,
transição e protegido, executar prévia e medir seus encontros. Nenhum dado de
projeto real foi usado nos novos exemplos ou testes. A biblioteca anterior e os
verificadores existentes não foram alterados semanticamente.

## O que mudou

- `sessao_blender.py --diagnosticar`: consulta fixa pelo cliente MCP existente;
  distingue seleção viva de flags persistidas e informa próximo passo.
- `edicao_guiada.py`: contexto explícito, cópia que preserva materiais, captura
  com conectividade/unidade, deslocamento por pesos explícitos e verificação da
  transição incluindo vizinhos por aresta. Ausência de critério não aprova.
- `trabalho_blender.py`: reaproveita o lançador headless e o invólucro
  `executa_com_relatorio.py`; captura traceback e separa execução de geometria.
- Roteamento direto em SKILL e referência condicional única para edição guiada;
  exemplo executável com superfície sintética aberta, sem promessa de fabricação.
- Manifesto atualizado; `.gitattributes` preserva bytes do produto, inclusive
  finais de linha, para que clonar/arquivar não mude sua identidade.

## Validação executada

Blender **5.2.1 LTS** em processo separado, `--background --factory-startup`.
Python do hospedeiro **3.12.9**. Nenhum teste conectou à sessão viva ou à porta MCP.

| Verificação | Resultado |
|---|---|
| Contratos do hospedeiro | 9 testes passaram |
| Geometria/contexto em Blender headless | 14 testes passaram |
| Exemplo completo em duas alturas | medidas conformes, perfil analítico conferido |
| Exceção no trabalho headless | código não zero e traceback gravado |
| Trabalho que devolve geometria reprovada | reprovação preservada, não promovida a aprovação |
| Paridade do validador anterior | 339 casos, zero falhas |
| Validação estrutural de SKILL | passou |
| Mesma suíte sobre pacote montado | passou |
| Mesma suíte sobre instalação local do Claude | passou |
| Ensaio legado de preenchimento, variante correta | 21 critérios, zero falhos |
| Bytes preparados no índice Git versus instalação | 31 arquivos idênticos; 30 hashes conferidos |

Os testes incluem: objeto oculto com flags antigas, seleção vazia, contexto com
objeto ativo ausente, alvo correto com dobra errada (reprovação somente pela dobra),
dobra no encontro com protegido, região protegida movida, conectividade alterada,
assinatura antiga, peso NaN, coordenada NaN, cópia de materiais e superfície
originalmente curva que não é aplainada pelo deslocamento analítico.

A primeira execução encontrou retorno de índices, em vez de vetores, na
triangulação da API 5.2. A leitura aceita as duas formas; a suíte foi repetida
depois dessa correção. A área do painel plano é comparada com expressão analítica
independente, não com um parâmetro que apenas declara o resultado esperado.

## Reproduzir

```powershell
python -B tests/roda_guiada.py --saida "<diretorio novo>"
python -B tests/roda_guiada.py --pacote "<pacote montado>" --saida "<outro diretorio novo>"
python -B produto/scripts/testa_paridade_validador.py
python -B empacota_produto.py --verificar
```

O executor grava comandos, códigos e stdout/stderr no destino informado. Relatórios
de execução podem conter caminhos locais; não entram na lista comercial. A montagem
identifica 31 arquivos e confere 30 hashes (o manifesto não se auto-hasheia).

## Limites que permanecem

Não houve novo ensaio de outro agente sem contexto, nem teste do complemento MCP
real na sessão do usuário. O protocolo foi testado com respostas controladas e a
consulta interna com Blender headless. Isso não certifica a integração viva.

Não há inferência automática de feição, seleção por imagem, reconstrução universal,
calibração automática de transição nem aprovação estética por área/ângulo. Os pesos
não crescem sozinhos por vizinhança. O verificador recusa correspondência perdida e
exige limites declarados; não prova auto-interseção, silhueta nem fabricação.

Os relatórios M1/M3 anteriores continuam históricos e não são evidência desta versão.
