# skill-modelagem-3d

Skill para [Claude Code](https://claude.com/claude-code) (e compatível com outros agentes que
suportem o formato de skills) para **criar, inspecionar, editar e verificar geometria 3D** —
por script (build123d) e via sessão viva do Blender (bpy/bmesh).

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
├── referencias/           # uma referência por rota (mover, preencher, arredondar, verificar, ...)
├── scripts/                # bl_ferramentas.py e os scripts que rodam dentro/fora do Blender
├── cenarios/               # cenas de exemplo para testar as rotas
└── verificadores/          # checagem de malha, de intenção do requisito, matriz de cobertura
```

## Instalar

Copie (ou faça symlink de) `produto/` para o diretório de skills do seu agente, por exemplo:

```bash
cp -r produto/ ~/.claude/skills/modelagem-3d
```

Configure o executável do Blender uma única vez por máquina, fora do pacote:

```
%LOCALAPPDATA%/modelagem-3d/ambiente.json
```
```json
{"blender_exe": "CAMINHO_ABSOLUTO_DO_EXECUTAVEL_OU_LAUNCHER"}
```

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
