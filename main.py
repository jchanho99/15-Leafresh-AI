import os
from dotenv import load_dotenv

from LLM_verify_model import ImageVerifyModel

# 환경 변수 불러오기
load_dotenv()
bucket_name = os.getenv("BUCKET_NAME")

if __name__ == "__main__" :
    verifier = ImageVerifyModel()
    result = verifier.image_verify(bucket_name=bucket_name, blob_name="example2.webp")

    print(f"[이미지 분석 결과] \n{result}")


# https://storage.cloud.google.com/leafresh-images/