markdown: kramdown

[![Docker Image Build & CI Tests](https://github.com/gestaogovbr/api-pgd/actions/workflows/ci_tests.yml/badge.svg)](https://github.com/gestaogovbr/api-pgd/actions/workflows/ci_tests.yml)

## TL;DR (too long; didn't read)

Para iniciar e configurar os serviços com configurações default e já começar
a desenvolver:

```bash
git clone git@github.com:gestaogovbr/api-pgd.git && \
cd api-pgd && \
make init-env && \
# aqui tem que entrar com a senha de usuário do sistema operacional local
sudo echo "127.0.1.1	fief" | sudo tee -a /etc/hosts && \
make up && \
make fief-config ARGS="-dev"
```

---

## Índice

(para começar a desenvolver)
* [1. Contextualização](#1-contextualização)
* [2. Init, up and down dos serviços em dev](#2-init-up-and-down-dos-serviços-em-dev)
* [3. Rodando testes](#3-rodando-testes)
---
(informações extras)
* [4. Informações e Configurações adicionais](#4-informações-e-configurações-adicionais)
* [5. Arquitetura da solução](#5-arquitetura-da-solução)
* [6. Dicas](#6-dicas)

---

## 1. Contextualização

O [Programa de Gestão](https://www.gov.br/servidor/pt-br/assuntos/programa-de-gestao),
segundo a
[Instrução Normativa Conjunta SEGES-SGPRT n.º 24, de 28 de julho de 2023](https://www.in.gov.br/en/web/dou/-/instrucao-normativa-conjunta-seges-sgprt-/mgi-n-24-de-28-de-julho-de-2023-499593248),
da Secretaria de Gestão e Inovação (SEGES e da Secretaria de Gestão de
Pessoas e de Relações de Trabalho (SGPRT) do
[Ministério da Gestão e da Inovação em Serviços Públicos (MGI)](https://www.gov.br/gestao/pt-br), é um:

> programa indutor de melhoria de desempenho institucional no serviço
> público, com foco na vinculação entre o trabalho dos participantes, as
> entregas das unidades e as estratégias organizacionais.

As atividades mensuradas podem ser realizadas tanto presencialmente
quanto na modalidade de teletrabalho.

O objetivo desta API integradora é receber os dados enviados por diversos
órgãos e entidades da administração, por meio dos seus próprios sistemas
que operacionalizam o PGD no âmbito de sua organização, de modo a
possibilitar a sua consolidação em uma base de dados.

## 2. Init, up and down dos serviços em dev

### 2.1. Instalar Docker CE

Instruções em [https://docs.docker.com/get-docker/](https://docs.docker.com/get-docker/)
variam conforme o sistema operacional.

### 2.2. Clonar o repositório

```bash
git clone git@github.com:gestaogovbr/api-pgd.git
```

### 2.3. Variáveis de ambiente

A gestão de usuários é realizada por uma aplicação chamada [`fief`](https://www.fief.dev/).

Para obter as suas configurações iniciais por meio da geração do arquivo `.env`:

O script em [2.3.1.](#231-opção-1-defalut-e-autogenerated) ou [2.3.2.](#232-opção-2-criação-manual)
irá criar o arquivo `.env` com as configurações necessárias do `fief` para o ambiente.

O template do arquivo `.env` pode ser encontrado em [init/.env.template](init/.env.template).

> As demais configurações da api, banco de dados e adicionais do próprio
> fief são definidas no arquivo [docker-compose.yml](docker-compose.yml)

### Para criar as variáveis de ambiente:

#### 2.3.1. [Opção 1] DEFALUT E AUTOGENERATED

Criado automaticamente as envs `email`, `password` e `fief_main_admin_api_key`
conforme configurações default em [load_fief_env.py](init/load_fief_env.py#L116).

```bash
make init-env
```

#### 2.3.2. [Opção 2] CRIAÇÃO MANUAL

Na execução do `make` abre prompt para definir manualmente `email`, `password`
e `fief_main_admin_api_key`.

> Se desejar criar manualmente também o `fief_main_admin_api_key`:
>
> Obter por python o valor aleatório com o comando:
> `import secrets; secrets.token_urlsafe()`
>
> Senão deixar em branco o prompt `FIEF_MAIN_API_KEY [leave blank if want auto-generated]:`
> que a variável `fief_main_admin_api_key` é gerada automaticamente.

```bash
make init-env ARGS="-it"
```

### 2.4. Configuração do `/etc/hosts`

Na gestão de usuários e controle de acesso da API é usada a aplicação
`fief`. Para o seu correto funcionamento pela
interface `swagger ui`, é **necessário que ela seja alcançável pelo mesmo host, tanto no navegador quanto dentro do container.** Para isso, em ambiente de desenvolvimento, será necessário estabelecer
um alias.
`fief` para o host `localhost` no arquivo `/etc/hosts`.

```bash
sudo echo "127.0.1.1	fief" | sudo tee -a /etc/hosts
```

### 2.5. Iniciando os serviços (`banco`, `api-pgd`, `fief`)

```bash
make up
```

> ⚠️ Caso apareçam erros de permissão em "database", pare os containers
> (`ctrl` + `C`) e digite:
>
> ```bash
> sudo chown -R 999 ./mnt/pgdata/
> ```
>
> Para ajustar as permissões das pastas `./mnt/pgdata/` e todas as suas
> subpastas

### 2.6. Configuração inicial do Fief

Configure o `fief` para incluir dados necessários ao funcionamento da `api-pgd`
em ambiente `dev` (uri de autenticação, campos personalizados de usuários
e outros... template das variáveis de ambiente em [.env.template](init/.env.template)).

```bash
make fief-config ARGS="-dev"
```

### 2.7. Conferir Acessos

  * [`http://localhost:5057`](http://localhost:5057): endpoint da api-pgd
  * [`http://localhost:5057/docs`](http://localhost:5057/docs): swagger ui da api-pgd
  * [`http://fief:8000/admin/`](http://fief:8000/admin/): ui de administração do fief
  * [`http://fief:8000/docs`](http://fief:8000/docs): swagger ui da api do fief

### 2.8. Desligar serviços

  ```bash
  make down
  ```
## 3. Rodando testes

Com os `containers` rodando
([2.5. Iniciando os serviços](#25-iniciando-os-serviços-banco-api-pgd-fief)):

```bash
make tests
```

Para rodar uma bateria de testes específica, especifique o arquivo que
contém os testes desejados. Por exemplo, os testes sobre atividades:

```bash
make test TEST_FILTER=test_create_huge_plano_trabalho
```

---
---

## 4. Informações e Configurações adicionais

>  **[ATENÇÃO]:** Se você chegou até aqui seu ambiente está funcionando e pronto
> para desenvolvimento.
>  As sessões a seguir são instruções para edição de algumas configurações do ambiente.

### 4.1. Usuário administrador e cadastro de usuários

Ao realizar a configuração inicial do `fief` já é criado um usuário
administrador, o qual pode alterar algumas configurações e cadastrar
novos usuários.

O usuário e senha desse usuário administrador ficam configurados nas
variáveis de ambiente `FIEF_MAIN_USER_EMAIL` e `FIEF_MAIN_USER_PASSWORD`
conforme item [2.3. Variáveis de ambiente](#23-variáveis-de-ambiente)

### 4.2. Atualizando imagem do api-pgd

Durante o desenvolvimento é comum a necessidade de inclusão de novas
bibliotecas `python` ou a instalação de novos pacotes `Linux`. Para que
as mudanças surtam efeitos é necessário apagar os containers e refazer a
imagem docker.

> Confira se os containers não estão `up` com o comando `$ docker ps`.
> Caso estejam: `$ make down`

```bash
make build
```

Para subir os serviços novamente:

```bash
make up
```

> Caso deseje subir os serviços com os logs na mesma sessão do terminal:
> usar o comando `$ docker compose up --wait` em vez de `$ make up`

## 5. Arquitetura da solução

O arquivo [`docker-compose.yml`](docker-compose.yml) descreve a `receita`
dos contêineres que compõem a solução. Atualmente são utilizados `3 containers`:

* [db](docker-compose.yml#L4); [postgres:15](https://hub.docker.com/_/postgres)
* [api-pgd](docker-compose.yml#L22); [ghcr.io/gestaogovbr/api-pgd:latest-dev](Dockerfile.dev)
* [fief](docker-compose.yml#L59); [ghcr.io/fief-dev/fief:0.27](https://github.com/fief-dev/fief/blob/main/docker/Dockerfile)

## 6. Dicas

* Para depuração, caso necessite ver como está o banco de dados no ambiente
  local, altere a porta do Postgres no [docker-compose.yml](docker-compose.yml#L8)
  de `"5432"` para `"5432:5432"` e o banco ficará exposto no host via `localhost`.
  Depois, basta usar uma ferramenta como o [dbeaver](https://dbeaver.io/)
  para acessar o banco.
* O `email/login` e `password` do `fief` são definidos no item
  [2.3. Variáveis de ambiente](#23-variáveis-de-ambiente).
  Depois disso eles ficam no arquivo `.env`, bem como o `client_id` e o `client_secret`
  usados na autenticação da API ([api-pgd-swagger-ui](http://localhost:5057/docs),
  [fief-swagger-ui](http://fief:8000/docs)) (variáveis `FIEF_CLIENT_ID` e
  `FIEF_CLIENT_SECRET`, respectivamente).
* Para subir o ambiente usando algum outro banco de dados externo, basta
  redefinir a variável de ambiente `SQLALCHEMY_DATABASE_URL` no
  [docker-compose.yml](docker-compose.yml#L38).


