# Health API QA Framework - Basic API Tests
# Testes funcionais básicos para demonstrar o framework

import pytest
import requests
import json

class TestBasicAPI:
    """Testes básicos da API para demonstração do framework"""
    
    @pytest.mark.smoke
    def test_api_health_check(self, api_helper):
        """
        Teste: Health check da API
        Critério: API deve estar saudável e responsiva
        """
        # Act
        response = api_helper.make_request("GET", "/health")
        
        # Assert
        api_helper.assert_response_status(response, 200)
        api_helper.assert_response_time(response, 1.0)
        
        data = api_helper.assert_response_json(response)
        
        # Validações específicas
        assert data["status"] == "healthy"
        assert data["service"] == "health-api"
        assert "timestamp" in data
    
    @pytest.mark.smoke
    def test_api_root_endpoint(self, api_helper):
        """
        Teste: Endpoint raiz da API
        Critério: Deve retornar informações da API
        """
        # Act
        response = api_helper.make_request("GET", "/")
        
        # Assert
        api_helper.assert_response_status(response, 200)
        api_helper.assert_response_time(response, 1.0)
        
        data = api_helper.assert_response_json(response)
        
        # Validações
        assert "Health API QA Framework" in data["message"]
        assert data["version"] == "1.0.0"
        assert data["status"] == "operational"
    
    @pytest.mark.smoke
    def test_patients_endpoint_get(self, api_v1_helper):
        """
        Teste: Endpoint GET de pacientes
        Critério: Deve retornar lista de pacientes
        """
        # Act
        response = api_v1_helper.make_request("GET", "/patients")
        
        # Assert
        api_v1_helper.assert_response_status(response, 200)
        api_v1_helper.assert_response_time(response, 2.0)
        
        data = api_v1_helper.assert_response_json(response)
        
        # Validações básicas
        assert "patients" in data
        assert "total" in data
        assert isinstance(data["patients"], list)
        assert isinstance(data["total"], int)
    
    @pytest.mark.smoke
    def test_patients_endpoint_post(self, api_v1_helper):
        """
        Teste: Endpoint POST de pacientes
        Critério: Deve criar novo paciente
        """
        # Arrange
        patient_data = {
            "name": "João Silva",
            "age": 35,
            "email": "joao@email.com"
        }
        
        # Act
        response = api_v1_helper.make_request("POST", "/patients", json=patient_data)
        
        # Assert
        api_v1_helper.assert_response_status(response, 200)
        api_v1_helper.assert_response_time(response, 2.0)
        
        data = api_v1_helper.assert_response_json(response)
        
        # Validações
        assert "message" in data
        assert "patient" in data
        assert "created successfully" in data["message"].lower()
        
        created_patient = data["patient"]
        assert created_patient["name"] == patient_data["name"]
        assert created_patient["age"] == patient_data["age"]
        assert created_patient["email"] == patient_data["email"]
    
    @pytest.mark.smoke
    def test_appointments_endpoint_get(self, api_v1_helper):
        """
        Teste: Endpoint GET de consultas
        Critério: Deve retornar lista de consultas
        """
        # Act
        response = api_v1_helper.make_request("GET", "/appointments")
        
        # Assert
        api_v1_helper.assert_response_status(response, 200)
        api_v1_helper.assert_response_time(response, 2.0)
        
        data = api_v1_helper.assert_response_json(response)
        
        # Validações básicas
        assert "appointments" in data
        assert "total" in data
        assert isinstance(data["appointments"], list)
        assert isinstance(data["total"], int)
    
    @pytest.mark.regression
    def test_api_cors_headers(self, api_helper):
        """
        Teste: Headers CORS da API
        Critério: Deve incluir headers CORS apropriados
        """
        # Act
        response = api_helper.make_request("GET", "/health")
        
        # Assert
        api_helper.assert_response_status(response, 200)
        
        # Verificar headers básicos
        assert "content-type" in response.headers
        assert response.headers["content-type"].startswith("application/json")
    
    @pytest.mark.negative
    def test_invalid_endpoint_404(self, api_helper):
        """
        Teste: Endpoint inexistente
        Critério: Deve retornar 404 para endpoints não existentes
        """
        # Act
        response = api_helper.make_request("GET", "/invalid-endpoint-test")
        
        # Assert
        api_helper.assert_response_status(response, 404)
        api_helper.assert_response_time(response, 1.0)
    
    @pytest.mark.performance
    def test_api_response_time(self, api_helper):
        """
        Teste: Tempo de resposta da API
        Critério: Endpoints devem responder rapidamente
        """
        endpoints = ["/", "/health", "/ready", "/live"]
        
        for endpoint in endpoints:
            # Act
            response = api_helper.make_request("GET", endpoint)
            
            # Assert
            api_helper.assert_response_status(response, 200)
            api_helper.assert_response_time(response, 1.0)  # Máximo 1 segundo
    
    @pytest.mark.security
    def test_api_security_headers(self, api_helper):
        """
        Teste: Headers de segurança
        Critério: API deve incluir headers de segurança básicos
        """
        # Act
        response = api_helper.make_request("GET", "/health")
        
        # Assert
        api_helper.assert_response_status(response, 200)
        
        # Verificar que não há informações sensíveis nos headers
        headers_text = str(response.headers).lower()
        sensitive_info = ["password", "secret", "token", "key"]
        
        for info in sensitive_info:
            assert info not in headers_text, f"Sensitive info '{info}' found in headers"
    
    @pytest.mark.boundary
    def test_api_concurrent_requests(self, api_helper):
        """
        Teste: Requisições concorrentes
        Critério: API deve suportar múltiplas requisições simultâneas
        """
        import threading
        import time
        
        results = []
        
        def make_request():
            try:
                response = api_helper.make_request("GET", "/health")
                results.append(response.status_code)
            except Exception as e:
                results.append(f"Error: {str(e)}")
        
        # Criar e executar threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Aguardar conclusão
        for thread in threads:
            thread.join()
        
        # Validar resultados
        assert len(results) == 5
        for result in results:
            assert result == 200, f"Expected 200, got {result}"
