# Library-service — Plano de entrega Flex

Nome definido para o repositório GitHub e o quadro Trello: **Library-service**.

Use no Trello as colunas **To Do (Backlog)**, **In Progress (Doing)**, **On Review**, **Done (Completed)**.

Quadro criado e verificado: [Library-service](https://trello.com/b/aMO6UPAz/library-service).

As quatro colunas estão criadas e os sete cartões estão em **On Review**, com branch, dependências e critérios de aceite. O código está implementado localmente; a publicação no GitHub e a revisão dos PRs ainda estão pendentes.

| Ordem | Cartão | Branch | Depende de | Critério de aceite |
|---|---|---|---|---|
| 1 | #3 Usuários por e-mail e JWT | `task/03-users-jwt` | Base | Cadastro seguro, perfil próprio e token pelo cabeçalho Authorize |
| 2 | #1 CRUD de livros | `task/01-books-crud` | Base | Criar, listar, detalhar, atualizar e excluir livros |
| 3 | #2 Permissões de livros | `task/02-books-permissions` | #1, #3 | Leitura pública, escrita somente staff |
| 4 | #4 Lista e detalhe de empréstimos | `task/04-borrowing-read` | #1, #3 | Datas consistentes e livro detalhado |
| 5 | #5 Criação de empréstimos | `task/05-borrowing-create` | #4 | Sem estoque negativo, usuário atual, uma unidade por empréstimo |
| 6 | #6 Filtros e isolamento | `task/06-borrowing-filters` | #4 | Dados próprios para clientes, filtros para staff |
| 7 | #7 Devolução | `task/07-borrowing-return` | #5, #6 | Devolução única e estoque restaurado |

## Revisão sugerida por cartão

1. Descrever o problema e o comportamento implementado.
2. Mostrar os endpoints e exemplos de requisição.
3. Anexar resultados dos testes relacionados.
4. Abrir um PR separado conforme a exigência do enunciado.
5. Mover para Done somente depois da revisão e integração.

## Histórico local e publicação

As branches foram organizadas em sequência por dependência. `main` contém a base inicial e `submission/flex-complete` contém a entrega integrada, testes e documentação. Isso permite publicar as branches sem fingir que PRs já foram revisados.

Abra primeiro `task/03-users-jwt` contra `main`; depois da integração, prossiga na ordem acima. Para evitar duplicação de alterações no próximo PR, prefira merge que preserve os commits; se usar squash, atualize/rebaseie a branch seguinte. Ao final, integre `submission/flex-complete`, que contém as verificações e documentação consolidadas.

Os testes consolidados foram adicionados na branch final. Antes de submeter cada PR, distribua seus testes correspondentes se a revisão da escola exigir validação independente em cada etapa. As branches intermediárias registram etapas de construção; a versão testada e pronta para executar é `submission/flex-complete`.

A escola exige links dos PRs encerrados para submissão. O ZIP e o Git bundle são materiais locais e não substituem esses links.
