# Health API QA Framework

<img width="1890" height="904" alt="Captura de tela 2025-07-09 190022" src="https://github.com/user-attachments/assets/df4b2c5b-1d8d-4595-8e81-059a01c3ac83" />

##  Visão Geral

Framework de QA abrangente para APIs de saúde, seguindo padrões internacionais **ISTQB**, **ISO/IEC 29119** e **OWASP**. Implementa estratégia de **Shift-Left Testing** com automação completa em pipeline CI/CD.

### Arquitetura de Testes

```
healthapi-qa-framework/
├── api/                    # Sistema Sob Teste (SUT) - FastAPI
├── tests/
│   ├── functional/         # Testes de API (PyTest + Requests)
│   ├── integration/        # Integração entre módulos
│   ├── performance/        # Testes de carga (Locust)
│   └── security/           # Testes OWASP ZAP automatizados
├── contracts/              # OpenAPI 3.0 Specifications
├── pipelines/              # CI/CD GitHub Actions
├── scripts/                # Utilitários e automação
└── docs/                   # Documentação e métricas
```

## Quick Start

### Pré-requisitos
- Python 3.9+
- Docker & Docker Compose
- Node.js 16+ (para ferramentas auxiliares)
- Make (opcional, mas recomendado)

### Instalação

```bash
# Clone o repositório
git clone https://github.com/your-org/healthapi-qa-framework.git
cd healthapi-qa-framework

# Setup completo do ambiente
make setup

# Executar todos os testes
make test-all

# Executar API em modo desenvolvimento
make dev
```

## Estratégia de Testes

### Pirâmide de Testes Implementada

| Nível | Tipo | Ferramenta | Cobertura |
|-------|------|------------|-----------|
| **Unit** | Testes unitários da API | PyTest | 90%+ |
| **Integration** | Integração entre módulos | PyTest + TestContainers | 80%+ |
| **Contract** | Validação OpenAPI | Pact/Dredd | 100% |
| **Functional** | Testes de API E2E | PyTest + Requests | 95%+ |
| **Performance** | Carga e stress | Locust | SLA compliance |
| **Security** | Vulnerabilidades OWASP | ZAP + Bandit | Zero critical |

### Critérios de Qualidade (Quality Gates)

- ✅ **Cobertura de código**: ≥ 85%
- ✅ **Testes funcionais**: 100% pass rate
- ✅ **Performance**: Response time < 200ms (P95)
- ✅ **Segurança**: Zero vulnerabilidades críticas/altas
- ✅ **Contratos**: 100% compliance OpenAPI
- ✅ **Code Quality**: SonarQube Grade A

## Comandos Principais

```bash
# Desenvolvimento
make dev                    # Inicia API em modo desenvolvimento
make test-unit             # Executa testes unitários
make test-functional       # Executa testes funcionais
make test-integration      # Executa testes de integração

# Performance & Segurança
make test-performance      # Executa testes de carga
make test-security         # Executa scan de segurança
make test-contracts        # Valida contratos OpenAPI

# Qualidade & Relatórios
make coverage              # Gera relatório de cobertura
make lint                  # Análise estática de código
make sonar                 # Análise SonarQube local

# CI/CD
make build                 # Build da aplicação
make deploy-staging        # Deploy para staging
make deploy-prod           # Deploy para produção
```

## Configuração

### Variáveis de Ambiente

```bash
# API Configuration
API_HOST=localhost
API_PORT=8000
DATABASE_URL=postgresql://user:pass@localhost:5432/healthapi

# Test Configuration
TEST_ENVIRONMENT=local
PARALLEL_WORKERS=4
TEST_TIMEOUT=30

# Security
OWASP_ZAP_URL=http://localhost:8080
SECURITY_SCAN_LEVEL=medium

# Performance
LOCUST_USERS=100
LOCUST_SPAWN_RATE=10
PERFORMANCE_THRESHOLD_P95=200
```

## Métricas e Monitoramento

- **Dashboard Grafana**: Métricas de performance em tempo real
- **Relatórios Allure**: Resultados detalhados de testes
- **SonarQube**: Qualidade de código e technical debt
- **OWASP ZAP**: Relatórios de segurança automatizados

## Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

### Padrões de Código

- **Python**: PEP 8 + Black formatter
- **Commits**: Conventional Commits
- **Testes**: AAA Pattern (Arrange, Act, Assert)
- **Documentação**: Docstrings + Sphinx

## Documentação

- [Plano de Testes](docs/test_plan.md)
- [Estratégia de QA](docs/qa_strategy.md)
- [Guia de Contribuição](docs/contributing.md)
- [API Documentation](docs/api_docs.md)
