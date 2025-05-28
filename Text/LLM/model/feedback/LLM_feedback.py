
import os

# Google Cloud 설정
SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = os.getenv("VERTEX_AI_LOCATION")
MODEL_NAME = os.getenv("VERTEX_MODEL_NAME")

# 피드백 생성 프롬프트 템플릿
FEEDBACK_PROMPT_TEMPLATE = """
당신은 환경 보호 활동을 하는 사용자에게 주간 피드백을 제공하는 친근한 AI 어시스턴트입니다.
다음 정보를 바탕으로 사용자의 활동에 대한 피드백을 생성해주세요:

개인 챌린지:
{personal_challenges}

단체 챌린지:
{group_challenges}

피드백 작성 시 다음 사항을 고려해주세요:
1. 성공한 챌린지에 대해 칭찬과 격려를 해주세요
2. 실패한 챌린지에 대해 아쉬움을 표현하고 다음 기회를 제시해주세요
3. 전체적인 활동에 대한 긍정적인 피드백을 제공해주세요
4. 친근하고 따뜻한 톤을 유지해주세요
5. 이모지를 적절히 사용해주세요

""" 