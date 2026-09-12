# Expandir a partir de uma face

Use quando o usuário marcou uma face e pediu a região conectada ou a superfície plana que a contém. O nome do objeto vem do diagnóstico da sessão: substitua NOMEDOOBJETO abaixo pelo nome real, nunca copie um nome ilustrativo.

Pré-condições: um objeto em Edit Mode, malha exclusiva sem modificadores/shape keys, exatamente uma face visível selecionada. Se há várias faces, não escolha uma silenciosamente: peça uma face inicial ou mantenha a seleção manual.

O Python do hospedeiro chama a ferramenta pronta; não precisa importar bpy:

```powershell
python "<raiz>/scripts/selecionar_regiao.py" --porta <porta confirmada> --objeto "NOMEDOOBJETO" --modo conectada
python "<raiz>/scripts/selecionar_regiao.py" --porta <porta confirmada> --objeto "NOMEDOOBJETO" --modo conectada --aplicar --captura TOKEN
```

A primeira chamada calcula o conjunto sem mudar a seleção. A segunda aplica. Conectividade aqui significa faces ligadas por arestas, independentemente do ângulo; pode selecionar toda a casca de um sólido. Faces ocultas bloqueiam a expansão. Objetos e ilhas separados não entram.

Para limitar ao plano da face inicial, use `--modo plano --angulo-graus <tolerancia angular> --distancia-mm <tolerancia de plano>`. As duas tolerâncias devem vir do pedido/precisão requerida, não de um valor universal. A distância compara todos os vértices ao mesmo plano inicial, e a normal também é comparada à normal inicial: não acumula pequenas inclinações ao longo da malha. Requer unidades métricas configuradas.

Confira as faces retornadas e mostre a captura atual pela ferramenta existente do MCP. Se a seleção estiver errada, restaure/reselecione a face inicial antes de repetir; a expansão não altera coordenadas ou topologia. Não promete identificar a região funcional do objeto nem detectar uma marcação acidental por intenção.

Timeout não autoriza repetir: primeiro inspecione a seleção atual. A resposta associa a chamada a um identificador, mas isso não resolve ambiguidade humana.

O preview retorna captura. Use esse token ao aplicar; se mudar geometria ou selecao,
refaca o preview e confira o alvo. captura_depois identifica a selecao expandida.
