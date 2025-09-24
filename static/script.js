// static/script.js

document.addEventListener('DOMContentLoaded', () => {
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const chatWindow = document.getElementById('chat-window');

    // Buat ID unik untuk sesi chat ini
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

        const p = document.createElement('p');
        p.textContent = text;

        messageContent.appendChild(p);
        messageContainer.appendChild(messageContent);
        chatWindow.appendChild(messageContainer);
        scrollToBottom();

        return { messageContainer, messageContent, p };
    }

    async function handleStream(question) {
        // Buat placeholder untuk jawaban bot
        const botMessageElements = addMessageToChat('bot', '...');
        const botParagraph = botMessageElements.p;
        botParagraph.textContent = ''; // Kosongkan placeholder

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

            // Baca stream data
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
                            // Tambahkan token (kata) ke paragraf
                            botParagraph.innerHTML += data.content.replace(/\n/g, '<br>');
                            fullAnswer += data.content;
                        } else if (data.type === 'sources') {
                            // Setelah selesai, tambahkan meta (copy, feedback, sources)
                            addMessageMeta(botMessageElements.messageContainer, question, fullAnswer, data.content);
                        }
                    } catch (e) {
                        console.error('Error parsing stream data:', e);
                    }
                }
                scrollToBottom();
            }

        } catch (error) {
            botParagraph.textContent = 'Maaf, terjadi kesalahan. Silakan coba lagi.';
            console.error('Streaming Error:', error);
        }
    }

    function addMessageMeta(messageContainer, question, answer, sources) {
        const metaContainer = document.createElement('div');
        metaContainer.classList.add('message-meta');

        // 1. Tampilkan Sumber
        if (sources && sources.length > 0) {
            const sourcesDiv = document.createElement('div');
            sourcesDiv.classList.add('source-docs');
            let sourcesHTML = '<strong>Sumber:</strong>';
            sources.forEach(s => {
                const fileName = s.source.split(/[\\/]/).pop(); // Ambil nama file saja
                sourcesHTML += `<div>- ${fileName} (Hal. ${s.page + 1})</div>`;
            });
            sourcesDiv.innerHTML = sourcesHTML;
            metaContainer.appendChild(sourcesDiv);
        }

        // 2. Tombol Copy
        const copyBtn = document.createElement('span');
        copyBtn.classList.add('copy-icon');
        copyBtn.innerHTML = '&#x1F4CB;'; // Clipboard icon
        copyBtn.title = 'Salin jawaban';
        copyBtn.addEventListener('click', () => {
            navigator.clipboard.writeText(answer).then(() => {
                copyBtn.innerHTML = '&#x2714;'; // Checkmark
                setTimeout(() => { copyBtn.innerHTML = '&#x1F4CB;'; }, 1500);
            });
        });
        metaContainer.appendChild(copyBtn);

        // 3. Tombol Feedback
        const feedbackDiv = document.createElement('div');
        feedbackDiv.classList.add('feedback-buttons');
        const likeBtn = createFeedbackButton('&#x1F44D;', 'like', question, answer); // Thumbs up
        const dislikeBtn = createFeedbackButton('&#x1F44E;', 'dislike', question, answer); // Thumbs down
        feedbackDiv.appendChild(likeBtn);
        feedbackDiv.appendChild(dislikeBtn);
        metaContainer.appendChild(feedbackDiv);

        messageContainer.appendChild(metaContainer);
    }

    function createFeedbackButton(icon, type, question, answer) {
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
            // Beri visual feedback bahwa tombol sudah diklik
            btn.parentElement.childNodes.forEach(child => child.style.opacity = '0.5');
            btn.style.opacity = '1';
        });
        return btn;
    }

    function scrollToBottom() {
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }
});