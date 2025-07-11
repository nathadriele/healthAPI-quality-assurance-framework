# Health API QA Framework - Locust Performance Tests
# Testes de carga e performance para a Health API

from locust import HttpUser, task, between
import json
import random
import time
from typing import Dict, Any

class HealthAPIUser(HttpUser):
    """Usuário simulado para testes de performance da Health API"""
    
    # Tempo de espera entre requisições (1-3 segundos)
    wait_time = between(1, 3)
    
    # Host será definido via linha de comando ou configuração
    # host = "http://localhost:8000"
    
    def on_start(self):
        """Executado quando o usuário inicia"""
        # Verificar se a API está disponível
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"API not healthy: {response.status_code}")
            else:
                response.success()
    
    @task(3)
    def get_health_check(self):
        """
        Teste de carga: Health check endpoint
        Peso: 3 (executado com mais frequência)
        """
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    response.success()
                else:
                    response.failure(f"API not healthy: {data}")
            else:
                response.failure(f"Health check failed: {response.status_code}")
    
    @task(2)
    def get_root_endpoint(self):
        """
        Teste de carga: Root endpoint
        Peso: 2
        """
        with self.client.get("/", catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                if "Health API QA Framework" in data.get("message", ""):
                    response.success()
                else:
                    response.failure("Invalid root response")
            else:
                response.failure(f"Root endpoint failed: {response.status_code}")
    
    @task(4)
    def get_patients_list(self):
        """
        Teste de carga: Listar pacientes
        Peso: 4 (endpoint mais usado)
        """
        with self.client.get("/api/v1/patients", catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                if "patients" in data and "total" in data:
                    response.success()
                else:
                    response.failure("Invalid patients response structure")
            else:
                response.failure(f"Get patients failed: {response.status_code}")
    
    @task(3)
    def get_appointments_list(self):
        """
        Teste de carga: Listar consultas
        Peso: 3
        """
        with self.client.get("/api/v1/appointments", catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                if "appointments" in data and "total" in data:
                    response.success()
                else:
                    response.failure("Invalid appointments response structure")
            else:
                response.failure(f"Get appointments failed: {response.status_code}")
    
    @task(2)
    def create_patient(self):
        """
        Teste de carga: Criar paciente
        Peso: 2 (operação menos frequente)
        """
        # Gerar dados aleatórios para o paciente
        patient_data = {
            "name": f"Paciente {random.randint(1000, 9999)}",
            "age": random.randint(18, 80),
            "email": f"paciente{random.randint(1000, 9999)}@email.com"
        }
        
        with self.client.post(
            "/api/v1/patients",
            json=patient_data,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "patient" in data and "message" in data:
                    response.success()
                else:
                    response.failure("Invalid create patient response")
            else:
                response.failure(f"Create patient failed: {response.status_code}")
    
    @task(1)
    def get_metrics(self):
        """
        Teste de carga: Endpoint de métricas
        Peso: 1 (menos frequente)
        """
        with self.client.get("/metrics", catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                expected_metrics = ["http_requests_total", "memory_usage_bytes"]
                if all(metric in data for metric in expected_metrics):
                    response.success()
                else:
                    response.failure("Missing expected metrics")
            else:
                response.failure(f"Get metrics failed: {response.status_code}")
    
    @task(1)
    def get_readiness_probe(self):
        """
        Teste de carga: Readiness probe
        Peso: 1
        """
        with self.client.get("/ready", catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "ready":
                    response.success()
                else:
                    response.failure("Service not ready")
            else:
                response.failure(f"Readiness probe failed: {response.status_code}")
    
    @task(1)
    def get_liveness_probe(self):
        """
        Teste de carga: Liveness probe
        Peso: 1
        """
        with self.client.get("/live", catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "alive":
                    response.success()
                else:
                    response.failure("Service not alive")
            else:
                response.failure(f"Liveness probe failed: {response.status_code}")

class StressTestUser(HttpUser):
    """Usuário para testes de stress - requisições mais agressivas"""
    
    # Tempo de espera menor para stress test
    wait_time = between(0.1, 0.5)
    
    @task(5)
    def rapid_health_checks(self):
        """Requisições rápidas para health check"""
        self.client.get("/health")
    
    @task(3)
    def rapid_patients_requests(self):
        """Requisições rápidas para pacientes"""
        self.client.get("/api/v1/patients")
    
    @task(2)
    def rapid_appointments_requests(self):
        """Requisições rápidas para consultas"""
        self.client.get("/api/v1/appointments")

class SpikeTestUser(HttpUser):
    """Usuário para testes de pico - simula picos de tráfego"""
    
    wait_time = between(0.1, 1.0)
    
    def on_start(self):
        """Simular pico inicial"""
        for _ in range(5):
            self.client.get("/health")
            time.sleep(0.1)
    
    @task
    def spike_requests(self):
        """Requisições em pico"""
        endpoints = [
            "/health",
            "/api/v1/patients",
            "/api/v1/appointments",
            "/metrics"
        ]
        
        # Fazer várias requisições rapidamente
        for endpoint in endpoints:
            self.client.get(endpoint)
            time.sleep(0.05)

# Configurações personalizadas para diferentes cenários
class LoadTestUser(HealthAPIUser):
    """Usuário para teste de carga normal"""
    wait_time = between(1, 3)

class VolumeTestUser(HealthAPIUser):
    """Usuário para teste de volume"""
    wait_time = between(2, 5)
    
    @task(10)
    def volume_patients_requests(self):
        """Alto volume de requisições para pacientes"""
        self.client.get("/api/v1/patients")
    
    @task(8)
    def volume_appointments_requests(self):
        """Alto volume de requisições para consultas"""
        self.client.get("/api/v1/appointments")

# Classe principal para execução padrão
class DefaultUser(HealthAPIUser):
    """Classe padrão para execução normal"""
    pass
