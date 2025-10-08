// static/script.js (Versi Final dengan Perbaikan Link)

// HAPUS SEMUA KONFIGURASI marked.js DARI SINI. KITA AKAN TANGANI SECARA BERBEDA.

document.addEventListener('DOMContentLoaded', () => {
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const chatWindow = document.getElementById('chat-window');
    const sessionId = `chat_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

    chatForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const question = userInput.value.trim();
        if (question === '') return;

        addMessageToChat('user', question);
        userInput.value = '';
        userInput.focus();
        handleStream(question);
    });

    function addMessageToChat(sender, text) {
        const messageContainer = document.createElement('div');
        messageContainer.classList.add('message', sender);
        const messageContent = document.createElement('div');
        messageContent.classList.add('message-content');
        messageContent.innerHTML = text;
        messageContainer.appendChild(messageContent);
        chatWindow.appendChild(messageContainer);
        scrollToBottom();
        return { messageContainer, messageContent };
    }

    // --- FUNGSI BARU UNTUK MEMPROSES LINK SETELAH RENDER ---
    function processRenderedContent(element) {
        // Cari semua tag <a> (link) di dalam elemen pesan bot
        const links = element.querySelectorAll('a');
        links.forEach(link => {
            // Tambahkan atribut agar terbuka di tab baru
            link.target = '_blank';
            link.rel = 'noopener noreferrer';
        });
    }

    async function handleStream(question) {
        const botMessageElements = addMessageToChat('bot',
            `<div class="typing-indicator"><span></span><span></span><span></span></div>`
        );
        const botContentDiv = botMessageElements.messageContent;

        try {
            const response = await fetch('/ask', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question, session_id: sessionId }),
            });

            if (!response.ok) throw new Error(`Server error: ${response.statusText}`);

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let fullAnswer = "";
            let isFirstToken = true;

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value, { stream: true });
                const lines = chunk.split('\n\n').filter(line => line.startsWith('data:'));

                for (const line of lines) {
                    const dataStr = line.replace('data: ', '');
                    try {
                        const data = JSON.parse(dataStr);
                        if (data.type === 'token') {
                            if (isFirstToken) {
                                botContentDiv.innerHTML = '';
                                isFirstToken = false;
                            }
                            fullAnswer += data.content;
                            // Biarkan marked.js bekerja seperti biasa
                            botContentDiv.innerHTML = marked.parse(fullAnswer + "▌");
                        }
                    } catch (e) { /* Abaikan error */ }
                }
                scrollToBottom();
            }

            if (isFirstToken) {
                botContentDiv.innerHTML = "<p>Saya tidak menemukan jawaban.</p>";
            } else {
                botContentDiv.innerHTML = marked.parse(fullAnswer);
                // --- PANGGIL FUNGSI BARU KITA DI SINI ---
                processRenderedContent(botContentDiv);
            }

            addMessageMeta(botMessageElements.messageContainer, question, fullAnswer);
            scrollToBottom();

        } catch (error) {
            botContentDiv.innerHTML = '<p>Maaf, terjadi kesalahan. Silakan coba lagi.</p>';
            console.error('Streaming Error:', error);
        }
    }

    function addMessageMeta(messageContainer, question, answer) {
        // ... (Fungsi ini tidak perlu diubah)
        const metaContainer = document.createElement('div');
        metaContainer.classList.add('message-meta');
        const copyBtn = document.createElement('span');
        copyBtn.classList.add('copy-icon');
        copyBtn.innerHTML = '&#x1F4CB;';
        copyBtn.title = 'Salin jawaban';
        copyBtn.addEventListener('click', () => {
            navigator.clipboard.writeText(answer).then(() => {
                copyBtn.innerHTML = '&#x2714;';
                setTimeout(() => { copyBtn.innerHTML = '&#x1F4CB;'; }, 1500);
            });
        });
        metaContainer.appendChild(copyBtn);
        const feedbackDiv = document.createElement('div');
        feedbackDiv.classList.add('feedback-buttons');
        const likeBtn = createFeedbackButton('&#x1F44D;', 'like', question, answer);
        const dislikeBtn = createFeedbackButton('&#x1F44E;', 'dislike', question, answer);
        feedbackDiv.appendChild(likeBtn);
        feedbackDiv.appendChild(dislikeBtn);
        metaContainer.appendChild(feedbackDiv);
        messageContainer.appendChild(metaContainer);
    }

    function createFeedbackButton(icon, type, question, answer) {
        // ... (Fungsi ini tidak perlu diubah)
        const btn = document.createElement('span');
        btn.classList.add('feedback-icon');
        btn.innerHTML = icon;
        btn.title = type === 'like' ? 'Jawaban membantu' : 'Jawaban tidak membantu';
        btn.addEventListener('click', async () => {
            await fetch('/feedback', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question, answer, feedback_type: type }),
            });
            btn.parentElement.childNodes.forEach(child => child.style.opacity = '0.5');
            btn.style.opacity = '1';
        });
        return btn;
    }

    function scrollToBottom() {
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }
});