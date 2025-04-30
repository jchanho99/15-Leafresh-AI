from vertexai import init
from vertexai.preview.generative_models import GenerativeModel, Image
from dotenv import load_dotenv
import os

load_dotenv()

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

# Vertex AI 프로젝트/리전 초기화
init(project="keen-scion-457104-n8", location="us-central1")

# 모델 정의
model = GenerativeModel("gemini-1.5-pro") 

# 이미지 업로드
image = Image.load_from_file("example.png")

# 조건 프롬프트 작성
prompt = (
    "이 이미지는 '텀블러 챌린지'에 적합한 이미지 인가요?"
    "텀블러를 사용한 것이 맞으면 모두 '예'로 출력해주세요."

    "적합한 이미지인지 예/아니오로 대답하고, 예일 경우 더이상의 말은 필요 없어, 아닐경우 이유도 간단히 한 줄로 설명해줘. (30자 넘지 않게)"
)

# API 호출
response = model.generate_content(
    [prompt, image],
    generation_config={
        "temperature": 0.4,
        "top_p": 1,
        "top_k": 32,
        "max_output_tokens": 512
    }
)

# 결과 출력
print("\n[이미지 분석 결과]")
print(response.text)

