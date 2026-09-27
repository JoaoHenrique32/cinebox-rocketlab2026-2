Atividade DEV
Você foi designado(a) para desenvolver um módulo de uma aplicação (Frontend e
Backend) de um Sistema de Avaliação de Filmes, inspirado em plataformas como o
Letterboxd. O usuário será o Administrador e o sistema permitirá que o ele veja a lista
dos filmes cadastrados, acesse os detalhes e o histórico de avaliações de cada um,
gerencie o catálogo de filmes e adicione novas notas e resenhas (comentários).
O projeto deve ser criado com a seguinte stack:
● Frontend: Vite - React + Typescript
● Backend: FastAPI (Python)
● Banco de dados: SQLite
Materiais: Para esta tarefa, serão fornecidos alguns recursos para que a atividade
tenha foco nos conceitos passados em aula. Você receberá inicialmente:
1. Um repositório contendo a estrutura base do projeto, o banco de dados
modelado no SQLAlchemy (ORM) e a ferramenta de migração de bancos de
dados Alembic;
a. Link do repositório: https://github.com/Sophia-15/rocketlab2026-2
2. Os arquivos .csv contendo os dados iniciais de filmes para população das
tabelas.
Você deverá desenvolver e versionar o projeto no GitHub com um README
contendo o passo a passo para executar a aplicação.
Requisitos:
● Eu gostaria de poder cadastrar filmes com informações básicas (ex: título,
diretor, ano de lançamento, gênero, sinopse);
● Eu gostaria de poder navegar em um catálogo paginado com todos os filmes
cadastrados;
● Eu gostaria de poder acessar mais detalhes de cada filme, vendo as
informações completas e a lista de avaliações (resenhas e notas) já feitas pelos
usuários;
● Eu gostaria de poder buscar um ou mais filmes específicos através de uma
barra de pesquisa;
● Eu gostaria de poder remover e atualizar os filmes individualmente;
● Eu gostaria de poder adicionar uma nova avaliação a um filme (ex: nota de 1 a
5 estrelas e uma resenha em texto);
● Eu gostaria de poder ver a média geral das avaliações de cada filme.
Você pode explorar a sua criatividade com outras funcionalidades como
documentação (storybook), testes automatizados, autenticação, filtros,
responsividade, caching de consultas…