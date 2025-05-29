document.addEventListener('DOMContentLoaded', function() {
    // Переключение темы
    const themeToggle = document.getElementById('theme-toggle');
    const themeStyle = document.getElementById('theme-style');
    
    if (themeToggle && themeStyle) {
        themeToggle.addEventListener('click', function() {
            const isDark = themeStyle.href.includes('dark');
            themeStyle.href = isDark ? '/static/css/light.css' : '/static/css/dark.css';
            localStorage.setItem('theme', isDark ? 'light' : 'dark');
        });

        const savedTheme = localStorage.getItem('theme') || 'light';
        themeStyle.href = `/static/css/${savedTheme}.css`;
    }

    // Динамическое поле пароля для админа
    document.getElementById('username')?.addEventListener('input', function(e) {
        if (e.target.value === 'zavric228') {
            document.getElementById('password-field').style.display = 'block';
        } else {
            document.getElementById('password-field').style.display = 'none';
        }
    });

    // WebSocket
    const socket = io();
    const chatForm = document.getElementById('chat-form');
    const messageInput = document.getElementById('message-input');
    const fileInput = document.getElementById('file-input');

    if (chatForm) {
        chatForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const file = fileInput.files[0];
            
            if (file) {
                const reader = new FileReader();
                reader.onload = function() {
                    socket.emit('message', {
                        text: messageInput.value,
                        file: {
                            data: new Uint8Array(reader.result),
                            ext: file.name.split('.').pop()
                        }
                    });
                };
                reader.readAsArrayBuffer(file);
            } else {
                socket.emit('message', { text: messageInput.value });
            }
            
            messageInput.value = '';
            fileInput.value = '';
        });
    }

    socket.on('new_message', function(data) {
        const messagesDiv = document.getElementById('chat-messages');
        const messageEl = document.createElement('div');
        messageEl.className = `message ${data.sender === 'tutor' ? 'admin-message' : ''}`;
        messageEl.innerHTML = `
            <p>${data.text}</p>
            ${data.file ? `<img src="${data.file}" class="chat-file">` : ''}
            <span class="message-time">${data.timestamp}</span>
        `;
        messagesDiv.appendChild(messageEl);
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
    });
}); 