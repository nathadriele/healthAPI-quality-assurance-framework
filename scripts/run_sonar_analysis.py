#!/usr/bin/env python3

import argparse
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional

import requests


class SonarAnalysisRunner:
    def __init__(self, sonar_host: str = "http://localhost:9000"):
        self.sonar_host = sonar_host
        self.project_key = "healthapi-qa-framework"
        self.project_root = Path(__file__).parent.parent

    def check_sonar_server(self) -> bool:
        try:
            response = requests.get(
                f"{self.sonar_host}/api/system/status",
                timeout=10,
            )

            if response.status_code == 200:
                status = response.json()
                return status.get("status") == "UP"

        except requests.RequestException:
            return False

        return False

    def wait_for_sonar_server(self, max_wait: int = 300) -> bool:
        print("Verificando disponibilidade do SonarQube...")

        start_time = time.time()

        while time.time() - start_time < max_wait:
            if self.check_sonar_server():
                print("SonarQube está disponível.")
                return True

            print("Aguardando SonarQube. Nova tentativa em 10 segundos.")
            time.sleep(10)

        print("SonarQube não está disponível após o tempo limite.")
        return False

    def run_tests_with_coverage(self) -> bool:
        print("Executando testes com cobertura...")

        cmd = [
            "pytest",
            "tests/",
            "--cov=api",
            "--cov-report=xml:coverage.xml",
            "--cov-report=html:htmlcov",
            "--cov-report=term-missing",
            "--junit-xml=test-results.xml",
            "-v",
        ]

        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode == 0:
                print("Testes executados com sucesso.")
                return True

            print(f"Testes falharam: {result.stderr}")
            return False

        except Exception as exc:
            print(f"Erro ao executar testes: {str(exc)}")
            return False

    def run_static_analysis(self) -> bool:
        print("Executando análise estática...")

        commands = [
            [
                "pylint",
                "api/",
                "tests/",
                "--output-format=json",
                "--reports=yes",
            ],
            [
                "bandit",
                "-r",
                "api/",
                "-f",
                "json",
                "-o",
                "bandit-report.json",
            ],
            [
                "flake8",
                "api/",
                "tests/",
                "--format=json",
                "--output-file=flake8-report.json",
            ],
        ]

        try:
            for cmd in commands:
                subprocess.run(
                    cmd,
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                    check=False,
                )

            print("Análise estática concluída.")
            return True

        except Exception as exc:
            print(f"Erro na análise estática: {str(exc)}")
            return False

    def run_sonar_scanner(self, token: Optional[str] = None) -> bool:
        print("Executando SonarQube Scanner...")

        cmd = [
            "sonar-scanner",
            f"-Dsonar.host.url={self.sonar_host}",
            f"-Dsonar.projectKey={self.project_key}",
            "-Dsonar.sources=api/",
            "-Dsonar.tests=tests/",
            "-Dsonar.python.coverage.reportPaths=coverage.xml",
            "-Dsonar.python.xunit.reportPath=test-results.xml",
            "-Dsonar.sourceEncoding=UTF-8",
        ]

        if token:
            cmd.append(f"-Dsonar.login={token}")

        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode == 0:
                print("SonarQube Scanner executado com sucesso.")
                print(f"Resultados disponíveis em: {self.sonar_host}")
                return True

            print(f"SonarQube Scanner falhou: {result.stderr}")
            return False

        except FileNotFoundError:
            print("sonar-scanner não encontrado. Instale o SonarQube Scanner.")
            print("Documentação: https://docs.sonarsource.com/sonarqube-server/analyzing-source-code/scanners/sonarscanner/")
            return False

        except Exception as exc:
            print(f"Erro ao executar SonarQube Scanner: {str(exc)}")
            return False

    def get_quality_gate_status(self, token: Optional[str] = None) -> Dict[str, Any]:
        headers = {}

        if token:
            headers["Authorization"] = f"Bearer {token}"

        try:
            print("Aguardando processamento da análise...")
            time.sleep(30)

            response = requests.get(
                f"{self.sonar_host}/api/qualitygates/project_status",
                params={"projectKey": self.project_key},
                headers=headers,
                timeout=30,
            )

            if response.status_code == 200:
                return response.json()

            return {"error": f"HTTP {response.status_code}"}

        except requests.RequestException as exc:
            return {"error": str(exc)}

    def run_full_analysis(self, token: Optional[str] = None, skip_tests: bool = False) -> bool:
        print("Iniciando análise completa do SonarQube...")
        print(f"Projeto: {self.project_key}")
        print(f"Servidor: {self.sonar_host}")
        print("=" * 50)

        if not self.wait_for_sonar_server():
            return False

        if not skip_tests and not self.run_tests_with_coverage():
            print("Testes falharam, mas a análise continuará.")

        self.run_static_analysis()

        if not self.run_sonar_scanner(token):
            return False

        print("Verificando Quality Gate...")
        quality_gate_status = self.get_quality_gate_status(token)

        if "error" in quality_gate_status:
            print(f"Erro ao verificar Quality Gate: {quality_gate_status['error']}")
        else:
            project_status = quality_gate_status.get("projectStatus", {})
            status = project_status.get("status", "UNKNOWN")

            if status == "OK":
                print("Quality Gate: PASSOU.")
            elif status == "ERROR":
                print("Quality Gate: FALHOU.")

                conditions = project_status.get("conditions", [])

                for condition in conditions:
                    if condition.get("status") == "ERROR":
                        metric = condition.get("metricKey")
                        actual = condition.get("actualValue")
                        threshold = condition.get("errorThreshold")
                        print(f"{metric}: {actual} | threshold: {threshold}")
            else:
                print(f"Quality Gate: {status}")

        print("=" * 50)
        print("Análise SonarQube concluída.")
        print(f"Acesse os resultados em: {self.sonar_host}/dashboard?id={self.project_key}")

        return True


def main():
    parser = argparse.ArgumentParser(
        description="Health API SonarQube Analysis Runner"
    )
    parser.add_argument(
        "--host",
        default="http://localhost:9000",
        help="SonarQube host",
    )
    parser.add_argument(
        "--token",
        help="SonarQube authentication token",
    )
    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="Skip test execution",
    )

    args = parser.parse_args()

    runner = SonarAnalysisRunner(args.host)

    success = runner.run_full_analysis(
        token=args.token,
        skip_tests=args.skip_tests,
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
