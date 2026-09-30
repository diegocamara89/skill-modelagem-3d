# Como testar

**O que existe:** `produto/` é a árvore de trabalho do pacote, versão **2.14.0**, **68
arquivos** (lista em `empacota_produto.py`, `PERMITIDOS`; identidade por arquivo em
`produto/INVENTARIO.json`). Licença **MIT**. São receitas para um agente sem histórico
interpretar um pedido de modelagem 3D, executar com as ferramentas que já existem e
**conferir** o resultado com número medido.

Todos os comandos rodam a partir desta pasta (`06_skill_universal`). Números esperados
conferidos na 2.14.0, em 30/09/2026, com Blender 5.2.2 LTS.

## Sem o Blender

**1. O pacote está íntegro e sem dado privado?** (~2 s)

```bash
python empacota_produto.py --verificar
```

Espere `"pacote_limpo": true`, 68 permitidos, `na_origem_e_fora_da_lista: []`,
`"varredura_funciona": true` e `manifesto_na_origem.resolve: true` (confere os hashes e
exige que todo arquivo da lista esteja no manifesto). `varredura_funciona` é o controle
positivo: um dado privado plantado fora do pacote tem que casar, senão a varredura diria
"0 achados" sobre padrão nenhum.

> **Distribua o pacote MONTADO, nunca a pasta `produto/` copiada.** Rodar os scripts de
> dentro dela cria `__pycache__`, e um `.pyc` guarda o caminho absoluto do fonte (nome de
> usuário e pastas). O destino montado por `--destino` não tem nenhum; o relatório de
> `--verificar` nomeia o que existe na árvore em `bytecode_na_arvore_de_origem`.

**2. O validador de requisitos concorda com o verificador?** (~3 s)

```bash
python produto/scripts/testa_paridade_validador.py
```

Espere `"veredito": "ATENDIDO"`, `n_casos` 339, `n_falhas` 0 e
`"paridade_da_tabela_de_tolerancia": "ATENDIDO"`.

**3. Testes de unidade** (<1 s)

```bash
python -m pytest -q tests/test_cliente_operacao.py tests/test_contratos_guiados.py tests/test_exportacao_segura.py tests/test_mover_selecao.py
```

Espere `23 passed`.

## Com o Blender (processo próprio, não toca na sessão aberta)

**4. O Blender está alcançável?** (~1 s)

```bash
python produto/scripts/roda_blender.py --achar
```

Espere o caminho do executável e em `"como"` de onde ele veio. A ordem é `--blender`,
`BLENDER_EXE`, `%LOCALAPPDATA%/modelagem-3d/ambiente.json`, alias e PATH. No Windows
Store vale o alias `blender-launcher.exe`; o `blender.exe` dentro de `WindowsApps` dá
"Acesso negado".

**5. Ensaio de edição completo** (~2 s por variante)

Crie um `cfg.json` com `{"variante": "correta"}` e rode:

```bash
python produto/scripts/roda_blender.py produto/cenarios/ensaio_preenchimento.py --resultado saida/ensaio.json --args cfg.json --passa-resultado --exigir veredito_global=ATENDIDO
```

Espere `"estado": "OK"` e, no relatório, `veredito_global: ATENDIDO` com **21 critérios**,
todos `ATENDIDO`. As variantes são `correta`, `ranhura`, `tangente`, `duplicado`,
`flutuante`, `parcial`; as quatro últimas são defeitos plantados, cada um atingindo um
verificador diferente. Se alguma sair `ATENDIDO`, o julgador está quebrado.

> **Sem `--exigir`, um relatório que diz `FALHOU` sai como `OK` com código zero.** O
> auxiliar sozinho só sabe dizer se o arquivo é legível. Legível não é aprovado.

**6. Edição por letras** (os verbos que o operador usa apontando na tela)

```bash
python produto/scripts/roda_blender.py tests/teste_verbos_letras_headless.py --resultado saida/verbos.json --passa-resultado
python produto/scripts/roda_blender.py tests/teste_apagar_letras_headless.py --resultado saida/apagar.json --passa-resultado
```

Cubo de 20 mm em cena mm. Espere `"estado": "OK"` nos dois. No primeiro, mover, desfazer,
extrudar, preencher e arredondar com `APLICADO` (desfazer: `RESTAURADO_DE`). No segundo, a
lasca apagada com `APAGADO_E_FECHADO` e `nao_manifold_restante` 0.

**7. Edição guiada** (hospedeiro + Blender headless, em pasta de resultados **nova**)

```powershell
python -B tests/roda_guiada.py --saida "<pasta temporaria nova>"
```

Testes do hospedeiro e dentro do Blender: flags em objeto oculto, contexto sem objeto
ativo, alvo certo com dobra errada na transição, região protegida alterada, captura
obsoleta, retesselação, medidas ausentes ou inválidas, erro com traceback e resultado
reprovado mantido como reprovado. Não conecta à porta da sessão aberta. Para testar um
pacote montado ou instalado, acrescente `--pacote "<raiz do pacote>"`.

Espere `{"estado": "ATENDIDO", "comandos": 6}` e, em `execucoes.json`, cada comando com o código
esperado: 9 testes do hospedeiro `OK`; 14 testes no Blender com `veredito_global: ATENDIDO`;
o exemplo documentado nas duas alturas (1,0 e 1,5) `CONCLUIDA`; a falha sintética com código
1, `ERRO` e traceback; o resultado reprovado mantido como reprovado. O `usage: ...
COLISAO_ENTRADA_SAIDA` no stderr do primeiro comando é um teste de recusa, não falha.

**8. Falhas, captura e exportação das chamadas prontas**

```powershell
python -B tests/roda_regressao_272.py --blender "CAMINHO_DO_EXECUTAVEL_BLENDER" --saida "PASTA_DE_EVIDENCIAS" --gui
```

Cria configuração temporária e sessão `--factory-startup` própria. `--gui` acrescenta
Undo/Redo reais; sem ele esses testes não contam como executados. `comandos.json`
registra argv, diretório e código de saída; os testes exigem JSON novo e a quantidade de
casos esperada, não só o código de saída. Cobre exportação atômica, respostas incompletas
e contraditórias, token antigo por mudança de geometria, seleção ou conectividade, falha
antes e depois da escrita e as quatro operações.

## O que nenhum destes testes mostra

Se um agente sem histórico escolhe a estratégia certa. Para isso: monte o pacote numa pasta
nova (`python empacota_produto.py --destino "<pasta nova>"`), peça a um agente sem contexto
deste projeto para fazer uma peça real com ele e registrar **onde a pasta o deixou na
mão**. O que medir não é se a peça saiu, é se ele precisou adivinhar alguma coisa.

Não há revisão independente sobre a 2.14.0. Os limites do pacote estão no `SKILL.md`
("O que este pacote não faz"); os abertos e de quem é a decisão, em `PENDENCIAS_PRODUTO.md`.

## Detalhes

`.gitattributes` conserva os bytes de `produto/` (`-text`): a configuração global de finais
de linha não deve invalidar os hashes ao clonar. Depois de editar `produto/`, rode
`python gera_inventario.py <versão>` e o comando 1.

Relatórios de fase (`M1_RESULTADO.md`, `M3_RESULTADO.md`, `evidencias_finais/`,
`evidencias_m1/`) são registro de versões anteriores, não execução da atual.
