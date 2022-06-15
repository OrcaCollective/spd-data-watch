IS_PROD := env_var_or_default("IS_PROD", "")
COMPOSE_FILE := " -f docker-compose.yml" + if IS_PROD == "true" {""} else {" -f docker-compose.override.yml"}
DC := "docker-compose" + COMPOSE_FILE
RUN := DC + " run --rm app"
set dotenv-load := false
set positional-arguments


default:
    @just -lu

# Build all containers
build: dotenv
    {{ DC }} build

# Create a dummy .env file
dotenv:
    @([ ! -f .env ] && touch .env) || true

# Print the docker-compose config
config:
    {{ DC }} config

# Spin up all (or the specified) services
up service="":
    {{ DC }} up -d {{ service }}

# Tear down all services
down:
    {{ DC }} down

# Attach logs to all (or the specified) services
logs service="":
    {{ DC }} logs -f {{ service }}

# Run a command using the web image
run *args:
    {{ RUN }} "$@"

# Pull the docker image
pull:
    {{ DC }} pull

# Pull, build, and deploy all services
deploy:
    -git pull
    @just pull
    @just up

# Run the static checks
lint:
    pre-commit run --all-files

# Run unit tests except acceptance tests
test *pytestargs:
    just run pytest -m "not acceptance" {{ pytestargs }}

# Only run acceptance tests
test-acceptance *pytestargs:
    just run pytest -m "acceptance" {{ pytestargs }}
