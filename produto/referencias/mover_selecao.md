# Mover faces selecionadas em eixo global

Use para translacao rigida da uniao dos vertices das faces selecionadas. Faces
adjacentes acompanham vertices compartilhados; forma dessas faces nao e certificada.
Exige objeto ativo nomeado em Edit Mode, malha exclusiva sem modificadores/shape keys,
unidades METRIC com escala correta e distancia finita diferente de zero em mm.

No Python do hospedeiro, a partir da raiz do pacote:
```
python scripts/mover_selecao.py --acao inspecionar --porta PORTA --objeto NOME
python scripts/mover_selecao.py --acao mover --porta PORTA --objeto NOME --eixo Z --distancia-mm 1 --captura TOKEN
```
Substitua NOME/PORTA reais e TOKEN pelo campo captura da inspecao.
A escrita exige que sessao, geometria e selecao ainda correspondam a essa captura.
O resultado traz captura_depois: use-a para proxima operacao se o alvo continua correto.

Para desfazer/refazer desta ferramenta, use --acao desfazer ou --acao refazer com
--captura atual. O historico proprio restaura coordenadas e recusa geometria externa
alterada. Nao e historico geral de Blender, materiais ou animacao.

DESLOCAMENTO_VERIFICADO mede deslocamento do alvo e preservacao dos outros vertices.
Nao certifica colisao, espessura, qualidade adjacente ou fabricacao. Confira viewport
quando houver duvida de exibicao; nao gere codigo novo para trocar a distancia.
Se o pedido exige reconstruir encontros, use edicao guiada.
Timeout/INDETERMINADO exige inspecao antes de repetir. Falha com estado final igual
retorna FALHA_SEM_ALTERACAO_LIQUIDA; isso nao prova que nenhuma escrita foi tentada.
