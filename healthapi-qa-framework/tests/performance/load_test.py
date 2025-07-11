# Health API QA Framework - Load Test Script
# Script para execução de testes de carga automatizados

import subprocess
import sys
import time
import json
import os
from pathlib import Path
from typing import Dict, Any, List

class LoadTestRunner:
    """Runner para testes de carga automatizados"""
    
    def __init__(self, host: str = "http://localhost:8000"):
        self.host = host
        self.results_dir = Path("docs/coverage_report/performance")
        self.results_dir.mkdir(parents=True, exist_ok=True)
    
    def run_load_test(
        self,
        users: int = 10,
        spawn_rate: int = 2,
        duration: str = "60s",
        test_name: str = "load_test"
    ) -> Dict[str, Any]:
        """
        Executa teste de carga com Locust
        
        Args:
            users: Número de usuários simultâneos
            spawn_rate: Taxa de criação de usuários por segundo
            duration: Duração do teste (ex: 60s, 2m)
            test_name: Nome do teste para relatórios
        
        Returns:
            Dicionário com resultados do teste
        """
        print(f"🚀 Iniciando teste de carga: {test_name}")
        print(f"   Usuários: {users}")
        print(f"   Taxa de spawn: {spawn_rate}/s")
        print(f"   Duração: {duration}")
        print(f"   Host: {self.host}")
        
        # Arquivo de saída para relatório HTML
        html_report = self.results_dir / f"{test_name}_report.html"
        csv_stats = self.results_dir / f"{test_name}_stats.csv"
        
        # Comando Locust
        cmd = [
            "locust",
            "-f", "tests/performance/locustfile.py",
            "--headless",
            "--users", str(users),
            "--spawn-rate", str(spawn_rate),
            "--run-time", duration,
            "--host", self.host,
            "--html", str(html_report),
            "--csv", str(csv_stats.with_suffix("")),  # Locust adiciona sufixos automaticamente
            "--user-class", "LoadTestUser"
        ]
        
        try:
            # Executar teste
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
                "test_name": test_name,
                "start_time": start_time,
                "end_time": end_time,
                "duration_seconds": end_time - start_time,
                "users": users,
                "spawn_rate": spawn_rate,
                "test_duration": duration,
                "host": self.host,
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "html_report": str(html_report),
                "csv_stats": str(csv_stats)
            }
            
            if result.returncode == 0:
                print("✅ Teste de carga concluído com sucesso!")
                print(f"📊 Relatório HTML: {html_report}")
                print(f"📈 Estatísticas CSV: {csv_stats}")
            else:
                print("❌ Teste de carga falhou!")
                print(f"Erro: {result.stderr}")
            
            return test_results
            
        except subprocess.TimeoutExpired:
            print("⏰ Teste de carga expirou (timeout)")
            return {
                "test_name": test_name,
                "success": False,
                "error": "Timeout expired"
            }
        except Exception as e:
            print(f"💥 Erro ao executar teste: {str(e)}")
            return {
                "test_name": test_name,
                "success": False,
                "error": str(e)
            }
    
    def run_stress_test(self, max_users: int = 50, duration: str = "120s") -> Dict[str, Any]:
        """Executa teste de stress"""
        return self.run_load_test(
            users=max_users,
            spawn_rate=5,
            duration=duration,
            test_name="stress_test"
        )
    
    def run_spike_test(self, spike_users: int = 100, duration: str = "30s") -> Dict[str, Any]:
        """Executa teste de pico"""
        return self.run_load_test(
            users=spike_users,
            spawn_rate=20,  # Spawn rápido para simular pico
            duration=duration,
            test_name="spike_test"
        )
    
    def run_volume_test(self, users: int = 20, duration: str = "300s") -> Dict[str, Any]:
        """Executa teste de volume (longa duração)"""
        return self.run_load_test(
            users=users,
            spawn_rate=1,
            duration=duration,
            test_name="volume_test"
        )
    
    def run_performance_suite(self) -> List[Dict[str, Any]]:
        """
        Executa suite completa de testes de performance
        
        Returns:
            Lista com resultados de todos os testes
        """
        print("🎯 Iniciando suite completa de testes de performance")
        
        tests = [
            ("Teste de Carga Básico", lambda: self.run_load_test(10, 2, "60s", "basic_load")),
            ("Teste de Stress", lambda: self.run_stress_test(30, "90s")),
            ("Teste de Pico", lambda: self.run_spike_test(50, "30s")),
            ("Teste de Volume", lambda: self.run_volume_test(15, "180s"))
        ]
        
        results = []
        
        for test_name, test_func in tests:
            print(f"\n{'='*50}")
            print(f"🧪 Executando: {test_name}")
            print(f"{'='*50}")
            
            result = test_func()
            results.append(result)
            
            # Pausa entre testes para não sobrecarregar
            if result["success"]:
                print("✅ Teste concluído. Aguardando 10 segundos...")
                time.sleep(10)
            else:
                print("❌ Teste falhou. Continuando...")
        
        # Salvar resumo dos resultados
        self._save_suite_summary(results)
        
        return results
    
    def _save_suite_summary(self, results: List[Dict[str, Any]]):
        """Salva resumo da suite de testes"""
        summary_file = self.results_dir / "performance_suite_summary.json"
        
        summary = {
            "timestamp": time.time(),
            "total_tests": len(results),
            "successful_tests": sum(1 for r in results if r.get("success", False)),
            "failed_tests": sum(1 for r in results if not r.get("success", False)),
            "results": results
        }
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        print(f"\n📋 Resumo da suite salvo em: {summary_file}")
        print(f"✅ Testes bem-sucedidos: {summary['successful_tests']}/{summary['total_tests']}")

def main():
    """Função principal para execução via linha de comando"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Health API Load Test Runner")
    parser.add_argument("--host", default="http://localhost:8000", help="Host da API")
    parser.add_argument("--users", type=int, default=10, help="Número de usuários")
    parser.add_argument("--spawn-rate", type=int, default=2, help="Taxa de spawn")
    parser.add_argument("--duration", default="60s", help="Duração do teste")
    parser.add_argument("--test-type", choices=["load", "stress", "spike", "volume", "suite"], 
                       default="load", help="Tipo de teste")
    
    args = parser.parse_args()
    
    runner = LoadTestRunner(args.host)
    
    if args.test_type == "load":
        result = runner.run_load_test(args.users, args.spawn_rate, args.duration)
    elif args.test_type == "stress":
        result = runner.run_stress_test(args.users, args.duration)
    elif args.test_type == "spike":
        result = runner.run_spike_test(args.users, args.duration)
    elif args.test_type == "volume":
        result = runner.run_volume_test(args.users, args.duration)
    elif args.test_type == "suite":
        results = runner.run_performance_suite()
        return
    
    if result["success"]:
        print("\n🎉 Teste de performance concluído com sucesso!")
        sys.exit(0)
    else:
        print("\n💥 Teste de performance falhou!")
        sys.exit(1)

if __name__ == "__main__":
    main()
