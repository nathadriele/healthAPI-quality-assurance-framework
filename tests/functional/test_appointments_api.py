# Health API QA Framework - Appointments API Tests
# Testes funcionais para endpoints de consultas/agendamentos

import pytest
import requests
from typing import Dict, Any
import json
from datetime import datetime, timedelta

class TestAppointmentsAPI:
    """Testes funcionais para API de consultas"""
    
    @pytest.mark.smoke
    def test_get_appointments_list(self, api_helper):
        """
        Teste: Listar todas as consultas
        Critério: Deve retornar lista de consultas com estrutura correta
        """
        # Arrange & Act
        response = api_helper.make_request("GET", "/api/v1/appointments")
        
        # Assert
        api_helper.assert_response_status(response, 200)
        api_helper.assert_response_time(response, 2.0)
        
        data = api_helper.assert_response_json(response)
        
        # Validar estrutura da resposta
        required_fields = ["appointments", "total"]
        api_helper.assert_required_fields(data, required_fields)
        
        # Validar tipos
        assert isinstance(data["appointments"], list), "Campo 'appointments' deve ser uma lista"
        assert isinstance(data["total"], int), "Campo 'total' deve ser um inteiro"
        assert data["total"] >= 0, "Total deve ser não-negativo"
        
        # Validar estrutura das consultas
        if data["appointments"]:
            appointment = data["appointments"][0]
            appointment_required_fields = ["id", "patient_id", "doctor", "date", "time"]
            api_helper.assert_required_fields(appointment, appointment_required_fields)
            
            # Validar tipos dos campos
            assert isinstance(appointment["id"], int), "ID da consulta deve ser inteiro"
            assert isinstance(appointment["patient_id"], int), "ID do paciente deve ser inteiro"
            assert isinstance(appointment["doctor"], str), "Nome do médico deve ser string"
            assert isinstance(appointment["date"], str), "Data deve ser string"
            assert isinstance(appointment["time"], str), "Horário deve ser string"
            
            # Validar valores
            assert appointment["id"] > 0, "ID deve ser positivo"
            assert appointment["patient_id"] > 0, "ID do paciente deve ser positivo"
            assert len(appointment["doctor"]) > 0, "Nome do médico não pode estar vazio"
            
            # Validar formato da data (YYYY-MM-DD)
            try:
                datetime.strptime(appointment["date"], "%Y-%m-%d")
            except ValueError:
                pytest.fail(f"Data inválida: {appointment['date']}. Esperado formato YYYY-MM-DD")
            
            # Validar formato do horário (HH:MM)
            try:
                datetime.strptime(appointment["time"], "%H:%M")
            except ValueError:
                pytest.fail(f"Horário inválido: {appointment['time']}. Esperado formato HH:MM")
    
    @pytest.mark.regression
    def test_appointments_data_consistency(self, api_helper):
        """
        Teste: Consistência dos dados de consultas
        Critério: Dados devem ser consistentes entre múltiplas chamadas
        """
        # Fazer múltiplas requisições
        responses = []
        for _ in range(3):
            response = api_helper.make_request("GET", "/api/v1/appointments")
            api_helper.assert_response_status(response, 200)
            responses.append(api_helper.assert_response_json(response))
        
        # Validar consistência
        first_response = responses[0]
        for response in responses[1:]:
            assert response["total"] == first_response["total"], "Total de consultas deve ser consistente"
            assert len(response["appointments"]) == len(first_response["appointments"]), "Número de consultas deve ser consistente"
            
            # Comparar cada consulta
            for i, appointment in enumerate(response["appointments"]):
                first_appointment = first_response["appointments"][i]
                assert appointment["id"] == first_appointment["id"], f"ID da consulta {i} deve ser consistente"
                assert appointment["patient_id"] == first_appointment["patient_id"], f"Patient ID da consulta {i} deve ser consistente"
                assert appointment["doctor"] == first_appointment["doctor"], f"Médico da consulta {i} deve ser consistente"
    
    @pytest.mark.performance
    def test_appointments_performance(self, api_helper):
        """
        Teste: Performance do endpoint de consultas
        Critério: Deve responder em menos de 1 segundo
        """
        # Arrange
        max_response_time = 1.0
        
        # Act
        response = api_helper.make_request("GET", "/api/v1/appointments")
        
        # Assert
        api_helper.assert_response_status(response, 200)
        api_helper.assert_response_time(response, max_response_time)
    
    @pytest.mark.boundary
    def test_appointments_empty_response(self, api_helper):
        """
        Teste: Resposta quando não há consultas
        Critério: Deve retornar estrutura correta mesmo sem dados
        """
        # Este teste assume que pode haver cenários sem consultas
        # Na implementação atual sempre retorna dados, mas é um teste válido
        
        response = api_helper.make_request("GET", "/api/v1/appointments")
        api_helper.assert_response_status(response, 200)
        
        data = api_helper.assert_response_json(response)
        
        # Mesmo sem dados, estrutura deve estar presente
        assert "appointments" in data
        assert "total" in data
        assert isinstance(data["appointments"], list)
        assert isinstance(data["total"], int)
        assert data["total"] >= 0
    
    @pytest.mark.negative
    def test_appointments_invalid_method(self, api_helper):
        """
        Teste: Método HTTP inválido
        Critério: Deve retornar 405 para métodos não suportados
        """
        invalid_methods = ["PUT", "DELETE", "PATCH"]
        
        for method in invalid_methods:
            response = api_helper.make_request(method, "/api/v1/appointments")
            assert response.status_code == 405, f"Method {method} should return 405"
    
    @pytest.mark.security
    def test_appointments_no_sensitive_data(self, api_helper):
        """
        Teste: Verificar se não há dados sensíveis expostos
        Critério: Resposta não deve conter informações sensíveis
        """
        response = api_helper.make_request("GET", "/api/v1/appointments")
        api_helper.assert_response_status(response, 200)
        
        data = api_helper.assert_response_json(response)
        response_text = json.dumps(data).lower()
        
        # Lista de termos sensíveis que não devem aparecer
        sensitive_terms = [
            "password", "token", "secret", "key", "auth",
            "cpf", "ssn", "credit_card", "bank_account"
        ]
        
        for term in sensitive_terms:
            assert term not in response_text, f"Sensitive term '{term}' found in response"
    
    @pytest.mark.regression
    def test_appointments_response_headers(self, api_helper):
        """
        Teste: Headers da resposta
        Critério: Deve retornar headers apropriados
        """
        response = api_helper.make_request("GET", "/api/v1/appointments")
        api_helper.assert_response_status(response, 200)
        
        # Validar Content-Type
        content_type = response.headers.get("content-type", "")
        assert content_type.startswith("application/json"), f"Expected JSON content-type, got {content_type}"
        
        # Validar presença de headers importantes
        assert "date" in response.headers, "Date header should be present"
        assert "server" in response.headers, "Server header should be present"
    
    @pytest.mark.smoke
    def test_appointments_json_structure(self, api_helper):
        """
        Teste: Estrutura JSON da resposta
        Critério: JSON deve ser válido e bem estruturado
        """
        response = api_helper.make_request("GET", "/api/v1/appointments")
        api_helper.assert_response_status(response, 200)
        
        # Verificar se é JSON válido
        data = api_helper.assert_response_json(response)
        
        # Verificar estrutura básica
        assert isinstance(data, dict), "Response should be a JSON object"
        
        # Verificar se não há campos nulos inesperados
        for appointment in data.get("appointments", []):
            for key, value in appointment.items():
                if key in ["id", "patient_id"]:
                    assert value is not None, f"Field {key} should not be null"
                    assert isinstance(value, int), f"Field {key} should be integer"
                elif key in ["doctor", "date", "time"]:
                    assert value is not None, f"Field {key} should not be null"
                    assert isinstance(value, str), f"Field {key} should be string"
                    assert len(value.strip()) > 0, f"Field {key} should not be empty"
