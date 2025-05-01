from vertexai import init
from vertexai.preview.generative_models import GenerativeModel, Image
from dotenv import load_dotenv
import os

# GCP Cloud Storage 연결
from google.cloud import storage  
import tempfile                     # 임시 파일 저장용


class ImageVerifyModel :
    def __init__(self, credential_env="GOOGLE_APPLICATION_CREDENTIALS", project_id="leafresh", region="us-central1"): 
        # 환경변수 로드 및 인증 초기화
        load_dotenv()
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv(credential_env)
        init(project=project_id, location=region)                                       # Vertex AI 프로젝트/리전 초기화
        self.model = GenerativeModel("gemini-2.0-flash")                                # 모델 정의
        self.storage_client = storage.Client()                                          # GCS 클라이언트 


    def image_verify(self, bucket_name: str, blob_name: str, challenge_type: str = "텀블러 챌린지") -> str :
        try:
            bucket = self.storage_client.bucket(bucket_name)                            # 이미지 업로드 
            blob = bucket.blob(blob_name)                                 
       
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
                blob.download_to_filename(temp_file.name)
                image = Image.load_from_file(temp_file.name)

            return self.response(image, challenge_type)

        except Exception as e:
            return f"[에러] GCS 이미지 로드 실패: {e}" 


    def response(self, image, challenge_type):
        # 조건 프롬프트 생성 
        prompt = (
            f"이 이미지는 '{challenge_type}'에 적합한 이미지 인가요?"
            "분위기가 아니라 물체가 존재해야합니다. 텀블러를 사용한 것이 맞으면 모두 '예'로 출력해주세요."
            "적합한 이미지인지 예/아니오로 대답해주세요."
            "대답에 따른 이유도 간단히 한 줄로 설명해주세요. (30자 넘지 않게)"
        )
        # API 호출
        result = self.model.generate_content(
            [prompt, image],
            generation_config={
                "temperature": 0.4,
                "top_p": 1,
                "top_k": 32,
                "max_output_tokens": 512
            }
        )
        return result.text
    

