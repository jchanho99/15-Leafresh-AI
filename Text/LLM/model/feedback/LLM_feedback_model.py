from typing import List, Dict, Any
from datetime import datetime, timedelta
from google.cloud import aiplatform
from .LLM_feedback import (
    SERVICE_ACCOUNT_FILE,
    PROJECT_ID,
    LOCATION,
    MODEL_NAME,
    FEEDBACK_PROMPT_TEMPLATE
)

class FeedbackModel:
    def __init__(self):
        self.vertex_ai = aiplatform.init(
            project=PROJECT_ID,
            location=LOCATION,
            credentials=SERVICE_ACCOUNT_FILE
        )
        self.model = self.vertex_ai.get_model(MODEL_NAME)
        # 한글 기준으로 2-3문장에 적절한 토큰 수 설정 (약 100-150자)
        self.max_tokens = 100

    def _is_within_last_week(self, date_str: str) -> bool:
        """주어진 날짜가 최근 일주일 이내인지 확인"""
        try:
            date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            one_week_ago = datetime.now() - timedelta(days=7)
            return date >= one_week_ago
        except (ValueError, TypeError):
            return False

    def _format_personal_challenges(self, challenges: List[Dict[str, Any]]) -> str:
        if not challenges:
            return "참여한 개인 챌린지가 없습니다."
        
        formatted = []
        for challenge in challenges:
            status = "성공" if challenge["isSuccess"] else "실패"
            formatted.append(f"- {challenge['title']} ({status})")
        return "\n".join(formatted)

    def _format_group_challenges(self, challenges: List[Dict[str, Any]]) -> str:
        if not challenges:
            return "참여한 단체 챌린지가 없습니다."
        
        formatted = []
        for challenge in challenges:
            # 실천 결과가 있는 챌린지만 필터링
            submissions = challenge.get("submissions", [])
            if not submissions:
                continue

            # 최근 일주일 이내의 제출만 필터링
            recent_submissions = [
                s for s in submissions
                if self._is_within_last_week(s["submittedAt"])
            ]
            
            if not recent_submissions:
                continue

            success_count = sum(1 for s in recent_submissions if s["isSuccess"])
            total_count = len(recent_submissions)
            
            formatted.append(
                f"- {challenge['title']}\n"
                f"  기간: {challenge['startDate']} ~ {challenge['endDate']}\n"
                f"  최근 일주일 성공률: {success_count}/{total_count}"
            )
        return "\n".join(formatted) if formatted else "최근 일주일 동안 참여한 단체 챌린지가 없습니다."

    def generate_feedback(self, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # 입력 데이터 검증
            if not data.get("memberId"):
                raise ValueError("memberId는 필수입니다.")
            
            if not data.get("personalChallenges") and not data.get("groupChallenges"):
                raise ValueError("최소 1개의 챌린지 데이터가 필요합니다.")

            # 챌린지 데이터 포맷팅
            personal_challenges = self._format_personal_challenges(data.get("personalChallenges", []))
            group_challenges = self._format_group_challenges(data.get("groupChallenges", []))

            # 프롬프트 생성
            prompt = FEEDBACK_PROMPT_TEMPLATE.format(
                personal_challenges=personal_challenges,
                group_challenges=group_challenges
            )

            # Vertex AI를 통한 피드백 생성 (max_tokens 설정)
            response = self.model.predict(
                prompt,
                max_tokens=self.max_tokens
            )

            feedback = response.text.strip()
            return {
                "status": 200,
                "message": "주간 피드백이 성공적으로 생성되었습니다.",
                "data": {
                    "memberId": data["memberId"],
                    "feedback": feedback
                }
            }

        except ValueError as e:
            return {
                "status": 422,
                "message": str(e),
                "data": None
            }
        except Exception as e:
            return {
                "status": 500,
                "message": "서버 오류로 피드백 생성을 완료하지 못했습니다. 잠시 후 다시 시도해주세요.",
                "data": None
            } 