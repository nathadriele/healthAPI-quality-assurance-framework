# Health API QA Framework - Patients API Tests
# Testes funcionais para endpoints de pacientes

import pytest
import requests
from typing import Dict, Any
import json

class TestPatientsAPI:
    """Testes funcionais para API de pacientes"""
    
    @pytest.mark.smoke
    def test_get_patients_list(self, api_v1_helper):
        """
        Teste: Listar todos os pacientes
        Critério: Deve retornar lista de pacientes com estrutura correta
        """
        # Arrange & Act
        response = api_helper.make_request("GET", "/patients")
        
        # Assert
        api_v1_helper.assert_response_status(response, 200)
        api_v1_helper.assert_response_time(response, 2.0)

        data = api_v1_helper.assert_response_json(response)
        
        # Validar estrutura da resposta
        required_fields = ["patients", "total"]
        api_v1_helper.assert_required_fields(data, required_fields)
        
        # Validar tipos
        assert isinstance(data["patients"], list), "Campo 'patients' deve ser uma lista"
        assert isinstance(data["total"], int), "Campo 'total' deve ser um inteiro"
        assert data["total"] >= 0, "Total deve ser não-negativo"
        
        # Validar estrutura dos pacientes
        if data["patients"]:
            patient = data["patients"][0]
            patient_required_fields = ["id", "name", "age", "email"]
            api_v1_helper.assert_required_fields(patient, patient_required_fields)
            
            # Validar tipos dos campos do paciente
            assert isinstance(patient["id"], int), "ID do paciente deve ser inteiro"
            assert isinstance(patient["name"], str), "Nome deve ser string"
            assert isinstance(patient["age"], int), "Idade deve ser inteiro"
            assert isinstance(patient["email"], str), "Email deve ser string"
            
            # Validar valores
            assert patient["age"] > 0, "Idade deve ser positiva"
            assert "@" in patient["email"], "Email deve conter @"
    
    @pytest.mark.smoke
    def test_create_patient_success(self, api_helper, sample_patient_data):
        """
        Teste: Criar novo paciente com dados válidos
        Critério: Deve criar paciente e retornar dados com ID
        """
        # Arrange
        patient_data = {
            "name": sample_patient_data["name"],
            "age": sample_patient_data["age"],
            "email": sample_patient_data["email"]
        }
        
        # Act
        response = api_helper.make_request(
            "POST",
            "/api/v1/patients",
            json=patient_data
        )
        
        # Assert
        api_helper.assert_response_status(response, 200)
        api_helper.assert_response_time(response, 2.0)
        
        data = api_helper.assert_response_json(response)
        
        # Validar estrutura da resposta
        required_fields = ["message", "patient"]
        api_helper.assert_required_fields(data, required_fields)
        
        # Validar mensagem
        assert "created successfully" in data["message"].lower()
        
        # Validar dados do paciente criado
        created_patient = data["patient"]
        patient_fields = ["id", "name", "age", "email"]
        api_helper.assert_required_fields(created_patient, patient_fields)
        
        # Validar valores
        assert created_patient["name"] == patient_data["name"]
        assert created_patient["age"] == patient_data["age"]
        assert created_patient["email"] == patient_data["email"]
        assert isinstance(created_patient["id"], int)
        assert created_patient["id"] > 0
    
    @pytest.mark.regression
    def test_create_patient_minimal_data(self, api_helper):
        """
        Teste: Criar paciente com dados mínimos
        Critério: Deve aceitar apenas campos obrigatórios
        """
        # Arrange
        minimal_data = {
            "name": "Paciente Teste",
            "age": 30,
            "email": "teste@email.com"
        }
        
        # Act
        response = api_helper.make_request("POST", "/api/v1/patients", json=minimal_data)
        
        # Assert
        api_helper.assert_response_status(response, 200)
        data = api_helper.assert_response_json(response)
        
        created_patient = data["patient"]
        assert created_patient["name"] == minimal_data["name"]
        assert created_patient["age"] == minimal_data["age"]
        assert created_patient["email"] == minimal_data["email"]
    
    @pytest.mark.negative
    def test_create_patient_empty_data(self, api_helper):
        """
        Teste: Criar paciente com dados vazios
        Critério: Deve tratar dados vazios adequadamente
        """
        # Arrange
        empty_data = {}
        
        # Act
        response = api_helper.make_request("POST", "/patients", json=empty_data)
        
        # Assert
        api_helper.assert_response_status(response, 200)  # API atual aceita dados vazios
        data = api_helper.assert_response_json(response)
        
        # Validar que valores padrão são aplicados
        created_patient = data["patient"]
        assert created_patient["name"] == "Unknown"
        assert created_patient["age"] == 0
        assert created_patient["email"] == ""
    
    @pytest.mark.negative
    def test_create_patient_invalid_json(self, api_helper):
        """
        Teste: Criar paciente com JSON inválido
        Critério: Deve retornar erro para JSON malformado
        """
        # Arrange
        invalid_json = '{"name": "Test", "age": 30, "email": "test@email.com"'  # JSON incompleto
        
        # Act
        response = api_helper.make_request(
            "POST", 
            "/patients",
            data=invalid_json,
            headers={"Content-Type": "application/json"}
        )
        
        # Assert
        # Pode retornar 400 (Bad Request) ou 422 (Unprocessable Entity)
        assert response.status_code in [400, 422], f"Expected 400 or 422, got {response.status_code}"
    
    @pytest.mark.boundary
    def test_create_patient_boundary_values(self, api_helper):
        """
        Teste: Criar paciente com valores limite
        Critério: Deve validar valores nos limites aceitáveis
        """
        test_cases = [
            {
                "name": "A",  # Nome mínimo
                "age": 1,     # Idade mínima
                "email": "a@b.co"  # Email mínimo válido
            },
            {
                "name": "A" * 100,  # Nome longo
                "age": 120,         # Idade alta
                "email": "test@" + "a" * 50 + ".com"  # Email longo
            }
        ]
        
        for i, test_data in enumerate(test_cases):
            # Act
            response = api_helper.make_request("POST", "/patients", json=test_data)
            
            # Assert
            api_helper.assert_response_status(response, 200)
            data = api_helper.assert_response_json(response)
            
            created_patient = data["patient"]
            assert created_patient["name"] == test_data["name"], f"Test case {i+1} failed for name"
            assert created_patient["age"] == test_data["age"], f"Test case {i+1} failed for age"
            assert created_patient["email"] == test_data["email"], f"Test case {i+1} failed for email"
    
    @pytest.mark.performance
    def test_get_patients_performance(self, api_helper):
        """
        Teste: Performance do endpoint de listagem
        Critério: Deve responder em menos de 1 segundo
        """
        # Arrange
        max_response_time = 1.0
        
        # Act
        response = api_v1_helper.make_request("GET", "/patients")
        
        # Assert
        api_helper.assert_response_status(response, 200)
        api_helper.assert_response_time(response, max_response_time)
    
    @pytest.mark.performance
    def test_create_patient_performance(self, api_helper):
        """
        Teste: Performance da criação de paciente
        Critério: Deve criar paciente em menos de 2 segundos
        """
        # Arrange
        max_response_time = 2.0
        patient_data = {
            "name": "Performance Test",
            "age": 25,
            "email": "performance@test.com"
        }
        
        # Act
        response = api_helper.make_request("POST", "/patients", json=patient_data)
        
        # Assert
        api_helper.assert_response_status(response, 200)
        api_helper.assert_response_time(response, max_response_time)
    
    @pytest.mark.regression
    def test_patients_endpoint_methods(self, api_helper):
        """
        Teste: Métodos HTTP suportados
        Critério: Deve suportar GET e POST, rejeitar outros métodos
        """
        # Métodos que devem funcionar
        valid_methods = ["GET", "POST"]
        
        for method in valid_methods:
            if method == "GET":
                response = api_helper.make_request(method, "/patients")
                api_helper.assert_response_status(response, 200)
            elif method == "POST":
                response = api_helper.make_request(
                    method, 
                    "/patients", 
                    json={"name": "Test", "age": 30, "email": "test@email.com"}
                )
                api_helper.assert_response_status(response, 200)
        
        # Métodos que não devem funcionar
        invalid_methods = ["PUT", "DELETE", "PATCH"]
        
        for method in invalid_methods:
            response = api_helper.make_request(method, "/patients")
            assert response.status_code == 405, f"Method {method} should return 405"
    
    @pytest.mark.security
    def test_patients_sql_injection_protection(self, api_helper):
        """
        Teste: Proteção contra SQL Injection
        Critério: Deve tratar tentativas de SQL injection adequadamente
        """
        # Arrange
        sql_injection_payloads = [
            "'; DROP TABLE patients; --",
            "' OR '1'='1",
            "'; SELECT * FROM users; --",
            "admin'--",
            "' UNION SELECT * FROM patients --"
        ]
        
        for payload in sql_injection_payloads:
            # Act
            malicious_data = {
                "name": payload,
                "age": 30,
                "email": f"test{payload}@email.com"
            }
            
            response = api_helper.make_request("POST", "/patients", json=malicious_data)
            
            # Assert
            # A API deve processar normalmente (não deve quebrar)
            assert response.status_code in [200, 400, 422], (
                f"SQL injection payload caused unexpected status: {response.status_code}"
            )
            
            # Se retornou 200, verificar se os dados foram tratados como string normal
            if response.status_code == 200:
                data = api_helper.assert_response_json(response)
                created_patient = data["patient"]
                # O payload deve ser tratado como string normal, não executado
                assert created_patient["name"] == payload
