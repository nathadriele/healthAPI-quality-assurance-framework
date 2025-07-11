# Health API QA Framework - OpenAPI Contract Tests
# Testes de conformidade com especificação OpenAPI 3.0

import pytest
import requests
import yaml
import json
from pathlib import Path
from typing import Dict, Any, List
import jsonschema
from jsonschema import validate, ValidationError

class TestOpenAPICompliance:
    """Testes de conformidade com contratos OpenAPI"""
    
    @pytest.fixture(scope="class")
    def openapi_spec(self):
        """Carrega especificação OpenAPI"""
        spec_path = Path("contracts/health_api.yaml")
        
        if not spec_path.exists():
            pytest.skip("OpenAPI specification not found")
        
        with open(spec_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    @pytest.fixture(scope="class")
    def api_base_url(self):
        """URL base da API"""
        return "http://localhost:8000"
    
    def get_schema_for_response(self, openapi_spec: Dict, path: str, method: str, status_code: str) -> Dict:
        """Extrai schema de resposta da especificação OpenAPI"""
        try:
            path_spec = openapi_spec["paths"][path]
            method_spec = path_spec[method.lower()]
            response_spec = method_spec["responses"][status_code]
            
            # Assumindo JSON como content-type padrão
            content_spec = response_spec["content"]["application/json"]
            schema = content_spec["schema"]
            
            # Resolver referências $ref
            if "$ref" in schema:
                ref_path = schema["$ref"].replace("#/components/schemas/", "")
                schema = openapi_spec["components"]["schemas"][ref_path]
            
            return schema
            
        except KeyError as e:
            pytest.fail(f"Schema not found for {method} {path} {status_code}: {e}")
    
    def validate_response_against_schema(self, response_data: Dict, schema: Dict, openapi_spec: Dict):
        """Valida resposta contra schema OpenAPI"""
        # Resolver todas as referências no schema
        resolved_schema = self.resolve_schema_refs(schema, openapi_spec)
        
        try:
            validate(instance=response_data, schema=resolved_schema)
        except ValidationError as e:
            pytest.fail(f"Response validation failed: {e.message}")
    
    def resolve_schema_refs(self, schema: Dict, openapi_spec: Dict) -> Dict:
        """Resolve referências $ref no schema"""
        if isinstance(schema, dict):
            if "$ref" in schema:
                ref_path = schema["$ref"].replace("#/components/schemas/", "")
                referenced_schema = openapi_spec["components"]["schemas"][ref_path]
                return self.resolve_schema_refs(referenced_schema, openapi_spec)
            else:
                resolved = {}
                for key, value in schema.items():
                    resolved[key] = self.resolve_schema_refs(value, openapi_spec)
                return resolved
        elif isinstance(schema, list):
            return [self.resolve_schema_refs(item, openapi_spec) for item in schema]
        else:
            return schema
    
    @pytest.mark.contracts
    def test_root_endpoint_contract(self, openapi_spec, api_base_url):
        """
        Teste: Contrato do endpoint raiz
        Critério: Resposta deve estar em conformidade com OpenAPI spec
        """
        # Fazer requisição
        response = requests.get(f"{api_base_url}/")
        
        # Verificar status code
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        # Verificar content-type
        content_type = response.headers.get("content-type", "")
        assert content_type.startswith("application/json"), f"Expected JSON, got {content_type}"
        
        # Validar resposta contra schema
        response_data = response.json()
        schema = self.get_schema_for_response(openapi_spec, "/", "get", "200")
        self.validate_response_against_schema(response_data, schema, openapi_spec)
        
        # Validações específicas do contrato
        assert "message" in response_data
        assert "version" in response_data
        assert "status" in response_data
        assert "environment" in response_data
        assert "timestamp" in response_data
        
        # Validar tipos e valores
        assert isinstance(response_data["message"], str)
        assert isinstance(response_data["version"], str)
        assert response_data["status"] in ["operational", "maintenance", "deprecated"]
        assert response_data["environment"] in ["development", "testing", "staging", "production"]
        assert isinstance(response_data["timestamp"], (int, float))
    
    @pytest.mark.contracts
    def test_health_endpoint_contract(self, openapi_spec, api_base_url):
        """
        Teste: Contrato do endpoint de saúde
        Critério: Resposta deve estar em conformidade com OpenAPI spec
        """
        response = requests.get(f"{api_base_url}/health")
        
        assert response.status_code == 200
        
        response_data = response.json()
        schema = self.get_schema_for_response(openapi_spec, "/health", "get", "200")
        self.validate_response_against_schema(response_data, schema, openapi_spec)
        
        # Validações específicas
        required_fields = ["status", "service", "version", "environment", "database", "timestamp"]
        for field in required_fields:
            assert field in response_data, f"Missing required field: {field}"
        
        # Validar enums
        assert response_data["status"] in ["healthy", "unhealthy", "degraded"]
        assert response_data["environment"] in ["development", "testing", "staging", "production"]
    
    @pytest.mark.contracts
    def test_patients_list_contract(self, openapi_spec, api_base_url):
        """
        Teste: Contrato do endpoint de listagem de pacientes
        Critério: Resposta deve estar em conformidade com OpenAPI spec
        """
        response = requests.get(f"{api_base_url}/api/v1/patients")
        
        assert response.status_code == 200
        
        response_data = response.json()
        schema = self.get_schema_for_response(openapi_spec, "/api/v1/patients", "get", "200")
        self.validate_response_against_schema(response_data, schema, openapi_spec)
        
        # Validações específicas
        assert "patients" in response_data
        assert "total" in response_data
        assert isinstance(response_data["patients"], list)
        assert isinstance(response_data["total"], int)
        assert response_data["total"] >= 0
        
        # Validar estrutura dos pacientes
        for patient in response_data["patients"]:
            required_patient_fields = ["id", "name", "age", "email"]
            for field in required_patient_fields:
                assert field in patient, f"Missing patient field: {field}"
            
            # Validar tipos
            assert isinstance(patient["id"], int)
            assert isinstance(patient["name"], str)
            assert isinstance(patient["age"], int)
            assert isinstance(patient["email"], str)
            
            # Validar constraints
            assert patient["id"] >= 1
            assert len(patient["name"]) >= 1
            assert 0 <= patient["age"] <= 150
            assert "@" in patient["email"]  # Validação básica de email
    
    @pytest.mark.contracts
    def test_patient_creation_contract(self, openapi_spec, api_base_url):
        """
        Teste: Contrato de criação de paciente
        Critério: Request e response devem estar em conformidade com OpenAPI spec
        """
        # Dados de teste válidos conforme schema
        patient_data = {
            "name": "João Silva",
            "age": 35,
            "email": "joao.silva@email.com"
        }
        
        response = requests.post(
            f"{api_base_url}/api/v1/patients",
            json=patient_data,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200
        
        response_data = response.json()
        schema = self.get_schema_for_response(openapi_spec, "/api/v1/patients", "post", "200")
        self.validate_response_against_schema(response_data, schema, openapi_spec)
        
        # Validações específicas
        assert "message" in response_data
        assert "patient" in response_data
        
        created_patient = response_data["patient"]
        assert "id" in created_patient
        assert created_patient["name"] == patient_data["name"]
        assert created_patient["age"] == patient_data["age"]
        assert created_patient["email"] == patient_data["email"]
    
    @pytest.mark.contracts
    def test_appointments_list_contract(self, openapi_spec, api_base_url):
        """
        Teste: Contrato do endpoint de listagem de consultas
        Critério: Resposta deve estar em conformidade com OpenAPI spec
        """
        response = requests.get(f"{api_base_url}/api/v1/appointments")
        
        assert response.status_code == 200
        
        response_data = response.json()
        schema = self.get_schema_for_response(openapi_spec, "/api/v1/appointments", "get", "200")
        self.validate_response_against_schema(response_data, schema, openapi_spec)
        
        # Validações específicas
        assert "appointments" in response_data
        assert "total" in response_data
        assert isinstance(response_data["appointments"], list)
        assert isinstance(response_data["total"], int)
        
        # Validar estrutura das consultas
        for appointment in response_data["appointments"]:
            required_fields = ["id", "patient_id", "doctor", "date", "time"]
            for field in required_fields:
                assert field in appointment, f"Missing appointment field: {field}"
            
            # Validar tipos
            assert isinstance(appointment["id"], int)
            assert isinstance(appointment["patient_id"], int)
            assert isinstance(appointment["doctor"], str)
            assert isinstance(appointment["date"], str)
            assert isinstance(appointment["time"], str)
            
            # Validar constraints
            assert appointment["id"] >= 1
            assert appointment["patient_id"] >= 1
            assert len(appointment["doctor"]) >= 1
            
            # Validar formato de data (YYYY-MM-DD)
            import re
            date_pattern = r'^\d{4}-\d{2}-\d{2}$'
            assert re.match(date_pattern, appointment["date"]), f"Invalid date format: {appointment['date']}"
            
            # Validar formato de horário (HH:MM)
            time_pattern = r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$'
            assert re.match(time_pattern, appointment["time"]), f"Invalid time format: {appointment['time']}"
    
    @pytest.mark.contracts
    def test_monitoring_endpoints_contracts(self, openapi_spec, api_base_url):
        """
        Teste: Contratos dos endpoints de monitoramento
        Critério: Todos os endpoints de monitoramento devem estar em conformidade
        """
        monitoring_endpoints = [
            ("/ready", "ReadinessStatus"),
            ("/live", "LivenessStatus"),
            ("/metrics", "SystemMetrics")
        ]
        
        for endpoint, expected_schema_name in monitoring_endpoints:
            response = requests.get(f"{api_base_url}{endpoint}")
            
            assert response.status_code == 200, f"Endpoint {endpoint} failed with {response.status_code}"
            
            response_data = response.json()
            schema = self.get_schema_for_response(openapi_spec, endpoint, "get", "200")
            self.validate_response_against_schema(response_data, schema, openapi_spec)
    
    @pytest.mark.contracts
    def test_error_responses_contract(self, openapi_spec, api_base_url):
        """
        Teste: Contratos de respostas de erro
        Critério: Respostas de erro devem estar em conformidade com OpenAPI spec
        """
        # Testar endpoint inexistente (404)
        response = requests.get(f"{api_base_url}/nonexistent-endpoint")
        
        assert response.status_code == 404
        
        # Verificar se a resposta de erro tem estrutura JSON válida
        try:
            error_data = response.json()
            # Verificar estrutura básica de erro
            assert "detail" in error_data or "error" in error_data
        except json.JSONDecodeError:
            # Se não é JSON, pelo menos não deve vazar informações sensíveis
            error_text = response.text.lower()
            sensitive_info = ["traceback", "internal server error", "database"]
            for info in sensitive_info:
                assert info not in error_text, f"Sensitive info '{info}' in error response"
    
    @pytest.mark.contracts
    def test_content_type_compliance(self, openapi_spec, api_base_url):
        """
        Teste: Conformidade de Content-Type
        Critério: Todos os endpoints devem retornar application/json conforme spec
        """
        endpoints = [
            "/",
            "/health",
            "/ready",
            "/live",
            "/metrics",
            "/api/v1/patients",
            "/api/v1/appointments"
        ]
        
        for endpoint in endpoints:
            response = requests.get(f"{api_base_url}{endpoint}")
            
            if response.status_code == 200:
                content_type = response.headers.get("content-type", "")
                assert content_type.startswith("application/json"), (
                    f"Endpoint {endpoint} returned {content_type}, expected application/json"
                )
    
    @pytest.mark.contracts
    def test_openapi_spec_validity(self, openapi_spec):
        """
        Teste: Validade da especificação OpenAPI
        Critério: Especificação deve ser válida conforme OpenAPI 3.0
        """
        # Verificar campos obrigatórios
        required_fields = ["openapi", "info", "paths"]
        for field in required_fields:
            assert field in openapi_spec, f"Missing required field: {field}"
        
        # Verificar versão OpenAPI
        assert openapi_spec["openapi"].startswith("3.0"), "Must be OpenAPI 3.0"
        
        # Verificar info obrigatória
        info = openapi_spec["info"]
        required_info_fields = ["title", "version"]
        for field in required_info_fields:
            assert field in info, f"Missing required info field: {field}"
        
        # Verificar que há pelo menos um path
        assert len(openapi_spec["paths"]) > 0, "Must have at least one path"
        
        # Verificar estrutura básica dos paths
        for path, path_spec in openapi_spec["paths"].items():
            assert isinstance(path_spec, dict), f"Path {path} must be an object"
            
            # Verificar que há pelo menos um método HTTP
            http_methods = ["get", "post", "put", "delete", "patch", "options", "head"]
            has_method = any(method in path_spec for method in http_methods)
            assert has_method, f"Path {path} must have at least one HTTP method"
