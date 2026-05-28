# Health API QA Framework - Guia de Contribuição

**Health API QA Framework** Este guia irá ajudá-lo a contribuir para o projeto.

---

## Índice

1. [Como Contribuir](#como-contribuir)
2. [Configuração do Ambiente](#configuração-do-ambiente)
3. [Padrões de Código](#padrões-de-código)
4. [Processo de Desenvolvimento](#processo-de-desenvolvimento)
5. [Tipos de Contribuição](#tipos-de-contribuição)
6. [Revisão de Código](#revisão-de-código)
7. [Documentação](#documentação)
8. [Comunidade](#comunidade)

---

## Como Contribuir

### Primeiros Passos

1. **Fork** o repositório
2. **Clone** fork localmente
3. **Configure** o ambiente de desenvolvimento
4. **Crie** uma branch para sua feature/fix
5. **Implemente** mudanças
6. **Teste** mudanças
7. **Submeta** um Pull Request

### Tipos de Contribuições Bem-vindas

- **Bug fixes**
- **Novas funcionalidades**
- **Melhorias na documentação**
- **Novos testes**
- **Otimizações de performance**
- **Melhorias de segurança**
- **Refatorações de código**

---

## Configuração do Ambiente

### Pré-requisitos

- **Python 3.11+**
- **Docker & Docker Compose**
- **Git**
- **Make**

### Setup Rápido

```bash
# 1. Clone o repositório
git clone https://github.com/nathadriele/healthapi-qa-framework.git
cd healthapi-qa-framework

# 2. Configure o ambiente
make setup

# 3. Execute os testes
make test-all

# 4. Inicie a API
make dev
```

### Setup Detalhado

#### 1. **Ambiente Python**
```bash
# Criar ambiente virtual
python -m venv venv

# Ativar ambiente (Linux/Mac)
source venv/bin/activate

# Ativar ambiente (Windows)
venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

#### 2. **Ambiente Docker**
```bash
# Subir serviços
docker-compose -f pipelines/docker-compose.yml up -d

# Verificar status
docker-compose -f pipelines/docker-compose.yml ps
```

#### 3. **Configuração de Desenvolvimento**
```bash
# Instalar pre-commit hooks
pre-commit install

# Configurar variáveis de ambiente
cp .env.example .env
# Editar .env conforme necessário
```

---

## 📝 Padrões de Código

### Python

#### **Formatação**
- **Black** para formatação automática
- **isort** para organização de imports
- **Linha máxima**: 88 caracteres

```bash
# Formatar código
black api/ tests/
isort api/ tests/
```

#### **Linting**
- **Flake8** para linting
- **Pylint** para análise estática
- **Bandit** para segurança

```bash
# Verificar código
flake8 api/ tests/
pylint api/ tests/
bandit -r api/
```

#### **Type Hints**
```python
# ✅
def create_patient(name: str, age: int) -> Dict[str, Any]:
    return {"id": 1, "name": name, "age": age}

# ❌
def create_patient(name, age):
    return {"id": 1, "name": name, "age": age}
```

#### **Docstrings**
```python
def validate_patient_data(data: Dict[str, Any]) -> bool:
    """
    Valida dados de paciente conforme regras de negócio.
    
    Args:
        data: Dicionário com dados do paciente
        
    Returns:
        True se dados são válidos, False caso contrário
        
    Raises:
        ValidationError: Se dados estão em formato inválido
        
    Example:
        >>> validate_patient_data({"name": "João", "age": 30})
        True
    """
    pass
```

### Testes

#### **Estrutura de Testes**
```python
class TestPatientAPI:
    """Testes para API de pacientes"""
    
    def test_create_patient_success(self, api_helper):
        """
        Teste: Criar paciente com dados válidos
        Critério: Deve retornar paciente criado com ID
        """
        # Arrange
        patient_data = {"name": "João", "age": 30}
        
        # Act
        response = api_helper.create_patient(patient_data)
        
        # Assert
        assert response.status_code == 201
        assert "id" in response.json()
```

#### **Naming Conventions**
- **Arquivos**: `test_*.py`
- **Classes**: `TestClassName`
- **Métodos**: `test_method_name_scenario`
- **Fixtures**: `descriptive_fixture_name`

#### **Markers**
```python
@pytest.mark.smoke
def test_health_check():
    """Teste crítico de health check"""
    pass

@pytest.mark.integration
def test_database_connection():
    """Teste de integração com banco"""
    pass
```

---

## Processo de Desenvolvimento

### Git Workflow

#### **Branch Naming**
```
feature/add-patient-validation
bugfix/fix-health-check-timeout
hotfix/security-vulnerability
docs/update-contributing-guide
```

#### **Commit Messages**
Seguimos o padrão [Conventional Commits](https://www.conventionalcommits.org/):

```
type(scope): description

feat(api): add patient validation endpoint
fix(tests): resolve flaky integration test
docs(readme): update installation instructions
test(security): add OWASP injection tests
```

**Tipos válidos**:
- `feat`: Nova funcionalidade
- `fix`: Correção de bug
- `docs`: Documentação
- `test`: Testes
- `refactor`: Refatoração
- `perf`: Melhoria de performance
- `ci`: CI/CD
- `chore`: Tarefas de manutenção

### Pull Request Process

#### **1. Preparação**
```bash
# Criar branch
git checkout -b feature/my-awesome-feature

# Fazer mudanças
# ... código ...

# Commit
git add .
git commit -m "feat(api): add awesome feature"

# Push
git push origin feature/my-awesome-feature
```

#### **2. Pull Request Template**
```markdown
## Descrição
Breve descrição das mudanças implementadas.

## Tipo de Mudança
- [ ] Bug fix
- [ ] Nova funcionalidade
- [ ] Breaking change
- [ ] Documentação

## Como Testar
1. Execute `make test-all`
2. Verifique endpoint `/api/v1/patients`
3. Confirme que testes passam

## Checklist
- [ ] Código segue padrões do projeto
- [ ] Testes foram adicionados/atualizados
- [ ] Documentação foi atualizada
- [ ] CI/CD pipeline passa
```

#### **3. Critérios de Aprovação**
- ✅ CI/CD pipeline verde
- ✅ Pelo menos 1 aprovação de reviewer
- ✅ Cobertura de código mantida (≥85%)
- ✅ Documentação atualizada
- ✅ Sem conflitos de merge

---

## Tipos de Contribuição

### Bug Reports

#### **Template de Bug Report**
```markdown
**Descrição do Bug**
Descrição clara e concisa do bug.

**Comportamento Esperado**
Descrição do que deveria acontecer.

**Comportamento Atual**
Descrição do que está acontecendo.

**Screenshots/Logs**
Se aplicável, adicione screenshots ou logs.

**Ambiente**
- OS: [e.g. Ubuntu 20.04]
- Python: [e.g. 3.11.0]
- Docker: [e.g. 20.10.17]
```

### Feature Requests

#### **Template de Feature Request**
```markdown
**Problema/Necessidade**
Descrição clara do problema que a feature resolve.

**Solução Proposta**
Descrição da solução que você gostaria de ver.

**Alternativas Consideradas**
Outras soluções que você considerou.

**Contexto Adicional**
Qualquer contexto adicional sobre a feature.
```

### Contribuições de Teste

#### **Novos Testes**
- Identifique gaps na cobertura
- Implemente testes seguindo padrões
- Documente cenários de teste
- Adicione markers apropriados

#### **Melhorias em Testes**
- Otimize testes lentos
- Reduza flakiness
- Melhore legibilidade
- Adicione validações

### Contribuições de Documentação

#### **Tipos de Documentação**
- **README**: Informações básicas
- **API Docs**: Documentação de endpoints
- **Guides**: Guias de uso
- **Architecture**: Documentação técnica

#### **Padrões de Documentação**
- Use Markdown
- Inclua exemplos práticos
- Mantenha atualizado
- Seja claro e conciso

---

## Revisão de Código

### Para Reviewers

#### **Checklist de Review**
- [ ] **Funcionalidade**: Código faz o que deveria?
- [ ] **Qualidade**: Código é limpo e legível?
- [ ] **Testes**: Testes adequados foram adicionados?
- [ ] **Performance**: Não há problemas de performance?
- [ ] **Segurança**: Não há vulnerabilidades?
- [ ] **Documentação**: Documentação foi atualizada?


## Documentação

### Estrutura da Documentação

```
docs/
├── README.md              # Visão geral
├── test_plan.md          # Plano de testes
├── qa_strategy.md        # Estratégia de QA
├── contributing.md       # Este arquivo
├── api_docs.md          # Documentação da API
├── architecture.md      # Arquitetura do sistema
└── deployment.md        # Guia de deployment
```

**Dúvidas?** Entre em contato conosco através dos canais de comunicação ou abra uma issue.
