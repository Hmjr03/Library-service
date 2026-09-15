# Library-service — Mate Academy Flex

API de biblioteca em Django REST Framework. Implementa **7 tarefas obrigatórias selecionadas: 1 a 7**, com autenticação JWT, inventário, empréstimos, devoluções, testes e OpenAPI/Swagger. Sem frontend separado: a interface navegável do DRF está disponível.

## Requisitos

- Python 3.13; dependências fixadas em `requirements.txt`.
- SQLite para estudo local. PostgreSQL é configurável por variáveis de ambiente para uso concorrente.
- Nenhuma credencial externa é necessária para as tarefas selecionadas.

## Executar no seu computador

Abra um terminal dentro da pasta do projeto:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

O comando `createsuperuser` solicita seu e-mail e senha. Escolha seus próprios dados. Não há administrador ou senha padrão.

- API navegável: http://127.0.0.1:8000/
- Swagger: http://127.0.0.1:8000/docs/
- ReDoc: http://127.0.0.1:8000/redoc/
- OpenAPI: http://127.0.0.1:8000/schema/
- Administração: http://127.0.0.1:8000/admin/
- Login por sessão para a interface navegável: http://127.0.0.1:8000/api-auth/login/

No Windows, ative o ambiente com `.venv\Scripts\activate`.

## Tarefas selecionadas

| Nº | Entrega | Código principal |
|---|---|---|
| 1 | CRUD de livros | `books/models.py`, `serializers.py`, `views.py` |
| 2 | Escrita somente para staff; leitura pública | `books/permissions.py` |
| 3 | Usuário por e-mail, cadastro, perfil, JWT | `users/` |
| 4 | Lista e detalhe de empréstimos com livro detalhado | `borrowings/models.py`, `serializers.py`, `views.py` |
| 5 | Criação, validação de estoque e atribuição do usuário | `borrowings/services.py` |
| 6 | Isolamento por usuário e filtros | `BorrowingViewSet.get_queryset` |
| 7 | Devolução única e reposição do exemplar | `return_borrowing` |

Stripe, Telegram, multas e tarefas agendadas pertencem às tarefas 8–15 e não fazem parte desta seleção Flex. O workflow de qualidade é um apoio adicional, sem mudar as sete tarefas selecionadas.

## Autenticação

Cadastre-se com `POST /users/`:

```json
{
  "email": "reader@example.com",
  "first_name": "Reader",
  "last_name": "Example",
  "password": "Use-your-own-strong-password"
}
```

Obtenha tokens em `POST /users/token/`, enviando `email` e `password`. O retorno contém `access` e `refresh`.

**Use o cabeçalho `Authorize`, conforme o exercício:**

```text
Authorize: Bearer <access>
```

`Authorization` não é o cabeçalho JWT configurado neste projeto. No Swagger, clique em **Authorize** e, na seção **jwtAuth**, informe `Bearer <access>` completo no campo Value (incluindo o prefixo `Bearer`). O esquema OpenAPI descreve o cabeçalho personalizado. Para renovar: `POST /users/token/refresh/` com `{"refresh": "<refresh>"}`.

A interface navegável também aceita login por sessão, com proteção CSRF. O cadastro não permite definir privilégios de administrador. As senhas são armazenadas com hash e nunca retornadas pela API. `PUT /users/me/` e `PATCH /users/me/` aceitam alteração de senha opcional.

## Endpoints

| Método | Caminho | Acesso / comportamento |
|---|---|---|
| GET | `/books/` | Público; lista paginada |
| POST | `/books/` | Staff; cria livro |
| GET | `/books/{id}/` | Público; detalhes |
| PUT/PATCH | `/books/{id}/` | Staff; altera livro/estoque disponível |
| DELETE | `/books/{id}/` | Staff; exclui livro sem histórico |
| POST | `/users/` | Cadastro público |
| POST | `/users/token/` | Obtém JWT |
| POST | `/users/token/refresh/` | Renova JWT |
| GET/PUT/PATCH | `/users/me/` | Perfil do usuário autenticado |
| GET | `/borrowings/` | Usuário: próprios; staff: todos |
| GET | `/borrowings/{id}/` | Mesmo isolamento da lista |
| POST | `/borrowings/` | Autenticado; retira um exemplar |
| POST | `/borrowings/{id}/return/` | Devolve uma única vez |

Listas usam 20 registros por página. Use `?page=2`. Retorno: `count`, `next`, `previous` e `results`.

### Criar livro como staff

```json
{
  "title": "Clean Code",
  "author": "Robert C. Martin",
  "cover": "SOFT",
  "inventory": 3,
  "daily_fee": "1.50"
}
```

`cover`: `HARD` ou `SOFT`. `inventory` representa exemplares disponíveis e aceita zero; valores negativos são inválidos. `daily_fee` é decimal em USD e deve ser maior que zero. Livros com histórico de empréstimos não podem ser excluídos: a API retorna 400 para preservar os registros.

### Criar empréstimo

`POST /borrowings/`:

```json
{
  "book": 1,
  "expected_return_date": "2030-12-20"
}
```

Escolha uma data igual ou posterior à data atual do servidor (UTC). O exemplo precisará ser atualizado se executado após essa data. O servidor preenche `user` e `borrow_date`. Cada empréstimo corresponde a um exemplar, reduzindo o estoque em 1. O retorno 201 inclui o empréstimo com os detalhes do livro.

### Filtrar

- `/borrowings/?is_active=true`: não devolvidos.
- `/borrowings/?is_active=false`: devolvidos.
- `/borrowings/?user_id=2`: filtro para staff.
- `/borrowings/?user_id=2&is_active=true`: combina os dois filtros.

Usuários comuns sempre veem apenas os próprios registros; fornecer `user_id` não amplia o acesso. Filtros inválidos retornam 400. A consulta direta ou tentativa de devolver um empréstimo de outro usuário retorna 404.

### Devolver

`POST /borrowings/1/return/`, sem corpo. Preenche a data atual e soma 1 ao estoque. Retorna 200 com o registro atualizado. Uma segunda devolução retorna 400 e não muda o estoque. Staff pode devolver em nome de um usuário.

Não há PUT/PATCH/DELETE de empréstimos: alterações devem respeitar as operações de retirada e devolução.

## Integridade e decisões

- Operações de retirada e devolução são transações: falhas desfazem suas alterações.
- A retirada decrementa o estoque com uma atualização condicional no banco (`inventory > 0`). A devolução atualiza somente registros ainda não devolvidos. Isso impede estoque negativo e reposição duplicada nessas operações, inclusive quando o chamador tem um objeto desatualizado.
- Datas são verificadas na API e por restrições do banco.
- E-mail é normalizado em minúsculas, com unicidade também no banco.
- Alterações administrativas de livros usam bloqueio de linha no PostgreSQL. O número informado pelo staff é o estoque **disponível**, não o total adquirido.
- SQLite facilita a avaliação local; ele não oferece o mesmo bloqueio de linha do PostgreSQL e pode apresentar erro de banco ocupado sob concorrência. Para operação multiusuário, use PostgreSQL e valide carga no ambiente de destino.
- O enunciado aceita devolução prevista no dia da retirada: esta implementação permite isso. Não há cobrança nesta seleção.
- O requisito de aproximadamente 30 MB/ano é uma estimativa do enunciado, não um resultado medido. Volume de 50 mil empréstimos/ano e carga de cinco usuários não foram certificados por teste de capacidade.

## Qualidade

```bash
ruff check .
ruff format --check .
python manage.py check
python manage.py makemigrations --check --dry-run
coverage run manage.py test
coverage report
coverage html
python manage.py spectacular --file schema.yaml --validate --fail-on-warn
```

Cobertura mínima exigida: **60%**. O relatório mede código customizado de `users`, `books` e `borrowings`, incluindo ramificações; exclui migrations, testes e registro do admin. O workflow de GitHub Actions executa essas verificações quando o projeto for publicado. Consulte `VALIDATION.md` para os resultados efetivamente obtidos.

## Configuração

`.env.sample` documenta as variáveis; o arquivo **não é carregado automaticamente**. Exporte as variáveis no terminal ou configure-as na hospedagem. Não versionar `.env`, senhas, tokens ou banco de dados.

Para PostgreSQL, configure `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST` e opcionalmente `POSTGRES_PORT`. Para exposição pública, configure `DEBUG=0`, `SECRET_KEY` e `ALLOWED_HOSTS`, além de HTTPS, servidor WSGI, arquivos estáticos e banco adequado. `runserver` é destinado a desenvolvimento.

## Organização da entrega

Veja `docs/TASK_BOARD.md` para cartões, dependências e roteiro de revisão. O histórico Git local usa uma branch por tarefa. O quadro [Library-service no Trello](https://trello.com/b/aMO6UPAz/library-service) está criado, com quatro colunas e sete cartões em On Review. O repositório privado [Hmjr03/Library-service](https://github.com/Hmjr03/Library-service) e os [PRs em rascunho](https://github.com/Hmjr03/Library-service/pulls) estão publicados. A versão completa executável está em `submission/flex-complete` e no PR #8; `main` contém a base enquanto aguarda revisão e integração.

Para enviar à Mate, conclua a revisão e integração dos PRs conforme orientação da escola. Os PRs ainda estão em rascunho, sem aprovação ou merge. Como o repositório é privado, o avaliador precisará de acesso. Não há avaliadores convidados nesta etapa. Consulte `docs/TASK_BOARD.md` para a sequência e os links.

## Referências

- Enunciado: https://docs.google.com/document/d/1kO29YuQh2RXB-xAB_jwX7tqRWkyNyf2a2q_M705BvY4/edit
- Simple JWT (cabeçalho): https://django-rest-framework-simplejwt.readthedocs.io/en/latest/settings.html#auth-header-name
- OpenAPI: https://drf-spectacular.readthedocs.io/en/stable/customization.html
- Django: https://docs.djangoproject.com/en/5.2/topics/db/transactions/
