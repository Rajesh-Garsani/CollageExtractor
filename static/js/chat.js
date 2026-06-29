export class ChatInterface {
    constructor() {
        this.terminal = document.getElementById('chatTerminal');
        this.input = document.getElementById('chatPromptInput');
        this.sendBtn = document.getElementById('sendPromptBtn');
        this.btnText = document.getElementById('btnText');
        this.btnSpinner = document.getElementById('btnSpinner');
    }

    bindChatEvents(onSendMessage) {
        this.sendBtn.addEventListener('click', () => this._handleSubmission(onSendMessage));
        this.input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                this._handleSubmission(onSendMessage);
            }
        });
    }

    _handleSubmission(onSendMessage) {
        const text = this.input.value.trim();
        if (!text) return;
        this.appendMessage(text, 'user');
        this.input.value = '';
        onSendMessage(text);
    }

    appendMessage(text, sender = 'system', downloadUrl = null) {
        const bubble = document.createElement('div');
        bubble.classList.add('chat-bubble', sender);

        if (downloadUrl) {
            // High-End Image Output UI
            bubble.innerHTML = `
                <div class="result-header mb-2 fw-bold text-success">
                    <span class="fs-5">✓</span> Processing Complete
                </div>
                <p class="mb-3 text-light">${text}</p>
                <div class="extracted-image-wrapper mb-3 text-center p-2 rounded" style="background: #000;">
                    <img src="${downloadUrl}" class="img-fluid rounded" style="max-height: 280px; box-shadow: 0 4px 12px rgba(0,0,0,0.5);" alt="Extracted Image">
                </div>
                <div class="d-grid">
                    <a href="${downloadUrl}" target="_blank" download class="btn btn-primary fw-bold">
                        ↓ Download Pro Result
                    </a>
                </div>
            `;
        } else {
            bubble.innerHTML = text;
        }

        this.terminal.appendChild(bubble);
        this.scrollToBottom();
    }

    setLoadingState(isLoading) {
        this.input.disabled = isLoading;
        this.sendBtn.disabled = isLoading;
        if (isLoading) {
            this.btnText.classList.add('d-none');
            this.btnSpinner.classList.remove('d-none');
            this.appendMessage("<span class='spinner-grow spinner-grow-sm text-primary me-2'></span> <i>Executing deep analysis and processing parameters...</i>", 'system-loading');
        } else {
            this.btnText.classList.remove('d-none');
            this.btnSpinner.classList.add('d-none');
            this.input.focus();

            // Remove the loading bubble
            const loadingBubble = this.terminal.querySelector('.system-loading');
            if (loadingBubble) loadingBubble.remove();
        }
    }

    reset() {
        this.input.disabled = true;
        this.sendBtn.disabled = true;
        this.input.value = '';
        this.terminal.innerHTML = `
            <div class="chat-bubble system">
                <h6 class="fw-bold mb-2 text-primary">⚡ System Initialized</h6>
                Waiting for image input... Upload a collage on the left to begin.
            </div>
        `;
    }

    scrollToBottom() {
        this.terminal.scrollTop = this.terminal.scrollHeight;
    }
}