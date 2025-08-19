// Anki LLM Assistant - Frontend JavaScript

class AnkiLLMAssistant {
    constructor() {
        this.chatMessages = document.getElementById('chatMessages');
        this.chatForm = document.getElementById('chatForm');
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.statusIndicator = document.getElementById('statusIndicator');
        this.ankiStatus = document.getElementById('ankiStatus');
        
        this.confirmToken = null;
        this.isProcessing = false;
        
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.checkHealth();
        this.setInterval(this.checkHealth.bind(this), 30000); // Check every 30 seconds
        
        // Auto-focus the input field on page load
        this.messageInput.focus();
    }
    
    bindEvents() {
        this.chatForm.addEventListener('submit', this.handleSubmit.bind(this));
        this.messageInput.addEventListener('keypress', this.handleKeyPress.bind(this));
        
        // Focus input when clicking anywhere in the chat container
        this.chatMessages.addEventListener('click', () => {
            if (!this.isProcessing) {
                this.messageInput.focus();
            }
        });
        
        // Focus input when the window regains focus (user returns to tab)
        window.addEventListener('focus', () => {
            if (!this.isProcessing) {
                this.ensureInputFocus();
            }
        });
        
        // Remove focus indicator when input loses focus
        this.messageInput.addEventListener('blur', () => {
            this.messageInput.classList.remove('focused');
        });
    }
    
    handleKeyPress(event) {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            this.handleSubmit(event);
        }
    }
    
    async handleSubmit(event) {
        event.preventDefault();
        
        if (this.isProcessing) return;
        
        const message = this.messageInput.value.trim();
        if (!message) return;
        
        this.addMessage('user', message);
        this.messageInput.value = '';
        
        this.setProcessing(true);
        
        try {
            const response = await this.sendMessage(message);
            this.handleResponse(response);
        } catch (error) {
            console.error('Error sending message:', error);
            this.addMessage('error', `Error: ${error.message}`);
        } finally {
            this.setProcessing(false);
        }
    }
    
    async sendMessage(message) {
        const payload = {
            message: message,
            confirm: false,
            confirm_token: this.confirmToken
        };
        
        const response = await fetch('/chat/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to send message');
        }
        
        return await response.json();
    }
    
    handleResponse(response) {
        if (response.needs_confirmation && response.confirm_token) {
            this.confirmToken = response.confirm_token;
            this.addMessage('assistant', response.message, true);
        } else {
            this.addMessage('assistant', response.message);
            this.confirmToken = null;
        }
    }
    
    addMessage(type, content, needsConfirmation = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        // Convert newlines to <br> tags and preserve formatting
        const formattedContent = content
            .replace(/\n\n/g, '</p><p>')
            .replace(/\n/g, '<br>');
        
        contentDiv.innerHTML = `<p>${formattedContent}</p>`;
        
        if (needsConfirmation) {
            const confirmButton = document.createElement('button');
            confirmButton.className = 'confirm-button';
            confirmButton.textContent = 'Confirm & Apply Changes';
            confirmButton.onclick = () => this.confirmChanges();
            contentDiv.appendChild(confirmButton);
        }
        
        messageDiv.appendChild(contentDiv);
        this.chatMessages.appendChild(messageDiv);
        
        // Scroll to bottom
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
        
        // Auto-focus the input field after adding a message
        this.ensureInputFocus();
    }
    
    async confirmChanges() {
        if (!this.confirmToken) return;
        
        this.setProcessing(true);
        
        try {
            const payload = {
                message: 'confirm',
                confirm: true,
                confirm_token: this.confirmToken
            };
            
            const response = await fetch('/chat/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to confirm changes');
            }
            
            const result = await response.json();
            this.addMessage('assistant', result.message);
            this.confirmToken = null;
            
        } catch (error) {
            console.error('Error confirming changes:', error);
            this.addMessage('error', `Error: ${error.message}`);
        } finally {
            this.setProcessing(false);
            // Auto-focus the input field after confirmation
            this.ensureInputFocus();
        }
    }
    
    setProcessing(processing) {
        this.isProcessing = processing;
        this.sendButton.disabled = processing;
        this.messageInput.disabled = processing;
        
        if (processing) {
            this.sendButton.innerHTML = '<span class="spinner"></span>Processing...';
            this.sendButton.classList.add('loading');
        } else {
            this.sendButton.innerHTML = '<span>Send</span>';
            this.sendButton.classList.remove('loading');
            
            // Auto-focus the input field after processing is complete
            this.ensureInputFocus();
        }
    }
    
    ensureInputFocus() {
        // Focus the input field if it's not disabled and not currently processing
        if (!this.isProcessing && !this.messageInput.disabled) {
            this.messageInput.focus();
            // Add visual focus indicator
            this.messageInput.classList.add('focused');
            console.log('Input field focused automatically');
        }
    }
    
    blurInput() {
        // Remove focus and visual indicator
        this.messageInput.blur();
        this.messageInput.classList.remove('focused');
    }
    
    async checkHealth() {
        try {
            const response = await fetch('/health');
            if (response.ok) {
                const health = await response.json();
                this.updateStatus(health);
            } else {
                this.updateStatus({
                    status: 'unhealthy',
                    anki_connect: false,
                    llm: false
                });
            }
        } catch (error) {
            console.error('Health check failed:', error);
            this.updateStatus({
                status: 'unhealthy',
                anki_connect: false,
                llm: false
            });
        }
    }
    
    updateStatus(health) {
        // Update main status
        this.statusIndicator.textContent = health.status;
        this.statusIndicator.className = `status-indicator ${health.status}`;
        
        // Update AnkiConnect status
        this.ankiStatus.textContent = health.anki_connect ? 'Connected' : 'Disconnected';
        this.ankiStatus.className = `status-indicator ${health.anki_connect ? 'healthy' : 'unhealthy'}`;
    }
    
    setInterval(callback, interval) {
        // Simple setInterval implementation
        const timer = setInterval(callback, interval);
        return timer;
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new AnkiLLMAssistant();
});
