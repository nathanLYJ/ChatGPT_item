import gradio as gr
import requests
import os
import re
import asyncio
import pygame
import tempfile
import random
import sqlite3
from datetime import datetime
from gtts import gTTS

# Initialize pygame mixer
pygame.mixer.init()
voice_channel = pygame.mixer.Channel(0)
music_channel = pygame.mixer.Channel(1)

# Database initialization
def init_db():
    with sqlite3.connect('recipes.db') as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS feedback
                        (id INTEGER PRIMARY KEY AUTOINCREMENT,
                         recipe TEXT,
                         rating INTEGER,
                         comment TEXT,
                         date TEXT)''')

init_db()

# API and ChatGPT functions
def chat_gpt_api(user_input, system_content):
    url = "https://open-api.jejucodingcamp.workers.dev/"
    data = [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_input}
    ]
    headers = {"Content-Type": "application/json"}
    
    response = requests.post(url, json=data, headers=headers)
    
    if response.status_code == 200:
        return response.json()['choices'][0]['message']['content']
    else:
        return f"Error: {response.status_code}, {response.text}"

def chatbot_response(message, history):
    system_content = """너는 세계최고의 요리사야. 요청한 요리의 레시피를 제시해주되, 다음 조건을 반드시 지켜야 해:
    1. 전체 요리 과정이 20분을 넘지 않아야 함
    2. 재료는 이미 준비되어 있다고 가정함
    3. 가능한 빠른 조리 방법을 사용 (예: 전자렌지, 믹서기, 소스)
    4. 각 단계는 최대 5분을 넘지 않도록 조절
    5. 레시피는 '재료:'와 '만드는 방법:'으로 구분해서 작성
    6. 만드는 방법의 각 단계 마지막에 '(X분 소요)'와 같이 소요 시간을 표시 (예: '양파를 다져주세요. (2분 소요)')
    7. 전체 요리 시간이 정확히 몇 분 걸리는지 '재료:' 마지막에 '전체 요리 시간: X분'과 같이 명시
    8. 과정을 단순화하여 사용자에게 더 쉽게 설명해줘.
    9. 만드는 방법 글짜 강조 없이, 과정마다 1줄로 설명해줘
    10. 레시피 마지막 총 소요시간 표시 안 함
    입력한 언어에 맞춰서 친절하게 설명해줘."""
    
    response = chat_gpt_api(message, system_content)
    history.append((message, response))
    return history

# Recipe processing functions
def extract_cooking_steps(recipe):
    match = re.search(r'만드는 방법:(.*?)$', recipe, re.DOTALL)
    if match:
        steps = [line.strip() for line in match.group(1).strip().split('\n') if line.strip()]
        return steps
    return ["만드는 방법을 찾을 수 없습니다. 다시 요청해 주세요."]

async def process_steps(steps):
    total_steps = len(steps)
    for index, step in enumerate(steps, 1):
        total_time_match = re.match(r'전체 요리 시간:\s*(\d+)분', step)
        if total_time_match:
            total_time = int(total_time_match.group(1))
            yield f"전체 요리 시간: {total_time}분"
            asyncio.create_task(text_to_speech_async(step))
            continue

        match = re.match(r'(.*?)\s*\((\d+)분\s*소요\)\s*$', step)
        if match:
            instruction, duration = match.groups()
            duration = int(duration)
        else:
            instruction, duration = step, 1
        
        yield f"단계 {index}/{total_steps}: {instruction} (소요 시간: {duration}분)"
        asyncio.create_task(text_to_speech_async(instruction))
        await asyncio.sleep(min(duration * 60, 300))

    yield "요리가 완성되었습니다. 피드백을 남겨주세요!"
    asyncio.create_task(text_to_speech_async("요리가 완성되었습니다! 맛은 어떠신가요? 1부터 5까지의 별점과 간단한 후기를 남겨주세요."))

# Audio functions
def text_to_speech(text):
    if not text or text.isspace():
        return None
    tts = gTTS(text, lang='ko', slow=False)
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
        temp_filename = temp_file.name
        tts.save(temp_filename)
    
    return temp_filename

async def text_to_speech_async(text):
    if not text or text.isspace():
        return
    audio_path = text_to_speech(text)
    if audio_path:
        sound = pygame.mixer.Sound(audio_path)
        voice_channel.play(sound)
        while voice_channel.get_busy():
            await asyncio.sleep(0.1)
        try:
            os.remove(audio_path)
        except Exception as e:
            print(f"Error removing temporary file: {e}")

def play_background_music():
    music_folder = "background_music"
    music_files = [f for f in os.listdir(music_folder) if f.endswith('.mp3')]
    if music_files:
        random_music = random.choice(music_files)
        music = pygame.mixer.Sound(os.path.join(music_folder, random_music))
        music_channel.play(music, loops=-1)

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

# Feedback function
def save_feedback(recipe, rating, comment):
    with sqlite3.connect('recipes.db') as conn:
        conn.execute("INSERT INTO feedback (recipe, rating, comment, date) VALUES (?, ?, ?, ?)",
                     (recipe, rating, comment, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

# Gradio interface functions
def respond(message, history):
    return chatbot_response(message, history)

async def start_cooking_process(history):
    if not history:
        yield "레시피를 먼저 요청해주세요."
        return
    last_response = history[-1][1]
    steps = extract_cooking_steps(last_response)
    if steps[0] == "만드는 방법을 찾을 수 없습니다. 다시 요청해 주세요.":
        yield steps[0]
        return
    async for status_update in process_steps(steps):
        yield status_update
    
def submit_feedback_fn(recipe, rating, comment):
    save_feedback(recipe, rating, comment)
    return "피드백이 성공적으로 저장되었습니다. 감사합니다!"

# Gradio interface
with gr.Blocks(css="CSS/Chef.css") as demo:
    with gr.Tabs():
        with gr.Tab("요리 레시피"):
            chat_interface = gr.Chatbot(label="20분 레시피")
            msg = gr.Textbox(label="20분 안에 만들고 싶은 요리를 입력하세요")
            clear = gr.Button("대화 내용 지우기")
            start_cooking = gr.Button("요리 시작")
            status = gr.Textbox(label="상태", value="대기 중")

        with gr.Tab("음악 설정"):
            with gr.Row():
                music_control = gr.Radio(["음악 켜기", "음악 끄기"], label="배경 음악", value="음악 끄기")
                music_volume_slider = gr.Slider(minimum=0, maximum=100, step=1, label="배경 음악 볼륨", value=50, interactive=False)
            music_volume_status = gr.Textbox(label="배경 음악 볼륨 상태", value="배경 음악 볼륨: 50%")
            voice_volume_slider = gr.Slider(minimum=0, maximum=100, step=1, label="음성 안내 볼륨", value=50)
            voice_volume_status = gr.Textbox(label="음성 안내 볼륨 상태", value="음성 안내 볼륨: 50%")

        with gr.Tab("피드백"):
            feedback_slider = gr.Slider(minimum=1, maximum=5, step=1, label="별점 (1-5)", value=5)
            feedback_text = gr.Textbox(label="요리에 대한 후기를 남겨주세요")
            submit_feedback = gr.Button("피드백 제출")   

    # Event handlers
    msg.submit(respond, [msg, chat_interface], [chat_interface])
    clear.click(lambda: None, None, chat_interface, queue=False)
    start_cooking.click(start_cooking_process, inputs=[chat_interface], outputs=[status])
    music_control.change(toggle_music, inputs=[music_control], outputs=[music_volume_slider, status])
    voice_volume_slider.change(set_voice_volume, inputs=[voice_volume_slider], outputs=[voice_volume_status])
    music_volume_slider.change(set_music_volume, inputs=[music_volume_slider], outputs=[music_volume_status])
    submit_feedback.click(submit_feedback_fn, inputs=[chat_interface, feedback_slider, feedback_text])

demo.launch()