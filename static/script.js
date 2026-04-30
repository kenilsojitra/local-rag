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
    let sourceCounter = 1;
    let currentSessionId = null;

    // --- Document Dashboard ---
    const manageDocsBtn = document.getElementById('manage-docs-btn');
    const dashboardModal = document.getElementById('dashboard-modal');
    const closeModalBtn = document.getElementById('close-modal');
    const docsTbody = document.getElementById('docs-tbody');

    if (manageDocsBtn) {
        manageDocsBtn.addEventListener('click', openDashboard);
    }
    
    if (closeModalBtn) {
        closeModalBtn.addEventListener('click', () => dashboardModal.classList.add('hidden'));
    }
    
    window.addEventListener('click', (e) => {
        if (e.target === dashboardModal) {
            dashboardModal.classList.add('hidden');
        }
    });

    async function openDashboard() {
        dashboardModal.classList.remove('hidden');
        docsTbody.innerHTML = '<tr><td colspan="3" style="text-align:center;">Loading...</td></tr>';
        
        try {
            const res = await fetch('/api/documents');
            const data = await res.json();
            
            docsTbody.innerHTML = '';
            if (data.documents && data.documents.length > 0) {
                data.documents.forEach(doc => {
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td>${doc.filename}</td>
                        <td>${doc.chunks}</td>
                        <td>
                            <button class="delete-btn" data-filename="${doc.filename}">Delete</button>
                        </td>
                    `;
                    docsTbody.appendChild(tr);
                });
                
                document.querySelectorAll('.delete-btn').forEach(btn => {
                    btn.addEventListener('click', async (e) => {
                        const filename = e.target.getAttribute('data-filename');
                        if (confirm(`Delete ${filename}? This will remove it from the context.`)) {
                            e.target.textContent = '...';
                            e.target.disabled = true;
                            try {
                                await fetch(`/api/documents/${encodeURIComponent(filename)}`, { method: 'DELETE' });
                                openDashboard();
                            } catch(err) {
                                alert('Error deleting document');
                                openDashboard();
                            }
                        }
                    });
                });
            } else {
                docsTbody.innerHTML = '<tr><td colspan="3" style="text-align:center;">No documents found.</td></tr>';
            }
        } catch(e) {
            docsTbody.innerHTML = '<tr><td colspan="3" style="text-align:center;color:#ef4444;">Error loading documents.</td></tr>';
        }
    }

    // --- Sources Sidebar ---
    const sourcesSidebar = document.getElementById('sources-sidebar');
    const closeSourcesBtn = document.getElementById('close-sources');
    const sourcesList = document.getElementById('sources-list');

    if (closeSourcesBtn) {
        closeSourcesBtn.addEventListener('click', () => sourcesSidebar.classList.add('hidden'));
    }

    function addSourceToSidebar(sourceData) {
        sourcesSidebar.classList.remove('hidden');
        const filename = sourceData.source.split(/[/\\]/).pop();
        
        // Prevent duplicates (simple check)
        const contentStr = sourceData.content.substring(0, 50);
        const existing = Array.from(sourcesList.querySelectorAll('p')).some(p => p.textContent.includes(contentStr));
        if (existing) return;
        
        const div = document.createElement('div');
        div.className = 'source-item';
        div.innerHTML = `
            <h4><i class="fa-solid fa-file-lines"></i> ${filename}</h4>
            <p>${sourceData.content}</p>
        `;
        sourcesList.appendChild(div);
    }

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
        currentSessionId = null;
        const welcome = chatBox.firstElementChild;
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

        // Clear sources list on new query
        sourcesList.innerHTML = '';
        sourcesSidebar.classList.add('hidden');

        // Append user message
        appendMessage('user', text);

        // Add to history
        const userMsg = { role: 'user', content: text };
        
        // Prepare request body
        const reqBody = {
            query: text,
            history: chatHistory,
            session_id: currentSessionId
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

                // Extract session_id (only sent once as first chunk)
                const sessionMatch = botText.match(/\[\[SESSION_ID\]\]([^\n]+)\n/);
                if (sessionMatch) {
                    currentSessionId = sessionMatch[1].trim();
                }

                // Extract sources
                const sourceRegex = /\[\[SOURCE\]\](\{.*?\})\n/g;
                let match;
                while ((match = sourceRegex.exec(botText)) !== null) {
                    try {
                        const sourceData = JSON.parse(match[1]);
                        addSourceToSidebar(sourceData);
                    } catch(e){}
                }

                // Display text stripped of all control markers
                const displayText = botText
                    .replace(/\[\[SESSION_ID\]\][^\n]+\n/, '')
                    .replace(/\[\[SOURCE\]\](\{.*?\})\n/g, '');

                botBubble.innerHTML = marked.parse(displayText);
                scrollToBottom();
            }
            
            const finalDisplayText = botText
                .replace(/\[\[SESSION_ID\]\][^\n]+\n/, '')
                .replace(/\[\[SOURCE\]\](\{.*?\})\n/g, '');
            chatHistory.push({ role: 'assistant', content: finalDisplayText });

        } catch (error) {
            botBubble.innerHTML = `<span style="color: #ef4444;">Error connecting to server.</span>`;
        }
    }

    // Initialize disabled state
    sendBtn.disabled = true;
});
