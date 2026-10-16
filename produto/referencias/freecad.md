# FreeCAD — reserva para sólido exato

O fluxo padrão é a peça ao vivo no Blender (gera.py + `mostrar_no_blender.py`, ver `SKILL.md`). O FreeCAD fica
como reserva quando a malha não basta: rosca fora do padrão métrico, arredondamento exato de aresta qualquer,
STEP para outro CAD, ou transformar malha em sólido editável. Tudo abaixo foi medido em out/2026 (FreeCAD 1.1.4,
Windows 11, impressora A1); o que não foi medido está marcado.

## 1. Instalação e partida

- Pacote portátil oficial: release estável em github.com/FreeCAD/FreeCAD/releases, arquivo
  `FreeCAD_<versão>-Windows-x86_64-py311.7z`. Confira o SHA256 publicado no release antes de extrair.
  Ocupa ~2,2 GB. O caminho local fica na memória do agente, não aqui.
- Não abre sozinho: não há atalho de inicialização e o servidor de automação vem com o início automático
  desligado. **Só abrir quando o operador pedir.**
- Sem janela (preferido para o agente): `bin/FreeCADCmd.exe script.py`. Partida 0,05 s; a presilha de teste
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
- **Imagem sem janela:** `FreeCADCmd` não desenha; `FreeCAD.exe --hidden` com configuração isolada gerou PNG em
  8,8 s. Para render, prefira o Blender.

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
- **Risco:** `execute_code` roda Python sem restrição com os privilégios do usuário, e o RPC aceita qualquer programa
  local enquanto estiver ligado. Ligar só durante o uso e desligar depois ("Stop RPC Server"); nunca ligar
  "Remote Connections".
- Ponte FreeCAD → Blender (testada, não adotada): um `DocumentObserver` em `slotRecomputedDocument` exporta o STL da
  última etapa válida e chama `mostrar_no_blender.py`; o Blender acompanhou em 0,7–2,4 s.

## 5. Por que não é o fluxo padrão

Comparado à ponte ao vivo no Blender, na mesma presilha: precisão igual (diferença de 0,01% no volume); o FreeCAD ganha
em arredondamento exato e rosca nativa, mas perde em edição de malha de terceiros, render, falhas silenciosas e custo
de contexto. O operador quer o Blender como lugar único. Outros avaliados: SolidCraft (descartado — rosca por `coil`
falhou e o projeto tinha 8 dias); Fusion (não testado — licença pessoal com limite de renda, exige conta e internet).
