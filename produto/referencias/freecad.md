# FreeCAD — rota prioritária: CAD por código, bancada de marcas e cálculo estrutural

Padrão escolhido pelo dono em 10/11/2026. Não reconstrua uma peça aprovada apenas para migrar.
Receitas abaixo medidas em out/2026 e ensaios locais de 07 e 10/11/2026, FreeCAD 1.1.4/Windows 11.
Interface por Python, sem Computer Use.

## 0. Bancada de marcas (o operador aponta, o agente lê)

Painel dentro do FreeCAD: o operador clica na peça e aparece **A, B, C…** no ponto; arrastar faz
traço; cada marca aceita nota. Funciona em malha (STL/3MF) e em sólido (STEP, PartDesign).

```powershell
python scripts/abrir_bancada_freecad.py "<projeto>" --documento Peca.FCStd      # documento existente
python scripts/abrir_bancada_freecad.py "<projeto>" --importar a.3mf b.step     # cria <pasta com _ no lugar de espaço>.FCStd
python scripts/abrir_bancada_freecad.py "<pasta vazia>" --testar                # ensaio, 14 verificações; recusa pasta com documento
```

- Em uma revisão com os grupos `Montado` e `Desmontado`, acrescente `--verificar-marcacao` ao lançador oficial. O teste faz cliques internos nas duas vistas em dois níveis de zoom, confere o JSON e a projeção renderizada e restaura as marcas reais. Resultado em `bancada_projecao.json`.

- Reaproveita o FreeCAD já aberto (uma janela só). Exige uma única vista 3D visível. O comando
  espera e imprime `bancada_pronto.json`. Se o `.FCStd` já existe, `--importar` é ignorado (avisa).
- **Ler:** `<projeto>/marcas.json`, lista na chave `marcas` → `id`, `tipo` (ponto/traco), `objeto`,
  `pontos` (globais, mm), `locais` (referencial do objeto, já sem o Placement: use estes para
  analisar a geometria), `descricao` (a nota do operador). Repita em uma frase o que entendeu antes
  de alterar. O arquivo fica preso ao nome do `.FCStd` (campo `origem`); outro documento na mesma
  pasta é recusado. Rodada nova: o operador apaga as marcas velhas no painel (Delete); antes disso,
  copie o `marcas.json` para a pasta da revisão se as notas ainda valem.
- **Falar com o painel sem RPC:** gravar `<projeto>/comando.json` (UTF-8 sem BOM); o painel lê a
  cada 0,5 s e apaga o arquivo. Ações: `{"acao":"diagnostico"}` → `bancada_diagnostico.json`;
  `"capturar"` → `bancada.png` (vista atual); `"vistas"` → `bancada_iso.png`, `_iso_oposto`, `_topo`,
  `_frente` (as quatro de `render_de_conferencia.md`, sem mexer na câmera do operador);
  `"reabrir"` → recarrega o `.FCStd` do disco (**obrigatório depois de editar o arquivo por
  `FreeCADCmd`**, senão a janela mostra a peça antiga; recusa se houver alteração não salva);
  `"recarregar"` → recarrega o código do painel. Lista fechada; não executa código. Erros em
  `<projeto>/bancada_erro.log`. Demais ações na tabela abaixo.

| Função do painel (aba) | O operador faz | O agente faz por `comando.json` | Saída |
|---|---|---|---|
| **Post-it** (Marcas) | liga/desliga "Mostrar as notas na peça" | — | até 3 linhas da nota ao lado da letra |
| **Antes / Depois** (Revisar) | escolhe uma versão em "Peça visível", depois a outra, e clica no botão | `{"acao":"comparar","antes":"<nome>","depois":"<nome>"}`; `{"acao":"isolar","peca":"<nome>"}` | alterna com a câmera parada |
| **Mapa** (Revisar) | "Mostrar mapa" | `{"acao":"mapa","limiar":30,"parede":1.2}`, `"limpar_mapa"` | vermelho = pede suporte, amarelo = parede fina; `bancada_mapa.json` |
| **Fatiar** (Revisar) | "Fatiar o que está visível" | `{"acao":"fatiar"}` | gramas, tempo e tempo de suporte no painel; `bancada_fatiado.json`, G-code em `fatiar/` |
| **Medidas** (aba só aparece se houver planilha com alias) | arrasta ou digita | `{"acao":"medida","nome":"<alias>","valor":80}` | peça refeita; `bancada_medidas.json` |

- **Antes/Depois exige as duas versões no mesmo lugar** (mesmo Placement) e como peças separadas da
  lista (objetos de topo; nomes vêm de `lista_de_pecas` no diagnóstico). Versão deslocada para o lado
  some da tela ao alternar.
- **Mapa é indicador, não prova.** Mesa = Z mais baixo do que está visível; inclinação medida a
  partir da horizontal (0 = teto), igual a `scripts/mapa_balanco.py`; parede = distância até a face
  oposta na normal de cada triângulo. Sólido é triangulado só para medir. Some ao trocar de peça ou
  de medida. Suporte zero só se confirma fatiando e lendo `; FEATURE: Support` no G-code. Face
  apoiada em outra peça visível também sai vermelha (só a mesa conta): isole a peça. Tempo medido:
  50 mil faces em ~5 s; casca densa de 100 mil em ~20 s (a janela fica parada enquanto calcula).
- **Fatiar** usa o Bambu Studio sem janela, um por vez (recusa se houver outro `bambu-studio.exe`),
  teto de 20 min, e **nunca envia à impressora**. Perfil vem de um 3MF salvo pelo Studio (variável
  `MODELO_3MF`; padrão: A1, PETG genérico, 0,20 mm) com suporte automático em árvore ligado, para
  o número mostrar o custo do suporte. O que está visível precisa caber na mesa: isole a peça.
  `visivel.3mf` é arquivo de medição, não de entrega (sem arranjo, brim ou ajustes do projeto).
- **Medidas** edita só célula com número literal (`=60 mm`, `3`); fórmula fica de fora. Número sem
  unidade e sem ponto (`3`) é tratado como contagem inteira: medida contínua leva unidade ou ponto
  (`=1 mm`, `1.0`). Defeito que o documento já tinha não bloqueia a mudança. Valor que
  deixa alguma etapa inválida é desfeito na hora e registrado em `recusada`. A mudança fica na
  janela, **não salva** o `.FCStd`: salvar é decisão do operador ou do agente depois do aval.
- Operador: modo **Navegar** para girar; Ctrl/Shift na lista seleciona várias; Delete apaga o lote;
  duplo clique edita a nota; letra apagada é reutilizada. Marcas não entram na geometria nem na exportação.
- Documento do dono não é regravado pela bancada; só o `.FCStd` novo criado por `--importar`.
- O clique é capturado por filtro Qt **antes** da seleção do FreeCAD. Callback do Coin direto falhou
  no clique humano (a peça inteira acendia): não trocar.
- Limite: o ensaio usa eventos Qt internos; clique humano foi comprovado no projeto Túneis V3
  (44 cliques), de onde este painel saiu. Vários documentos abertos com vista 3D: feche os outros.
- Ampliar o painel (seta, região pintada, medida entre marcas, cor por situação, corte ao vivo,
  pendências por marca: propostas ainda não feitas) é Qt + Coin3D em
  `freecad/bancada_freecad.py`; rode `--testar` depois de qualquer mudança.

## 1. Instalação e partida

- Pacote portátil oficial: release estável em github.com/FreeCAD/FreeCAD/releases, arquivo
  `FreeCAD_<versão>-Windows-x86_64-py311.7z`. Confira o SHA256 publicado no release antes de extrair.
  Ocupa ~2,2 GB. Instalação existente:
  `D:/Diego/Pessoal/3D/Ferramentas/FreeCAD/FreeCAD_1.1.4-Windows-x86_64-py311/`.
  Confira existência/versão; não reinstale por rotina.
- Não abre sozinho: não há atalho de inicialização e o servidor de automação vem com o início automático
  desligado. Abra a janela quando o operador for olhar ou marcar a peça (seção 0).
- Sem janela (preferido para cálculo do agente): `bin/FreeCADCmd.exe script.py`. Partida 0,05 s; a presilha de teste
  levou 0,25 s e 61 MB de RAM.
- Com janela: `FreeCAD.exe` (interface em português de Portugal: "Ficheiro"). Com a janela aberta, ~190–640 MB.

## 2. Receitas que funcionaram (sem janela)

```python
import FreeCAD as App, Part, MeshPart
doc = App.newDocument("Peca")
# ... PartDesign/Part ...
doc.recompute()
corpo = doc.getObject("Corpo")
assert corpo.Shape.isValid() and all("Invalid" not in o.State for o in doc.Objects)  # ver seção 3
MeshPart.meshFromShape(Shape=corpo.Shape, LinearDeflection=0.02, AngularDeflection=0.2).write("peca.stl")
```

- **Medidas que o operador edita:** `Spreadsheet::Sheet` com alias (`sh.set('B1','=20 mm'); sh.setAlias('B1','largura')`)
  e `obj.setExpression('Length', 'Medidas.largura')`. Vale também para posição:
  `obj.setExpression('.Placement.Base.y', 'Medidas.largura / 2')`.
- **Peça simples sem esboço:** `PartDesign::AdditiveBox`, `SubtractiveCylinder`, `SubtractiveCone` dentro de um
  `PartDesign::Body`; arredondamento com `PartDesign::Fillet` apontando a aresta (`Base=(obj, ['EdgeN'])`).
- **Rosca de garrafa (PET, passo 3, filete 1,2 mm):** `PartDesign::AdditiveHelix` com o perfil num esboço.
  0,7 s, um sólido válido, 0,1% da referência em manifold3d. A varredura `makePipeShell` com hélice (Frenet)
  **falha**: dois sólidos e auto-interseção. Tampa (rosca interna): `SubtractiveHelix`.
- **Rosca métrica:** macho com `AdditiveHelix`/`SubtractiveHelix`; fêmea com `PartDesign::Hole` e
  `ModelThread = True`, `ThreadSize = "M8x1.25"` (o furo de macho que ele usa é Ø6,83).
- **Malha → sólido:** funcionou para uma malha fechada simples; a subtração direto na malha (`Mesh.difference`)
  não mudou o volume (não investigado).
- **Imagem sem desktop:** `FreeCADCmd` não desenha; a GUI por macro/Python com configuração isolada gera PNG.
  Use a API nativa de câmera/salvar imagem e desligue temporariamente a transição animada antes de cada lote.
  Não abrir Blender apenas para conferência; não clicar nem capturar a tela.

## 3. Armadilhas medidas

| Armadilha | O que fazer |
|---|---|
| `doc.recompute()` termina sem erro mesmo com etapa inválida, e a janela segue mostrando a peça antiga | Conferir `obj.State` de cada objeto e `shape.isValid()` depois de todo recompute |
| Acabamento preso a uma face (`Chamfer` em `Face2`) fica inválido quando uma medida muda e as faces são renumeradas | Avisar o operador; refazer o acabamento depois de mudar medidas grandes |
| Arredondamento que consome a parede inteira (raio = metade da espessura) dá `StdFail_NotDone` | Usar um pouco menos (0,79 numa parede de 1,6) |
| `Part.cut` devolve `Compound` | Usar `.Solids[0]` antes de medir centro de massa |
| A API muda entre versões (`sk.Support` virou `AttachmentSupport` na 1.1) | Conferir no `FreeCADCmd --version` antes de reaproveitar script antigo |
| Erros pouco explicativos (`StdFail_NotDone`, `IndexError`) | Medir volume e validade em vez de confiar na ausência de erro |

## 4. Automação com a janela aberta (MCP comunitário)

- Projeto: neka-nat/freecad-mcp (MIT). Complemento em `%APPDATA%\FreeCAD\v1-1\Mod\FreeCADMCP`; servidor RPC em
  `127.0.0.1:9875`. Ligar: bancada "MCP Addon" > "Start RPC Server", ou abrir `FreeCAD.exe macro.py` com uma macro que
  faça `from rpc_server import rpc_server; rpc_server.start_rpc_server()`.
- Servidor MCP por stdio a partir do clone revisado: `uv --directory <clone> run freecad-mcp`. 17 ferramentas, ~7 mil
  tokens de contexto por sessão quando ligado.
- **Risco:** `execute_code` roda Python com os privilégios do usuário. O token é opcional e, sem ele, qualquer
  programa local que alcance a porta pode chamar o RPC. CLI Python também não é sandbox. Prefira CLI para
  cálculos isolados; ponte temporária somente se precisar atualizar documento vivo, local, com autenticação
  configurada e sem expor segredo. Desligue pela API ao terminar; nunca habilite Remote Connections por rotina.
- Ponte FreeCAD→Blender foi ensaiada, mas não é o fluxo adotado. Não instale observador que exporta/importa
  malhas automaticamente; preserve a sessão Blender do dono.

## 5. Cálculo estrutural: escolher o método

Fórmulas de viga, momentos, seções e comparações de nervuras em Python continuam válidas com SolidCraft,
Blender ou FreeCAD. São estimativas conforme suas hipóteses; medir espessura não demonstra carga admissível.
Não reclassifique estudos anteriores como FEM nem como inválidos apenas pelo CAD usado.

Para tensões/deformações distribuídas, concentração perto de furos ou geometria que fuja da idealização,
considere a bancada FEM do FreeCAD com solucionador apropriado (ex.: CalculiX). Sua presença/configuração
não foi verificada neste ambiente: confira antes de prometer execução. Montar pelo Python, sem cliques.

Defina carga/direção, apoios/contatos e material com procedência; gere a malha de elementos finitos,
confira reações de equilíbrio e convergência do resultado ao refinar a malha, e compare com um caso
simples conhecido. Só então use o resultado para comparar espessuras. Em FDM, propriedades por direção,
perímetros/infill, adesão de camada e fluência não são descritos automaticamente por escolher “PETG”.
Declare o que foi medido e o que é cenário. Simulação elástica estática não comprova ruptura, impacto
ou deformação durante meses. Ensaio físico necessário permanece separado.

## 6. Escopo local já demonstrado

FreeCADCmd abriu/recompôs projeto nativo e STEP do ensaio de suporte de celular: quatro sólidos válidos.
Medidas/ângulos recompuseram nas amostras; movimento por Placement não testou juntas nativas Assembly.
Isso prova aquelas operações, não toda a bancada FEM ou robustez geral. STEP não recupera o histórico
de outro CAD. Exportação CSG pode fixar valores ou triangular; não equivale a gerador SCAD parametrizável.
