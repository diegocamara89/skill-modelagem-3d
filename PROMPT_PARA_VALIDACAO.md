# Prompt para mandar ao Astra (ou a qualquer agente) validar o trabalho

Copie tudo o que está dentro do bloco abaixo e mande como mensagem. Não acrescente
contexto: a validação só vale se ele **não** souber o que eu concluí.

---

```
Preciso que você VALIDE um trabalho de terceiro, com ceticismo. Não é para melhorar
nem para continuar: é para descobrir onde ele está errado, onde afirma sem provar, e
onde um usuário seria enganado por ele.

O QUE É

Uma pasta de receitas para modelagem 3D por script (Blender e build123d), pensada para
um agente sem histórico usar: instruções, referências, auxiliares e verificadores. Ela
vem acompanhada de relatórios que declaram critérios de aceite com evidência medida.

ONDE ESTÁ

Repositório local (é onde está tudo, inclusive os relatórios):
C:\Users\marce\OneDrive\Documentos\Modelagem 3D\06_skill_universal

O pacote entregável é a subpasta `produto/`. Há também uma cópia montada e nunca
executada em C:\Users\marce\AppData\Local\Temp\pacote_intocado_22 (se ela não existir
mais, monte uma com `python empacota_produto.py --destino <pasta nova>`).

Use o `python` do sistema: ele já tem as dependências. Se algum import falhar, a lista
está em DEPENDENCIAS_E_LICENCAS.md.

REGRAS QUE NÃO PODEM SER QUEBRADAS

1. Há um Blender ABERTO nesta máquina, com um projeto meu e alterações não salvas. Não
   toque nele. NÃO use `produto/scripts/mcp_blender.py` nem nada que fale com o socket
   127.0.0.1:9876 — isso alcançaria a minha cena. Tudo em Blender headless.
2. Não altere nada dentro de `produto/`. Não faça commit, não faça push, não crie
   branch. Se quiser escrever arquivos, use uma pasta temporária sua.
3. Não instale nada nem mude configuração global.

O QUE EU QUERO QUE VOCÊ FAÇA

Comece por COMO_TESTAR.md e rode o que ele manda. Depois vá além dele:

(a) CONFIRA A TABELA DE ACEITE, NÃO ACREDITE NELA. M1_RESULTADO.md e M3_RESULTADO.md
    declaram dezenas de critérios como ATENDIDO, cada um com um caminho de evidência.
    Escolha os que mais decidem e verifique se a evidência citada realmente sustenta o
    que a linha afirma. Procure especificamente:
    - número apresentado como "medido" que na verdade é parâmetro, constante ou
      consequência aritmética da receita;
    - evidência que existe mas foi gerada por uma versão anterior do código;
    - critério que passa porque o predicado é fraco, e não porque a coisa funciona.

(b) TENTE FAZER O PACOTE APROVAR ALGO ERRADO. Os verificadores existem para reprovar.
    Construa uma peça que esteja errada de um jeito que você acha que passaria: cota
    fora, furo que não atravessa, corpo a mais, malha suja, região que devia estar
    intacta e não está. Se algum defeito seu passar como aprovado, é isso que eu quero
    saber, com o comando e o número.

(c) USE AS RECEITAS COMO UM AGENTE SEM CONTEXTO USARIA. Escolha uma peça sua, siga a
    referência da rota, e registre TODA vez que você teve que adivinhar, todo exemplo
    que não rodou como está escrito, e toda mensagem de erro que não disse o que fazer.

(d) PROCURE VAZAMENTO. O pacote promete não conter nenhum dado de projeto privado —
    nome, medida, caminho, geometria. Tente encontrar algum, inclusive em arquivo
    binário e em nome de arquivo.

O QUE ME ENTREGAR

Um relatório, em português, com:

1. Cada comando que você rodou, na íntegra, com diretório e código de saída.
2. Para cada crítica: arquivo, linha, o que ele afirma, o que você mediu, e o comando
   que reproduz. Sem isso eu não consigo agir.
3. Separado do resto: as coisas que funcionaram exatamente como estão escritas. Preciso
   disso para saber o peso das críticas.
4. No fim, uma frase: você confiaria nesta pasta para um trabalho seu de verdade? Sim
   ou não, e o que falta.

Não seja gentil. Um "está bom" me custa mais caro que dez achados.
```

---

## Se preferir que ele trabalhe pelo GitHub

Troque o caminho local por:

```
git clone https://github.com/diegocamara89/skill-modelagem-3d
```

É privado, então ele precisa estar autenticado na sua conta. O repositório remoto tem
**um commit único**: a história completa, com 23 commits, ficou local no branch
`master`, porque 13 daqueles commits carregam um token do projeto privado que originou
o trabalho.

## O que já foi feito, para você não pedir de novo

Cinco revisões independentes por outro modelo (43 achados, todos corrigidos) e seis
sessões de agente sem histórico (34 achados, todos corrigidos). Os relatórios estão em
`evidencias_finais/`, sem edição minha. **Não mostre isso ao validador antes dele
terminar** — se ele souber o que já foi achado, ele procura no lugar errado.
