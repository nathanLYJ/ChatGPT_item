import gradio as gr
import requests
from gtts import gTTS
import os
import re
import time
import asyncio
import pygame
import tempfile
import random

pygame.mixer.init()

voice_channel = pygame.mixer.Channel(0)
music_channel = pygame.mixer.Channel(1)

def chat_gpt_api(user_input, system_content):
    url = "https://open-api.jejucodingcamp.workers.dev/"
    data = [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_input}
    ]
    headers = {"Content-Type": "application/json"}
    
    response = requests.post(url, json=data, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        return result['choices'][0]['message']['content']
    else:
        return f"Error : {response.status_code}, {response.text}"

def chatbot_response(message, history):
    history = history or []
    system_content = """너는 세계최고의 요리사야. 요청한 요리의 레시피를 제시해주되, 다음 조건을 반드시 지켜야 해:
    1. 전체 요리 과정이 20분을 넘지 않아야 함
    2. 재료는 이미 준비되어 있다고 가정함
    3. 가능한 빠른 조리 방법을 사용 (시간 줄일수있는 제조법 제시)
    4. 각 단계는 최대 5분을 넘지 않도록 조절
    5. 레시피는 '재료:'와 '만드는 방법:'으로 구분해서 작성
    6. 만드는 방법의 각 단계 마지막에 '(X분 소요)'와 같이 소요 시간을 표시 (예: '양파를 다져주세요. (2분 소요)')
    7. 전체 요리 시간이 정확히 몇 분 걸리는지 레시피 마지막에 '전체 요리 시간: X분'과 같이 명시
    8. 과정을 단순화하여 사용자에게 더 쉽게 설명해줘.
    9. 만드는 방법 글짜 강조 없이, 과정마다 1줄로 설명해줘
    입력한 언어에 맞춰서 친절하게 설명해줘."""
    
    response = chat_gpt_api(message, system_content)
    history.append((message, response))
    return history

def extract_cooking_steps(recipe):
    print("Received recipe:", recipe)  # 디버깅용 출력
    
    # '만드는 방법:' 이후부터 끝까지의 모든 내용을 추출
    match = re.search(r'만드는 방법:(.*?)$', recipe, re.DOTALL)
    if match:
        steps = match.group(1).strip()
        # 각 줄을 분리하고 빈 줄은 제거
        steps = [line.strip() for line in steps.split('\n') if line.strip()]
        
        print("Extracted steps:", steps)  # 디버깅용 출력
        return steps
    
    print("No steps found")  # 디버깅용 출력
    return ["만드는 방법을 찾을 수 없습니다. 다시 요청해 주세요."]

def text_to_speech(text):
    if not text or text.isspace():
        return None
    tts = gTTS(text, lang='ko', slow=False)
    
    # 임시 파일 생성
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
        temp_filename = temp_file.name
        tts.save(temp_filename)
    
    return temp_filename

def play_audio_with_delay(file_path, delay):
    sound = pygame.mixer.Sound(file_path)
    voice_channel.play(sound)
    while voice_channel.get_busy():
        pygame.time.Clock().tick(10)
    if delay > 0:
        time.sleep(delay)
    
    # 임시 파일 삭제
    try:
        os.remove(file_path)
    except Exception as e:
        print(f"Error removing temporary file: {e}")

def play_background_music():
    music_folder = "background_music"  # 배경 음악 파일이 있는 폴더
    music_files = [f for f in os.listdir(music_folder) if f.endswith('.mp3')]
    if music_files:
        random_music = random.choice(music_files)
        music = pygame.mixer.Sound(os.path.join(music_folder, random_music))
        music_channel.play(music, loops=-1)  # -1은 무한 반복을 의미합니다

def stop_background_music():
    music_channel.stop()

def set_voice_volume(volume):
    voice_channel.set_volume(volume / 100)
    return f"음성 안내 볼륨: {volume}%"

def set_music_volume(volume):
    music_channel.set_volume(volume / 100)
    return f"배경 음악 볼륨: {volume}%"

def toggle_music(choice):
    if choice == "음악 켜기":
        play_background_music()
        return gr.update(interactive=True), "배경 음악이 켜졌습니다."
    else:
        stop_background_music()
        return gr.update(interactive=False), "배경 음악이 꺼졌습니다."

async def process_steps(steps):
    for step in steps:
        # 전체 요리 시간을 확인
        total_time_match = re.match(r'전체 요리 시간:\s*(\d+)분', step)
        if total_time_match:
            total_time = int(total_time_match.group(1))
            print(f"전체 요리 시간: {total_time}분")
            audio_path = text_to_speech(step)
            if audio_path:
                play_audio_with_delay(audio_path, 0)  # 대기 시간 없이 재생만 함
            continue

        # 일반적인 요리 단계 처리
        match = re.match(r'(.*?)\s*\((\d+)분\s*소요\)\s*$', step)
        if match:
            instruction = match.group(1)
            duration = int(match.group(2))
        else:
            instruction = step
            duration = 1
        
        print(f"Processing step: {instruction} (Duration: {duration} minutes)")
        
        audio_path = text_to_speech(instruction)
        if audio_path:
            play_audio_with_delay(audio_path, min(duration * 60, 300))  # 최대 5분으로 제한
        await asyncio.sleep(1)  # 짧은 대기 시간 추가
    
    return "20분 레시피 안내가 완료되었습니다."

with gr.Blocks() as demo:
    chat_interface = gr.Chatbot(label="20분 레시피 챗봇")
    msg = gr.Textbox(label="20분 안에 만들고 싶은 요리를 입력하세요")
    clear = gr.Button("대화 내용 지우기")
    start_cooking = gr.Button("요리 시작")
    status = gr.Textbox(label="상태", value="대기 중")
    
    # 음악 컨트롤 추가
    music_control = gr.Radio(["음악 켜기", "음악 끄기"], label="배경 음악", value="음악 끄기")
    music_volume_slider = gr.Slider(minimum=0, maximum=100, step=1, label="배경 음악 볼륨", value=50, interactive=False)
    music_volume_status = gr.Textbox(label="배경 음악 볼륨 상태", value="배경 음악 볼륨: 50%")

    # 음성 안내 볼륨 컨트롤 추가
    voice_volume_slider = gr.Slider(minimum=0, maximum=100, step=1, label="음성 안내 볼륨", value=50)
    voice_volume_status = gr.Textbox(label="음성 안내 볼륨 상태", value="음성 안내 볼륨: 50%")


    def respond(message, history):
        history = chatbot_response(message, history)
        return history

    async def start_cooking_process(history):
        if not history:
            return "레시피를 먼저 요청해주세요."
        last_response = history[-1][1]
        steps = extract_cooking_steps(last_response)
        if steps[0] == "만드는 방법을 찾을 수 없습니다. 다시 요청해 주세요.":
            return steps[0]
        result = await process_steps(steps)
        return result

    msg.submit(respond, [msg, chat_interface], [chat_interface])
    clear.click(lambda: None, None, chat_interface, queue=False)
    start_cooking.click(start_cooking_process, inputs=[chat_interface], outputs=[status])
    music_control.change(toggle_music, inputs=[music_control], outputs=[music_volume_slider, status])
    voice_volume_slider.change(set_voice_volume, inputs=[voice_volume_slider], outputs=[voice_volume_status])
    music_volume_slider.change(set_music_volume, inputs=[music_volume_slider], outputs=[music_volume_status])

demo.launch()