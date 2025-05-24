from PIL import Image
import requests
from io import BytesIO
import pillow_avif

url = "https://storage.googleapis.com/leafresh-images/init/2_%E1%84%8B%E1%85%B5%E1%84%87%E1%85%A6%E1%86%AB%E1%84%90%E1%85%B3_%E1%84%89%E1%85%A5%E1%86%BC%E1%84%80%E1%85%A9%E1%86%BC.png"
response = requests.get(url)
img = Image.open(BytesIO(response.content))
img_resized = img.resize((1024, int(img.height * 1024 / img.width)))

print("✅ Image size:", img.size)  # 출력: (width, height)
print("✅ Image size:", img_resized.size)
