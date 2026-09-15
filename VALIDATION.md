# Verificação da entrega local

Data: 15/09/2026. Ambiente: macOS, Python 3.13.7, SQLite.

## Resultados executados

- **34 testes aprovados** também na versão integrada, em 23,127 segundos, após a distribuição dos testes por etapa.
- **97% de cobertura total**, incluindo ramificações (242 instruções e 34 ramificações medidas).
- `manage.py check`: nenhum problema identificado.
- `makemigrations --check --dry-run`: nenhuma alteração pendente.
- OpenAPI gerado em `schema.yaml`, validado com `--validate --fail-on-warn`, sem falhas ou avisos.
- Migrations aplicadas com sucesso ao banco local.
- Análise Ruff e formatação verificadas.
- Servidor iniciado localmente; Swagger aberto e conferido no navegador. O diálogo jwtAuth mostrou `Name: Authorize`, `In: header` e exigência do prefixo Bearer.

## Comportamentos exercitados

Cadastro, hash de senha, tentativa de elevação de privilégios, e-mails duplicados sem distinção de maiúsculas, alteração de senha/perfil, login JWT, renovação, token inválido e cabeçalho personalizado.

Leitura pública dos livros, escrita restrita a staff, CRUD administrativo, dados inválidos e proteção de livros com histórico.

Autenticação obrigatória para empréstimos, isolamento por usuário, consulta administrativa, filtros ativos/inativos, filtros inválidos, retirada sem estoque, data passada, devolução no mesmo dia, devolução repetida, objeto desatualizado e rollback de retirada quando a criação do registro falha.

O teste de lista sem filtros encontrou um erro de interpretação do parâmetro booleano ausente. A implementação foi corrigida; a suíte completa passou após a correção.

## Revisão das branches

Cada branch passou separadamente por testes, cobertura mínima, Ruff, verificação Django, ausência de migrations pendentes e validação OpenAPI.

| Branch | Testes | Cobertura |
|---|---:|---:|
| task/03-users-jwt | 11 | 96% |
| task/01-books-crud | 13 | 96% |
| task/02-books-permissions | 16 | 96% |
| task/04-borrowing-read | 20 | 97% |
| task/05-borrowing-create | 27 | 98% |
| task/06-borrowing-filters | 30 | 97% |
| task/07-borrowing-return | 34 | 97% |

Correção da revisão: as primeiras branches carregavam apps ainda inexistentes. A lista de apps e as rotas agora correspondem ao conteúdo de cada etapa. Os testes e o workflow passaram a acompanhar cada PR. O histórico publicado foi preservado por commits adicionais e merges de dependências.

## Limites da validação

- A suíte foi executada com SQLite. PostgreSQL está configurável, mas não foi executado neste ambiente.
- Não foi realizado teste de carga de cinco usuários simultâneos nem medição de crescimento anual do banco.
- Swagger/ReDoc e o esquema foram verificados por requisições de teste; o workflow também foi executado com sucesso no GitHub Actions após a publicação (ver registro abaixo).
- A cobertura não inclui migrations, testes nem configuração administrativa. Não equivale a garantia de ausência de defeitos.
- Trello criado e conferido em 15/09/2026: https://trello.com/b/aMO6UPAz/library-service — quatro colunas e sete cartões com descrição.
- GitHub: repositório privado Hmjr03/Library-service criado; nove branches publicadas; sete PRs de tarefas e um PR de integração criados em rascunho.
- GitHub Actions: execução do push f75f8f3 concluída com sucesso: https://github.com/Hmjr03/Library-service/actions/runs/34936764934 (49 segundos).
- Aprovação, merge dos PRs e submissão à Mate ainda estão pendentes.
