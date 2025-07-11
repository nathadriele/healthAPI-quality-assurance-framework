# Health API QA Framework - Health Endpoints Tests
# Testes funcionais para endpoints de saúde e monitoramento

import pytest
import requests
from typing import Dict, Any
import time

class TestHealthEndpoints:
    """Testes para endpoints de saúde e monitoramento da API"""
    
    @pytest.mark.smoke
    def test_root_endpoint(self, api_helper):
        """
        Teste: Endpoint raiz da API
        Critério: Deve retornar informações básicas da API
        """
        # Arrange & Act
        response = api_helper.make_request("GET", "/")
        
        # Assert
        api_helper.assert_response_status(response, 200)
        api_helper.assert_response_time(response, 1.0)
        
        data = api_helper.assert_response_json(response)
        
        # Validar campos obrigatórios
        required_fields = ["message", "version", "status", "environment"]
        api_helper.assert_required_fields(data, required_fields)
        
        # Validar valores específicos
        assert data["version"] == "1.0.0"
        assert data["status"] == "operational"
        assert "Health API QA Framework" in data["message"]
    
    @pytest.mark.smoke
    def test_health_check_endpoint(self, api_helper):
        """
        Teste: Health check endpoint
        Critério: Deve retornar status healthy com informações do sistema
        """
        # Arrange & Act
        response = api_helper.make_request("GET", "/health")
        
        # Assert
        api_helper.assert_response_status(response, 200)
        api_helper.assert_response_time(response, 1.0)
        
        data = api_helper.assert_response_json(response)
        
        # Validar estrutura da resposta
        required_fields = ["status", "service", "version", "environment", "database", "timestamp"]
        api_helper.assert_required_fields(data, required_fields)
        
        # Validar valores
        assert data["status"] == "healthy"
        assert data["service"] == "health-api"
        assert data["version"] == "1.0.0"
        assert data["database"] == "simulated"
        assert isinstance(data["timestamp"], (int, float))
        assert data["timestamp"] > 0
    
    @pytest.mark.smoke
    def test_readiness_probe(self, api_helper):
        """
        Teste: Readiness probe para Kubernetes
        Critério: Deve indicar que a aplicação está pronta
        """
        # Arrange & Act
        response = api_helper.make_request("GET", "/ready")
        
        # Assert
        api_helper.assert_response_status(response, 200)
        api_helper.assert_response_time(response, 0.5)
        
        data = api_helper.assert_response_json(response)
        
        # Validar resposta
        assert data["status"] == "ready"
        assert data["service"] == "health-api"
        assert "timestamp" in data
    
    @pytest.mark.smoke
    def test_liveness_probe(self, api_helper):
        """
        Teste: Liveness probe para Kubernetes
        Critério: Deve indicar que a aplicação está viva
        """
        # Arrange & Act
        response = api_helper.make_request("GET", "/live")
        
        # Assert
        api_helper.assert_response_status(response, 200)
        api_helper.assert_response_time(response, 0.5)
        
        data = api_helper.assert_response_json(response)
        
        # Validar resposta
        assert data["status"] == "alive"
        assert data["service"] == "health-api"
        assert "timestamp" in data
    
    @pytest.mark.regression
    def test_metrics_endpoint(self, api_helper):
        """
        Teste: Endpoint de métricas
        Critério: Deve retornar métricas básicas do sistema
        """
        # Arrange & Act
        response = api_helper.make_request("GET", "/metrics")
        
        # Assert
        api_helper.assert_response_status(response, 200)
        api_helper.assert_response_time(response, 1.0)
        
        data = api_helper.assert_response_json(response)
        
        # Validar métricas básicas
        expected_metrics = [
            "http_requests_total",
            "http_request_duration_seconds",
            "database_connections_active",
            "memory_usage_bytes"
        ]
        
        for metric in expected_metrics:
            assert metric in data, f"Métrica {metric} não encontrada"
            assert isinstance(data[metric], (int, float)), f"Métrica {metric} deve ser numérica"
    
    @pytest.mark.regression
    def test_health_endpoint_consistency(self, api_helper):
        """
        Teste: Consistência do health endpoint
        Critério: Múltiplas chamadas devem retornar dados consistentes
        """
        responses = []
        
        # Fazer múltiplas requisições
        for _ in range(5):
            response = api_helper.make_request("GET", "/health")
            api_helper.assert_response_status(response, 200)
            responses.append(api_helper.assert_response_json(response))
            time.sleep(0.1)
        
        # Validar consistência
        first_response = responses[0]
        for response in responses[1:]:
            # Campos que devem ser consistentes
            consistent_fields = ["status", "service", "version", "environment", "database"]
            for field in consistent_fields:
                assert response[field] == first_response[field], (
                    f"Campo {field} inconsistente: {response[field]} != {first_response[field]}"
                )
    
    @pytest.mark.negative
    def test_invalid_endpoint(self, api_helper):
        """
        Teste: Endpoint inexistente
        Critério: Deve retornar 404 para endpoints não existentes
        """
        # Arrange & Act
        response = api_helper.make_request("GET", "/invalid-endpoint")
        
        # Assert
        api_helper.assert_response_status(response, 404)
        api_helper.assert_response_time(response, 1.0)
    
    @pytest.mark.negative
    def test_invalid_method(self, api_helper):
        """
        Teste: Método HTTP inválido
        Critério: Deve retornar 405 para métodos não permitidos
        """
        # Arrange & Act
        response = api_helper.make_request("DELETE", "/health")
        
        # Assert
        api_helper.assert_response_status(response, 405)
        api_helper.assert_response_time(response, 1.0)
    
    @pytest.mark.performance
    def test_health_endpoint_performance(self, api_helper):
        """
        Teste: Performance do health endpoint
        Critério: Deve responder em menos de 100ms
        """
        # Arrange
        max_response_time = 0.1  # 100ms
        
        # Act
        start_time = time.time()
        response = api_helper.make_request("GET", "/health")
        end_time = time.time()
        
        # Assert
        api_helper.assert_response_status(response, 200)
        
        response_time = end_time - start_time
        assert response_time <= max_response_time, (
            f"Response time {response_time:.3f}s exceeded {max_response_time}s"
        )
    
    @pytest.mark.boundary
    def test_concurrent_health_requests(self, api_helper):
        """
        Teste: Requisições concorrentes ao health endpoint
        Critério: Deve suportar múltiplas requisições simultâneas
        """
        import threading
        import queue
        
        # Arrange
        num_threads = 10
        results = queue.Queue()
        
        def make_health_request():
            try:
                response = api_helper.make_request("GET", "/health")
                results.put(("success", response.status_code))
            except Exception as e:
                results.put(("error", str(e)))
        
        # Act
        threads = []
        for _ in range(num_threads):
            thread = threading.Thread(target=make_health_request)
            threads.append(thread)
            thread.start()
        
        # Aguardar conclusão
        for thread in threads:
            thread.join()
        
        # Assert
        success_count = 0
        while not results.empty():
            result_type, result_value = results.get()
            if result_type == "success":
                assert result_value == 200
                success_count += 1
            else:
                pytest.fail(f"Request failed: {result_value}")
        
        assert success_count == num_threads, f"Expected {num_threads} successful requests, got {success_count}"
