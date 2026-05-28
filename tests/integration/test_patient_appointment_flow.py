# Health API QA Framework - Patient-Appointment Integration Tests
# Testes de integração entre módulos de pacientes e consultas

import pytest
import requests
from typing import Dict, Any
import json
import time

class TestPatientAppointmentIntegration:
    """Testes de integração entre pacientes e consultas"""
    
    @pytest.mark.integration
    def test_patient_appointment_workflow(self, api_v1_helper):
        """
        Teste: Fluxo completo paciente -> consulta
        Critério: Deve ser possível criar paciente e agendar consulta
        """
        # Step 1: Criar paciente
        patient_data = {
            "name": "Maria Silva",
            "age": 32,
            "email": "maria.silva@email.com"
        }
        
        patient_response = api_v1_helper.make_request("POST", "/patients", json=patient_data)
        api_v1_helper.assert_response_status(patient_response, 200)
        
        patient_result = api_v1_helper.assert_response_json(patient_response)
        created_patient = patient_result["patient"]
        patient_id = created_patient["id"]
        
        # Validar que paciente foi criado corretamente
        assert patient_id > 0
        assert created_patient["name"] == patient_data["name"]
        assert created_patient["email"] == patient_data["email"]
        
        # Step 2: Verificar se paciente aparece na listagem
        patients_response = api_v1_helper.make_request("GET", "/patients")
        api_v1_helper.assert_response_status(patients_response, 200)
        
        patients_data = api_v1_helper.assert_response_json(patients_response)
        
        # Verificar se o paciente criado está na lista
        patient_found = False
        for patient in patients_data["patients"]:
            if patient["id"] == patient_id:
                patient_found = True
                assert patient["name"] == patient_data["name"]
                break
        
        assert patient_found, f"Paciente com ID {patient_id} não encontrado na listagem"
        
        # Step 3: Verificar consultas existentes
        appointments_response = api_v1_helper.make_request("GET", "/appointments")
        api_v1_helper.assert_response_status(appointments_response, 200)
        
        appointments_data = api_v1_helper.assert_response_json(appointments_response)
        initial_appointments_count = appointments_data["total"]
        
        # Validar estrutura das consultas
        assert "appointments" in appointments_data
        assert "total" in appointments_data
        assert isinstance(appointments_data["appointments"], list)
        assert isinstance(appointments_data["total"], int)
    
    @pytest.mark.integration
    def test_data_consistency_between_endpoints(self, api_v1_helper):
        """
        Teste: Consistência de dados entre endpoints
        Critério: Dados devem ser consistentes entre diferentes endpoints
        """
        # Obter dados de pacientes
        patients_response = api_v1_helper.make_request("GET", "/patients")
        api_v1_helper.assert_response_status(patients_response, 200)
        patients_data = api_v1_helper.assert_response_json(patients_response)
        
        # Obter dados de consultas
        appointments_response = api_v1_helper.make_request("GET", "/appointments")
        api_v1_helper.assert_response_status(appointments_response, 200)
        appointments_data = api_v1_helper.assert_response_json(appointments_response)
        
        # Validar que IDs de pacientes nas consultas existem na lista de pacientes
        patient_ids = [patient["id"] for patient in patients_data["patients"]]
        
        for appointment in appointments_data["appointments"]:
            patient_id = appointment["patient_id"]
            assert patient_id in patient_ids, (
                f"Patient ID {patient_id} in appointment {appointment['id']} "
                f"not found in patients list"
            )
    
    @pytest.mark.integration
    def test_api_endpoints_response_format_consistency(self, api_v1_helper):
        """
        Teste: Consistência de formato de resposta entre endpoints
        Critério: Todos os endpoints devem seguir padrão similar de resposta
        """
        endpoints = ["/patients", "/appointments"]
        
        for endpoint in endpoints:
            response = api_v1_helper.make_request("GET", endpoint)
            api_v1_helper.assert_response_status(response, 200)
            
            data = api_v1_helper.assert_response_json(response)
            
            # Validar estrutura comum
            assert isinstance(data, dict), f"Response from {endpoint} should be a dict"
            assert "total" in data, f"Response from {endpoint} should have 'total' field"
            assert isinstance(data["total"], int), f"'total' field should be integer in {endpoint}"
            
            # Validar que o campo principal é uma lista
            main_field = endpoint.split("/")[-1]  # patients ou appointments
            assert main_field in data, f"Response from {endpoint} should have '{main_field}' field"
            assert isinstance(data[main_field], list), f"'{main_field}' should be a list in {endpoint}"
    
    @pytest.mark.integration
    def test_api_error_handling_consistency(self, api_v1_helper):
        """
        Teste: Consistência no tratamento de erros
        Critério: Endpoints devem tratar erros de forma consistente
        """
        # Testar endpoints inexistentes
        invalid_endpoints = ["/patients/invalid", "/appointments/invalid", "/nonexistent"]
        
        for endpoint in invalid_endpoints:
            response = api_v1_helper.make_request("GET", endpoint)
            
            # Deve retornar 404 para endpoints inexistentes
            api_v1_helper.assert_response_status(response, 404)
            
            # Verificar formato da resposta de erro
            error_data = api_v1_helper.assert_response_json(response)
            assert "detail" in error_data, f"Error response should have 'detail' field for {endpoint}"
    
    @pytest.mark.integration
    def test_api_performance_consistency(self, api_v1_helper):
        """
        Teste: Consistência de performance entre endpoints
        Critério: Todos os endpoints devem ter performance similar
        """
        endpoints = ["/patients", "/appointments"]
        response_times = {}
        
        for endpoint in endpoints:
            start_time = time.time()
            response = api_v1_helper.make_request("GET", endpoint)
            end_time = time.time()
            
            api_v1_helper.assert_response_status(response, 200)
            
            response_time = end_time - start_time
            response_times[endpoint] = response_time
            
            # Cada endpoint deve responder em menos de 2 segundos
            assert response_time < 2.0, f"Endpoint {endpoint} took {response_time:.3f}s (> 2.0s)"
        
        # Verificar que não há discrepância muito grande entre endpoints
        max_time = max(response_times.values())
        min_time = min(response_times.values())
        
        # Diferença não deve ser maior que 1 segundo
        time_difference = max_time - min_time
        assert time_difference < 1.0, (
            f"Performance difference between endpoints too large: {time_difference:.3f}s"
        )
    
    @pytest.mark.integration
    def test_api_concurrent_access(self, api_v1_helper):
        """
        Teste: Acesso concorrente aos endpoints
        Critério: API deve suportar acesso concorrente sem problemas
        """
        import threading
        import queue
        
        results = queue.Queue()
        
        def make_concurrent_requests():
            try:
                # Fazer requisições para diferentes endpoints
                patients_response = api_v1_helper.make_request("GET", "/patients")
                appointments_response = api_v1_helper.make_request("GET", "/appointments")
                
                results.put({
                    "patients_status": patients_response.status_code,
                    "appointments_status": appointments_response.status_code,
                    "success": True
                })
            except Exception as e:
                results.put({
                    "error": str(e),
                    "success": False
                })
        
        # Criar e executar threads
        threads = []
        num_threads = 5
        
        for _ in range(num_threads):
            thread = threading.Thread(target=make_concurrent_requests)
            threads.append(thread)
            thread.start()
        
        # Aguardar conclusão
        for thread in threads:
            thread.join()
        
        # Validar resultados
        success_count = 0
        while not results.empty():
            result = results.get()
            
            if result["success"]:
                assert result["patients_status"] == 200
                assert result["appointments_status"] == 200
                success_count += 1
            else:
                pytest.fail(f"Concurrent request failed: {result['error']}")
        
        assert success_count == num_threads, f"Expected {num_threads} successful concurrent requests"
    
    @pytest.mark.integration
    def test_api_data_validation_integration(self, api_v1_helper):
        """
        Teste: Validação de dados entre endpoints relacionados
        Critério: Dados devem ser validados consistentemente
        """
        # Testar criação de paciente com dados válidos
        valid_patient = {
            "name": "João Santos",
            "age": 45,
            "email": "joao.santos@email.com"
        }
        
        response = api_v1_helper.make_request("POST", "/patients", json=valid_patient)
        api_v1_helper.assert_response_status(response, 200)
        
        data = api_v1_helper.assert_response_json(response)
        created_patient = data["patient"]
        
        # Validar que os dados foram processados corretamente
        assert created_patient["name"] == valid_patient["name"]
        assert created_patient["age"] == valid_patient["age"]
        assert created_patient["email"] == valid_patient["email"]
        assert isinstance(created_patient["id"], int)
        assert created_patient["id"] > 0
        
        # Verificar que o paciente aparece na listagem
        list_response = api_v1_helper.make_request("GET", "/patients")
        api_v1_helper.assert_response_status(list_response, 200)
        
        list_data = api_v1_helper.assert_response_json(list_response)
        
        # Procurar o paciente criado na lista
        found_patient = None
        for patient in list_data["patients"]:
            if patient["id"] == created_patient["id"]:
                found_patient = patient
                break
        
        assert found_patient is not None, "Created patient not found in list"
        assert found_patient["name"] == valid_patient["name"]
        assert found_patient["age"] == valid_patient["age"]
        assert found_patient["email"] == valid_patient["email"]
