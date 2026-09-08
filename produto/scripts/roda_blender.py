# -*- coding: utf-8 -*-
"""roda_blender.py - executa um script dentro do Blender e recolhe o resultado.

RODA FORA DO BLENDER, no Python do hospedeiro.

POR QUE ESTE ARQUIVO EXISTE. Duas lacunas medidas em 07/09/2026, no Blender 5.2.1
LTS instalado pela Microsoft Store:

1. `blender.exe` dentro de `C:\\Program Files\\WindowsApps\\...` NAO e executavel
   direto: da "Acesso negado", tanto pelo shell quanto pelo Python. O caminho que
   funciona e o alias de execucao `blender-launcher.exe`.
2. `blender-launcher.exe` devolve **stdout VAZIO**, sempre: medido em 8 modos de
   execucao diferentes, 0 bytes em stdout e 0 em stderr nos oito.

3. o codigo de saida e prova NEGATIVA e nao prova POSITIVA. Medido, e a versao
   anterior deste texto estava errada ao dizer que ele "nao diz nada":

   | O que o script de dentro faz | Codigo devolvido |
   |---|---|
   | `sys.exit(0)` / termina normalmente | 0 |
   | `sys.exit(1)` / `sys.exit(2)` | **1** / **2**, propagados |
   | levanta excecao nao tratada | **0** |
   | erro de sintaxe no script | **0** |
   | importa modulo que nao existe | **0** |
   | chama operador do Blender que nao existe | **0** |

   Ou seja: o codigo propaga a saida DELIBERADA do script, e engole toda falha
   IMPREVISTA — que sao exatamente as que ninguem planeja. Codigo nao zero e sinal
   confiavel de falha; codigo zero nao e sinal de nada.

A consequencia pratica, e o motivo de este auxiliar existir: quem chamar o Blender
esperando ler stdout vai concluir que "rodou" a partir de um silencio, e quem
confiar no codigo zero vai concluir o mesmo. O contrato aqui e outro: o script de
dentro ESCREVE um arquivo de resultado, e este auxiliar espera esse arquivo
aparecer. Sem arquivo, nao houve resultado. A medicao dos oito modos esta em
`evidencias_finais/CODIGO_DE_SAIDA_DO_LANCADOR.json`.

Uso:
    python roda_blender.py <script.py> --resultado <saida.json> [--args ...]
    python roda_blender.py --achar          # so localiza o executavel

Como modulo:
    from roda_blender import roda, acha_blender
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time

# ordem de preferencia: alias de execucao, PATH, caminhos comuns
CANDIDATOS = [
    os.path.join(os.environ.get("LOCALAPPDATA", ""),
                 "Microsoft", "WindowsApps", "blender-launcher.exe"),
    os.path.join(os.environ.get("LOCALAPPDATA", ""),
                 "Microsoft", "WindowsApps", "blender.exe"),
]
NOMES_NO_PATH = ["blender", "blender-launcher"]

# Bandeira com que o caminho do resultado e entregue ao script de dentro. Nomeada, e
# nao posicional, para nao competir com os argumentos do chamador.
ROTULO_DO_RESULTADO = "--resultado-em"


def acha_blender(dica=None):
    """Devolve (caminho, como_foi_achado) ou (None, motivo)."""
    if dica:
        if os.path.isfile(dica):
            return dica, "informado pelo chamador"
        return None, "o caminho informado nao existe: %s" % dica
    dica_ambiente = os.environ.get("BLENDER_EXE")
    if dica_ambiente:
        if os.path.isfile(dica_ambiente):
            return dica_ambiente, "variavel de ambiente BLENDER_EXE"
        return None, "BLENDER_EXE aponta para caminho inexistente: %s" % dica_ambiente
    for c in CANDIDATOS:
        if c and os.path.isfile(c):
            return c, "alias de execucao do Windows"
    for n in NOMES_NO_PATH:
        p = shutil.which(n)
        if p:
            return p, "PATH"
    return None, ("Blender nao encontrado. Procurado no alias de execucao do Windows, "
                  "no PATH e em BLENDER_EXE. Se estiver instalado pela Microsoft Store, "
                  "o executavel em Program Files\\WindowsApps NAO e chamavel direto: use "
                  "o alias blender-launcher.exe.")


def roda(script, resultado, args=(), blender=None, tempo_limite_s=300,
         cena=None, fabrica=True, intervalo=0.5, exigir=None,
         passa_resultado=False):
    """Executa `script` dentro do Blender e espera `resultado` aparecer.

    cena: caminho de .blend a abrir. None usa cena inicial.
    fabrica: --factory-startup, para nao herdar preferencias nem complementos do
             usuario. Deixar ligado nos testes: e o que torna o ensaio reprodutivel.

    Devolve dicionario com o conteudo do resultado, ou com o impedimento."""
    exe, como = acha_blender(blender)
    if exe is None:
        return {"estado": "SEM_BLENDER", "motivo": como}

    # SEMPRE absoluto. O script de dentro roda com outro diretorio corrente, e um
    # caminho relativo faz os dois lados apontarem para arquivos diferentes: o
    # auxiliar espera aqui, o script escreve la, e o veredito sai SEM_RESULTADO com
    # o arquivo existindo em outro lugar.
    resultado = os.path.abspath(resultado)

    # CONFERIR A ENTRADA ANTES DE APAGAR QUALQUER COISA. A ordem aqui e o defeito, nao
    # um detalhe: a versao anterior removia o arquivo de resultado e SO DEPOIS conferia
    # a cena. Com o mesmo caminho nos dois papeis — um descuido banal de linha de
    # comando — a cena era DESTRUIDA e o retorno dizia "cena nao encontrada",
    # apresentando a perda como ausencia. Achado por validacao adversarial em
    # 08/09/2026.
    if cena:
        cena = os.path.abspath(cena)
        if not os.path.isfile(cena):
            return {"estado": "SEM_CENA", "motivo": "cena nao encontrada: %s" % cena,
                    "nada_foi_apagado": True}
        mesmo = os.path.normcase(cena) == os.path.normcase(resultado)
        if not mesmo and os.path.isfile(resultado):
            try:
                mesmo = os.path.samefile(cena, resultado)
            except OSError:
                mesmo = False
        if mesmo:
            return {"estado": "COLISAO_DE_CAMINHO", "nada_foi_apagado": True,
                    "cena": cena, "resultado": resultado,
                    "motivo": ("a cena e o resultado apontam para o MESMO arquivo. "
                               "Este auxiliar apaga o resultado antes de executar, "
                               "entao seguir adiante destruiria a cena de entrada. "
                               "Informe caminhos distintos.")}

    if os.path.exists(resultado):
        os.remove(resultado)            # nunca aceitar resultado de execucao anterior

    cmd = [exe, "--background"]
    if fabrica:
        cmd.append("--factory-startup")
    if cena:
        cmd.append(cena)
    cmd += ["--python", script]
    # `passa_resultado` entrega o caminho de resultado ao script. Sem isso, o caminho
    # tem que ser escrito DUAS vezes — aqui e dentro do arquivo de parametros — e nada
    # confere se as duas grafias coincidem; foi por ai que um exemplo documentado
    # deixou de rodar.
    #
    # CORRIGIDO depois da quinta revisao: a primeira versao acrescentava o caminho
    # como ULTIMO argumento e os cenarios liam `argv[1]`. Com dois argumentos do
    # chamador, o script gravava sobre o SEGUNDO argumento dele e o chamador esperava
    # outro arquivo — e toda a evidencia usava exatamente um argumento, portanto nao
    # discriminava o erro. Posicao e contrato fragil: agora vai NOMEADO.
    extras = [str(a) for a in args]
    if passa_resultado:
        extras += [ROTULO_DO_RESULTADO, resultado]
    if extras:
        cmd.append("--")
        cmd += extras

    t0 = time.time()
    try:
        proc = subprocess.Popen(cmd, stdin=subprocess.DEVNULL,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                text=True)
    except OSError as e:
        return {"estado": "FALHA_AO_INICIAR", "motivo": "%s: %s" % (type(e).__name__, e),
                "executavel": exe}

    saida_do_processo = ""
    try:
        saida_do_processo = proc.communicate(timeout=tempo_limite_s)[0] or ""
    except subprocess.TimeoutExpired:
        proc.kill()
        return {"estado": "TEMPO_ESGOTADO", "segundos": tempo_limite_s,
                "executavel": exe, "como_foi_achado": como,
                "nota": ("tempo esgotado NAO prova que o script parou dentro do "
                         "Blender. Inspecionar antes de repetir.")}

    # O lancador pode desanexar, e nesse caso o resultado chega depois de o processo
    # pai sair — por isso a espera existe. Mas esperar o tempo-limite INTEIRO com o
    # processo ja morto e sem arquivo e desperdicio puro: uma sessao limpa mediu 300 s
    # queimados para um erro que estava decidido no primeiro segundo. A espera longa
    # so se justifica enquanto ha alguem para escrever; depois de o processo sair, uma
    # carencia curta basta.
    limite = t0 + tempo_limite_s
    carencia = min(5.0, tempo_limite_s)
    fim_da_carencia = time.time() + carencia
    while not os.path.isfile(resultado):
        agora = time.time()
        if agora >= limite:
            break
        if proc.poll() is not None and agora >= fim_da_carencia:
            break          # processo saiu e a carencia passou: nao vai aparecer
        time.sleep(intervalo)

    r = {"estado": None, "executavel": exe, "como_foi_achado": como,
         "segundos": round(time.time() - t0, 2),
         "codigo_de_saida_do_lancador": proc.returncode,
         "o_que_o_codigo_prova": ("nao zero e sinal confiavel de falha; zero nao "
                                  "prova nada, porque falha imprevista dentro do "
                                  "Blender tambem devolve zero"),
         "segundos_de_espera_pelo_arquivo": round(time.time() - t0, 2),
         "saida_do_processo": (saida_do_processo or "")[-2000:],
         "arquivo_de_resultado": resultado}
    if not os.path.isfile(resultado):
        r["estado"] = "SEM_RESULTADO"
        r["motivo"] = ("o script nao escreveu o arquivo de resultado. MEDIDO: excecao "
                       "nao tratada, erro de sintaxe, import inexistente e erro de "
                       "API do Blender devolvem codigo 0, com stdout vazio — entao "
                       "codigo zero nao prova que rodou. Codigo NAO zero, quando "
                       "aparece, e sinal confiavel de falha: veja "
                       "codigo_de_saida_do_lancador. Ver tambem saida_do_processo.")
        return r
    try:
        r["resultado"] = json.load(open(resultado, encoding="utf-8"))
        r["estado"] = "OK"
    except ValueError as e:
        r["estado"] = "RESULTADO_ILEGIVEL"
        r["motivo"] = "%s: %s" % (type(e).__name__, e)
        return r

    # CORRIGIDO 08/09/2026, depois de validacao adversarial: o codigo de saida era
    # REGISTRADO e nao participava do veredito. Um processo terminando em 7, com um
    # relatorio favoravel no disco, saia como OK e codigo 0 — inclusive com --exigir.
    # E o proprio cabecalho deste arquivo documenta que codigo nao zero e sinal
    # confiavel de falha: medir um sinal e nao usa-lo e pior que nao medir.
    if proc.returncode not in (0, None):
        r["estado"] = "PROCESSO_COM_ERRO"
        r["motivo"] = ("o relatorio existe e e legivel, mas o processo terminou com "
                       "codigo %s. Codigo nao zero e sinal confiavel de falha: o "
                       "relatorio pode ter sido escrito antes do erro, ou por outra "
                       "execucao. Nao aceite o conteudo sem inspecionar."
                       % proc.returncode)
        return r
    # CORRIGIDO depois da terceira revisao: este invocador classificava como OK
    # QUALQUER JSON legivel, sem olhar o conteudo. Um relatorio que diz
    # "veredito_global": "FALHOU" saia como sucesso, inclusive no codigo de saida da
    # CLI. `exigir` e um par campo=valor: quando informado, o estado so e OK se o
    # relatorio trouxer aquele campo com aquele valor.
    if exigir:
        campo, esperado = exigir
        obtido = r["resultado"].get(campo) if isinstance(r["resultado"], dict) else None
        r["exigencia"] = {"campo": campo, "esperado": esperado, "obtido": obtido}
        if obtido != esperado:
            r["estado"] = "VEREDITO_NEGATIVO"
            r["motivo"] = ("o script rodou e o relatorio traz %s = %r, e a exigencia "
                           "era %r. Resultado legivel nao e resultado aprovado."
                           % (campo, obtido, esperado))
    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("script", nargs="?")
    ap.add_argument("--resultado")
    ap.add_argument("--cena")
    ap.add_argument("--blender")
    ap.add_argument("--tempo-limite", type=int, default=300)
    ap.add_argument("--sem-fabrica", action="store_true")
    ap.add_argument("--achar", action="store_true")
    ap.add_argument("--args", nargs="*", default=[])
    ap.add_argument("--exigir", help=("CAMPO=VALOR que o relatorio tem que trazer "
                                      "para o estado ser OK. Exemplo: "
                                      "--exigir veredito_global=ATENDIDO"))
    ap.add_argument("--passa-resultado", action="store_true",
                    help=("entrega o caminho de --resultado ao script na bandeira "
                          "NOMEADA %s, acrescentada ao fim dos seus argumentos, para "
                          "nao ter que repeti-lo dentro do arquivo de parametros. Os "
                          "scripts de cenario deste pacote leem essa bandeira. "
                          "CORRIGIDO depois de uma sessao limpa notar que esta ajuda "
                          "continuava ensinando o contrato POSICIONAL que o codigo "
                          "havia abandonado: seguir a ajuda faria o script gravar "
                          "sobre o seu segundo argumento." % ROTULO_DO_RESULTADO))
    a = ap.parse_args()

    if a.achar:
        exe, como = acha_blender(a.blender)
        print(json.dumps({"executavel": exe, "como": como}, ensure_ascii=False, indent=1))
        return 0 if exe else 1
    if not a.script or not a.resultado:
        ap.error("informe o script e --resultado")
    exigir = None
    if a.exigir:
        if "=" not in a.exigir:
            ap.error("--exigir espera CAMPO=VALOR")
        campo, valor = a.exigir.split("=", 1)
        exigir = (campo, valor)
    r = roda(a.script, a.resultado, args=a.args, blender=a.blender,
             tempo_limite_s=a.tempo_limite, cena=a.cena, fabrica=not a.sem_fabrica,
             exigir=exigir, passa_resultado=a.passa_resultado)
    print(json.dumps(r, ensure_ascii=False, indent=1))
    return 0 if r.get("estado") == "OK" else 1


if __name__ == "__main__":
    sys.exit(main())
