# Validar fotos e medidas por HTML

Rota para reconstruir/adaptar peça a partir de fotos, medidas e correções do operador.
Antes de fechar dimensões, mostre como cada cota foi entendida numa página local em
português. Reutilize a mesma página nas revisões. Não exige HTML para uma edição simples
com região e medida já inequívocas no Blender.

## Página de revisão

- Identificação, data, revisão e unidades (normalmente mm).
- Vistas esquemáticas suficientes para localizar a peça, orientação e cotas com letras
  estáveis. Declare quando forem sem escala; rótulo atualizado não altera geometria.
- Cada cota ligada à foto original, valor e descrição do trecho medido. Diferencie
  leitura do instrumento, interpretação geométrica e confirmação pelo operador.
- Tabela com valores e descrições editáveis, observações, exportação JSON e impressão/PDF.
- Galeria completa das referências com links para abrir os originais, hipóteses de
  funcionamento e lista de medidas ainda faltantes.
- Referências externas ao projeto com origem, arquivo e condições; não embuta fotos ou
  dados privados do operador na skill pública.

Use HTML/CSS/JS local sem CDN ou dependência de rede. Organize as fotos em `imagens/`,
preservando nomes/conteúdo e evitando sobrescrita. Quando o operador usa uma referência
em outro projeto, consulte-a antes de criar outra. Desenho legível acima da ornamentação:
vistas, cotas e fotos devem ter correspondência direta; layout responsivo.

## Correção e persistência

Uma correção pode mudar o número ou o trecho que ele representa. Atualize o valor adotado
na página e no registro do projeto, sem apagar a leitura original da foto. Confirmação
de uma cota não aprova as demais, folgas, orientação ou mecanismo. Não transforme uma
largura de boca ambígua em diâmetro interno por suposição.

Campos editáveis atualizam os rótulos; descreva se o esquema não se redesenha em escala.
Se usar `localStorage`, versione os dados para que valores antigos não sobrescrevam uma
revisão corrigida. Explique que armazenamento no navegador não grava no arquivo do projeto;
o JSON exportado guarda as correções. Ao receber os ajustes, incorpore-os aos arquivos.

## Conferir a entrega

Confira sintaxe do JS, caminhos das imagens, letras, valores e descrições; abra a página
e confira visualmente. Para captura headless local, use a receita já disponível em
`entregas_em_movimento.md`. Exercite ao menos alteração de uma cota, atualização do rótulo
e exportação JSON. Se a conferência visual ou funcional não puder ser feita, declare o
alcance realizado. HTML não substitui CAD, medição física, quatro vistas da geometria
criada ou verificação de montagem; ele valida o entendimento antes dessas etapas.
