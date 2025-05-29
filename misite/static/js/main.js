document.addEventListener('DOMContentLoaded', function() {
    // Переключение темы
    const themeToggle = document.getElementById('theme-toggle');
    const themeStyle = document.getElementById('theme-style');
    
    if (themeToggle && themeStyle) {
        themeToggle.addEventListener('click', function() {
            const isDark = themeStyle.href.includes('dark');
            themeStyle.href = isDark 
                ? '/static/css/light.css' 
                : '/static/css/dark.css';
            localStorage.setItem('theme', isDark ? 'light' : 'dark');
        });

        // Восстановление темы
        const savedTheme = localStorage.getItem('theme') || 'light';
        themeStyle.href = `/static/css/${savedTheme}.css`;
    }

    // Управление табами
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            
            this.classList.add('active');
            document.getElementById(this.dataset.tab).classList.add('active');
        });
    });

    if (chatForm) {
        chatForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const messageInput = document.getElementById('message-input');
            const text = messageInput.value.trim();
            
            if (!text && !fileInput.files[0]) return;
            
            if (fileInput.files[0]) {
                const reader = new FileReader();
                reader.onload = function() {
                    socket.emit('message', {
                        text: text,
                        file: {
                            data: Array.from(new Uint8Array(reader.result)),
                            ext: fileInput.files[0].name.split('.').pop()
                        }
                    });
                };
                reader.readAsArrayBuffer(fileInput.files[0]);
            } else {
                socket.emit('message', { text: text });
            }
            
            messageInput.value = '';
            fileInput.value = '';
        });
    }

    // Обработка новых сообщений
    socket.on('new_message', function(data) {
        const messagesDiv = document.getElementById('chat-messages');
        const messageEl = document.createElement('div');
        messageEl.className = `message ${data.sender === '{{ session.user }}' ? 'my-message' : ''}`;
        
        messageEl.innerHTML = `
            <p>${data.text}</p>
            ${data.file ? `<img src="${data.file}" class="chat-file">` : ''}
            <span class="message-time">${data.timestamp}</span>
        `;
        
        messagesDiv.appendChild(messageEl);
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
    });

    // Модальное окно редактирования
    const editModal = document.getElementById('edit-modal');
    if (editModal) {
        document.querySelectorAll('[data-modal-toggle]').forEach(btn => {
            btn.addEventListener('click', () => {
                editModal.style.display = 'block';
            });
        });

        editModal.querySelector('.close-btn').addEventListener('click', () => {
            editModal.style.display = 'none';
        });

        window.addEventListener('click', (e) => {
            if (e.target === editModal) editModal.style.display = 'none';
        });
    }
});