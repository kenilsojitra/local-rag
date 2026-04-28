document.addEventListener('DOMContentLoaded', () => {
    // UI Elements
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const uploadStatus = document.getElementById('upload-status');
    const statusText = document.getElementById('status-text');
    
    const chatBox = document.getElementById('chat-box');
    const chatInput = document.getElementById('chat-input');
    const sendBtn = document.getElementById('send-btn');
    const clearChatBtn = document.getElementById('clear-chat');

    let chatHistory = [];

    // --- File Upload Logic ---
    dropZone.addEventListener('click', () => fileInput.click());

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => dropZone.classList.add('dragover'), false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => dropZone.classList.remove('dragover'), false);
    });

    dropZone.addEventListener('drop', (e) => {
        const files = e.dataTransfer.files;
        handleFiles(files);
    });

    fileInput.addEventListener('change', function() {
        handleFiles(this.files);
    });

    async function handleFiles(files) {
        if (files.length === 0) return;

        const formData = new FormData();
        for (let i = 0; i < files.length; i++) {
            formData.append('files', files[i]);
        }

        uploadStatus.classList.remove('hidden');
        statusText.textContent = `Ingesting ${files.length} file(s)...`;
        dropZone.style.pointerEvents = 'none';
        dropZone.style.opacity = '0.5';

        try {
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });
            const data = await response.json();
            
            if (data.status === 'success') {
                statusText.textContent = 'Upload Complete!';
                statusText.style.color = '#10b981'; // Green
                setTimeout(() => {
                    uploadStatus.classList.add('hidden');
                    statusText.style.color = '';
                }, 3000);
            } else {
                statusText.textContent = 'Error: ' + data.message;
                statusText.style.color = '#ef4444'; // Red
            }
        } catch (error) {
            statusText.textContent = 'Upload failed.';
            statusText.style.color = '#ef4444';
        } finally {
            dropZone.style.pointerEvents = 'auto';
            dropZone.style.opacity = '1';
        }
    }

    // --- Chat Logic ---

    // Auto-resize textarea
    chatInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
        if (this.value.trim() === '') {
            sendBtn.disabled = true;
        } else {
            sendBtn.disabled = false;
        }
    });

    chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    sendBtn.addEventListener('click', sendMessage);
    clearChatBtn.addEventListener('click', () => {
        chatHistory = [];
        const welcome = chatBox.firstElementChild; // Keep welcome message
        chatBox.innerHTML = '';
        if(welcome) chatBox.appendChild(welcome);
    });

    function appendMessage(role, content) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${role}`;
        
        const avatar = document.createElement('div');
        avatar.className = 'avatar';
        avatar.innerHTML = role === 'user' ? '<i class="fa-solid fa-user"></i>' : '<i class="fa-solid fa-robot"></i>';
        
        const bubble = document.createElement('div');
        bubble.className = 'bubble';
        
        if (role === 'user') {
            bubble.textContent = content;
        } else {
            // Render markdown for bot
            bubble.innerHTML = marked.parse(content);
        }

        msgDiv.appendChild(avatar);
        msgDiv.appendChild(bubble);
        chatBox.appendChild(msgDiv);
        scrollToBottom();
        
        return bubble; // Return bubble so we can update it in real-time
    }

    function scrollToBottom() {
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    async function sendMessage() {
        const text = chatInput.value.trim();
        if (!text) return;

        // Reset input
        chatInput.value = '';
        chatInput.style.height = 'auto';
        sendBtn.disabled = true;

        // Append user message
        appendMessage('user', text);

        // Add to history
        const userMsg = { role: 'user', content: text };
        
        // Prepare request body
        const reqBody = {
            query: text,
            history: chatHistory
        };
        
        chatHistory.push(userMsg);

        // Append empty bot message for streaming
        const botBubble = appendMessage('system', '');
        let botText = '';

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(reqBody)
            });

            if (!response.body) throw new Error('No readable stream');

            const reader = response.body.getReader();
            const decoder = new TextDecoder();

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                
                const chunk = decoder.decode(value, { stream: true });
                botText += chunk;
                
                // Update UI with parsed markdown
                botBubble.innerHTML = marked.parse(botText);
                scrollToBottom();
            }
            
            // Add bot response to history
            chatHistory.push({ role: 'assistant', content: botText });

        } catch (error) {
            botBubble.innerHTML = `<span style="color: #ef4444;">Error connecting to server.</span>`;
        }
    }

    // Initialize disabled state
    sendBtn.disabled = true;
});
