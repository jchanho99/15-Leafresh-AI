from vertexai.preview.generative_models import GenerativeModel

def generate_group_prompt(challenge_name: str) -> str:      # challenge_info도 수정 필요 
    model = GenerativeModel("gemini-2.0-flash")

    system_prompt_message = (
        "당신은 사용자 챌린지를 위한 프롬프트를 설계하는 AI입니다. "
        "입력받은 챌린지 이름과 설명을 기반으로 이미지 검증에 사용할 수 있는 프롬프트를 생성하세요.\n"
        "결과는 반드시 사용자의 이미지가 챌린지에 적합한지 판별할 수 있는 형태여야 하며, 예/아니오로만 대답하게 유도해야 합니다.\n"
    )

    prompt_input = f"[챌린지 이름]: {challenge_name} "  # \n[챌린지 설명] : {challenge_info} \n

    response = model.generate_content(
        [system_prompt_message, prompt_input],       # Chat 기반의 멀티턴 메시지 구조를 지원하므로 두개로 나누어서 함 
        generation_config={
            "temperature": 0.4,
            "top_p": 1,
            "top_k": 32,
            "max_output_tokens": 512
        }
    )

    return response.text
    
