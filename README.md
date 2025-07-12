## Health API QA Framework

<img width="3037" height="997" alt="image" src="https://github.com/user-attachments/assets/07b5bd75-b712-47af-b604-c7008244c45f" />

Framework de QA abrangente para APIs de saúde, seguindo os padrões ISTQB, ISO/IEC 29119 e OWASP. Estruturado para suportar automação completa, testes contínuos e qualidade em todas as etapas do ciclo de vida da API.

### Arquitetura de Testes

```
healthapi-qa-framework/
├── api/                    # Sistema Sob Teste (FastAPI)
├── tests/
│   ├── functional/         # Testes funcionais (PyTest + Requests)
│   ├── integration/        # Testes de integração
│   ├── performance/        # Testes de performance (Locust)
│   └── security/           # Testes de segurança (ZAP)
├── contracts/              # Especificações OpenAPI 3.0
├── pipelines/              # Workflows GitHub Actions
├── scripts/                # Scripts utilitários
└── docs/                   # Documentação e métricas
```

<img width="541" height="362" alt="image" src="https://github.com/user-attachments/assets/8369b0ec-b8d7-4dc0-b8b0-3e9d6a46780f" />

### Quick Start

#### Pré-requisitos
- Python 3.9+
- Docker e Docker Compose
- Node.js 16+
- Make 

#### Instalação

```
git clone https://github.com/nathadriele/healthapi-qa-framework.git
cd healthapi-qa-framework
make setup
make test-all
make dev
```

### Estratégia de Testes

<img width="751" height="482" alt="image" src="https://github.com/user-attachments/assets/526ce742-692e-4ba6-979e-771c39aa4c9c" />

### Quality Gates

- ✅ Cobertura de código ≥ 85%
- ✅ Testes funcionais: 100% sucesso
- ✅ Performance: < 200ms (P95)
- ✅ Segurança: zero vulnerabilidades críticas
- ✅ Contratos: 100% compliance OpenAPI
- ✅ Code Quality: SonarQube Grade A

### Comandos Principais

<img width="246" height="550" alt="image" src="https://github.com/user-attachments/assets/07e07a9e-e703-4876-a0b6-1fd5843e4cd6" />

### Variáveis de Ambiente

<img width="548" height="500" alt="image" src="https://github.com/user-attachments/assets/93d6a42d-18c0-4907-90f1-d271d1ef856c" />

### Métricas e Monitoramento

- Grafana: Métricas em tempo real
- Allure Reports: Detalhamento dos testes
- SonarQube: Qualidade de código
- OWASP ZAP: Relatórios de vulnerabilidades

### Documentação

- ✅ docs/test_plan.md – Plano de Testes
- ✅ docs/qa_strategy.md – Estratégia de QA
- ✅ docs/contributing.md – Guia de Contribuição
- ✅ docs/api_docs.md – Documentação da API
