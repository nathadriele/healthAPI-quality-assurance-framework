# Health API QA Framework - Makefile
# Automação de comandos para desenvolvimento e CI/CD

.PHONY: help setup dev test-all test-unit test-functional test-integration test-performance test-security test-contracts coverage lint sonar build clean docker-up docker-down

# Configurações
PYTHON := python3
PIP := pip3
PYTEST := pytest
DOCKER_COMPOSE := docker-compose
API_PORT := 8000
TEST_WORKERS := 4

# Cores para output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[1;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

help: ## Mostra esta mensagem de ajuda
	@echo "$(BLUE)Health API QA Framework - Comandos Disponíveis$(NC)"
	@echo "=================================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

setup: ## Configura ambiente completo de desenvolvimento
	@echo "$(YELLOW)🔧 Configurando ambiente de desenvolvimento...$(NC)"
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	$(PIP) install -r requirements-dev.txt
	pre-commit install
	@echo "$(GREEN)✅ Ambiente configurado com sucesso!$(NC)"

dev: ## Inicia API em modo desenvolvimento
	@echo "$(YELLOW)🚀 Iniciando API em modo desenvolvimento...$(NC)"
	cd api && uvicorn main:app --reload --host 0.0.0.0 --port $(API_PORT)

test-all: test-unit test-functional test-integration test-contracts ## Executa todos os testes
	@echo "$(GREEN)✅ Todos os testes executados com sucesso!$(NC)"

test-unit: ## Executa testes unitários
	@echo "$(YELLOW)🧪 Executando testes unitários...$(NC)"
	$(PYTEST) tests/unit/ -v --cov=api --cov-report=html --cov-report=xml --cov-report=term-missing
	@echo "$(GREEN)✅ Testes unitários concluídos!$(NC)"

test-functional: ## Executa testes funcionais de API
	@echo "$(YELLOW)🔍 Executando testes funcionais...$(NC)"
	$(PYTEST) tests/functional/ -v --workers=$(TEST_WORKERS) --html=docs/coverage_report/functional_report.html
	@echo "$(GREEN)✅ Testes funcionais concluídos!$(NC)"

test-integration: ## Executa testes de integração
	@echo "$(YELLOW)🔗 Executando testes de integração...$(NC)"
	$(PYTEST) tests/integration/ -v --html=docs/coverage_report/integration_report.html
	@echo "$(GREEN)✅ Testes de integração concluídos!$(NC)"

test-performance: ## Executa testes de performance com Locust
	@echo "$(YELLOW)⚡ Executando testes de performance...$(NC)"
	cd tests/performance && locust --headless --users 100 --spawn-rate 10 --run-time 60s --host http://localhost:$(API_PORT) --html ../../docs/coverage_report/performance_report.html
	@echo "$(GREEN)✅ Testes de performance concluídos!$(NC)"

test-security: ## Executa testes de segurança OWASP ZAP
	@echo "$(YELLOW)🔒 Executando testes de segurança...$(NC)"
	$(PYTHON) tests/security/owasp_zap_scan.py
	@echo "$(GREEN)✅ Testes de segurança concluídos!$(NC)"

test-contracts: ## Valida contratos OpenAPI
	@echo "$(YELLOW)📋 Validando contratos OpenAPI...$(NC)"
	$(PYTEST) tests/contracts/ -v
	dredd contracts/health_api.yaml http://localhost:$(API_PORT)
	@echo "$(GREEN)✅ Validação de contratos concluída!$(NC)"

coverage: ## Gera relatório de cobertura completo
	@echo "$(YELLOW)📊 Gerando relatório de cobertura...$(NC)"
	$(PYTEST) --cov=api --cov-report=html:docs/coverage_report/htmlcov --cov-report=xml:docs/coverage_report/coverage.xml --cov-report=term-missing
	@echo "$(GREEN)✅ Relatório de cobertura gerado em docs/coverage_report/$(NC)"

lint: ## Executa análise estática de código
	@echo "$(YELLOW)🔍 Executando análise estática...$(NC)"
	black --check api/ tests/
	flake8 api/ tests/
	pylint api/ tests/
	bandit -r api/
	safety check
	@echo "$(GREEN)✅ Análise estática concluída!$(NC)"

format: ## Formata código com Black
	@echo "$(YELLOW)🎨 Formatando código...$(NC)"
	black api/ tests/
	isort api/ tests/
	@echo "$(GREEN)✅ Código formatado!$(NC)"

sonar: ## Executa análise SonarQube local
	@echo "$(YELLOW)📈 Executando análise SonarQube...$(NC)"
	sonar-scanner
	@echo "$(GREEN)✅ Análise SonarQube concluída!$(NC)"

build: ## Build da aplicação
	@echo "$(YELLOW)🏗️ Fazendo build da aplicação...$(NC)"
	docker build -t healthapi-qa:latest .
	@echo "$(GREEN)✅ Build concluído!$(NC)"

docker-up: ## Sobe ambiente Docker completo
	@echo "$(YELLOW)🐳 Subindo ambiente Docker...$(NC)"
	$(DOCKER_COMPOSE) up -d
	@echo "$(GREEN)✅ Ambiente Docker ativo!$(NC)"

docker-down: ## Para ambiente Docker
	@echo "$(YELLOW)🐳 Parando ambiente Docker...$(NC)"
	$(DOCKER_COMPOSE) down
	@echo "$(GREEN)✅ Ambiente Docker parado!$(NC)"

clean: ## Limpa arquivos temporários e cache
	@echo "$(YELLOW)🧹 Limpando arquivos temporários...$(NC)"
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	rm -rf .coverage htmlcov/ .tox/ dist/ build/
	@echo "$(GREEN)✅ Limpeza concluída!$(NC)"

install-hooks: ## Instala pre-commit hooks
	@echo "$(YELLOW)🪝 Instalando pre-commit hooks...$(NC)"
	pre-commit install
	pre-commit install --hook-type commit-msg
	@echo "$(GREEN)✅ Hooks instalados!$(NC)"

ci-pipeline: lint test-all test-security coverage ## Pipeline completo de CI
	@echo "$(GREEN)🎉 Pipeline de CI executado com sucesso!$(NC)"

deploy-staging: ## Deploy para ambiente de staging
	@echo "$(YELLOW)🚀 Fazendo deploy para staging...$(NC)"
	# Adicionar comandos de deploy específicos
	@echo "$(GREEN)✅ Deploy para staging concluído!$(NC)"

deploy-prod: ## Deploy para produção
	@echo "$(YELLOW)🚀 Fazendo deploy para produção...$(NC)"
	# Adicionar comandos de deploy específicos
	@echo "$(GREEN)✅ Deploy para produção concluído!$(NC)"

# Default target
.DEFAULT_GOAL := help
