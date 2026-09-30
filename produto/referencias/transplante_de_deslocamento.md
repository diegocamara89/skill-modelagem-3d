# Transplante de deslocamento — combinar versões da mesma malha sem booleana

Quando várias versões de uma malha têm **a mesma ordem de vértices** (só as posições
mudam — típico de edições por deslocamento: engrossar, suavizar, piso de espessura), dá
para montar a versão final pegando cada região de uma delas e levá-la para uma malha
**derivada** (que já passou por corte ou booleana), sem fazer booleana nova.

Validado numa peça impressa (23/09/2026), onde a fusão por booleana não funcionou.
Script: `scripts/transplante_deslocamento.py`.

## Quando usar

- Aprovou-se uma região de uma versão e outra região de outra, e as duas partem da mesma malha.
- A peça final precisa de uma operação já feita e validada numa versão antiga (feição
  removida, furo de encaixe), e refazer essa booleana na versão nova é arriscado
  (malha engrossada costuma ter auto-interseção; ver `criar_e_parametrizar.md`, booleana).

## Receita

1. **Conferir topologia igual.** Mesma contagem de vértices e faces, e a maioria dos
   vértices idênticos entre as versões. O script recusa se as contagens diferem.
2. **Escolher a divisa** onde nenhum vértice é mexido pelas duas versões. O script
   recusa se a versão "abaixo" mexer algo acima da divisa. Na validação: z = −2 mm, uma região
   acima, outra abaixo, zero conflitos.
3. **Mapear a derivada para o ancestral comum** (a versão de mesma topologia da qual a
   derivada foi feita) por coincidência exata de vértices (< 0,1 µm). Recusa se menos de
   metade casar — sinal de ancestral errado.
4. Vértice herdado recebe a posição-alvo. Vértice **novo** (criado pelo corte/furo)
   recebe o deslocamento interpolado dos 8 vizinhos herdados (inverso da distância).
5. **Conferir** que watertight, número de corpos e euler ficaram iguais aos da derivada.

```
python scripts/transplante_deslocamento.py --base base_V.npy --divisa z=-2 \
    --acima versaoA_V.npy --abaixo versaoB_V.npy \
    --derivada derivada_V.npy derivada_F.npy --ancestral ancestral_V.npy --saida FINAL
```

Medido na validação: 198.831 vértices casados, 1.641 novos interpolados, deslocamento
máximo 0,9 mm, fechado, 1 corpo, euler −122 igual ao da derivada, 0,9–1,9 s. O script
reproduziu o arquivo impresso bit a bit.

Tudo por `.npy`: resultado de booleana não sobrevive ao round-trip de STL (ver
`criar_e_parametrizar.md`, booleana).

## Antes: de qual versão saiu o cupom aprovado?

Cupom (corpo de prova) aprovado tem de ser ligado à malha inteira de onde saiu.
`scripts/origem_do_recorte.py` acha isso por **coincidência exata de vértices**: pega um
vértice do recorte, testa todas as translações candidatas e descarta com poucos vértices
(`cKDTree.query` com `distance_upper_bound`). Entre versões de mesma topologia a translação
é a mesma, então calcula uma vez.

- **1 segundo**, contra mais de 7 minutos da varredura em grade.
- A fonte certa fica com 80–90% de vértices exatos (o resto são as faces do corte); as
  erradas, no patamar do que não foi mexido (~58%).
- **Limite:** recorte engrossado **depois** de cortado não bate exatamente com nenhuma malha
  inteira — todas ficam baixas e parecidas. Nesse caso, a malha inteira equivalente é a
  versão com a mesma espessura aplicada na feição inteira.
