from vertexai import init
from vertexai.preview.generative_models import GenerativeModel

import os
from dotenv import load_dotenv
from typing import List

from datetime import datetime
from collections import Counter

class CensorshipModel :
    def __init__(self):
        load_dotenv()
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        init(project="leafresh", location="us-central1")
        self.model = GenerativeModel("gemini-2.0-flash")

    def validate(self, challenge_name: str, start_date: str, end_date: str, existing: List[dict]):
        def dates_overlap(s1, e1, s2, e2):
            return max(s1, s2) <= min(e1, e2)
        
        # 공백만 존재하거나 5자 이하 챌린지 이름 필터링
        if not challenge_name.strip() or len(challenge_name.strip()) <= 5:
            return False, "동일한 챌린지가 존재하여 챌린지 생성이 불가능합니다."
        
        # 같은 단어가 3번 이상 반복된 경우
        words = challenge_name.strip().split()
        word_counts = Counter(words)
        for word, count in word_counts.items():     # word 빼면 코드 실행 불가능 
            if count >= 3:
                return False, "같은 단어가 반복적으로 사용되어 챌린지 생성이 불가능합니다."

        existing_names = "\n".join([f"- {c.name}" for c in existing if c.name]) or "- 없음"             # 모든 기존 챌린지 이름을 나열

        # 이름/의미 유사 여부만 판단
        prompt = (
            f"새로 생성하려는 챌린지 이름은 '{challenge_name}'입니다.\n"
            "기존 챌린지 이름 목록은 다음과 같습니다:\n"
            f"{existing_names}\n\n"
            "챌린지의 이름이 환경과 관련이 없거나 의미가 모호한 경우 'No'라고 답해주세요. \n"
            "의미가 모호하거나 명확하지 않은 문장(예: 대충, 뭐든지, 그냥, 뭔가 등)이 포함되어 있으면 'No'라고 답해주세요. \n"
            "새로운 챌린지와 이름이 같거나, 단어는 다르지만 의미나 목적이 유사한 챌린지가 존재한다면 'No'라고 답해주세요.\n"
            "스팸이나 광고성, 홍보성, 마케팅성 문구일 경우 'No'라고 답해주세요. 하지만, 친환경과 관련된 경우 'Yes'라고 답해주세요. \n"
            "특수문자만 들어간 경우, 숫자만 들어간 경우 'No'라고 답해주세요. \n"
            "같은 단어가 여러번 반복되는 경우 'No'라고 답해주세요. \n"
            "그렇지 않다면 'Yes'라고 답해주세요. \n"
            "답변은 반드시 'Yes.' 또는 'No.'로 시작해야 합니다. \n"
        )

        try:
            result = self.model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.3,
                    "top_p": 1,
                    "top_k": 32,
                    "max_output_tokens": 512
                }
            )
            answer = result.text.strip().lower()

            if answer.startswith("yes"):
                return True, "챌린지 생성이 가능합니다."
            elif answer.startswith("no"):
                
                for c in existing:
                    if not (c.startDate and c.endDate):
                        continue
                    try:
                        new_start = datetime.strptime(start_date, "%Y-%m-%d")
                        new_end = datetime.strptime(end_date, "%Y-%m-%d")
                        exist_start = datetime.strptime(c.startDate, "%Y-%m-%d")
                        exist_end = datetime.strptime(c.endDate, "%Y-%m-%d")

                        if dates_overlap(new_start, new_end, exist_start, exist_end):
                            return False, "동일한 챌린지가 존재하여 챌린지 생성이 불가능합니다."
                    except:
                        continue
                    
                # 'No'이지만, 기간이 겹치지 않음 
                return True, "챌린지 생성이 가능합니다."
            else:
                return False, "모델 응답이 명확하지 않아 챌린지 생성이 불가능합니다."

        except Exception as e:
            print("[BUG] 응답 실패 ", e)
            return False, "챌린지 검열 중 오류가 발생했습니다."

        
