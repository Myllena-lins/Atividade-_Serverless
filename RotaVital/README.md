# RotaVital

Projeto Spring Boot para demonstrar processamento sequencial e paralelo de solicitações. O módulo original fica em `src/`; o módulo da atividade Serverless foi adicionado em `serverless/` sem alterar a API Java existente.

## Módulo Serverless

A função AWS Lambda local recebe `POST /guias` e devolve uma guia de transporte simulada. Ela usa AWS SAM CLI, Python 3.12 e Docker; não precisa ser publicada na nuvem.

Consulte [`serverless/README.md`](serverless/README.md) para pré-requisitos, comandos de execução, experimento de timeout, respostas às perguntas do enunciado e evidências a registrar.
