# ArenaPulse API

Backend de uma plataforma de desafios e campanhas para comunidades de EA Sports FC e FPS.
O projeto combina jogos, gamificação e engajamento digital: participantes entram em desafios,
registram resultados, ganham pontos e disputam rankings por recompensas.

## Por que este projeto é bom para portfólio

- Tem identidade: nasce do interesse por FIFA/EA FC, FPS e inovação.
- Resolve um problema real de comunidades, creators, eventos e campanhas de marca.
- Vai além de CRUD: autenticação, regras de pontuação, transações, ranking e dashboard.
- Pode evoluir para filas, antifraude, notificações e análise de campanha.

## Stack

- Python 3.12 e FastAPI
- SQLAlchemy 2
- PostgreSQL em produção e SQLite para desenvolvimento simples
- JWT com senha protegida por Argon2
- Pytest
- Docker Compose
- Deploy serverless na Vercel

## Funcionalidades do MVP

- Cadastro e login por JWT.
- Catálogo público de jogos.
- Criação e busca paginada de desafios.
- Entrada de jogadores em desafios.
- Envio de resultados com pontuação calculada pelo servidor.
- Ranking com critérios de desempate.
- Dashboard pessoal.
- Swagger/OpenAPI automático.

## Executar sem Docker

Requer Python 3.12 ou superior.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

Sem configurar `.env`, a aplicação usa SQLite e cria `arenapulse.db` automaticamente.
Acesse:

- API: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

## Executar com Docker e PostgreSQL

```powershell
Copy-Item .env.example .env
docker compose up --build
```

Troque `JWT_SECRET` antes de qualquer publicação.

## Deploy na Vercel

O projeto usa um entrypoint FastAPI reconhecido automaticamente pela Vercel. Em um deploy sem
`DATABASE_URL`, ele usa SQLite em `/tmp` apenas para demonstração; os dados podem desaparecer
quando a função reiniciar. Para persistência real, configure `DATABASE_URL` com uma instância
PostgreSQL e gere uma chave segura para `JWT_SECRET` nas variáveis de ambiente do projeto.

## Testar

```powershell
pytest
ruff check .
```

## Fluxo principal da API

1. `POST /api/v1/auth/register`
2. `POST /api/v1/auth/login` usando formulário OAuth2 (`username` e `password`)
3. Copie o token ou use **Authorize** no Swagger.
4. `GET /api/v1/games`
5. `POST /api/v1/challenges`
6. `POST /api/v1/challenges/{id}/join`
7. `POST /api/v1/challenges/{id}/results`
8. `GET /api/v1/challenges/{id}/leaderboard`
9. `GET /api/v1/me/dashboard`

## Roadmap recomendado

### Versão 0.2 — produto confiável

- Alembic para migrações.
- Aprovação de resultados pelo adversário ou moderador.
- Evidências por screenshot e armazenamento em S3.
- Idempotência no envio de resultados.
- Testes de autorização e concorrência.

### Versão 0.3 — inovação e campanhas

- Organizações e marcas criando campanhas patrocinadas.
- Cupons, badges e catálogo de recompensas.
- Segmentação de desafios por comunidade e perfil.
- Eventos de domínio e workers com Redis/Celery.
- Webhooks para CRM, Discord e WhatsApp.
- Métricas de aquisição, participação, retenção e conclusão.

### Versão 1.0 — diferencial técnico

- Detecção de resultados suspeitos.
- Ranking sazonal e sistema de ligas.
- Matchmaking por nível.
- Atualização em tempo real via WebSocket.
- Observabilidade com logs estruturados, métricas e tracing.

## Decisões de domínio

- O resultado é calculado pelo servidor a partir do placar; o cliente não escolhe quantos
  pontos recebeu.
- O ranking desempata por pontos, vitórias e data de entrada.
- O mesmo usuário só pode entrar uma vez em cada desafio.
- Um resultado pertence à participação, preservando o contexto do usuário e do desafio.

Para uma aplicação pública, a primeira evolução deve ser a validação de resultados. O MVP
aceita resultados autodeclarados intencionalmente para manter o escopo adequado ao portfólio.
