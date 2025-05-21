from transformers import AutoModelForCausalLM, AutoTokenizer

model_id = "mistralai/Mistral-7B-Instruct-v0.3"

print("모델 다운로드 시작...")
model = AutoModelForCausalLM.from_pretrained(model_id)
tokenizer = AutoTokenizer.from_pretrained(model_id)
print("모델 다운로드 및 캐시 완료!") 