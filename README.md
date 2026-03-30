# WalletFinance 💰

Um aplicativo web moderno e completo para controle financeiro pessoal. Construído com Python, Flask e arquitetura limpa, o WalletFinance permite gerenciar receitas e despesas, importar dados em massa e visualizar a saúde financeira através de um dashboard analítico interativo.

![Status](https://img.shields.io/badge/Status-Em%20Desenvolvimento-green)
![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-2.0+-lightgrey.svg)
![SQLite](https://img.shields.io/badge/Database-SQLite-blue)

## ✨ Principais Funcionalidades

* **Autenticação Segura:** Cadastro e login de usuários com proteção CSRF em todas as rotas.
* **Gestão de Transações:** CRUD completo (Criar, Ler, Atualizar, Deletar) de receitas e despesas.
* **Integração Relacional:** Categorias dinâmicas amarradas a transações. Alterar o nome de uma categoria atualiza todo o histórico.
* **UX Inteligente (Filtros JS):** Formulários dinâmicos que exibem categorias específicas baseadas no tipo de transação selecionada (Receita ou Despesa).
* **Filtros Avançados:** Busca em banco de dados por mês, tipo, status e descrição, com paginação *Server-side* para suportar milhares de registros.
* **Importação em Massa:** Ferramenta para upload de arquivos `.CSV` que processa centenas de linhas e cria categorias faltantes automaticamente.
* **Exportação de Dados:** Botão de exportação que gera relatórios `.CSV` perfeitamente formatados para o Excel brasileiro (com vírgulas decimais).
* **Dashboard Analítico:** 5 Gráficos interativos (Chart.js) detalhando saldo, evolução anual, despesas por categoria e status de inadimplência.

---

## 🚀 Como executar o projeto localmente

Você pode rodar o WalletFinance utilizando o Docker (Recomendado) ou configurando um ambiente virtual Python tradicional.

### Opção 1: Usando Docker (Recomendado)

O uso do Docker garante que o aplicativo rode com as versões corretas de Python e Node, sem precisar instalar dependências diretamente na sua máquina.

1. **Clone o repositório:**
   ```bash
   git clone https://github.com/brunoramalho01/walletfinance.git
   
   cd walletfinance

## Docker Quickstart

This app can be run completely using `Docker` and `docker compose`. **Using Docker is recommended, as it guarantees the application is run using compatible versions of Python and Node**.

There are three main services:

To run the development version of the app

```bash
docker compose up flask-dev
```

To run the production version of the app

```bash
docker compose up flask-prod
```

The list of `environment:` variables in the `docker compose.yml` file takes precedence over any variables specified in `.env`.

To run any commands using the `Flask CLI`

```bash
docker compose run --rm manage <<COMMAND>>
```

Therefore, to initialize a database you would run

```bash
docker compose run --rm manage db init
docker compose run --rm manage db migrate
docker compose run --rm manage db upgrade
```

A docker volume `node-modules` is created to store NPM packages and is reused across the dev and prod versions of the application. For the purposes of DB testing with `sqlite`, the file `dev.db` is mounted to all containers. This volume mount should be removed from `docker compose.yml` if a production DB server is used.

Go to `http://localhost:8080`. You will see a pretty welcome screen.

### Running locally

Run the following commands to bootstrap your environment if you are unable to run the application using Docker

```bash
cd walletfinance
pip install -r requirements/dev.txt
npm install
npm run-script build
npm start  # run the webpack dev server and flask server using concurrently
```

Go to `http://localhost:5000`. You will see a pretty welcome screen.

#### Database Initialization (locally)

Once you have installed your DBMS, run the following to create your app's
database tables and perform the initial migration

```bash
flask db init
flask db migrate
flask db upgrade
```

## Deployment

When using Docker, reasonable production defaults are set in `docker compose.yml`

```text
FLASK_ENV=production
FLASK_DEBUG=0
```

Therefore, starting the app in "production" mode is as simple as

```bash
docker compose up flask-prod
```

If running without Docker

```bash
export FLASK_ENV=production
export FLASK_DEBUG=0
export DATABASE_URL="<YOUR DATABASE URL>"
npm run build   # build assets with webpack
flask run       # start the flask server
```

## Shell

To open the interactive shell, run

```bash
docker compose run --rm manage shell
flask shell # If running locally without Docker
```

By default, you will have access to the flask `app`.

## Running Tests/Linter

To run all tests, run

```bash
docker compose run --rm manage test
flask test # If running locally without Docker
```

To run the linter, run

```bash
docker compose run --rm manage lint
flask lint # If running locally without Docker
```

The `lint` command will attempt to fix any linting/style errors in the code. If you only want to know if the code will pass CI and do not wish for the linter to make changes, add the `--check` argument.

## Migrations

Whenever a database migration needs to be made. Run the following commands

```bash
docker compose run --rm manage db migrate
flask db migrate # If running locally without Docker
```

This will generate a new migration script. Then run

```bash
docker compose run --rm manage db upgrade
flask db upgrade # If running locally without Docker
```

To apply the migration.

For a full migration command reference, run `docker compose run --rm manage db --help`.

If you will deploy your application remotely (e.g on Heroku) you should add the `migrations` folder to version control.
You can do this after `flask db migrate` by running the following commands

```bash
git add migrations/*
git commit -m "Add migrations"
```

Make sure folder `migrations/versions` is not empty.

## Asset Management

Files placed inside the `assets` directory and its subdirectories
(excluding `js` and `css`) will be copied by webpack's
`file-loader` into the `static/build` directory. In production, the plugin
`Flask-Static-Digest` zips the webpack content and tags them with a MD5 hash.
As a result, you must use the `static_url_for` function when including static content,
as it resolves the correct file name, including the MD5 hash.
For example

```html
<link rel="shortcut icon" href="{{static_url_for('static', filename='build/favicon.ico') }}">
```

If all of your static files are managed this way, then their filenames will change whenever their
contents do, and you can ask Flask to tell web browsers that they
should cache all your assets forever by including the following line
in ``.env``:

```text
SEND_FILE_MAX_AGE_DEFAULT=31556926  # one year
```
