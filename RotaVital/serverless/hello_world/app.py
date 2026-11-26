"""Handler AWS Lambda para gerar uma guia de transporte do Rota Vital."""

import json
import time

# Persiste apenas enquanto o mesmo ambiente de execução for reaproveitado.
contador = 0


def lambda_handler(event, context):
    """Recebe um evento proxy do API Gateway e responde com a guia em JSON."""
    global contador
    contador += 1

    corpo = event.get("body") or "{}"
    try:
        pedido = json.loads(corpo) if isinstance(corpo, str) else corpo
    except (json.JSONDecodeError, TypeError):
        return resposta(400, {"erro": "corpo da requisição deve ser um JSON válido"})

    if not isinstance(pedido, dict):
        return resposta(400, {"erro": "o corpo deve ser um objeto JSON"})

    requisicao_id = pedido.get("requisicaoId")
    if not requisicao_id:
        return resposta(400, {"erro": "requisicaoId obrigatório"})

    if pedido.get("demorar"):
        time.sleep(5)  # Ultrapassa o timeout inicial de 3 segundos.

    guia = {
        "guia": "G-" + str(requisicao_id),
        "hospital": pedido.get("hospital"),
        "bolsas": pedido.get("bolsas", []),
        "invocacaoNesteAmbiente": contador,
    }
    return resposta(201, guia)


def resposta(status_code, body):
    """Formato de retorno aceito pela integração proxy do API Gateway."""
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body, ensure_ascii=False),
    }
