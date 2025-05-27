# test_performance_chatbot.py
# 챗봇 성능 테스트 스크립트
import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Any
import os
from dotenv import load_dotenv
import subprocess
import sys
import statistics
import matplotlib.pyplot as plt
import seaborn as sns
from concurrent.futures import ThreadPoolExecutor, as_completed

# 환경변수 로드
load_dotenv()

# API 엔드포인트
BASE_URL = "http://127.0.0.1:9000"  # FastAPI 기본 포트

class ChatbotPerformanceTester:
    def __init__(self):
        self.results = {
            "base_info_performance": [],
            "free_text_performance": [],
            "concurrent_performance": [],
            "summary": {}
        }
        self.server_process = None
    
    def start_server(self):
        """로컬 서버 시작"""
        print("로컬 서버를 시작합니다...")
        try:
            os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            self.server_process = subprocess.Popen(
                [sys.executable, "main.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # 서버 시작 대기
            max_retries = 10
            retry_count = 0
            while retry_count < max_retries:
                try:
                    response = requests.get(f"{BASE_URL}/docs")
                    if response.status_code == 200:
                        print("서버가 성공적으로 시작되었습니다.")
                        return
                except requests.exceptions.ConnectionError:
                    pass
                
                if self.server_process.poll() is not None:
                    stdout, stderr = self.server_process.communicate()
                    print("서버 시작 실패:")
                    print("STDOUT:", stdout)
                    print("STDERR:", stderr)
                    raise Exception("서버 시작 실패")
                
                time.sleep(1)
                retry_count += 1
                print(f"서버 시작 대기 중... ({retry_count}/{max_retries})")
            
            raise Exception("서버 시작 시간 초과")
            
        except Exception as e:
            print(f"서버 시작 중 오류 발생: {str(e)}")
            self.stop_server()
            sys.exit(1)
    
    def stop_server(self):
        """서버 종료"""
        if self.server_process:
            print("\n서버를 종료합니다...")
            self.server_process.terminate()
            self.server_process.wait()
            print("서버가 종료되었습니다.")
    
    def __del__(self):
        """소멸자에서 서버 종료"""
        self.stop_server()
    
    def test_base_info_performance(self, num_requests=100):
        """기본 정보 기반 추천 성능 테스트"""
        print("\n=== 기본 정보 기반 추천 성능 테스트 ===")
        
        test_cases = [
            {
                "location": "도시",
                "workType": "사무직",
                "category": "제로웨이스트"
            },
            {
                "location": "농촌",
                "workType": "현장직",
                "category": "에너지절약"
            },
            {
                "location": "해안",
                "workType": "영업직",
                "category": "플로깅"
            }
        ]
        
        for _ in range(num_requests):
            test_case = test_cases[_ % len(test_cases)]
            start_time = time.time()
            
            try:
                response = requests.post(
                    f"{BASE_URL}/ai/chatbot/recommendation/base-info",
                    json=test_case
                )
                end_time = time.time()
                
                self.results["base_info_performance"].append({
                    "input": test_case,
                    "response_time": end_time - start_time,
                    "status_code": response.status_code,
                    "success": response.status_code == 200
                })
                
            except Exception as e:
                print(f"테스트 실행 중 오류 발생: {str(e)}")
    
    def test_free_text_performance(self, num_requests=100):
        """자유 텍스트 기반 추천 성능 테스트"""
        print("\n=== 자유 텍스트 기반 추천 성능 테스트 ===")
        
        test_cases = [
            "환경 보호를 위한 일상적인 실천 방법을 알려주세요.",
            "플라스틱 사용을 줄이기 위한 방법을 추천해주세요.",
            "에너지 절약을 위한 실천 방법을 알려주세요."
        ]
        
        for _ in range(num_requests):
            test_case = test_cases[_ % len(test_cases)]
            start_time = time.time()
            
            try:
                response = requests.post(
                    f"{BASE_URL}/ai/chatbot/recommendation/free-text",
                    json={"message": test_case}
                )
                end_time = time.time()
                
                self.results["free_text_performance"].append({
                    "input": test_case,
                    "response_time": end_time - start_time,
                    "status_code": response.status_code,
                    "success": response.status_code == 200
                })
                
            except Exception as e:
                print(f"테스트 실행 중 오류 발생: {str(e)}")
    
    def test_concurrent_performance(self, num_concurrent=10, num_requests=100):
        """동시 요청 처리 성능 테스트"""
        print("\n=== 동시 요청 처리 성능 테스트 ===")
        
        def make_request(request_type):
            if request_type == "base_info":
                return requests.post(
                    f"{BASE_URL}/ai/chatbot/recommendation/base-info",
                    json={
                        "location": "도시",
                        "workType": "사무직",
                        "category": "제로웨이스트"
                    }
                )
            else:
                return requests.post(
                    f"{BASE_URL}/ai/chatbot/recommendation/free-text",
                    json={"message": "환경 보호 방법을 알려주세요."}
                )
        
        with ThreadPoolExecutor(max_workers=num_concurrent) as executor:
            futures = []
            for _ in range(num_requests):
                request_type = "base_info" if _ % 2 == 0 else "free_text"
                futures.append(executor.submit(make_request, request_type))
            
            for future in as_completed(futures):
                try:
                    response = future.result()
                    self.results["concurrent_performance"].append({
                        "status_code": response.status_code,
                        "success": response.status_code == 200
                    })
                except Exception as e:
                    print(f"동시 요청 처리 중 오류 발생: {str(e)}")
    
    def calculate_performance_metrics(self):
        """성능 메트릭 계산"""
        metrics = {
            "base_info": {
                "total_requests": len(self.results["base_info_performance"]),
                "successful_requests": sum(1 for r in self.results["base_info_performance"] if r["success"]),
                "response_times": [r["response_time"] for r in self.results["base_info_performance"]],
                "avg_response_time": 0,
                "p95_response_time": 0,
                "p99_response_time": 0
            },
            "free_text": {
                "total_requests": len(self.results["free_text_performance"]),
                "successful_requests": sum(1 for r in self.results["free_text_performance"] if r["success"]),
                "response_times": [r["response_time"] for r in self.results["free_text_performance"]],
                "avg_response_time": 0,
                "p95_response_time": 0,
                "p99_response_time": 0
            },
            "concurrent": {
                "total_requests": len(self.results["concurrent_performance"]),
                "successful_requests": sum(1 for r in self.results["concurrent_performance"] if r["success"])
            }
        }
        
        # 응답 시간 통계 계산
        for endpoint in ["base_info", "free_text"]:
            if metrics[endpoint]["response_times"]:
                metrics[endpoint]["avg_response_time"] = statistics.mean(metrics[endpoint]["response_times"])
                metrics[endpoint]["p95_response_time"] = statistics.quantiles(metrics[endpoint]["response_times"], n=20)[18]
                metrics[endpoint]["p99_response_time"] = statistics.quantiles(metrics[endpoint]["response_times"], n=100)[98]
        
        self.results["summary"] = metrics
    
    def generate_performance_plots(self):
        """성능 테스트 결과 시각화"""
        # 응답 시간 분포 플롯
        plt.figure(figsize=(12, 6))
        
        # 기본 정보 기반 추천 응답 시간
        base_info_times = [r["response_time"] for r in self.results["base_info_performance"]]
        sns.histplot(base_info_times, label="Base Info", alpha=0.5)
        
        # 자유 텍스트 기반 추천 응답 시간
        free_text_times = [r["response_time"] for r in self.results["free_text_performance"]]
        sns.histplot(free_text_times, label="Free Text", alpha=0.5)
        
        plt.title("Response Time Distribution")
        plt.xlabel("Response Time (seconds)")
        plt.ylabel("Count")
        plt.legend()
        
        # 플롯 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        plt.savefig(f"performance_plot_{timestamp}.png")
        plt.close()
    
    def save_results(self):
        """테스트 결과를 파일로 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"test_performance_chatbot_{timestamp}.json"
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        print(f"\n테스트 결과가 {filename}에 저장되었습니다.")

def run_performance_tests():
    """성능 테스트 실행"""
    tester = ChatbotPerformanceTester()
    
    try:
        # 서버 시작
        tester.start_server()
        
        # 기본 정보 기반 추천 성능 테스트
        tester.test_base_info_performance(num_requests=100)
        
        # 자유 텍스트 기반 추천 성능 테스트
        tester.test_free_text_performance(num_requests=100)
        
        # 동시 요청 처리 성능 테스트
        tester.test_concurrent_performance(num_concurrent=10, num_requests=100)
        
        # 성능 메트릭 계산
        tester.calculate_performance_metrics()
        
        # 성능 플롯 생성
        tester.generate_performance_plots()
        
        # 결과 저장
        tester.save_results()
        
    finally:
        # 서버 종료
        tester.stop_server()

if __name__ == "__main__":
    print("챗봇 성능 테스트를 시작합니다...")
    run_performance_tests()
    print("테스트가 완료되었습니다.") 