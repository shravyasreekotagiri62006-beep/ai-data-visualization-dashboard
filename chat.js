// chat.js - Handles AI Chat Widget explicitly contained within DOM block (not floating)

document.addEventListener('DOMContentLoaded', () => {
    const chatBody = document.getElementById('chat-messages');
    const chatInput = document.getElementById('chat-input');
    const sendBtn = document.getElementById('send-chat');

    // Send Message
    async function sendMessage() {
        const text = chatInput.value.trim();
        if (!text) return;

        appendMessage(text, 'user');
        chatInput.value = '';
        
        const typingId = `ty-${Date.now()}`;
        appendMessage('...', 'ai', typingId);

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: text })
            });

            const data = await response.json();
            document.getElementById(typingId).remove();
            
            if (response.ok) {
                appendMessage(data.response, 'ai');
            } else {
                appendMessage('Error: Cannot reach AI server.', 'ai');
            }
        } catch (err) {
            document.getElementById(typingId)?.remove();
            appendMessage('Connection Error.', 'ai');
        }
    }

    sendBtn.addEventListener('click', sendMessage);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });

    function appendMessage(text, sender, id = null) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${sender}`;
        msgDiv.innerText = text; // Prevent basic XSS
        if (id) msgDiv.id = id;
        chatBody.appendChild(msgDiv);
        chatBody.scrollTop = chatBody.scrollHeight;
    }
});
