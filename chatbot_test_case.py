# chatbot_performance_test.py
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
import signal
import time

# 환경변수 로드
load_dotenv()

# API 엔드포인트
BASE_URL = "http://127.0.0.1:9000"  # FastAPI 기본 포트

class ChatbotTester:
    def __init__(self):
        self.results = {
            "base_info_tests": [],
            "free_text_tests": [],
            "error_tests": [],
            "performance_metrics": {}
        }
        self.server_process = None
    
    def start_server(self):
        """로컬 서버 시작"""
        print("로컬 서버를 시작합니다...")
        try:
            # main.py가 있는 디렉토리로 이동
            os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            
            # 서버 프로세스 시작
            self.server_process = subprocess.Popen(
                [sys.executable, "main.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # 서버가 시작될 때까지 잠시 대기
            time.sleep(2)
            print("서버가 시작되었습니다.")
            
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
    
    def test_base_info_recommendation(self, test_cases: List[Dict[str, Any]]):
        """기본 정보 기반 추천 테스트"""
        print("\n=== 기본 정보 기반 추천 테스트 ===")
        
        for case in test_cases:
            print(f"\n테스트 케이스: {case['description']}")
            start_time = time.time()
            
            try:
                response = requests.post(
                    f"{BASE_URL}/ai/chatbot/recommendation/base-info",
                    json=case["input"]
                )
                end_time = time.time()
                
                result = {
                    "description": case["description"],
                    "input": case["input"],
                    "status_code": response.status_code,
                    "response_time": end_time - start_time,
                    "response": response.json() if response.status_code == 200 else None,
                    "expected_status": case.get("expected_status", 200),
                    "passed": response.status_code == case.get("expected_status", 200)
                }
                
                print(f"상태 코드: {response.status_code}")
                print(f"응답 시간: {result['response_time']:.3f}초")
                print(f"테스트 결과: {'성공' if result['passed'] else '실패'}")
                
                self.results["base_info_tests"].append(result)
                
            except Exception as e:
                print(f"테스트 실행 중 오류 발생: {str(e)}")
                self.results["base_info_tests"].append({
                    "description": case["description"],
                    "input": case["input"],
                    "error": str(e),
                    "passed": False
                })
    
    def test_free_text_recommendation(self, test_cases: List[Dict[str, Any]]):
        """자유 텍스트 기반 추천 테스트"""
        print("\n=== 자유 텍스트 기반 추천 테스트 ===")
        
        for case in test_cases:
            print(f"\n테스트 케이스: {case['description']}")
            start_time = time.time()
            
            try:
                response = requests.post(
                    f"{BASE_URL}/ai/chatbot/recommendation/free-text",
                    json=case["input"]
                )
                end_time = time.time()
                
                result = {
                    "description": case["description"],
                    "input": case["input"],
                    "status_code": response.status_code,
                    "response_time": end_time - start_time,
                    "response": response.json() if response.status_code == 200 else None,
                    "expected_status": case.get("expected_status", 200),
                    "passed": response.status_code == case.get("expected_status", 200)
                }
                
                print(f"상태 코드: {response.status_code}")
                print(f"응답 시간: {result['response_time']:.3f}초")
                print(f"테스트 결과: {'성공' if result['passed'] else '실패'}")
                
                self.results["free_text_tests"].append(result)
                
            except Exception as e:
                print(f"테스트 실행 중 오류 발생: {str(e)}")
                self.results["free_text_tests"].append({
                    "description": case["description"],
                    "input": case["input"],
                    "error": str(e),
                    "passed": False
                })
    
    def test_error_handling(self, test_cases: List[Dict[str, Any]]):
        """오류 처리 테스트"""
        print("\n=== 오류 처리 테스트 ===")
        
        for case in test_cases:
            print(f"\n테스트 케이스: {case['description']}")
            start_time = time.time()
            
            try:
                response = requests.post(
                    f"{BASE_URL}{case['endpoint']}",
                    json=case["input"]
                )
                end_time = time.time()
                
                result = {
                    "description": case["description"],
                    "input": case["input"],
                    "status_code": response.status_code,
                    "response_time": end_time - start_time,
                    "response": response.json() if response.status_code == 200 else None,
                    "expected_status": case["expected_status"],
                    "passed": response.status_code == case["expected_status"]
                }
                
                print(f"상태 코드: {response.status_code}")
                print(f"응답 시간: {result['response_time']:.3f}초")
                print(f"테스트 결과: {'성공' if result['passed'] else '실패'}")
                
                self.results["error_tests"].append(result)
                
            except Exception as e:
                print(f"테스트 실행 중 오류 발생: {str(e)}")
                self.results["error_tests"].append({
                    "description": case["description"],
                    "input": case["input"],
                    "error": str(e),
                    "passed": False
                })
    
    def calculate_performance_metrics(self):
        """성능 메트릭 계산"""
        metrics = {
            "base_info": {
                "total_tests": len(self.results["base_info_tests"]),
                "passed_tests": sum(1 for t in self.results["base_info_tests"] if t.get("passed", False)),
                "avg_response_time": 0,
                "max_response_time": 0,
                "min_response_time": float('inf')
            },
            "free_text": {
                "total_tests": len(self.results["free_text_tests"]),
                "passed_tests": sum(1 for t in self.results["free_text_tests"] if t.get("passed", False)),
                "avg_response_time": 0,
                "max_response_time": 0,
                "min_response_time": float('inf')
            }
        }
        
        # 기본 정보 기반 추천 메트릭
        response_times = [t["response_time"] for t in self.results["base_info_tests"] if "response_time" in t]
        if response_times:
            metrics["base_info"]["avg_response_time"] = sum(response_times) / len(response_times)
            metrics["base_info"]["max_response_time"] = max(response_times)
            metrics["base_info"]["min_response_time"] = min(response_times)
        
        # 자유 텍스트 기반 추천 메트릭
        response_times = [t["response_time"] for t in self.results["free_text_tests"] if "response_time" in t]
        if response_times:
            metrics["free_text"]["avg_response_time"] = sum(response_times) / len(response_times)
            metrics["free_text"]["max_response_time"] = max(response_times)
            metrics["free_text"]["min_response_time"] = min(response_times)
        
        self.results["performance_metrics"] = metrics
    
    def save_results(self):
        """테스트 결과를 파일로 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"chatbot_performance_test_{timestamp}.json"
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        print(f"\n테스트 결과가 {filename}에 저장되었습니다.")

def run_tests():
    """테스트 실행"""
    tester = ChatbotTester()
    
    try:
        # 서버 시작
        tester.start_server()
        
        # 기본 정보 기반 추천 테스트 케이스
        base_info_test_cases = [
            # 정상 케이스
            {
                "description": "도시 사무직 제로웨이스트 추천",
                "input": {
                    "location": "도시",
                    "workType": "사무직",
                    "category": "제로웨이스트"
                }
            },
            {
                "description": "농촌 현장직 에너지절약 추천",
                "input": {
                    "location": "농촌",
                    "workType": "현장직",
                    "category": "에너지절약"
                }
            },
            {
                "description": "해안 영업직 플로깅 추천",
                "input": {
                    "location": "해안",
                    "workType": "영업직",
                    "category": "플로깅"
                }
            },
            {
                "description": "산간 재택근무 디지털탄소 추천",
                "input": {
                    "location": "산간",
                    "workType": "재택근무",
                    "category": "디지털탄소"
                }
            },
            {
                "description": "도시 영업직 비건 추천",
                "input": {
                    "location": "도시",
                    "workType": "영업직",
                    "category": "비건"
                }
            },
            # 경계값 테스트
            {
                "description": "최소 길이 카테고리",
                "input": {
                    "location": "도시",
                    "workType": "사무직",
                    "category": "비건"
                }
            },
            {
                "description": "최대 길이 카테고리",
                "input": {
                    "location": "도시",
                    "workType": "사무직",
                    "category": "디지털탄소"
                }
            },
            {
                "description": "복합적인 카테고리 추천",
                "input": {
                    "location": "도시",
                    "workType": "사무직",
                    "category": "제로웨이스트,에너지절약"
                }
            },
            {
                "description": "새로운 카테고리 추천",
                "input": {
                    "location": "도시",
                    "workType": "사무직",
                    "category": "친환경교통"
                }
            },
            {
                "description": "모든 지역 조합 테스트",
                "input": {
                    "location": "도시,농촌,해안,산간",
                    "workType": "사무직",
                    "category": "제로웨이스트"
                }
            },
            {
                "description": "모든 직종 조합 테스트",
                "input": {
                    "location": "도시",
                    "workType": "사무직,영업직,현장직,재택근무",
                    "category": "에너지절약"
                }
            },
            {
                "description": "영문 카테고리 테스트",
                "input": {
                    "location": "도시",
                    "workType": "사무직",
                    "category": "zerowaste"
                }
            }
        ]
        
        # 자유 텍스트 기반 추천 테스트 케이스
        free_text_test_cases = [
            # 일반적인 환경 보호 관련 질문
            {
                "description": "일반적인 환경 보호 방법 문의",
                "input": {
                    "message": "환경 보호를 위한 일상적인 실천 방법을 알려주세요."
                }
            },
            {
                "description": "플라스틱 사용 줄이기 문의",
                "input": {
                    "message": "플라스틱 사용을 줄이기 위한 방법을 추천해주세요."
                }
            },
            {
                "description": "에너지 절약 방법 문의",
                "input": {
                    "message": "에너지 절약을 위한 실천 방법을 알려주세요."
                }
            },
            # 구체적인 상황 기반 질문
            {
                "description": "사무실에서의 환경 보호",
                "input": {
                    "message": "사무실에서 할 수 있는 환경 보호 활동이 궁금해요."
                }
            },
            {
                "description": "재택근무 환경 보호",
                "input": {
                    "message": "재택근무하면서 환경 보호를 실천하는 방법이 있을까요?"
                }
            },
            {
                "description": "영업직 환경 보호",
                "input": {
                    "message": "영업직으로 일하면서 환경 보호를 실천할 수 있는 방법이 있나요?"
                }
            },
            # 특정 카테고리 관련 질문
            {
                "description": "제로웨이스트 관련 질문",
                "input": {
                    "message": "제로웨이스트 실천 방법을 알려주세요."
                }
            },
            {
                "description": "플로깅 관련 질문",
                "input": {
                    "message": "플로깅을 시작하고 싶은데 어떻게 해야 할까요?"
                }
            },
            {
                "description": "비건 관련 질문",
                "input": {
                    "message": "비건 식단으로 전환하고 싶은데 도움이 필요해요."
                }
            },
            # 복합적인 질문
            {
                "description": "복합 환경 보호 방법 문의",
                "input": {
                    "message": "플라스틱 줄이기와 에너지 절약을 동시에 할 수 있는 방법이 있을까요?"
                }
            },
            {
                "description": "지역별 환경 보호 방법 문의",
                "input": {
                    "message": "도시에서 할 수 있는 환경 보호 활동과 농촌에서 할 수 있는 활동이 어떻게 다른가요?"
                }
            },
            {
                "description": "구체적인 상황 기반 질문",
                "input": {
                    "message": "회사에서 점심시간에 할 수 있는 환경 보호 활동이 있을까요?"
                }
            },
            {
                "description": "계절별 환경 보호 방법 문의",
                "input": {
                    "message": "여름철에 할 수 있는 환경 보호 활동을 추천해주세요."
                }
            },
            {
                "description": "시간대별 환경 보호 방법",
                "input": {
                    "message": "아침 출근 시간에 할 수 있는 환경 보호 활동이 있을까요?"
                }
            },
            {
                "description": "날씨별 환경 보호 방법",
                "input": {
                    "message": "비 오는 날에 할 수 있는 환경 보호 활동을 추천해주세요."
                }
            },
            {
                "description": "연령대별 환경 보호 방법",
                "input": {
                    "message": "20대 직장인이 할 수 있는 환경 보호 활동이 궁금해요."
                }
            },
            {
                "description": "가족 단위 환경 보호 방법",
                "input": {
                    "message": "가족과 함께 할 수 있는 환경 보호 활동을 추천해주세요."
                }
            }
        ]
        
        # 오류 처리 테스트 케이스
        error_test_cases = [
            # 필수 필드 누락 테스트
            {
                "description": "location 필드 누락",
                "endpoint": "/ai/chatbot/recommendation/base-info",
                "input": {
                    "workType": "사무직",
                    "category": "제로웨이스트"
                },
                "expected_status": 400
            },
            {
                "description": "workType 필드 누락",
                "endpoint": "/ai/chatbot/recommendation/base-info",
                "input": {
                    "location": "도시",
                    "category": "제로웨이스트"
                },
                "expected_status": 400
            },
            {
                "description": "category 필드 누락",
                "endpoint": "/ai/chatbot/recommendation/base-info",
                "input": {
                    "location": "도시",
                    "workType": "사무직"
                },
                "expected_status": 400
            },
            # 잘못된 입력값 테스트
            {
                "description": "잘못된 location 값",
                "endpoint": "/ai/chatbot/recommendation/base-info",
                "input": {
                    "location": "우주",
                    "workType": "사무직",
                    "category": "제로웨이스트"
                },
                "expected_status": 200
            },
            {
                "description": "잘못된 workType 값",
                "endpoint": "/ai/chatbot/recommendation/base-info",
                "input": {
                    "location": "도시",
                    "workType": "우주인",
                    "category": "제로웨이스트"
                },
                "expected_status": 200
            },
            {
                "description": "잘못된 category 값",
                "endpoint": "/ai/chatbot/recommendation/base-info",
                "input": {
                    "location": "도시",
                    "workType": "사무직",
                    "category": "우주여행"
                },
                "expected_status": 200
            },
            # 자유 텍스트 오류 테스트
            {
                "description": "빈 메시지",
                "endpoint": "/ai/chatbot/recommendation/free-text",
                "input": {
                    "message": ""
                },
                "expected_status": 400
            },
            {
                "description": "최소 길이 미만 메시지",
                "endpoint": "/ai/chatbot/recommendation/free-text",
                "input": {
                    "message": "환경"
                },
                "expected_status": 422
            },
            {
                "description": "비속어 포함 메시지",
                "endpoint": "/ai/chatbot/recommendation/free-text",
                "input": {
                    "message": "시발 환경 보호 방법 알려줘"
                },
                "expected_status": 200
            },
            {
                "description": "환경 관련 키워드 없는 메시지",
                "endpoint": "/ai/chatbot/recommendation/free-text",
                "input": {
                    "message": "오늘 날씨가 좋네요"
                },
                "expected_status": 200
            },
            # 특수 문자 테스트
            {
                "description": "특수 문자 포함 메시지",
                "endpoint": "/ai/chatbot/recommendation/free-text",
                "input": {
                    "message": "환경 보호 방법!!! 알려주세요~~~"
                },
                "expected_status": 200
            },
            {
                "description": "긴 메시지 테스트",
                "endpoint": "/ai/chatbot/recommendation/free-text",
                "input": {
                    "message": "환경 보호를 위해 제가 할 수 있는 일이 무엇이 있을까요? 저는 현재 도시에서 사무직으로 일하고 있고, 평소에는 플라스틱 사용을 줄이려고 노력하고 있습니다. 하지만 더 효과적인 방법이 있는지 궁금합니다. 특히 일상생활에서 실천할 수 있는 구체적인 방법을 알고 싶습니다."
                },
                "expected_status": 200
            },
            {
                "description": "잘못된 엔드포인트 테스트",
                "endpoint": "/ai/chatbot/recommendation/wrong-endpoint",
                "input": {
                    "message": "환경 보호 방법 알려주세요"
                },
                "expected_status": 404
            },
            {
                "description": "SQL 인젝션 시도",
                "endpoint": "/ai/chatbot/recommendation/free-text",
                "input": {
                    "message": "환경 보호 방법'; DROP TABLE users; --"
                },
                "expected_status": 200
            },
            {
                "description": "XSS 시도",
                "endpoint": "/ai/chatbot/recommendation/free-text",
                "input": {
                    "message": "환경 보호 방법<script>alert('xss')</script>"
                },
                "expected_status": 200
            },
            {
                "description": "너무 긴 메시지",
                "endpoint": "/ai/chatbot/recommendation/free-text",
                "input": {
                    "message": "환경" * 1000
                },
                "expected_status": 422
            }
        ]
        
        # 테스트 실행
        tester.test_base_info_recommendation(base_info_test_cases)
        tester.test_free_text_recommendation(free_text_test_cases)
        tester.test_error_handling(error_test_cases)
        
        # 성능 메트릭 계산
        tester.calculate_performance_metrics()
        
        # 결과 저장
        tester.save_results()
        
    finally:
        # 서버 종료
        tester.stop_server()

if __name__ == "__main__":
    print("챗봇 성능 테스트를 시작합니다...")
    run_tests()
    print("테스트가 완료되었습니다.") 