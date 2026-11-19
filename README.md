# skill-modelagem-3d

Skill para [Claude Code](https://claude.com/claude-code) (e compatível com outros agentes que
suportem o formato de skills) para **criar, inspecionar, editar e verificar geometria 3D**.

- **Padrão: FreeCAD por código**, numa janela só, com a **bancada de marcas**: o operador clica
  na peça e aparece A, B, C… no ponto (arrastar faz traço), cada marca aceita uma nota, e o agente
  lê tudo em `marcas.json`, sem print. O painel também tem Antes/Depois, mapa de suporte e parede
  fina, fatiamento pelo Bambu Studio e edição de medidas.
- **Blender** (bpy/bmesh) para ajuste orgânico de malha e render de apresentação.
- **SolidCraft** só a pedido.

Não é doutrina: é um conjunto de receitas com chamadas testadas, cada uma com uma referência
carregável sob demanda e um verificador que mede o resultado em vez de aceitar "concluído" por
aparência.

## O produto está em `produto/`

A pasta [`produto/`](produto/) é o pacote pronto para instalar como skill — é ela que deve ser
copiada para o diretório de skills do agente. O resto do repositório (`prototipo/`,
`cenas_de_teste/`, `evidencias_*/`, os `.md` de desenho e resultado de milestone) é o histórico de
desenvolvimento e a evidência que sustenta cada decisão; não é necessário para usar a skill.

```
produto/
├── SKILL.md              # ponto de entrada: quando usar, como classificar o pedido, onde está cada receita
├── INVENTARIO.json        # versão do pacote e da biblioteca, com hash de cada arquivo
├── LICENSE
├── freecad/               # bancada de marcas (painel Qt dentro do FreeCAD), ensaio e localizador de programas
├── assets/                # página de bancada (HTML) e perfil de fatiamento A1/PETG (só configurações)
├── blender/               # complementos do Blender (letras na peça, ponte ao vivo)
├── referencias/           # uma referência por rota (freecad.md primeiro; mover, preencher, verificar, ...)
├── scripts/                # abrir_bancada_freecad.py, bl_ferramentas.py e scripts dentro/fora do Blender
├── cenarios/               # cenas de exemplo para testar as rotas
└── verificadores/          # checagem de malha, de intenção do requisito, matriz de cobertura
```

## Instalar

Copie (ou faça symlink de) `produto/` para o diretório de skills do seu agente, por exemplo:

```bash
cp -r produto/ ~/.claude/skills/modelagem-3d
```

Requisitos (Windows): Python 3, **FreeCAD 1.1** e, para a aba Fatiar da bancada, Bambu Studio.
Blender só se for usar a rota de malha orgânica.

Instalados em Arquivos de Programas, FreeCAD e Bambu Studio são achados sozinhos. Em outro lugar
(ex.: FreeCAD portátil), grave o caminho uma vez por máquina, fora do pacote:

```
%LOCALAPPDATA%/modelagem-3d/ambiente.json
```
```json
{
  "freecad_exe": "CAMINHO/bin/freecad.exe",
  "bambu_studio_exe": "CAMINHO/bambu-studio.exe",
  "modelo_3mf": "opcional: 3MF salvo pelo Bambu Studio com o seu perfil",
  "blender_exe": "CAMINHO_ABSOLUTO_DO_EXECUTAVEL_OU_LAUNCHER"
}
```

As variáveis de ambiente `FREECAD_EXE`, `BAMBU_STUDIO_EXE` e `MODELO_3MF` têm precedência sobre o
arquivo. Sem `modelo_3mf`, a bancada fatia com o perfil do pacote (A1, PETG genérico, 0,20 mm).

Prova de que a bancada ficou pronta (abre uma janela de teste do FreeCAD, que fecha sozinha):

```bash
python scripts/abrir_bancada_freecad.py "PASTA_VAZIA" --testar
```

O resultado esperado é `"resultado": "PASSOU"`, com 14 verificações.

No Windows Store, use o alias `blender-launcher.exe`, não o binário protegido dentro de
`Program Files/WindowsApps`. Para conferir a resolução sem executar nada:

```bash
python scripts/roda_blender.py --achar
```

## Como a skill pensa

Três regras valem em todas as rotas:

1. **Meça, não presuma.** Uma chamada que devolve "concluído" não prova efeito — foi medido que
   `transform.translate` com seleção vazia devolve `CANCELLED` sem erro e nada muda.
2. **Validade geométrica não é atendimento ao pedido.** Malha fechada pode ter a forma errada;
   são duas verificações separadas.
3. **Diga o alcance.** Amostragem prova os pontos amostrados, não a peça inteira.

Antes de agir, o pedido é classificado em três eixos independentes — **o que fazer** (criar,
editar, reconstruir, parametrizar), **em que** (sólido, superfície, malha, montagem) e **para
quê** (visualização, intercâmbio, montagem, impressão, usinagem) — porque cada combinação muda a
rota e as verificações exigidas.

Detalhes completos, tabela de rotas e o que a skill **não** faz estão em
[`produto/SKILL.md`](produto/SKILL.md).

## Desenvolvimento

`empacota_produto.py` monta `produto/` a partir da fonte e recalcula `INVENTARIO.json`. Os
arquivos `M1_RESULTADO.md`, `M2_RESULTADO.md`, `M3_RESULTADO.md`, `REVISAO_*_CONTEXTO.md` e a
pasta `evidencias_finais/` documentam as rodadas de revisão adversarial (Codex) e a evidência
medida por trás de cada versão liberada.

## Licença

MIT — texto completo em [`produto/LICENSE`](produto/LICENSE). O pacote contém somente código do
autor: nenhuma biblioteca de terceiros e nenhum binário são redistribuídos.
