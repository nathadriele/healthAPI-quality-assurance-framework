# Health API QA Framework - System Health Integration Tests
# Testes de integração para verificar saúde geral do sistema

import pytest
import requests
import time
import json
from typing import Dict, Any, List

class TestSystemHealthIntegration:
    """Testes de integração para saúde do sistema"""
    
    @pytest.mark.integration
    def test_system_startup_sequence(self, api_helper):
        """
        Teste: Sequência de inicialização do sistema
        Critério: Todos os endpoints de saúde devem estar funcionais
        """
        health_endpoints = [
            ("/", "root"),
            ("/health", "health_check"),
            ("/ready", "readiness"),
            ("/live", "liveness")
        ]
        
        results = {}
        
        for endpoint, name in health_endpoints:
            response = api_helper.make_request("GET", endpoint)
            
            # Todos devem retornar 200
            api_helper.assert_response_status(response, 200)
            api_helper.assert_response_time(response, 2.0)
            
            data = api_helper.assert_response_json(response)
            results[name] = {
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds(),
                "data": data
            }
        
        # Validar dados específicos de cada endpoint
        assert "Health API QA Framework" in results["root"]["data"]["message"]
        assert results["health_check"]["data"]["status"] == "healthy"
        assert results["readiness"]["data"]["status"] == "ready"
        assert results["liveness"]["data"]["status"] == "alive"
        
        # Validar que todos têm timestamp
        for name, result in results.items():
            assert "timestamp" in result["data"], f"Endpoint {name} missing timestamp"
            assert isinstance(result["data"]["timestamp"], (int, float))
    
    @pytest.mark.integration
    def test_api_endpoints_integration(self, api_v1_helper):
        """
        Teste: Integração entre endpoints da API
        Critério: Todos os endpoints principais devem estar funcionais
        """
        api_endpoints = [
            ("/patients", "GET"),
            ("/appointments", "GET")
        ]
        
        results = {}
        
        for endpoint, method in api_endpoints:
            response = api_v1_helper.make_request(method, endpoint)
            
            api_v1_helper.assert_response_status(response, 200)
            api_v1_helper.assert_response_time(response, 3.0)
            
            data = api_v1_helper.assert_response_json(response)
            results[endpoint] = {
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds(),
                "data": data
            }
        
        # Validar estrutura consistente
        for endpoint, result in results.items():
            data = result["data"]
            main_field = endpoint.split("/")[-1]  # patients ou appointments
            
            assert main_field in data, f"Missing main field {main_field} in {endpoint}"
            assert "total" in data, f"Missing total field in {endpoint}"
            assert isinstance(data[main_field], list)
            assert isinstance(data["total"], int)
            assert data["total"] >= 0
    
    @pytest.mark.integration
    def test_system_load_handling(self, api_helper, api_v1_helper):
        """
        Teste: Capacidade do sistema de lidar com carga
        Critério: Sistema deve manter performance sob carga moderada
        """
        import threading
        import queue
        
        results = queue.Queue()
        num_requests = 20
        
        def make_load_requests():
            try:
                # Mix de requisições para diferentes endpoints
                endpoints_and_helpers = [
                    (api_helper, "/health"),
                    (api_helper, "/"),
                    (api_v1_helper, "/patients"),
                    (api_v1_helper, "/appointments")
                ]
                
                for helper, endpoint in endpoints_and_helpers:
                    start_time = time.time()
                    response = helper.make_request("GET", endpoint)
                    end_time = time.time()
                    
                    results.put({
                        "endpoint": endpoint,
                        "status_code": response.status_code,
                        "response_time": end_time - start_time,
                        "success": response.status_code == 200
                    })
                    
            except Exception as e:
                results.put({
                    "error": str(e),
                    "success": False
                })
        
        # Executar requisições em paralelo
        threads = []
        for _ in range(5):  # 5 threads fazendo 4 requisições cada = 20 total
            thread = threading.Thread(target=make_load_requests)
            threads.append(thread)
            thread.start()
        
        # Aguardar conclusão
        for thread in threads:
            thread.join()
        
        # Analisar resultados
        successful_requests = 0
        total_requests = 0
        response_times = []
        
        while not results.empty():
            result = results.get()
            total_requests += 1
            
            if result.get("success", False):
                successful_requests += 1
                if "response_time" in result:
                    response_times.append(result["response_time"])
            else:
                print(f"Failed request: {result}")
        
        # Validações
        success_rate = successful_requests / total_requests if total_requests > 0 else 0
        assert success_rate >= 0.95, f"Success rate {success_rate:.2%} below 95%"
        
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)
            
            assert avg_response_time < 2.0, f"Average response time {avg_response_time:.3f}s too high"
            assert max_response_time < 5.0, f"Max response time {max_response_time:.3f}s too high"
    
    @pytest.mark.integration
    def test_system_error_recovery(self, api_helper):
        """
        Teste: Capacidade de recuperação do sistema após erros
        Critério: Sistema deve se recuperar graciosamente de erros
        """
        # Fazer requisições que devem falhar
        error_requests = [
            "/nonexistent-endpoint",
            "/invalid/path/here",
            "/api/v1/invalid"
        ]
        
        for endpoint in error_requests:
            response = api_helper.make_request("GET", endpoint)
            # Deve retornar erro, mas não quebrar o sistema
            assert response.status_code in [404, 405, 422, 500]
        
        # Verificar que o sistema ainda está funcionando normalmente
        health_response = api_helper.make_request("GET", "/health")
        api_helper.assert_response_status(health_response, 200)
        
        health_data = api_helper.assert_response_json(health_response)
        assert health_data["status"] == "healthy"
        
        # Verificar que endpoints normais ainda funcionam
        root_response = api_helper.make_request("GET", "/")
        api_helper.assert_response_status(root_response, 200)
    
    @pytest.mark.integration
    def test_system_monitoring_integration(self, api_helper):
        """
        Teste: Integração dos endpoints de monitoramento
        Critério: Endpoints de monitoramento devem fornecer dados consistentes
        """
        monitoring_endpoints = ["/health", "/ready", "/live", "/metrics"]
        
        responses = {}
        
        for endpoint in monitoring_endpoints:
            response = api_helper.make_request("GET", endpoint)
            api_helper.assert_response_status(response, 200)
            
            data = api_helper.assert_response_json(response)
            responses[endpoint] = data
        
        # Validar consistência entre endpoints de monitoramento
        health_data = responses["/health"]
        ready_data = responses["/ready"]
        live_data = responses["/live"]
        metrics_data = responses["/metrics"]
        
        # Todos devem ter timestamp
        for endpoint, data in responses.items():
            if endpoint != "/metrics":  # metrics pode ter formato diferente
                assert "timestamp" in data, f"Missing timestamp in {endpoint}"
        
        # Validar que se health está healthy, ready e live também devem estar ok
        if health_data["status"] == "healthy":
            assert ready_data["status"] == "ready"
            assert live_data["status"] == "alive"
        
        # Validar que metrics contém dados esperados
        expected_metrics = ["http_requests_total", "http_request_duration_seconds"]
        for metric in expected_metrics:
            assert metric in metrics_data, f"Missing metric {metric}"
            assert isinstance(metrics_data[metric], (int, float))
    
    @pytest.mark.integration
    def test_api_version_consistency(self, api_helper, api_v1_helper):
        """
        Teste: Consistência de versão da API
        Critério: Versão deve ser consistente em todos os endpoints
        """
        # Verificar versão no endpoint raiz
        root_response = api_helper.make_request("GET", "/")
        api_helper.assert_response_status(root_response, 200)
        root_data = api_helper.assert_response_json(root_response)
        
        # Verificar versão no health check
        health_response = api_helper.make_request("GET", "/health")
        api_helper.assert_response_status(health_response, 200)
        health_data = api_helper.assert_response_json(health_response)
        
        # Versões devem ser consistentes
        assert root_data["version"] == health_data["version"]
        assert root_data["version"] == "1.0.0"
        
        # Verificar que endpoints v1 estão funcionando
        patients_response = api_v1_helper.make_request("GET", "/patients")
        api_v1_helper.assert_response_status(patients_response, 200)
        
        appointments_response = api_v1_helper.make_request("GET", "/appointments")
        api_v1_helper.assert_response_status(appointments_response, 200)
    
    @pytest.mark.integration
    def test_system_resource_usage(self, api_helper):
        """
        Teste: Uso de recursos do sistema
        Critério: Sistema deve reportar uso de recursos adequadamente
        """
        # Fazer várias requisições para gerar alguma atividade
        for _ in range(10):
            api_helper.make_request("GET", "/health")
            time.sleep(0.1)
        
        # Verificar métricas
        metrics_response = api_helper.make_request("GET", "/metrics")
        api_helper.assert_response_status(metrics_response, 200)
        
        metrics_data = api_helper.assert_response_json(metrics_response)
        
        # Validar que métricas fazem sentido
        assert metrics_data["http_requests_total"] > 0
        assert metrics_data["http_request_duration_seconds"] > 0
        assert metrics_data["database_connections_active"] >= 0
        assert metrics_data["memory_usage_bytes"] > 0
        
        # Verificar que valores estão em ranges razoáveis
        assert metrics_data["http_request_duration_seconds"] < 10.0  # Não deve ser muito alto
        assert metrics_data["memory_usage_bytes"] < 1073741824  # Menos que 1GB
