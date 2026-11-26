# Função serverless do Rota Vital

Este módulo atende à Atividade Individual 1 de Serverless. Ele adiciona ao Rota Vital um endpoint independente implementado como AWS Lambda com Python 3.12 e executado localmente pelo AWS SAM CLI. A aplicação Java existente e seu endpoint `/api/processamento/estoque` permanecem separados; a função serverless expõe `POST /guias` na porta local 3000.

A função recebe uma solicitação simulada de transporte do Rota Vital e gera uma guia. Exemplo de corpo:

```json
{
  "requisicaoId": "R-001",
  "hospital": "H-Recife",
  "bolsas": ["O-NEG-0142"]
}
```

Resposta esperada: HTTP 201 com identificador da guia, hospital, bolsas e contador da invocação no ambiente atual.

## Requisitos

- Docker instalado e iniciado;
- AWS SAM CLI;
- Python 3.12 (para desenvolvimento local fora do container).

Não é necessário criar conta AWS nem publicar a função. O SAM inicia o runtime local em container.

## Invocação por evento

No terminal, entre nesta pasta (`RotaVital/serverless`) e gere o evento proxy do API Gateway:

```bash
sam local generate-event apigateway aws-proxy --method POST --path guias \
  --body '{"requisicaoId":"R-001","hospital":"H-Recife","bolsas":["O-NEG-0142"]}' \
  > events/pedido.json
sam build
time sam local invoke GuiaTransporteFunction -e events/pedido.json
```

Repita `time sam local invoke GuiaTransporteFunction -e events/pedido.json` uma segunda vez e anote os dois tempos reais. Guarde prints em `evidencias/`.

| Invocação | Tempo observado |
|---|---|
| Primeira | 63,00 s |
| Segunda | 18,84 s |

## Chamada HTTP

Inicie a API local:

```bash
sam local start-api
```

Em outro terminal, chame o endpoint três vezes:

```bash
curl -X POST http://127.0.0.1:3000/guias \
  -H "Content-Type: application/json" \
  -d '{"requisicaoId":"R-002","hospital":"H-Caruaru","bolsas":["O-POS-0351"]}'
```

Observe `invocacaoNesteAmbiente`. Interrompa o SAM com `Ctrl+C`, reinicie com containers aquecidos e repita as chamadas:

```bash
sam local start-api --warm-containers LAZY
```

Registre os valores que aparecerem; o resultado pode variar conforme o comportamento dos containers no seu ambiente.

| Modo | Valores observados em `invocacaoNesteAmbiente` |
|---|---|
| Inicialização padrão | 1 em cada uma das três chamadas |
| `--warm-containers LAZY` | 1, 2 e 3 nas três chamadas |

## Experimento de timeout

Com o servidor no timeout de 3 segundos, envie a requisição que faz a função esperar cinco segundos:

```bash
curl -X POST http://127.0.0.1:3000/guias \
  -H "Content-Type: application/json" \
  -d '{"requisicaoId":"R-003","hospital":"H-Recife","demorar":true}'
```

Registre a mensagem de timeout. Em `template.yaml`, altere `Timeout: 3` para `Timeout: 10`. Pare o servidor, reconstrua e inicie novamente:

```bash
sam build
sam local start-api
```

Repita a chamada `demorar: true`; registre a resposta após o aumento do timeout. Coloque prints dos dois resultados em `evidencias/`.

Neste ambiente, com o timeout de 3 segundos a chamada respondeu com `Internal server error`. Após alterar para 10 segundos e executar `sam build`, uma nova chamada levou aproximadamente 7,04 s e retornou HTTP 201, com `invocacaoNesteAmbiente: 2`.

## Respostas da atividade

Reescreva estas respostas com suas palavras e acrescente os resultados que você mediu no seu computador.

### 1. Por que a primeira invocação pode demorar mais? O que ocorre em Init?

Na primeira invocação, o serviço prepara o ambiente de execução, inicia o runtime do Python, carrega o código e inicializa o handler. Essa etapa é chamada **Init**. Chamadas seguintes podem reaproveitar um ambiente já iniciado e evitar parte desse trabalho. Nesta execução local, medi 63,00 s na primeira invocação e 18,84 s na segunda. A primeira foi mais lenta porque o SAM precisou baixar/construir a imagem de emulação do Python 3.12; na segunda, a imagem já estava disponível. A fase Init prepara o runtime, carrega o código e cria o ambiente antes da execução do handler.

### 2. O que o campo `invocacaoNesteAmbiente` mostrou? O que isso diz sobre variável global?

No modo padrão, as três chamadas por HTTP devolveram `invocacaoNesteAmbiente: 1`, porque cada chamada foi atendida sem reaproveitamento visível do ambiente. Com `--warm-containers LAZY`, as chamadas devolveram 1, 2 e 3, mostrando que o mesmo container manteve a variável global entre invocações. Uma variável global pode manter seu valor apenas enquanto o ambiente é reaproveitado; não há garantia de persistência entre ambientes ou de que o estado estará disponível em todas as chamadas.

### 3. O que aconteceu com `demorar: true`? Qual o limite do Lambda e o que fazer com algo mais longo?

Com timeout de três segundos, a função que espera cinco segundos excede o limite configurado e termina com timeout. Para uma função Lambda padrão, o limite configurável chega a 15 minutos. Para trabalho mais longo, é melhor dividir o processamento e continuar de forma assíncrona, por exemplo com uma fila ou uma orquestração como AWS Step Functions.

### 4. Quanto custa um milhão de chamadas com 128 MB e 100 ms?

Usando os preços fornecidos no enunciado para `us-east-1`:

- `128 MB ÷ 1024 = 0,125 GB`;
- `100 ms = 0,1 s`;
- `0,125 GB × 0,1 s = 0,0125 GB-s` por chamada;
- `0,0125 × 1.000.000 = 12.500 GB-s`;
- computação: `12.500 × US$ 0,0000166667 = US$ 0,20833375`;
- requisições: `1.000.000 ÷ 1.000.000 × US$ 0,20 = US$ 0,20`;
- total estimado: `US$ 0,40833375`, aproximadamente **US$ 0,41**.

A conta inclui apenas as tarifas indicadas na atividade.

### 5. Onde essa função faria sentido no Rota Vital e onde não faria?

Ela faz sentido numa etapa curta e independente, como validar uma solicitação e emitir os dados iniciais da guia de transporte. Não é indicada para acompanhar continuamente uma viagem, reter o estado na memória ou executar um processo que leve muito tempo. Esses casos precisam de persistência, mensageria ou outro processamento assíncrono.

## Evidências e vídeo

Salve em `evidencias/` prints legíveis de:

1. `sam build` e duas invocações por evento, com os tempos;
2. `sam local start-api` e as chamadas HTTP;
3. o contador com inicialização padrão e com containers aquecidos;
4. timeout de 3 segundos e chamada concluída após a mudança para 10 segundos.

As evidências textuais reais estão em:

- `evidencias/01_invocacoes_evento.txt`;
- `evidencias/02_http_timeout_3s.txt`;
- `evidencias/03_http_warm_lazy.txt`;
- `evidencias/04_http_timeout_10s.txt`.

Vídeo não enviado nesta entrega por falta de tempo para gravá-lo. Para entregar integralmente o requisito, grave um vídeo de até 3 minutos mostrando o handler, uma invocação por evento, uma chamada HTTP e o experimento de timeout.

## Uso de IA

Ferramenta: Copilot SDK em VS Code. Finalidade: auxiliar na integração do módulo AWS SAM/Python ao projeto RotaVital, preparar a documentação e registrar os resultados dos experimentos. Validação: executei localmente AWS SAM CLI 1.174.1 e Docker 29.1.3, compilei o template, executei o handler por evento, chamei a API HTTP nos modos padrão e LAZY e revisei as respostas geradas.
