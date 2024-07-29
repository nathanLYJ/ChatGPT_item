import gradio as gr
import requests

def chat_gpt_api(user_input, mbti_type, age_preference):
    # API 엔드포인트 URL
    url = "https://open-api.jejucodingcamp.workers.dev/"

    # 연상, 연하, 동갑에 따른 대화 스타일 설정
    age_content = {
        "연상": "상대방이 연상인 대화 스타일을 사용해줘.",
        "연하": "상대방이 연하인 대화 스타일을 사용해줘.",
        "동갑": "상대방이 동갑인 대화 스타일을 사용해줘."
    }

    # API에 요청에 사용할 데이터
    data = [
        {"role": "system", "content": f"너는 사용자로부터 MBTI 성격 유형을 입력받아 해당 성격에 맞춤형 답혹은 질문을 출력해주는 Chatbot이야. 너의 성격은 {mbti_type}야. {age_content[age_preference]} 사용자와 자연스럽게 대화해줘."},
        {"role": "user", "content": f"{user_input}"} 
    ]
    
    headers = {
        "Content-Type" : "application/json"
    }
    response = requests.post(url, json=data, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        return result['choices'][0]['message']['content']
    else:
        return f"Error : {response.status_code}, {response.text}"

def chatbot_interface(user_input, mbti_type, age_preference):
    return chat_gpt_api(user_input, mbti_type, age_preference)

def main():
    # Gradio 인터페이스 정의
    with gr.Blocks() as demo:
        gr.Markdown("## MBTI 성격 유형 기반 Chatbot")
        
        mbti_type = gr.Textbox(label="MBTI 성격 유형을 입력하세요 (예: ENFP)")
        user_input = gr.Textbox(label="채팅 입력")
        age_preference = gr.Radio(label="대화 상대의 연령을 선택하세요", choices=["연상", "연하", "동갑"], value="동갑")
        output = gr.Textbox(label="Chatbot 응답")
        
        btn = gr.Button("전송")
        btn.click(fn=chatbot_interface, inputs=[user_input, mbti_type, age_preference], outputs=output)
        
    demo.launch()

if __name__ == "__main__":
    main()

