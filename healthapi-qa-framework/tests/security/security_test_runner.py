# Health API QA Framework - Security Test Runner
# Script para execução automatizada de testes de segurança

import subprocess
import sys
import json
import time
from pathlib import Path
from typing import Dict, Any, List
import requests

class SecurityTestRunner:
    """Runner para testes de segurança automatizados"""
    
    def __init__(self, host: str = "http://localhost:8000"):
        self.host = host
        self.results_dir = Path("docs/coverage_report/security")
        self.results_dir.mkdir(parents=True, exist_ok=True)
    
    def check_api_availability(self) -> bool:
        """Verifica se a API está disponível"""
        try:
            response = requests.get(f"{self.host}/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def run_owasp_tests(self) -> Dict[str, Any]:
        """
        Executa testes de segurança OWASP
        
        Returns:
            Dicionário com resultados dos testes
        """
        print("🔒 Executando testes de segurança OWASP...")
        
        if not self.check_api_availability():
            return {
                "success": False,
                "error": "API não está disponível",
                "timestamp": time.time()
            }
        
        # Arquivo de relatório
        html_report = self.results_dir / "owasp_security_report.html"
        json_report = self.results_dir / "owasp_security_report.json"
        
        # Comando pytest para testes de segurança
        cmd = [
            "pytest",
            "tests/security/test_owasp_security.py",
            "-v",
            "--tb=short",
            f"--html={html_report}",
            f"--json-report",
            f"--json-report-file={json_report}",
            "-m", "security"
        ]
        
        try:
            start_time = time.time()
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutos timeout
            )
            end_time = time.time()
            
            # Processar resultados
            test_results = {
                "test_type": "owasp_security",
                "start_time": start_time,
                "end_time": end_time,
                "duration_seconds": end_time - start_time,
                "host": self.host,
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "html_report": str(html_report),
                "json_report": str(json_report)
            }
            
            # Tentar extrair estatísticas do output
            if "passed" in result.stdout or "failed" in result.stdout:
                test_results["summary"] = self._extract_test_summary(result.stdout)
            
            if result.returncode == 0:
                print("✅ Testes de segurança OWASP concluídos com sucesso!")
                print(f"📊 Relatório HTML: {html_report}")
            else:
                print("⚠️ Alguns testes de segurança falharam!")
                print(f"📊 Relatório HTML: {html_report}")
            
            return test_results
            
        except subprocess.TimeoutExpired:
            print("⏰ Testes de segurança expiraram (timeout)")
            return {
                "test_type": "owasp_security",
                "success": False,
                "error": "Timeout expired"
            }
        except Exception as e:
            print(f"💥 Erro ao executar testes: {str(e)}")
            return {
                "test_type": "owasp_security",
                "success": False,
                "error": str(e)
            }
    
    def run_basic_security_scan(self) -> Dict[str, Any]:
        """
        Executa scan básico de segurança
        
        Returns:
            Dicionário com resultados do scan
        """
        print("🔍 Executando scan básico de segurança...")
        
        if not self.check_api_availability():
            return {
                "success": False,
                "error": "API não está disponível"
            }
        
        scan_results = {
            "timestamp": time.time(),
            "host": self.host,
            "checks": {}
        }
        
        # Verificações básicas de segurança
        checks = [
            ("SSL/TLS", self._check_ssl),
            ("Security Headers", self._check_security_headers),
            ("Information Disclosure", self._check_info_disclosure),
            ("HTTP Methods", self._check_http_methods),
            ("Error Handling", self._check_error_handling)
        ]
        
        for check_name, check_func in checks:
            try:
                print(f"  🔍 Verificando: {check_name}")
                result = check_func()
                scan_results["checks"][check_name] = result
                
                if result.get("passed", False):
                    print(f"    ✅ {check_name}: OK")
                else:
                    print(f"    ⚠️ {check_name}: {result.get('message', 'Falhou')}")
                    
            except Exception as e:
                scan_results["checks"][check_name] = {
                    "passed": False,
                    "error": str(e)
                }
                print(f"    ❌ {check_name}: Erro - {str(e)}")
        
        # Salvar resultados
        scan_file = self.results_dir / "basic_security_scan.json"
        with open(scan_file, 'w', encoding='utf-8') as f:
            json.dump(scan_results, f, indent=2, ensure_ascii=False)
        
        print(f"📋 Resultados salvos em: {scan_file}")
        
        return {
            "success": True,
            "results": scan_results,
            "report_file": str(scan_file)
        }
    
    def _check_ssl(self) -> Dict[str, Any]:
        """Verifica configuração SSL/TLS"""
        if not self.host.startswith("https://"):
            return {
                "passed": False,
                "message": "API não está usando HTTPS",
                "recommendation": "Implementar HTTPS em produção"
            }
        
        # Se fosse HTTPS, verificaríamos certificado, versões TLS, etc.
        return {
            "passed": True,
            "message": "HTTPS não configurado (desenvolvimento)",
            "note": "Verificar HTTPS em produção"
        }
    
    def _check_security_headers(self) -> Dict[str, Any]:
        """Verifica headers de segurança"""
        try:
            response = requests.get(f"{self.host}/health", timeout=5)
            headers = response.headers
            
            # Headers de segurança recomendados
            security_headers = {
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": ["DENY", "SAMEORIGIN"],
                "X-XSS-Protection": "1; mode=block"
            }
            
            missing_headers = []
            present_headers = []
            
            for header, expected in security_headers.items():
                if header in headers:
                    present_headers.append(header)
                else:
                    missing_headers.append(header)
            
            return {
                "passed": len(missing_headers) == 0,
                "present_headers": present_headers,
                "missing_headers": missing_headers,
                "message": f"Headers presentes: {len(present_headers)}, Ausentes: {len(missing_headers)}"
            }
            
        except Exception as e:
            return {"passed": False, "error": str(e)}
    
    def _check_info_disclosure(self) -> Dict[str, Any]:
        """Verifica vazamento de informações"""
        try:
            response = requests.get(f"{self.host}/health", timeout=5)
            
            # Verificar headers que podem vazar informações
            info_headers = ["Server", "X-Powered-By", "X-AspNet-Version"]
            disclosed_info = []
            
            for header in info_headers:
                if header in response.headers:
                    disclosed_info.append(f"{header}: {response.headers[header]}")
            
            return {
                "passed": len(disclosed_info) == 0,
                "disclosed_info": disclosed_info,
                "message": "Sem vazamento de informações" if not disclosed_info else f"Informações expostas: {len(disclosed_info)}"
            }
            
        except Exception as e:
            return {"passed": False, "error": str(e)}
    
    def _check_http_methods(self) -> Dict[str, Any]:
        """Verifica métodos HTTP permitidos"""
        try:
            # Testar métodos perigosos
            dangerous_methods = ["TRACE", "CONNECT", "DELETE"]
            allowed_dangerous = []
            
            for method in dangerous_methods:
                try:
                    response = requests.request(method, f"{self.host}/health", timeout=5)
                    if response.status_code not in [405, 501]:  # Method Not Allowed
                        allowed_dangerous.append(method)
                except:
                    pass  # Método rejeitado, que é bom
            
            return {
                "passed": len(allowed_dangerous) == 0,
                "allowed_dangerous_methods": allowed_dangerous,
                "message": "Métodos HTTP seguros" if not allowed_dangerous else f"Métodos perigosos permitidos: {allowed_dangerous}"
            }
            
        except Exception as e:
            return {"passed": False, "error": str(e)}
    
    def _check_error_handling(self) -> Dict[str, Any]:
        """Verifica tratamento de erros"""
        try:
            # Testar endpoint inexistente
            response = requests.get(f"{self.host}/nonexistent-endpoint-test", timeout=5)
            
            if response.status_code == 404:
                # Verificar se não há vazamento de informações no erro
                error_text = response.text.lower()
                sensitive_info = ["traceback", "stack trace", "internal server error"]
                
                leaked_info = [info for info in sensitive_info if info in error_text]
                
                return {
                    "passed": len(leaked_info) == 0,
                    "leaked_info": leaked_info,
                    "message": "Tratamento de erro seguro" if not leaked_info else f"Informações vazadas: {leaked_info}"
                }
            else:
                return {
                    "passed": False,
                    "message": f"Endpoint inexistente retornou {response.status_code} em vez de 404"
                }
                
        except Exception as e:
            return {"passed": False, "error": str(e)}
    
    def _extract_test_summary(self, output: str) -> Dict[str, Any]:
        """Extrai resumo dos testes do output do pytest"""
        lines = output.split('\n')
        summary = {}
        
        for line in lines:
            if "passed" in line and "failed" in line:
                # Linha de resumo do pytest
                summary["raw_summary"] = line.strip()
                break
        
        return summary
    
    def run_security_suite(self) -> List[Dict[str, Any]]:
        """
        Executa suite completa de testes de segurança
        
        Returns:
            Lista com resultados de todos os testes
        """
        print("🛡️ Iniciando suite completa de testes de segurança")
        
        tests = [
            ("Scan Básico de Segurança", self.run_basic_security_scan),
            ("Testes OWASP", self.run_owasp_tests)
        ]
        
        results = []
        
        for test_name, test_func in tests:
            print(f"\n{'='*50}")
            print(f"🔒 Executando: {test_name}")
            print(f"{'='*50}")
            
            result = test_func()
            result["test_name"] = test_name
            results.append(result)
            
            if result.get("success", False):
                print("✅ Teste concluído com sucesso!")
            else:
                print("⚠️ Teste apresentou problemas!")
        
        # Salvar resumo da suite
        self._save_security_suite_summary(results)
        
        return results
    
    def _save_security_suite_summary(self, results: List[Dict[str, Any]]):
        """Salva resumo da suite de segurança"""
        summary_file = self.results_dir / "security_suite_summary.json"
        
        summary = {
            "timestamp": time.time(),
            "total_tests": len(results),
            "successful_tests": sum(1 for r in results if r.get("success", False)),
            "failed_tests": sum(1 for r in results if not r.get("success", False)),
            "results": results
        }
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        print(f"\n📋 Resumo da suite de segurança salvo em: {summary_file}")
        print(f"✅ Testes bem-sucedidos: {summary['successful_tests']}/{summary['total_tests']}")

def main():
    """Função principal para execução via linha de comando"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Health API Security Test Runner")
    parser.add_argument("--host", default="http://localhost:8000", help="Host da API")
    parser.add_argument("--test-type", choices=["owasp", "basic", "suite"], 
                       default="suite", help="Tipo de teste de segurança")
    
    args = parser.parse_args()
    
    runner = SecurityTestRunner(args.host)
    
    if args.test_type == "owasp":
        result = runner.run_owasp_tests()
    elif args.test_type == "basic":
        result = runner.run_basic_security_scan()
    elif args.test_type == "suite":
        results = runner.run_security_suite()
        return
    
    if result.get("success", False):
        print("\n🎉 Testes de segurança concluídos com sucesso!")
        sys.exit(0)
    else:
        print("\n⚠️ Testes de segurança apresentaram problemas!")
        sys.exit(1)

if __name__ == "__main__":
    main()
