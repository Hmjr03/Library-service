# Verificação da entrega local

Data: 15/09/2026. Ambiente: macOS, Python 3.13.7, SQLite.

## Resultados executados

- **33 testes aprovados**, em 21,652 segundos na execução final da suíte.
- **97% de cobertura total**, incluindo ramificações (242 instruções e 34 ramificações medidas).
- `manage.py check`: nenhum problema identificado.
- `makemigrations --check --dry-run`: nenhuma alteração pendente.
- OpenAPI gerado em `schema.yaml`, validado com `--validate --fail-on-warn`, sem falhas ou avisos.
- Migrations aplicadas com sucesso ao banco local.
- Análise Ruff e formatação verificadas.

## Comportamentos exercitados

Cadastro, hash de senha, tentativa de elevação de privilégios, e-mails duplicados sem distinção de maiúsculas, alteração de senha/perfil, login JWT, renovação, token inválido e cabeçalho personalizado.

Leitura pública dos livros, escrita restrita a staff, CRUD administrativo, dados inválidos e proteção de livros com histórico.

Autenticação obrigatória para empréstimos, isolamento por usuário, consulta administrativa, filtros ativos/inativos, filtros inválidos, retirada sem estoque, data passada, devolução no mesmo dia, devolução repetida, objeto desatualizado e rollback de retirada quando a criação do registro falha.

O teste de lista sem filtros encontrou um erro de interpretação do parâmetro booleano ausente. A implementação foi corrigida; a suíte completa passou após a correção.

## Limites da validação

- A suíte foi executada com SQLite. PostgreSQL está configurável, mas não foi executado neste ambiente.
- Não foi realizado teste de carga de cinco usuários simultâneos nem medição de crescimento anual do banco.
- Swagger/ReDoc e o esquema foram verificados por requisições de teste; integração remota do GitHub Actions não foi executada.
- A cobertura não inclui migrations, testes nem configuração administrativa. Não equivale a garantia de ausência de defeitos.
- GitHub, PRs, Trello e submissão à Mate não foram criados/enviados.
