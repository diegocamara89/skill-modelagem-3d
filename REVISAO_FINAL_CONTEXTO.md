# Contexto para revisão independente — estado final de M1 a M3

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

**Fases M1, M2 e M3, no estado final.** Pacote **2.1.0**, `bl_ferramentas`
**1.5.0**, hash do pacote
`8a4182c24ee3c9046a8f0e41d05e4b7db88985ecfa5783eadced7ce78b6859ae`, sobre 24 arquivos,
medido em pacote recém-montado e **nunca executado** (rodar um script de dentro dele
cria `__pycache__`, e a primeira medição contou 31 arquivos por isso).

**Já houve CINCO revisões independentes, todas com BLOQUEIA, e os 43 achados foram
corrigidos e medidos.** Estão em `evidencias_finais/revisao_1_codex.txt` a
`revisao_5_codex.txt`. Em paralelo, **seis** sessões limpas independentes acharam mais
34 defeitos, também corrigidos; as três últimas estão preservadas em
`evidencias_finais/SESSAO_LIMPA_D.md`, `SESSAO_LIMPA_E.md` e `SESSAO_LIMPA_F.md`, com
nove, nove e sete achados, e **não foram editadas**. D percorreu a rota de criar por
código; E, a de edição; F escreveu o **próprio** script de dentro do Blender.

**Esta é a sexta passada, e ela existe porque a evidência foi regerada depois da
quinta.** Não relate de novo achado já corrigido: confira a correção e diga se ela
fecha o ponto. O que interessa aqui é: a evidência de `evidencias_finais/` corresponde
aos bytes de **2.1.0**? Os critérios executáveis do ensaio julgam de fato? Sobrou
afirmação sem medida?

Duas coisas úteis para calibrar o esforço desta passada. A quarta revisão encontrou
defeito **na correção da terceira**, e a sessão E encontrou uma afirmação de medida que
era parâmetro de amostragem — as duas do mesmo tipo. E o achado mais recente saiu do
**próprio instrumento de evidência**, não do produto: o `pip list` era gravado truncado
e a conferência de dependências respondia "0 instalados" sobre lista nenhuma. Vale
desconfiar do instrumento tanto quanto do produto.

**Um padrão que já se repetiu três vezes, e que merece atenção especial nesta
passada:** eu corrijo os exemplos medidos e deixo o contrato aberto. Foi assim na união
de pontos por distância (arredondei o índice duas vezes), na tabela de tolerância por
tipo (transcrevi à mão e errei em `furo`, e o erro sobreviveu a uma revisão inteira
porque estava protegido por uma lista de *extras* que era afirmação minha, não medida)
e no julgador do ensaio (que aceitava estado inesperado em passo que nenhum predicado
cobria). Procure onde **ainda** há afirmação minha no lugar de oráculo.

Sob revisão, com caminho completo:

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

`produto/INVENTARIO.json` traz os hashes sha256 dos **23 arquivos** do pacote na
versão **1.7.0**, com caminhos **relativos à raiz do pacote** — e a auditoria do
destino **consome** o manifesto em vez de conferir a lista paralela de permissão.
`INVENTARIO.json` não se auto-hasheia, por isso 23 declarados em 24 arquivos.
`produto/verificadores/PROVENIENCIA.json` traz os hashes dos cinco verificadores
copiados byte a byte da base pós-M0.

### Comandos reprodutíveis

Da pasta `06_skill_universal`:

```bash
python produto/scripts/roda_blender.py --achar
```

```bash
python produto/scripts/roda_blender.py produto/cenarios/ensaio_preenchimento.py --resultado saida.json --args cfg.json --passa-resultado --exigir veredito_global=ATENDIDO
```

O `cfg.json` é `{"variante": "...", "cenario": {...}}`. O vocabulário de variante é
**fechado** — `correta`, `ranhura`, `tangente`, `duplicado`, `flutuante`, `parcial` — e
nome fora dele é recusado com a recusa **gravada** no relatório como `ESPEC_INVALIDA`.
`cenario` sobrescreve os parâmetros do gerador.

`--passa-resultado` entrega o caminho de `--resultado` ao script como último argumento,
para ele não ter que ser escrito em dois lugares. **Sem `--exigir`, o invocador
considera `OK` qualquer relatório legível**, inclusive um que diga `FALHOU`; com ele, o
estado vira `VEREDITO_NEGATIVO` e o código de saída não é zero.

```bash
python produto/scripts/testa_paridade_validador.py
```

Compara `valida_requisitos.py` com o `check_intent.py` congelado na **mesma entrada**,
339 casos, e confere que a tabela de tolerância por tipo é igual à **extraída** do fonte
do verificador por `produto/scripts/extrai_tolerancias.py`.

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

`PENDENCIAS_PRODUTO.md` é a lista viva. Fechados: **P1** (a documentação de
`check_intent.py` omitia `--malha`) e **P2** (a tabela de tolerância por tipo estava
errada em `furo`). Abertos, e cada um diz de quem é a decisão: **D1** licença do produto
— decisão do autor, e por isso C18 fica `PENDENTE`; **D2** nenhum requisito prova furo
passante; **D3** `A_CALIBRAR` sem número medido; **D4** falha ao criar o diretório de
saída da varredura sobe como traceback, e o verificador é cópia congelada; **D5** três
capacidades declaradas e não implementadas.

**Os nove achados da sessão limpa D já estão tratados** (ver `M3_RESULTADO.md`, C22 a
C26, e `PENDENCIAS_PRODUTO.md` D2 e D4). Não os relate de novo: confira se a correção
fecha o ponto.

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
