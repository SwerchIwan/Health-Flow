const chatCircle = document.getElementById('chat-circle');
const chatSupport = document.getElementById('chat-support');
const chatMessages = document.getElementById('chat-messagesAI');

chatCircle.addEventListener('click', () => {
    chatCircle.style.display = 'none';
    chatSupport.style.display = 'flex';
    chatSupport.classList.add('is-open');
});

function closeChat() {
    chatCircle.style.display = 'grid';
    chatSupport.style.display = 'none';
    chatSupport.classList.remove('is-open');
}

function getCsrfToken() {
    return document.cookie.split('; ').find(c => c.startsWith('csrftoken='))?.split('=')[1] || '';
}

function scrollChatToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function appendAIMessage(text, className) {
    const el = document.createElement('div');
    el.innerText = text;
    el.className = 'message ' + className;
    chatMessages.appendChild(el);
    scrollChatToBottom();
    return el;
}

function showTyping() {
    const el = document.createElement('div');
    el.className = 'message support-message typing';
    const dots = document.createElement('span');
    dots.className = 'typing__dots';
    dots.append(document.createElement('i'), document.createElement('i'), document.createElement('i'));
    const label = document.createElement('span');
    label.className = 'typing__label';
    label.textContent = 'Health Flow AI печатает…';
    el.append(dots, label);
    chatMessages.appendChild(el);
    scrollChatToBottom();
    return el;
}

let aiPending = false;

function sendMessage() {
    const messageInput = document.getElementById('message-inputAI');
    const sendBtn = messageInput.closest('.chat-support__composer').querySelector('button');
    const message = messageInput.value;

    if (message.trim() === '' || aiPending) {
        return;
    }

    appendAIMessage(message, 'user-message text-right');
    messageInput.value = '';
    aiPending = true;
    sendBtn.disabled = true;
    const typing = showTyping();

    fetch('/process-message/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken(),
        },
        body: JSON.stringify({ message: message }),
    })
    .then(response => response.json().then(data => ({ ok: response.ok, data })))
    .then(({ ok, data }) => {
        typing.remove();
        if (!ok || !data.response) {
            appendAIMessage(data.error || 'Не удалось получить ответ. Попробуйте ещё раз.', 'support-message support-message--error');
            return;
        }
        appendAIMessage(data.response, 'support-message');
    })
    .catch(error => {
        typing.remove();
        console.error('Error:', error);
        appendAIMessage('Нет связи с сервером. Проверьте интернет и попробуйте снова.', 'support-message support-message--error');
    })
    .finally(() => {
        aiPending = false;
        sendBtn.disabled = false;
    });
}

function handleAISendKey(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
}

let isFullscreen = false;

function toggleFullscreen() {
    const chatSupport = document.getElementById('chat-support');
    isFullscreen = !isFullscreen;
    chatSupport.classList.toggle('is-fullscreen', isFullscreen);
}
