# Health API QA Framework - PyTest Configuration
# Configurações globais, fixtures e utilitários para testes

import pytest
import requests
import json
import time
from typing import Dict, Any, Generator
from dataclasses import dataclass
import logging

# Configuração de logging para testes
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configurações base
BASE_URL = "http://localhost:8000"
API_VERSION = "v1"
API_BASE_URL = f"{BASE_URL}/api/{API_VERSION}"

@dataclass
class TestConfig:
    """Configuração centralizada para testes"""
    base_url: str = BASE_URL
    api_base_url: str = API_BASE_URL
    timeout: int = 30
    retry_attempts: int = 3
    retry_delay: float = 1.0
    
    # Headers padrão
    default_headers: Dict[str, str] = None
    
    def __post_init__(self):
        if self.default_headers is None:
            self.default_headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "HealthAPI-QA-Framework/1.0.0"
            }

@pytest.fixture(scope="session")
def test_config() -> TestConfig:
    """Fixture de configuração global para testes"""
    return TestConfig()

@pytest.fixture(scope="session")
def api_client(test_config: TestConfig) -> Generator[requests.Session, None, None]:
    """Fixture de cliente HTTP configurado para testes de API"""
    session = requests.Session()
    session.headers.update(test_config.default_headers)
    session.timeout = test_config.timeout
    
    # Verificar se a API está disponível
    max_attempts = 10
    for attempt in range(max_attempts):
        try:
            response = session.get(f"{test_config.base_url}/health")
            if response.status_code == 200:
                logger.info("✅ API está disponível para testes")
                break
        except requests.exceptions.ConnectionError:
            if attempt == max_attempts - 1:
                pytest.fail("❌ API não está disponível. Certifique-se de que está rodando.")
            logger.warning(f"⏳ Tentativa {attempt + 1}/{max_attempts} - Aguardando API...")
            time.sleep(2)
    
    yield session
    session.close()

@pytest.fixture
def sample_patient_data() -> Dict[str, Any]:
    """Fixture com dados de exemplo para paciente"""
    return {
        "name": "João Silva",
        "age": 35,
        "email": "joao.silva@email.com",
        "phone": "+55 11 99999-9999",
        "cpf": "123.456.789-00",
        "address": {
            "street": "Rua das Flores, 123",
            "city": "São Paulo",
            "state": "SP",
            "zip_code": "01234-567"
        }
    }

@pytest.fixture
def sample_appointment_data() -> Dict[str, Any]:
    """Fixture com dados de exemplo para consulta"""
    return {
        "patient_id": 1,
        "doctor": "Dr. Maria Santos",
        "specialty": "Cardiologia",
        "date": "2025-07-15",
        "time": "14:30",
        "duration": 30,
        "notes": "Consulta de rotina"
    }

@pytest.fixture
def invalid_patient_data() -> Dict[str, Any]:
    """Fixture com dados inválidos para testes negativos"""
    return {
        "name": "",  # Nome vazio
        "age": -5,   # Idade negativa
        "email": "email-invalido",  # Email inválido
        "phone": "123",  # Telefone muito curto
    }

class APITestHelper:
    """Classe auxiliar para testes de API"""
    
    def __init__(self, client: requests.Session, base_url: str):
        self.client = client
        self.base_url = base_url
    
    def make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Faz requisição HTTP com retry automático"""
        url = f"{self.base_url}{endpoint}"
        
        for attempt in range(3):
            try:
                response = self.client.request(method, url, **kwargs)
                return response
            except requests.exceptions.RequestException as e:
                if attempt == 2:  # Última tentativa
                    raise e
                time.sleep(1)
    
    def assert_response_status(self, response: requests.Response, expected_status: int):
        """Valida status code da resposta"""
        assert response.status_code == expected_status, (
            f"Expected status {expected_status}, got {response.status_code}. "
            f"Response: {response.text}"
        )
    
    def assert_response_json(self, response: requests.Response) -> Dict[str, Any]:
        """Valida e retorna JSON da resposta"""
        assert response.headers.get("content-type", "").startswith("application/json"), (
            f"Expected JSON response, got {response.headers.get('content-type')}"
        )
        
        try:
            return response.json()
        except json.JSONDecodeError as e:
            pytest.fail(f"Invalid JSON response: {e}. Response: {response.text}")
    
    def assert_response_time(self, response: requests.Response, max_time: float = 2.0):
        """Valida tempo de resposta"""
        response_time = response.elapsed.total_seconds()
        assert response_time <= max_time, (
            f"Response time {response_time}s exceeded maximum {max_time}s"
        )
    
    def assert_required_fields(self, data: Dict[str, Any], required_fields: list):
        """Valida presença de campos obrigatórios"""
        missing_fields = [field for field in required_fields if field not in data]
        assert not missing_fields, f"Missing required fields: {missing_fields}"

@pytest.fixture
def api_helper(api_client: requests.Session, test_config: TestConfig) -> APITestHelper:
    """Fixture do helper para testes de API"""
    return APITestHelper(api_client, test_config.base_url)

@pytest.fixture
def api_v1_helper(api_client: requests.Session, test_config: TestConfig) -> APITestHelper:
    """Fixture do helper para testes de API v1"""
    return APITestHelper(api_client, test_config.api_base_url)

# Hooks do PyTest
def pytest_configure(config):
    """Configuração inicial do PyTest"""
    logger.info("🚀 Iniciando Health API QA Framework Tests")

def pytest_unconfigure(config):
    """Limpeza final do PyTest"""
    logger.info("✅ Health API QA Framework Tests concluídos")

def pytest_runtest_setup(item):
    """Setup antes de cada teste"""
    logger.info(f"🧪 Executando teste: {item.name}")

def pytest_runtest_teardown(item, nextitem):
    """Teardown após cada teste"""
    logger.info(f"✅ Teste concluído: {item.name}")

# Markers personalizados
def pytest_configure(config):
    """Registra markers personalizados"""
    config.addinivalue_line("markers", "smoke: marca testes de smoke")
    config.addinivalue_line("markers", "regression: marca testes de regressão")
    config.addinivalue_line("markers", "integration: marca testes de integração")
    config.addinivalue_line("markers", "performance: marca testes de performance")
    config.addinivalue_line("markers", "security: marca testes de segurança")
    config.addinivalue_line("markers", "negative: marca testes negativos")
    config.addinivalue_line("markers", "boundary: marca testes de valores limite")

# Parametrização para diferentes ambientes
@pytest.fixture(params=["development", "staging"])
def environment(request):
    """Fixture para testes em diferentes ambientes"""
    return request.param
