# Contexto para revisão independente — M1

Documento de apoio à revisão. **Fora do inventário comercial**: não entra no pacote.

## 1. Objetivo do produto, e o que ele deliberadamente NÃO é

Receitas para um agente **sem histórico** interpretar um pedido de modelagem 3D,
escolher ferramentas que já existem, executar, verificar e deixar o trabalho
retomável. O produto empacota instruções, referências condicionais e os auxiliares
com utilidade demonstrada.

Arquitetura **enxuta, por decisão do autor**. Está explicitamente **fora de escopo**,
e não deve ser recomendado por preferência arquitetural:

- interface visual própria, viewer, painéis;
- servidor MCP próprio ou proxy do Blender — o MCP comunitário já existe e é usado;
- banco de projetos, árvore de revisões, cache de verificações;
- gerenciador geral de trabalhos;
- extração ampla dos protótipos para um núcleo novo;
- contratos genéricos para toda operação futura.

Criar código **somente** quando uma receita precisar de capacidade que a ferramenta
existente não dá, ou quando repetição justificar um auxiliar pequeno.

## 2. Fase e escopo exato desta revisão

Fase **M1**. Sob revisão, com caminho completo:

| O que | Caminho |
|---|---|
| plano vigente | `C:\Users\marce\OneDrive\Documentos\Modelagem 3D\06_skill_universal\PLANO_IMPLEMENTACAO_PLUGIN.md` |
| desenho vigente | `...\06_skill_universal\DESENHO_PLUGIN.md` |
| referência de origem | `...\06_skill_universal\REFERENCIA_BLENDER_EDICAO_GUIADA.md` |
| método, como contexto | `...\06_skill_universal\DESENHO.md` |
| **o produto** | `...\06_skill_universal\produto\` |
| relatório desta fase | `...\06_skill_universal\M1_RESULTADO.md` |
| base pré-M0, intocada | `...\06_skill_universal\base_congelada\` |
| base pós-M0, congelada em M1 | `...\06_skill_universal\base_pos_m0\` |
| resultado de M0 | `...\06_skill_universal\base_congelada\M0_RESULTADO.md` |
| correções já identificadas | `...\06_skill_universal\PENDENCIAS_PRODUTO.md` |

Há histórico em git no próprio `06_skill_universal`, a partir do commit `c9cf867`,
que é o estado pós-M0.

## 3. Manifesto, ambiente e como reproduzir

### Ambiente medido

- Windows 11; Python do hospedeiro 3.12/3.13
- **Blender 5.2.1 LTS**, instalado pela Microsoft Store, Python interno **3.13.13**
- bibliotecas do hospedeiro: `trimesh`, `numpy`, `manifold3d`, `shapely`,
  `build123d`, `lib3mf`
- **ausentes, e nunca exigidas:** `rtree`, `matplotlib`, `fast_simplification`

### Manifesto

`produto/INVENTARIO.json` traz os hashes sha256 dos **19 arquivos** do pacote na
versão **1.1.0**, congelados antes do ensaio de sessão limpa que vale como aceite.
`produto/verificadores/PROVENIENCIA.json` traz os hashes dos cinco verificadores
copiados byte a byte da base pós-M0.

### Comandos reprodutíveis

Da pasta `06_skill_universal`:

```bash
python produto/scripts/roda_blender.py --achar
```

```bash
python produto/scripts/roda_blender.py produto/cenarios/ensaio_preenchimento.py --resultado saida.json --args cfg.json
```

O `cfg.json` é `{"variante": "...", "saida": "saida.json", "cenario": {...}}`, com
variante em `correta`, `ranhura`, `tangente`, `duplicado` ou `flutuante`, e `cenario`
sobrescrevendo os parâmetros do gerador.

Da pasta `produto`:

```bash
PYTHONPATH=cenarios python verificadores/sweep_params.py --modulo familia_exemplo --funcao familia_placa --grade "L=70,80;d=4,5" --saida saida --json varredura.json
```

```bash
python verificadores/check_mesh.py --malha peca.stl
```

```bash
python verificadores/check_intent.py --malha peca.stl --requisitos req.json
```

### Duas advertências de execução

**Todo comando que escreve roda em cópia.** `base_congelada/` e `base_pos_m0/` são
cópias congeladas, não áreas de execução. Os ensaios geram os cenários do zero, em
diretório temporário.

**Não toque na cena real do usuário.** Há uma sessão do Blender aberta na máquina,
com um projeto privado e **alterações não salvas**. Todos os ensaios correm em modo
headless, em processo próprio, com `--factory-startup`. O socket do MCP comunitário
em `127.0.0.1:9876` foi usado **uma vez, só para leitura** (`get_scene_info`), para
provar a conexão.

## 4. Aceite, evidências e controles

A tabela por critério está em `M1_RESULTADO.md`: método, caminho da evidência,
resultado observado e estado. Os controles, resumidos:

| Controle | O que prova | Resultado |
|---|---|---|
| seleção vazia barra a edição | operação não vira não-efeito silencioso | `PRECONDICAO` |
| caixa de mundo sem faces barra | não há crédito por seleção inexistente | `PRECONDICAO` |
| seleção válida desloca de fato | a guarda não recusa tudo | `geometria_mudou: true`, 20,0 → 22,0 |
| variante `ranhura` | forma errada com topologia **limpa** | só o perfil reprova, desvio 0,5 |
| variante `duplicado` | topologia suja com a forma **certa** | só a degeneração, 5 → 0 |
| variante `flutuante` | volume que não toca o material | interseção **0,0**, barra antes de medir junção |
| variante `tangente` | sobreposição zero | `PRECONDICAO` antes da união |
| variante girada 30° | fora do domínio declarado | `PRECONDICAO` nomeando o eixo |
| variante de outra medida | generaliza para outras dimensões | perfil 0,0, sobreposição derivada 1,5 |
| captura de seleção envelhecida | índice que **ainda existe** apontando para outra face | barra; e passa quando nada mudou |
| dependência ausente | rota dependente informa, independente funciona | código 1 com motivo; `check_mesh` roda |
| cópias dos verificadores | equivalência semântica com a base pós-M0 | **todos** os campos idênticos em 3 malhas |

**Modelo operador:** o mesmo modelo implementador, em subagente **sem histórico**
deste projeto — definição dada pelo autor. Duas rodadas. A primeira **não conta como
aceite**, porque eu alterei `produto/` durante a execução dela e a `VERSAO` não
mudou; ela vale como piloto e rendeu seis achados, todos corrigidos. A segunda corre
contra os bytes de `INVENTARIO.json`.

## 5. O que mudou, e o que já é sabido

Desde `c9cf867`, `prototipo/` está **intacto** — `git diff` vazio. Tudo o que M1
acrescentou está em `produto/`, `base_pos_m0/`, `cenas_de_teste/` e nos relatórios.

Defeitos que a própria construção encontrou e corrigiu, com evidência em
`M1_RESULTADO.md`:

- assinatura lida de cópia desatualizada em Edit Mode, reportando "não mudou" com a
  edição aplicada;
- comparação de região protegida emitindo veredito sobre conjunto **vazio**;
- medição de degrau contaminada pela própria inclinação da rampa;
- volume de preenchimento subindo 0,3 **acima** da superfície protegida, defeito que
  a amostragem de perfil **escondeu** e a seção revelou.

**Separação que a revisão precisa respeitar.** Capacidades **fora de escopo**, sem
medidor, e que não são requisito desta fase: folga de encaixe — `A_CALIBRAR`, sem
número medido —, parede mínima, folga entre peças, silhueta contra imagem, geometria
de junta, reconstrução de CAD a partir de malha, seleção por imagem. Requisito
**pendente desta fase** é apenas o que a tabela de aceite marcar como `PENDENTE`.

Correção identificada e ainda **não** aplicada, por disciplina de não editar o pacote
durante um ensaio: `PENDENCIAS_PRODUTO.md`, item P1 — a documentação de
`check_intent.py` omite `--malha`.

## 6. Pergunta adversarial

> Algum critério recebeu aprovação sem evidência válida, pelo motivo errado, ou para
> outra geometria? Alguma receita exige improvisação crítica do agente? Há dado
> privado, regressão, dependência oculta ou infraestrutura duplicada?
>
> Responda **BLOQUEIA** ou **PODE_AVANCAR** para esta fase, com defeito concreto,
> arquivo e linha quando aplicável, evidência e a correção mínima.
>
> **Não amplie o produto por preferência arquitetural**: as exclusões da seção 1 são
> decisão do autor, não omissão.
