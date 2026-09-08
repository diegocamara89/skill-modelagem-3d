# Como testar, amanhã

Escrito para você abrir primeiro. Nada aqui exige ler os relatórios de fase.

**O que existe:** `produto/` é a **árvore de trabalho** do pacote, versão **2.4.0**, 25 arquivos, hash
`6fc1727d6e90bdfa65ec3ca80f15c19e1a9e33da9203ff98f33269a36116135b`. Licença **MIT**. É um conjunto de
receitas para um agente **sem histórico** interpretar um pedido de modelagem 3D,
executar com as ferramentas que já existem, e **conferir** o resultado com número
medido.

Licenciado em **MIT**: pode usar, copiar, modificar, distribuir e vender, mantendo o aviso de copyright e o texto da licença.

---

## Os quatro comandos que valem a pena rodar

Todos a partir desta pasta (`06_skill_universal`). Os três primeiros **não** precisam
do Blender.

**1. O pacote está íntegro e sem dado privado?** (~2 s)

```bash
python empacota_produto.py --verificar
```

> **O que se distribui é o pacote MONTADO, nunca a pasta `produto/` copiada.** Rodar
> os scripts de dentro dela cria `__pycache__`, e um `.pyc` guarda o caminho absoluto
> do fonte — logo carrega nome de usuário e estrutura de pastas. A lista de permissão
> exclui esses arquivos: o destino montado por `--destino` tem **zero**. O relatório
> de `--verificar` traz `bytecode_na_arvore_de_origem`, que **nomeia** o que existe na
> árvore, justamente para a distinção não ficar implícita.

Espere `"pacote_limpo": true`, 25 permitidos, `na_origem_e_fora_da_lista: []`,
`"varredura_funciona": true` e `manifesto_na_origem.resolve: true` — este último
confere os **hashes** e exige que todo arquivo que deve ser identificado esteja no
manifesto. Esse último é um **controle positivo**: um dado privado
plantado fora do pacote tem que casar, senão a varredura estaria reportando "0 achados"
sobre padrão nenhum — o que já aconteceu uma vez e foi pego por este controle.

**2. O validador de requisitos concorda com o verificador?** (~3 s)

```bash
python produto/scripts/testa_paridade_validador.py
```

Espere `"veredito": "ATENDIDO"`, 339 casos, 0 falhas,
`"paridade_da_tabela_de_tolerancia": "ATENDIDO"`. Este teste existe porque o validador
**anunciava** espelhar o verificador e não espelhava.

**3. O Blender está alcançável?** (~1 s)

```bash
python produto/scripts/roda_blender.py --achar
```

Espere o caminho de `blender-launcher.exe` e `"como": "alias de execucao do Windows"`.
O `blender.exe` dentro de `WindowsApps` **não** é chamável direto — dá "Acesso negado".

**4. O ensaio completo, dentro do Blender** (~2 s por variante)

Crie um `cfg.json` com `{"variante": "correta"}` e rode:

```bash
python produto/scripts/roda_blender.py produto/cenarios/ensaio_preenchimento.py --resultado saida/ensaio.json --args cfg.json --passa-resultado --exigir veredito_global=ATENDIDO
```

Espere `"estado": "OK"` e, no relatório, `veredito_global: ATENDIDO` com **21
critérios** e **0 falhos**. Roda em segundo plano, em processo próprio, com
`--factory-startup`: **não toca na sua sessão do Blender aberta**.

As variantes são `correta`, `ranhura`, `tangente`, `duplicado`, `flutuante`, `parcial`.
As quatro últimas são defeitos plantados de propósito, cada um atingindo um verificador
diferente — se alguma delas sair `ATENDIDO` por engano, o julgador está quebrado, e é
isso que elas medem.

> **Sem `--exigir`, um relatório que diz `FALHOU` sai como `OK` com código zero.** O
> auxiliar sozinho só sabe dizer se o arquivo é legível. Legível não é aprovado.

---

## Onde olhar quando quiser entender uma decisão

| O quê | Onde |
|---|---|
| como usar o pacote, do zero | `produto/SKILL.md` |
| o que cada ferramenta faz e o que ela **não** faz | `produto/referencias/mapa_de_ferramentas.md` |
| tabela de aceite de M1, critério por critério | `M1_RESULTADO.md` |
| tabela de aceite de M3, 42 critérios | `M3_RESULTADO.md` |
| o que está aberto e de quem é a decisão | `PENDENCIAS_PRODUTO.md` |
| as evidências, com hash de cada arquivo | `evidencias_finais/` |
| o que agentes sem histórico acharam de errado | `evidencias_finais/SESSAO_LIMPA_D.md`, `_E.md`, `_F.md` |
| o que as revisões independentes acharam | `evidencias_finais/revisao_1_codex.txt` a `revisao_5_codex.txt` |

Os três relatórios de sessão limpa **não foram editados por mim**. São o registro do
que um agente sem contexto conseguiu e onde a pasta o deixou na mão, com as palavras
dele — inclusive nos pontos em que ele me contradiz.

---

## O que está pendente, e por quê

**1. Nenhuma revisão independente passou sobre 2.4.0.** Foram **seis** tentativas: cinco
concluíram, todas com `BLOQUEIA`, e os 43 achados foram corrigidos e medidos. A sexta
não concluiu — o Codex bateu no limite de uso da conta. A estrutura disto é o resultado
mais importante da noite e vale dizer sem enfeite: **cada correção regenera a evidência
que a revisão examinou**, então sempre falta uma passada sobre o estado atual. Não é
formalidade: a quarta revisão achou um defeito **na correção da terceira**, e uma sessão
limpa achou um defeito que **sobreviveu a uma revisão inteira** porque estava protegido
por uma lista de exceções que eu mesmo havia declarado. Por isso o critério `C17` está
`PENDENTE` em vez de "concluído".

**2. A licença está decidida: MIT.** `produto/LICENSE` traz o texto completo. O
pacote contém somente código seu, e o `LICENSE` registra que os scripts que importam
`bpy` executam **dentro** do Blender sem conter código dele. Nada mais impede
distribuir.

**3. Cinco limites medidos, em `PENDENCIAS_PRODUTO.md`:** nenhum requisito prova que um
furo é **passante** (só dá evidência indireta, e o `SKILL.md` diz isso); `A_CALIBRAR`, a
separação mínima entre diâmetro de furo e parede, continua sem número medido; falha ao
criar o diretório de saída da varredura sobe como traceback, porque o verificador é
cópia congelada; e a tolerância que decide a forma é a única sem procedência
obrigatória.

---

## Se você quiser o teste que mais informa

Peça a um agente **sem histórico deste projeto** para usar
`C:\Users\marce\AppData\Local\Temp\pacote_intocado_24` e fazer uma peça sua de verdade,
com a instrução de registrar **onde a pasta o deixou na mão**. Foi assim que apareceram
os 34 defeitos que as revisões não tinham visto — inclusive o pior de todos, que era o
validador recusando uma tolerância que o verificador **usa para decidir**.

O que medir na resposta dele não é se a peça saiu: é se ele precisou **adivinhar**
alguma coisa.
