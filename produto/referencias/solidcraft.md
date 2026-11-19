# SolidCraft — só a pedido do dono

Foi prioridade de 07 a 10/11/2026; o dono voltou ao FreeCAD (`freecad.md`) porque o SolidCraft
0.30.1 não oferece marcação de vários pontos visíveis na peça (clique acende a peça inteira; a
automação não desenha na cena). Use-o quando o dono pedir, por exemplo para ver a árvore de
operações sendo construída. As receitas abaixo continuam válidas. Nunca controle
mouse, teclado ou menus nem capture o desktop. Janela visível e automação por API são compatíveis.

## Ambiente e execução

Instalação local comprovada0.30.1:
`D:/Diego/Pessoal/3D/Ferramentas/SolidCraft/v0.30.1/portatil/solidcraft-0.30.1-windows-x64-portable/`.
Binários `solidcraft.exe` e `solidcraft-cli.exe`. Confira existência/versão antes de usar;
não reinstale nem configure MCP global. Receitas independem da pasta do laboratório.

O caminho mais curto para execução sem janela é uma lista JSON de comandos:

```json
[
  {"command":"parameters.add","params":{"name":"comprimento","expression":20,"unit":"mm"}},
  {"command":"solid.box","params":{"length":"comprimento","width":10,"height":3,"name":"Base"}}
]
```

```powershell
& '<pasta dos binários>/solidcraft-cli.exe' run '<projeto>/receita.json' --param-check strict --save '<projeto>/Peca_R01.sc' --out '<projeto>/Peca_R01.step' --json-out '<projeto>/resultado.json'
```

Troque os marcadores pelos caminhos absolutos do projeto. `run --help` e
`solidcraft-cli commands` mostram o contrato local. Não usar `--allow-errors` para entregar.
Salvar `.sc` e o script preserva a definição; STEP/STL transportam a forma, não o histórico.

## Sessão persistente ou janela acompanhada pelo operador

- MCP nativo por stdio: `solidcraft-cli mcp --headless --param-check strict --allow-path '<projeto>'`.
  Dura só enquanto o processo existir; não precisa instalar plugin global.
- Para acompanhar construção na janela, use canal local iniciado pelo executável
  `solidcraft.exe --control PORT` e MCP `--connect 127.0.0.1:PORT`, da mesma versão.
  Leia o estado/path/dirty antes de abrir ou alterar documentos; preserve alterações do dono.
  Use perfil de execução separado e só um controlador por documento. Não feche a janela para
  corrigir um problema da ponte. Não coloque token em logs, argumentos, documentos ou respostas.
- Já existe cliente Python testado em
  `D:/Diego/Pessoal/3D/Modelagem 3D/Laboratorio SolidCraft/scripts/solidcraft_lab.py`.
  `Client(name, allowed=Path(projeto))` cria sessão headless; `connect` e `profile` atendem a janela.
  Ele guarda logs no laboratório: confira isso antes de usá-lo fora de ensaio; não copie outro
  cliente por rotina. Scripts `testar_funcoes.py` e `solidcraft_braco.py` no mesmo diretório
  contêm operações reais, não precisam ser lidos inteiros para toda peça.
- Descubra só o necessário com `list_commands`/`describe_command`; execute recursos nomeados,
  parâmetros explícitos e lotes curtos. `batch` oferece rollback; confirme `rolled_back` em falha.
  `parameters.change`, `inspect_design`, `measure` e `check_parameters` cobrem edição/verificação.
  Confira o schema da ferramenta antes de supor campos. Sem resposta, inspecione o estado antes
  de repetir uma mutação: timeout não prova que ela deixou de executar.

O token e `--allow-path` reduzem acidentes; não confinam um agente que também tem shell.
Não use `--allow-any-path`, conexões remotas ou configuração global como solução de rotina.
Finalize processos headless/ponte que iniciou ao concluir, preservando documentos e janela do dono.

## Conferência e limites comprovados

- Após criar ou alterar, confira erros do histórico, sólidos fechados, volume, cotas, furos,
  folgas e interferências relevantes. Salve/reabra e confira também o arquivo exportado.
- Para imagens, use `screenshot`/render nativos, conforme contrato, em lote e apenas das vistas
  necessárias à conferência. Não use Computer Use. Gere `iso`, vista oposta que mostre base,
  topo e frente; leia `render_de_conferencia.md`. Imagem nativa não prova a janela visível.
- Uma união de garfo falhou após furos/fillet e passou ao reordenar as operações. Isso é um
  caso comprovado, não garantia de que reordenar conserte toda booleana. Investigue o erro.
- `mesh.convert` tem domínio limitado. No ensaio, caixaSTL converteu; placaSTL furada e busto
  foram recusados. Não converta malha densa à força para fingir CAD editável.
- Roscas M8 e hélice sintética passaram digitalmente nas amostras; não substituem nossa
  receita impressa M6 com folgas calibradas nem comprovam encaixe/resistência físicos.
- Não existe conversor SCAD geral comprovado. SCADBridge reproduziu a placa inicial, mas
  congelou medidas no teste60→80. Conversor próprio/híbrido validado só em retânguloXY
  extrudado+furosZ+Rvertical; montagem/rosca são recusadas. Para MakerWorld, preparar fonte
  SCAD autocontida e testar parâmetros localmente; execução online é uma verificação separada.
- Formato48 da0.30.1 não abre em versões anteriores. Preserve originais e versões nativas;
  confira a versão antes de atualizar ou abrir projeto, sem prometer compatibilidade futura.

## Voltar ao padrão

FreeCAD (`freecad.md`) é o padrão: marcação pelo operador, CAD, malha e FEM. Ao levar uma peça
daqui para lá, exporte cópia e confira unidades/posições; STEP não transfere parâmetros nem histórico.

Blender (`blender.md`): deformação orgânica/local, operação de malha que sua receita já resolve,
preservação de uma cena editada pelo dono ou render de apresentação. Pintura3MF e rosca
NumPy/manifold3d podem continuar como scripts externos, sem abrir Blender. Não reimplemente
receita validada apenas para encaixá-la no CAD padrão.
