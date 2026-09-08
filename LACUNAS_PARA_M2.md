# Lacunas concretas que M1 demonstrou, para M2 decidir

Regra do plano: M2 consolida **somente** o que M1 demonstrou. Nada aqui é
infraestrutura antecipada, e nada entra só para "preencher M2". Se uma lacuna for
resolvível com o que já existe, ela se resolve na receita e não gera código.

## L1 — cliente do socket do MCP, com estados de falha explícitos

**Lacuna demonstrada.** `referencias/mapa_de_ferramentas.md` descreve o protocolo do
MCP comunitário — socket em `127.0.0.1:9876`, `{"type": ..., "params": {...}}` →
`{"status": "success", "result": {...}}` — mas o pacote **não** traz cliente. O agente
tem que escrevê-lo, e escrever cliente de socket com leitura incremental de JSON é
exatamente o "trecho mecânico frágil" que a referência de origem manda entregar
pronto.

Agrava: o aceite de M2 pede que **falha de conexão seja declarada** e que o
**controle conectado funcione**. Hoje não há onde essa declaração more.

**O que resolveria, e só isso:** um auxiliar pequeno, com estados nomeados —
`OK`, `SEM_SERVIDOR`, `TEMPO_ESGOTADO`, `RESPOSTA_ILEGIVEL`, `ERRO_DO_ADDON` — e a
regra de que **tempo esgotado não prova que o código parou dentro do Blender**, logo
não se repete automaticamente. Somente leitura por padrão; escrita exige parâmetro
explícito, porque a cena é do usuário.

**Não é:** servidor MCP próprio, proxy, nem transporte alternativo. É cliente do que
já existe.

## L2 — a documentação de `check_intent.py` está errada

Ver `PENDENCIAS_PRODUTO.md`, item P1. É correção de texto, não código. Entra antes de
qualquer revisão do pacote.

## L3 — custo de `mede_topo_em_pontos` em malha grande

**Medido por leitura do código, não por execução:** a função testa cada ponto contra
**todas** as faces. Com 87 pontos e 34 faces é irrelevante. Numa malha de 100 mil
faces são 8,7 milhões de testes ponto-em-triângulo.

Ainda **não** foi medido em malha grande, e por isso a lacuna é declarada como
**suspeita, não confirmada**. M2 deve primeiro medir; se o custo for aceitável para o
tamanho de peça que as receitas suportam, não há o que fazer. Se não for, a correção
mínima é um índice por caixa envolvente, não uma estrutura geral.

## L4 — face não convexa cortada em mais de dois pontos

`secao_por_plano` **conta** essas faces e declara que a poligonal está incompleta
quando a contagem não é zero.

**Correção de uma afirmação que virou falsa.** Este documento dizia que a contagem foi
sempre 0 nos cenários medidos. **Não é mais verdade**, e o ensaio julgador é que
mostrou: na variante `duplicado`, aplicar a mesma união duas vezes **produz** face não
convexa. Medido: **2** faces cortadas em mais de dois pontos, **12 pontos e apenas 10
segmentos** — a poligonal fica incompleta de fato.

Ou seja, a lacuna **está** demonstrada, num caso realista: um agente que repete a
operação depois de um tempo esgotado sem inspecionar. O que existe hoje é a declaração
honesta do limite, e ela funciona: a ferramenta acusa em vez de devolver poligonal
incompleta em silêncio, e o ensaio passou a exigir esse aviso naquela variante.

Implementar a poligonal completa para face não convexa fica como lacuna **aberta e
declarada**, com o caso que a demonstra. Não foi implementada nesta entrega, e a razão
é escopo, não ausência de necessidade — o que é diferente do que este documento dizia
antes.

## Aceites de M2 que M1 já cobriu, e onde está a evidência

Registrados aqui para M2 não refazer trabalho nem inventar teste:

| Aceite de M2 | Situação | Evidência |
|---|---|---|
| comparar campos semânticos dos verificadores alterados contra a base pós-M0 | **nenhum verificador foi alterado**; as cópias do pacote são byte a byte e produzem saída idêntica em todos os campos, em 3 malhas | `M1_RESULTADO.md`; `produto/verificadores/PROVENIENCIA.json` |
| rodar as suítes completas em cópia e verificar regressão | 11 casos e 30 mutações, **zero divergências** campo por campo | comparação contra `base_pos_m0/pos_m0_*.json` |
| defeito intencional no campo comparado reprova a comparação | as variantes `ranhura`, `duplicado` e `flutuante` fazem isso, cada uma no detector previsto | relatórios de ensaio |
| erro operacional plantado não recebe nome de reprovação geométrica | medido em M0.2 e reexercitado na rota de criar | `base_congelada/M0_RESULTADO.md` |
| caminhos de entrada não são sobrescritos incidentalmente | `salva_cena` recusa sobrescrever a origem por padrão | `referencias/recuperar_salvar_exportar.md` |
| testar falha e sucesso no ponto certo de uma escrita | M0.2, com prova de que a injeção atingiu a escrita do 3MF e não etapa anterior | `base_congelada/M0_RESULTADO.md` |
| falha de conexão declarada, e o controle conectado funciona | **parcial**: o controle conectado está provado (leitura por socket devolveu `status: success`); a declaração de falha depende de L1 | — |
| não encerrar o Blender do usuário nem repetir automaticamente | regra escrita; a sessão viva não foi tocada em nenhum ensaio | `SKILL.md`, `referencias/mapa_de_ferramentas.md` |
