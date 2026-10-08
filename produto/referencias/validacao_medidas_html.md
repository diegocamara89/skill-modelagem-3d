# Validar fotos e medidas por HTML

Rota para reconstruir/adaptar peça a partir de fotos, medidas e correções do operador.
Antes de fechar dimensões, mostre como cada cota foi entendida numa página local em
português. Reutilize a mesma página nas revisões. Não exige HTML para uma edição simples
com região e medida já inequívocas no Blender.

## Começar pelo modelo pronto

Não escreva a página do zero. Gere a partir do modelo:

```
python scripts/nova_pagina_bancada.py --pasta "<pasta do projeto>" --projeto "<nome>" foto1.jpg foto2.jpg
```

O script cria `<pasta>/revisao.html` a partir de `assets/pagina_bancada.html` (tema escuro,
sem CDN), copia as fotos para `imagens/` sem sobrescrever e preenche projeto, data e fotos.
Depois, edite **só** o bloco `/*DADOS*/ ... /*FIM DADOS*/`:

- `conceitos`: `{id, nome, tag, rec, como, pro[], con[], svg}`. Use quando houver mais de um
  mecanismo; o recomendado leva `rec:true`.
- `vistas`: `{titulo, tag, svg, legenda}`. Cada cota no SVG usa
  `<tspan data-value="C"></tspan>`, que a tabela atualiza.
- `cotas`: `{id, valor|null, visor|null, estado:'confirmado'|'interpretado'|'pendente', descricao, foto}`.
- `fotos`, `listas` (pendências, hipóteses, referências) e `rodape`.

**Conceito de mecanismo se mostra renderizado, não em croqui.** O operador recusou desenho
de traços ("parece desenho de criança") e quer cena do Blender: um trecho do objeto real
(grade, porta) mais a peça, em cada estado (fechado, aberto) e a peça sozinha. Modele por
script e renderize em processo separado (`trabalho_blender.py`), em Workbench com
`color_type="OBJECT"` (uma cor por papel: objeto existente, peça) e as quatro vistas com
`_camera_para` de `render_conferencia.py`, usando a **mesma** caixa de enquadramento em
todos os estados, para que eles se comparem. Exemplo completo:
`Modelagem 3D/Trava porta gaiola hamster/conceitos_r01.py`.

- `renders`: `{titulo, nota, pasta, nomes:{iso:'...'}, opcoes:[{valor:'<prefixo>', rotulo, vistas:[...]}]}`
  vira o seletor com quatro vistas, como em `Suporte garrafinha ratos/modelo_v1.html`.
- Cota em cima do render: `<svg class="render" viewBox="0 0 1000 750"><image href=...>` e as
  linhas por cima. Os pixels dos pontos saem do próprio Blender
  (`bpy_extras.object_utils.world_to_camera_view`, `x*largura`, `(1-y)*altura`), nunca no olho.
- Medida que falta entra **suposta** no modelo e aparece assim na tabela de cotas.

Classes de desenho já prontas no CSS: `part`, `part-ghost` (posição alternativa), `dim` e
`dim-text` (cota), `uncertain`, `wire`, `wire-dot`, `door`, `door-thin`, `pivot`, `label`.
Funções auxiliares de desenho podem ficar dentro do bloco DADOS. Diagramas são SVG locais:
não use Mermaid nem outro CDN. Na impressão, a página passa sozinha para tema claro.

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

Confira sintaxe do JS (`node --check` no conteúdo do `<script>`), caminhos das imagens,
letras, valores e descrições; abra a página e confira visualmente. O painel de navegador
do Claude abre `file://` como cópia estática sem as imagens de `imagens/`: confira as fotos
pelo screenshot headless do Edge. Para captura headless local, use a receita já disponível em
`entregas_em_movimento.md`. Exercite ao menos alteração de uma cota, atualização do rótulo
e exportação JSON. Se a conferência visual ou funcional não puder ser feita, declare o
alcance realizado. HTML não substitui CAD, medição física, quatro vistas da geometria
criada ou verificação de montagem; ele valida o entendimento antes dessas etapas.
