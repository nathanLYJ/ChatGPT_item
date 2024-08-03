document.querySelectorAll(".tab-link").forEach((button) => {
    button.addEventListener("click", () => {
        document.querySelectorAll(".tab-link").forEach((btn) => btn.classList.remove("active"));
        button.classList.add("active");

        document.querySelectorAll(".tab-content").forEach((content) => content.classList.remove("active"));
        document.getElementById(button.getAttribute("data-tab")).classList.add("active");

        if (button.getAttribute("data-tab") === "feedback") {
            loadReviews();
        }
    });
});

// 배경 음악 설정
const backgroundAudio = document.getElementById("background-audio");
const musicOn = document.getElementById("music-on");
const musicOff = document.getElementById("music-off");

// 페이지 로드 시 음악 끄기 설정
document.addEventListener("DOMContentLoaded", () => {
    backgroundAudio.pause();
    backgroundAudio.volume = document.getElementById("background-volume").value / 100;
});

musicOn.addEventListener("change", () => {
    if (musicOn.checked) {
        backgroundAudio.play();
    }
});

musicOff.addEventListener("change", () => {
    if (musicOff.checked) {
        backgroundAudio.pause();
    }
});

// 배경 음악 볼륨 동기화
const backgroundVolume = document.getElementById("background-volume");
const backgroundVolumeNumber = document.getElementById("background-volume-number");
backgroundVolume.addEventListener("input", () => {
    backgroundVolumeNumber.textContent = backgroundVolume.value;
    backgroundAudio.volume = backgroundVolume.value / 100;
});

// 음성 안내 볼륨 동기화
const voiceVolume = document.getElementById("voice-volume");
const voiceVolumeNumber = document.getElementById("voice-volume-number");
voiceVolume.addEventListener("input", () => {
    voiceVolumeNumber.textContent = voiceVolume.value;
});

// 별점 동기화
const rating = document.getElementById("rating");
const ratingNumber = document.getElementById("rating-number");
rating.addEventListener("input", () => {
    ratingNumber.textContent = rating.value;
});

// 요리 시작 버튼 기능
const startButton = document.querySelector(".start-button");
const statusText = document.getElementById("status-text");
startButton.addEventListener("click", async () => {
    const recipeOutput = document.getElementById("recipe-output");
    const steps = Array.from(recipeOutput.querySelectorAll(".chat-bubble.step")).map((step) => step.textContent);
    statusText.textContent = "요리 시작...";
    await processRecipe(steps);
});

// 레시피 생성 버튼 기능
const input = document.getElementById("chat-input");
const sendButton = document.getElementById("send-button");
const chatOutput = document.getElementById("recipe-output");
sendButton.addEventListener("click", async () => {
    sendMessage();
});

function sendMessage() {
    const message = input.value.trim();
    if (message) {
        const messageElement = document.createElement("div");
        messageElement.classList.add("message");
        messageElement.textContent = message;
        chatOutput.appendChild(messageElement);
        input.value = "";
        chatOutput.scrollTop = chatOutput.scrollHeight;
        generateRecipe(message);
    }
}

input.addEventListener("keypress", function (e) {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

// 대화 내용 지우기 버튼 기능
const clearButton = document.querySelector(".clear-button");
clearButton.addEventListener("click", () => {
    chatOutput.innerHTML = "";
});

// 피드백 제출 버튼 기능
const submitFeedbackButton = document.querySelector(".submit-feedback");
const feedbackTextarea = document.getElementById("feedback-textarea");
submitFeedbackButton.addEventListener("click", async () => {
    const ratingValue = document.getElementById("rating").value;
    const comment = feedbackTextarea.value;
    const recipe = document.getElementById("recipe-output").innerText;

    const feedback = {
        rating: ratingValue,
        comment: comment,
        recipe: recipe,
    };

    const response = await fetch("http://localhost:3000/feedback", { // 여기에 실제 백엔드 서버 주소를 사용합니다.
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(feedback),
    });

    if (response.ok) {
        alert("피드백이 제출되었습니다. 감사합니다!");
        feedbackTextarea.value = "";
        document.getElementById("rating").value = 5;
        document.getElementById("rating-number").textContent = "5";
        loadReviews();
    } else {
        alert("피드백 제출에 실패했습니다. 다시 시도해주세요.");
    }
});

// Web Speech API를 사용하여 텍스트를 음성으로 변환
function speak(text) {
    return new Promise((resolve, reject) => {
        if (!("speechSynthesis" in window)) {
            alert("이 브라우저는 음성 합성을 지원하지 않습니다.");
            reject(new Error("Speech Synthesis not supported"));
        }

        const speech = new SpeechSynthesisUtterance();
        speech.text = text;
        speech.lang = "ko-KR"; // 한국어 설정
        speech.volume = document.getElementById("voice-volume").value / 100; // 슬라이더 값 사용
        speech.onend = resolve;
        speech.onerror = reject;
        window.speechSynthesis.speak(speech);
    });
}

// API를 호출하여 레시피를 생성하는 함수
async function generateRecipe(userInput) {
    const systemContent = `너는 세계최고의 요리사야. 요청한 요리의 레시피를 제시해주되, 다음 조건을 반드시 지켜야 해:
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
        입력한 언어에 맞춰서 친절하게 설명해줘.`;
    const url = "https://open-api.jejucodingcamp.workers.dev/";
    const data = [
        { role: "system", content: systemContent },
        { role: "user", content: userInput },
    ];
    const headers = { "Content-Type": "application/json" };

    statusText.textContent = "레시피 생성 중...";

    const response = await fetch(url, {
        method: "POST",
        headers: headers,
        body: JSON.stringify(data),
    });

    if (response.status === 200) {
        const result = await response.json();
        const recipe = result.choices[0].message.content;
        displayRecipe(recipe);
        statusText.textContent = "레시피 생성 완료";
    } else {
        statusText.textContent = `Error: ${response.status}, ${response.statusText}`;
    }
}

// 레시피를 단계별로 처리하는 함수
async function processRecipe(steps) {
    for (const step of steps) {
        statusText.textContent = step; // 현재 단계의 내용을 statusText에 출력

        await speak(step);

        const timeMatch = step.match(/\((\d+)분 소요\)/);
        const time = timeMatch ? parseInt(timeMatch[1], 10) : 0;

        await new Promise((resolve) => setTimeout(resolve, time * 60000)); // 분을 밀리초로 변환하여 대기
    }

    statusText.textContent = "요리가 완성되었습니다. 맛있게 드세요!";
    await speak("요리가 완성되었습니다. 맛있게 드세요!");
    statusText.textContent = "완료";
}

// 생성된 레시피를 화면에 표시하는 함수
function displayRecipe(recipe) {
    const recipeOutput = document.getElementById("recipe-output");
    recipeOutput.innerHTML = ""; // 이전 출력 초기화
    const lines = recipe.split("\n");
    let inMethod = false;

    for (const line of lines) {
        const bubble = document.createElement("div");
        bubble.classList.add("chat-bubble");
        if (line.startsWith("재료:")) {
            bubble.textContent = line;
            recipeOutput.appendChild(bubble);
            inMethod = false;
        } else if (line.startsWith("만드는 방법:")) {
            bubble.textContent = line;
            recipeOutput.appendChild(bubble);
            inMethod = true;
        } else if (inMethod) {
            bubble.textContent = line;
            bubble.classList.add("step");
            recipeOutput.appendChild(bubble);
        } else {
            bubble.textContent = line;
            recipeOutput.appendChild(bubble);
        }
    }
}

// 저장된 피드백을 로드하는 함수
async function loadReviews() {
    const response = await fetch("http://localhost:3000/reviews"); // 여기에 실제 백엔드 서버 주소를 사용합니다.
    const reviews = await response.json();

    const sortedReviews = reviews.sort((a, b) => b.rating - a.rating);
    const reviewsContainer = document.getElementById("reviews-container");
    reviewsContainer.innerHTML = "";

    sortedReviews.forEach((review) => {
        const reviewElement = document.createElement("div");
        reviewElement.classList.add("review");

        const ratingElement = document.createElement("div");
        ratingElement.classList.add("rating");
        ratingElement.textContent = `별점: ${review.rating}`;

        const commentElement = document.createElement("div");
        commentElement.classList.add("comment");
        commentElement.textContent = review.comment;

        reviewElement.appendChild(ratingElement);
        reviewElement.appendChild(commentElement);
        reviewsContainer.appendChild(reviewElement);
    });
}
