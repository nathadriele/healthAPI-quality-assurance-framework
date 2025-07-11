#!/usr/bin/env python3
# Health API QA Framework - SonarQube Analysis Runner
# Script para executar análise SonarQube local

import subprocess
import sys
import os
import time
import requests
from pathlib import Path
from typing import Dict, Any, Optional

class SonarAnalysisRunner:
    """Runner para análise SonarQube"""
    
    def __init__(self, sonar_host: str = "http://localhost:9000"):
        self.sonar_host = sonar_host
        self.project_key = "healthapi-qa-framework"
        self.project_root = Path(__file__).parent.parent
        
    def check_sonar_server(self) -> bool:
        """Verifica se o servidor SonarQube está disponível"""
        try:
            response = requests.get(f"{self.sonar_host}/api/system/status", timeout=10)
            if response.status_code == 200:
                status = response.json()
                return status.get("status") == "UP"
        except:
            pass
        return False
    
    def wait_for_sonar_server(self, max_wait: int = 300) -> bool:
        """Aguarda o servidor SonarQube ficar disponível"""
        print("🔍 Verificando disponibilidade do SonarQube...")
        
        start_time = time.time()
        while time.time() - start_time < max_wait:
            if self.check_sonar_server():
                print("✅ SonarQube está disponível!")
                return True
            
            print("⏳ Aguardando SonarQube... (tentativa em 10s)")
            time.sleep(10)
        
        print("❌ SonarQube não está disponível após timeout")
        return False
    
    def run_tests_with_coverage(self) -> bool:
        """Executa testes com cobertura para análise"""
        print("🧪 Executando testes com cobertura...")
        
        try:
            # Executar testes com cobertura
            cmd = [
                "pytest",
                "tests/",
                "--cov=api",
                "--cov-report=xml:coverage.xml",
                "--cov-report=html:htmlcov",
                "--cov-report=term-missing",
                "--junit-xml=test-results.xml",
                "-v"
            ]
            
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("✅ Testes executados com sucesso!")
                return True
            else:
                print(f"❌ Testes falharam: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"💥 Erro ao executar testes: {str(e)}")
            return False
    
    def run_static_analysis(self) -> bool:
        """Executa análise estática adicional"""
        print("🔍 Executando análise estática...")
        
        try:
            # Pylint
            print("  📊 Executando Pylint...")
            subprocess.run([
                "pylint", "api/", "tests/",
                "--output-format=json",
                "--reports=yes"
            ], cwd=self.project_root, capture_output=True)
            
            # Bandit
            print("  🔒 Executando Bandit...")
            subprocess.run([
                "bandit", "-r", "api/",
                "-f", "json",
                "-o", "bandit-report.json"
            ], cwd=self.project_root, capture_output=True)
            
            # Flake8
            print("  📏 Executando Flake8...")
            subprocess.run([
                "flake8", "api/", "tests/",
                "--format=json",
                "--output-file=flake8-report.json"
            ], cwd=self.project_root, capture_output=True)
            
            print("✅ Análise estática concluída!")
            return True
            
        except Exception as e:
            print(f"💥 Erro na análise estática: {str(e)}")
            return False
    
    def run_sonar_scanner(self, token: Optional[str] = None) -> bool:
        """Executa o SonarQube Scanner"""
        print("📈 Executando SonarQube Scanner...")
        
        try:
            # Comando base do sonar-scanner
            cmd = [
                "sonar-scanner",
                f"-Dsonar.host.url={self.sonar_host}",
                f"-Dsonar.projectKey={self.project_key}",
                "-Dsonar.sources=api/",
                "-Dsonar.tests=tests/",
                "-Dsonar.python.coverage.reportPaths=coverage.xml",
                "-Dsonar.python.xunit.reportPath=test-results.xml",
                "-Dsonar.sourceEncoding=UTF-8"
            ]
            
            # Adicionar token se fornecido
            if token:
                cmd.append(f"-Dsonar.login={token}")
            
            # Executar scanner
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("✅ SonarQube Scanner executado com sucesso!")
                print(f"📊 Resultados disponíveis em: {self.sonar_host}")
                return True
            else:
                print(f"❌ SonarQube Scanner falhou: {result.stderr}")
                return False
                
        except FileNotFoundError:
            print("❌ sonar-scanner não encontrado. Instale o SonarQube Scanner.")
            print("💡 Download: https://docs.sonarqube.org/latest/analysis/scan/sonarscanner/")
            return False
        except Exception as e:
            print(f"💥 Erro ao executar SonarQube Scanner: {str(e)}")
            return False
    
    def get_quality_gate_status(self, token: Optional[str] = None) -> Dict[str, Any]:
        """Verifica status do Quality Gate"""
        try:
            headers = {}
            if token:
                headers["Authorization"] = f"Bearer {token}"
            
            # Aguardar processamento
            print("⏳ Aguardando processamento da análise...")
            time.sleep(30)
            
            # Verificar status do Quality Gate
            response = requests.get(
                f"{self.sonar_host}/api/qualitygates/project_status",
                params={"projectKey": self.project_key},
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            return {"error": str(e)}
    
    def run_full_analysis(self, token: Optional[str] = None, skip_tests: bool = False) -> bool:
        """Executa análise completa"""
        print("🚀 Iniciando análise completa do SonarQube...")
        print(f"📁 Projeto: {self.project_key}")
        print(f"🌐 Servidor: {self.sonar_host}")
        print("=" * 50)
        
        # 1. Verificar servidor SonarQube
        if not self.wait_for_sonar_server():
            return False
        
        # 2. Executar testes (se não for para pular)
        if not skip_tests:
            if not self.run_tests_with_coverage():
                print("⚠️ Testes falharam, mas continuando com análise...")
        
        # 3. Executar análise estática
        self.run_static_analysis()
        
        # 4. Executar SonarQube Scanner
        if not self.run_sonar_scanner(token):
            return False
        
        # 5. Verificar Quality Gate
        print("🎯 Verificando Quality Gate...")
        qg_status = self.get_quality_gate_status(token)
        
        if "error" in qg_status:
            print(f"⚠️ Erro ao verificar Quality Gate: {qg_status['error']}")
        else:
            project_status = qg_status.get("projectStatus", {})
            status = project_status.get("status", "UNKNOWN")
            
            if status == "OK":
                print("✅ Quality Gate: PASSOU!")
            elif status == "ERROR":
                print("❌ Quality Gate: FALHOU!")
                conditions = project_status.get("conditions", [])
                for condition in conditions:
                    if condition.get("status") == "ERROR":
                        metric = condition.get("metricKey")
                        actual = condition.get("actualValue")
                        threshold = condition.get("errorThreshold")
                        print(f"  ❌ {metric}: {actual} (threshold: {threshold})")
            else:
                print(f"⚠️ Quality Gate: {status}")
        
        print("=" * 50)
        print("🎉 Análise SonarQube concluída!")
        print(f"📊 Acesse os resultados em: {self.sonar_host}/dashboard?id={self.project_key}")
        
        return True

def main():
    """Função principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Health API SonarQube Analysis Runner")
    parser.add_argument("--host", default="http://localhost:9000", help="SonarQube host")
    parser.add_argument("--token", help="SonarQube authentication token")
    parser.add_argument("--skip-tests", action="store_true", help="Skip test execution")
    
    args = parser.parse_args()
    
    runner = SonarAnalysisRunner(args.host)
    
    success = runner.run_full_analysis(
        token=args.token,
        skip_tests=args.skip_tests
    )
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
