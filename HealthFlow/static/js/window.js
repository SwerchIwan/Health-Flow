const chatCircle = document.getElementById('chat-circle');
const chatSupport = document.getElementById('chat-support');
const chatMessages = document.getElementById('chat-messagesAI');

chatCircle.addEventListener('click', () => {
    chatCircle.style.display = 'none';
    chatSupport.style.display = 'flex';
});

function closeChat() {
    chatCircle.style.display = 'block';
    chatSupport.style.display = 'none';
}

function sendMessage() {
    const messageInput = document.getElementById('message-inputAI');
    const message = messageInput.value;

    if (message.trim() === '') {
        return;
    }

    const messageElement = document.createElement('div');
    messageElement.innerText = message;
    messageElement.className = 'message user-message text-right';

    chatMessages.appendChild(messageElement);

    // Send a request to your neural network here
    fetch('/process-message/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            // Add any additional headers if needed
        },
        body: JSON.stringify({ message: message }),
    })
    .then(response => response.json())
    .then(data => {
        const response = data.response;
        const responseElement = document.createElement('div');
        responseElement.innerText = response;
        responseElement.className = 'message support-message';
        chatMessages.appendChild(responseElement);
    })
    .catch(error => {
        console.error('Error:', error);
    });

    messageInput.value = '';
}

function toggleFullscreen() {
    const chatSupport = document.getElementById('chat-support');
    isFullscreen = !isFullscreen;

    if (isFullscreen) {
        chatSupport.style.width = '100%';
        chatSupport.style.height = '90vh'; // Adjust height as needed
        chatSupport.style.top = '5%'; // Center the chat vertically
        chatSupport.style.left = '0';
    } else {
        chatSupport.style.width = '300px';
        chatSupport.style.height = 'auto';
        chatSupport.style.top = 'auto';
        chatSupport.style.left = 'auto';
    }
}
