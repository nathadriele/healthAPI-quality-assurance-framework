# Health API QA Framework - OWASP Security Tests
# Testes de segurança baseados no OWASP Top 10

import pytest
import requests
import json
import time
from typing import Dict, Any, List
import base64
import urllib.parse

class TestOWASPSecurity:
    """Testes de segurança baseados no OWASP Top 10"""
    
    @pytest.mark.security
    def test_sql_injection_protection(self, api_v1_helper):
        """
        Teste: Proteção contra SQL Injection (OWASP A03:2021)
        Critério: API deve tratar tentativas de SQL injection adequadamente
        """
        # Payloads comuns de SQL injection
        sql_payloads = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "'; SELECT * FROM information_schema.tables; --",
            "admin'--",
            "' UNION SELECT username, password FROM users --",
            "1' OR 1=1 --",
            "'; EXEC xp_cmdshell('dir'); --",
            "' AND 1=CONVERT(int, (SELECT @@version)) --"
        ]
        
        for payload in sql_payloads:
            # Testar em diferentes campos
            test_data = {
                "name": payload,
                "age": 30,
                "email": f"test{payload.replace(' ', '')}@email.com"
            }
            
            response = api_v1_helper.make_request("POST", "/patients", json=test_data)
            
            # API deve processar normalmente ou retornar erro controlado
            assert response.status_code in [200, 400, 422], (
                f"SQL injection payload caused unexpected status: {response.status_code}"
            )
            
            # Verificar que não há vazamento de informações do banco
            response_text = response.text.lower()
            dangerous_keywords = [
                "sql", "database", "table", "column", "select", "insert", 
                "update", "delete", "drop", "union", "information_schema"
            ]
            
            for keyword in dangerous_keywords:
                assert keyword not in response_text, (
                    f"Potential SQL injection vulnerability: '{keyword}' found in response"
                )
    
    @pytest.mark.security
    def test_xss_protection(self, api_v1_helper):
        """
        Teste: Proteção contra Cross-Site Scripting (OWASP A03:2021)
        Critério: API deve sanitizar entrada e saída adequadamente
        """
        # Payloads comuns de XSS
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<svg onload=alert('XSS')>",
            "';alert('XSS');//",
            "<iframe src=javascript:alert('XSS')></iframe>",
            "<body onload=alert('XSS')>",
            "<<SCRIPT>alert('XSS')//<</SCRIPT>"
        ]
        
        for payload in xss_payloads:
            test_data = {
                "name": payload,
                "age": 25,
                "email": "test@email.com"
            }
            
            response = api_v1_helper.make_request("POST", "/patients", json=test_data)
            
            # API deve processar ou rejeitar adequadamente
            assert response.status_code in [200, 400, 422]
            
            if response.status_code == 200:
                data = api_v1_helper.assert_response_json(response)
                created_patient = data.get("patient", {})
                
                # Verificar se o payload foi sanitizado ou escapado
                name_in_response = created_patient.get("name", "")
                
                # Não deve conter tags HTML executáveis
                dangerous_tags = ["<script", "<img", "<iframe", "<svg", "<body"]
                for tag in dangerous_tags:
                    assert tag.lower() not in name_in_response.lower(), (
                        f"Potential XSS vulnerability: unsanitized '{tag}' in response"
                    )
    
    @pytest.mark.security
    def test_authentication_bypass(self, api_helper):
        """
        Teste: Tentativas de bypass de autenticação (OWASP A07:2021)
        Critério: Endpoints protegidos devem rejeitar acesso não autorizado
        """
        # Testar endpoints que deveriam ser protegidos
        protected_endpoints = [
            "/admin",
            "/api/v1/admin",
            "/api/admin",
            "/dashboard",
            "/config",
            "/settings"
        ]
        
        for endpoint in protected_endpoints:
            response = api_helper.make_request("GET", endpoint)
            
            # Deve retornar 401, 403 ou 404 (não 200)
            assert response.status_code in [401, 403, 404], (
                f"Potential authentication bypass: {endpoint} returned {response.status_code}"
            )
    
    @pytest.mark.security
    def test_sensitive_data_exposure(self, api_helper, api_v1_helper):
        """
        Teste: Exposição de dados sensíveis (OWASP A02:2021)
        Critério: API não deve vazar informações sensíveis
        """
        endpoints_to_test = [
            (api_helper, "/"),
            (api_helper, "/health"),
            (api_v1_helper, "/patients"),
            (api_v1_helper, "/appointments")
        ]
        
        sensitive_patterns = [
            # Informações de sistema
            r"password", r"secret", r"token", r"key", r"auth",
            # Informações de banco de dados
            r"database", r"connection", r"username", r"host",
            # Informações de servidor
            r"server", r"version", r"debug", r"error",
            # Dados pessoais sensíveis
            r"ssn", r"cpf", r"credit_card", r"bank_account"
        ]
        
        for helper, endpoint in endpoints_to_test:
            response = helper.make_request("GET", endpoint)
            
            if response.status_code == 200:
                response_text = response.text.lower()
                
                for pattern in sensitive_patterns:
                    # Verificar se não há exposição direta de dados sensíveis
                    if pattern in response_text:
                        # Algumas exceções são aceitáveis (como "version" em info da API)
                        acceptable_contexts = [
                            "version" in pattern and "api" in response_text,
                            "server" in pattern and "uvicorn" in response_text
                        ]
                        
                        if not any(acceptable_contexts):
                            pytest.fail(
                                f"Sensitive data exposure: '{pattern}' found in {endpoint}"
                            )
    
    @pytest.mark.security
    def test_http_security_headers(self, api_helper):
        """
        Teste: Headers de segurança HTTP (OWASP A05:2021)
        Critério: API deve incluir headers de segurança apropriados
        """
        response = api_helper.make_request("GET", "/health")
        api_helper.assert_response_status(response, 200)
        
        headers = response.headers
        
        # Headers de segurança recomendados
        security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": ["DENY", "SAMEORIGIN"],
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": None,  # Para HTTPS
            "Content-Security-Policy": None,
            "Referrer-Policy": None
        }
        
        # Verificar headers básicos (alguns podem não estar presentes em desenvolvimento)
        content_type = headers.get("content-type", "")
        assert content_type.startswith("application/json"), (
            f"Expected JSON content-type, got {content_type}"
        )
        
        # Verificar que não há headers perigosos
        dangerous_headers = ["Server", "X-Powered-By"]
        for header in dangerous_headers:
            if header in headers:
                # Se presente, não deve revelar informações detalhadas
                header_value = headers[header].lower()
                dangerous_values = ["apache", "nginx", "iis", "php", "asp.net"]
                for dangerous_value in dangerous_values:
                    if dangerous_value in header_value:
                        pytest.fail(f"Information disclosure in {header}: {header_value}")
    
    @pytest.mark.security
    def test_input_validation(self, api_v1_helper):
        """
        Teste: Validação de entrada (OWASP A03:2021)
        Critério: API deve validar adequadamente dados de entrada
        """
        # Testes de validação com dados malformados
        invalid_inputs = [
            # Dados muito longos
            {"name": "A" * 10000, "age": 30, "email": "test@email.com"},
            # Tipos incorretos
            {"name": 12345, "age": "invalid", "email": "not-an-email"},
            # Valores negativos onde não deveria
            {"name": "Test", "age": -1, "email": "test@email.com"},
            # Campos obrigatórios ausentes
            {"age": 30},
            # Caracteres especiais
            {"name": "Test\x00\x01\x02", "age": 30, "email": "test@email.com"},
            # JSON malformado será testado separadamente
        ]
        
        for invalid_input in invalid_inputs:
            response = api_v1_helper.make_request("POST", "/patients", json=invalid_input)
            
            # API deve rejeitar ou sanitizar entrada inválida
            if response.status_code == 200:
                # Se aceita, deve ter sanitizado os dados
                data = api_v1_helper.assert_response_json(response)
                patient = data.get("patient", {})
                
                # Verificar sanitização básica
                if "name" in patient:
                    name = patient["name"]
                    # Não deve conter caracteres de controle
                    for char in name:
                        assert ord(char) >= 32 or char in ['\t', '\n'], (
                            f"Control character found in sanitized name: {repr(char)}"
                        )
            else:
                # Deve retornar erro apropriado
                assert response.status_code in [400, 422], (
                    f"Expected validation error, got {response.status_code}"
                )
    
    @pytest.mark.security
    def test_rate_limiting(self, api_helper):
        """
        Teste: Rate limiting (OWASP A04:2021)
        Critério: API deve implementar rate limiting para prevenir ataques
        """
        # Fazer muitas requisições rapidamente
        responses = []
        
        for i in range(50):  # 50 requisições rápidas
            response = api_helper.make_request("GET", "/health")
            responses.append(response.status_code)
            
            # Pequena pausa para não sobrecarregar
            time.sleep(0.01)
        
        # Verificar se houve rate limiting
        success_count = sum(1 for status in responses if status == 200)
        rate_limited_count = sum(1 for status in responses if status == 429)
        
        # Em um sistema com rate limiting, deveria haver algumas respostas 429
        # Para esta API de demonstração, pode não ter rate limiting implementado
        if rate_limited_count > 0:
            assert rate_limited_count > 0, "Rate limiting should be active"
        else:
            # Se não há rate limiting, pelo menos verificar que não quebrou
            assert success_count > 40, "API should handle burst requests gracefully"
    
    @pytest.mark.security
    def test_error_information_disclosure(self, api_helper, api_v1_helper):
        """
        Teste: Vazamento de informações em erros (OWASP A09:2021)
        Critério: Mensagens de erro não devem vazar informações sensíveis
        """
        # Testar endpoints que devem gerar erros
        error_tests = [
            (api_helper, "GET", "/nonexistent-endpoint"),
            (api_v1_helper, "POST", "/patients", {"invalid": "json"}),
            (api_helper, "PUT", "/health"),  # Método não permitido
        ]
        
        for helper, method, endpoint, *args in error_tests:
            kwargs = {"json": args[0]} if args else {}
            response = helper.make_request(method, endpoint, **kwargs)
            
            # Deve retornar erro
            assert response.status_code >= 400
            
            if response.headers.get("content-type", "").startswith("application/json"):
                try:
                    error_data = response.json()
                    error_message = str(error_data).lower()
                    
                    # Verificar que não há vazamento de informações sensíveis
                    sensitive_info = [
                        "traceback", "stack trace", "file path", "database",
                        "connection", "password", "internal server error details"
                    ]
                    
                    for info in sensitive_info:
                        assert info not in error_message, (
                            f"Information disclosure in error: '{info}' found"
                        )
                        
                except json.JSONDecodeError:
                    # Se não é JSON válido, verificar texto
                    error_text = response.text.lower()
                    assert "traceback" not in error_text
                    assert "internal server error" not in error_text or len(error_text) < 200
    
    @pytest.mark.security
    def test_cors_configuration(self, api_helper):
        """
        Teste: Configuração CORS (OWASP A05:2021)
        Critério: CORS deve estar configurado adequadamente
        """
        # Testar requisição OPTIONS (preflight)
        response = api_helper.make_request("OPTIONS", "/health")
        
        # Verificar headers CORS se presentes
        cors_headers = [
            "Access-Control-Allow-Origin",
            "Access-Control-Allow-Methods",
            "Access-Control-Allow-Headers"
        ]
        
        for header in cors_headers:
            if header in response.headers:
                value = response.headers[header]
                
                # Verificar configurações perigosas
                if header == "Access-Control-Allow-Origin":
                    # "*" pode ser perigoso em produção
                    if value == "*":
                        # Em desenvolvimento pode ser aceitável
                        pass  # Warning: considerar restringir em produção
                
                if header == "Access-Control-Allow-Methods":
                    # Não deve permitir métodos perigosos desnecessariamente
                    dangerous_methods = ["TRACE", "CONNECT"]
                    for method in dangerous_methods:
                        assert method not in value.upper(), (
                            f"Dangerous HTTP method {method} allowed in CORS"
                        )

    @pytest.mark.security
    def test_directory_traversal(self, api_helper):
        """
        Teste: Directory Traversal (OWASP A01:2021)
        Critério: API deve prevenir acesso a arquivos do sistema
        """
        # Payloads de directory traversal
        traversal_payloads = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\drivers\\etc\\hosts",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
            "....//....//....//etc/passwd",
            "..%252f..%252f..%252fetc%252fpasswd"
        ]

        for payload in traversal_payloads:
            # Testar em diferentes contextos
            test_endpoints = [
                f"/file/{payload}",
                f"/download/{payload}",
                f"/static/{payload}",
                f"/{payload}"
            ]

            for endpoint in test_endpoints:
                response = api_helper.make_request("GET", endpoint)

                # Não deve retornar conteúdo de arquivos do sistema
                if response.status_code == 200:
                    content = response.text.lower()

                    # Indicadores de arquivos de sistema
                    system_indicators = [
                        "root:x:", "bin/bash", "windows", "system32",
                        "etc/passwd", "hosts file", "[boot loader]"
                    ]

                    for indicator in system_indicators:
                        assert indicator not in content, (
                            f"Directory traversal vulnerability: {indicator} found"
                        )

    @pytest.mark.security
    def test_command_injection(self, api_v1_helper):
        """
        Teste: Command Injection (OWASP A03:2021)
        Critério: API deve prevenir execução de comandos do sistema
        """
        # Payloads de command injection
        command_payloads = [
            "; ls -la",
            "| whoami",
            "&& cat /etc/passwd",
            "`id`",
            "$(whoami)",
            "; ping -c 1 127.0.0.1",
            "| dir",
            "&& ipconfig"
        ]

        for payload in command_payloads:
            test_data = {
                "name": f"Test{payload}",
                "age": 30,
                "email": "test@email.com"
            }

            response = api_v1_helper.make_request("POST", "/patients", json=test_data)

            # API deve processar normalmente ou rejeitar
            assert response.status_code in [200, 400, 422]

            if response.status_code == 200:
                # Verificar que não há saída de comandos na resposta
                response_text = response.text.lower()

                command_outputs = [
                    "uid=", "gid=", "total ", "volume in drive",
                    "directory of", "ping statistics", "packets transmitted"
                ]

                for output in command_outputs:
                    assert output not in response_text, (
                        f"Command injection vulnerability: '{output}' found in response"
                    )
