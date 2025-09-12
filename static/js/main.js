document.addEventListener('DOMContentLoaded', () => {
    // Get references to all the necessary HTML elements
    const chatWindow = document.getElementById('chat-window');
    const chatForm = document.getElementById('chat-form');
    const messageInput = document.getElementById('message-input');
    const newChatBtn = document.getElementById('new-chat-btn');
    const deleteChatBtn = document.getElementById('delete-chat-btn'); // New button
    const chatHistoryEl = document.getElementById('chat-history');

    let chatHistory = {};
    let activeChatId = null;

    // --- Core Functions for Chat Management ---

    const loadChats = () => {
        chatHistory = JSON.parse(localStorage.getItem('floatChatHistory')) || {};
        const chatIds = Object.keys(chatHistory);
        if (chatIds.length === 0) {
            startNewChat();
        } else {
            activeChatId = chatIds[chatIds.length - 1]; // Load the most recent chat
            renderChatHistory();
            renderActiveChat();
        }
    };

    const saveChats = () => {
        localStorage.setItem('floatChatHistory', JSON.stringify(chatHistory));
    };
    
    const startNewChat = () => {
        const newChatId = `chat_${Date.now()}`;
        chatHistory[newChatId] = {
            id: newChatId,
            title: 'New Chat',
            messages: []
        };
        activeChatId = newChatId;
        renderChatHistory();
        renderActiveChat();
        saveChats();
    };
    
    const switchChat = (chatId) => {
        activeChatId = chatId;
        renderChatHistory();
        renderActiveChat();
    };

    // --- New function to handle chat deletion ---
    const deleteActiveChat = () => {
        const chatIds = Object.keys(chatHistory);
        if (chatIds.length <= 1) {
            alert("Cannot delete the last chat.");
            return;
        }

        if (confirm("Are you sure you want to delete this chat?")) {
            delete chatHistory[activeChatId];
            saveChats();
            loadChats(); // Reload to switch to a new active chat
        }
    };

    // --- Rendering Functions to Display Content ---

    const renderChatHistory = () => {
        chatHistoryEl.innerHTML = '';
        Object.values(chatHistory).forEach(chat => {
            const sessionEl = document.createElement('div');
            sessionEl.classList.add('chat-session');
            if (chat.id === activeChatId) {
                sessionEl.classList.add('active');
            }
            sessionEl.textContent = chat.title;
            sessionEl.addEventListener('click', () => switchChat(chat.id));
            chatHistoryEl.appendChild(sessionEl);
        });
    };
    
    const renderActiveChat = () => {
        chatWindow.innerHTML = '';
        const activeChat = chatHistory[activeChatId];
        if (activeChat) {
            activeChat.messages.forEach(msg => appendMessage(msg.role, msg.content, msg.sql_query));
        }
    };

    // Add sql_query as an optional parameter
    const appendMessage = (role, content, sql_query = null) => {
        const messageEl = document.createElement('div');
        messageEl.classList.add('message', `${role}-message`);

        if (content === 'loading') {
            const indicator = document.createElement('div');
            indicator.classList.add('thinking-indicator');
            
            const loader = document.createElement('div');
            loader.classList.add('loader');
            
            const text = document.createElement('span');
            text.textContent = 'FloatChat is thinking...';
            
            indicator.appendChild(loader);
            indicator.appendChild(text);
            messageEl.appendChild(indicator);
        } else {
            // Render the main content (text or table)
            renderResponse(messageEl, content, sql_query);
        }
        
        chatWindow.appendChild(messageEl);
        chatWindow.scrollTop = chatWindow.scrollHeight;
    };
    
    // Updated to handle displaying the SQL query
    const renderResponse = (element, data, sqlQuery) => {
        if (Array.isArray(data) && data.length > 0) {
            element.appendChild(createTable(data));
        } else if (Array.isArray(data) && data.length === 0) {
            element.textContent = "Query returned no results.";
        } else {
            element.textContent = data;
        }

        // Add the collapsible SQL query view if a query exists
        if (sqlQuery) {
            const details = document.createElement('details');
            const summary = document.createElement('summary');
            summary.textContent = 'View SQL Query';
            
            const pre = document.createElement('pre');
            pre.textContent = sqlQuery;
            
            details.appendChild(summary);
            details.appendChild(pre);
            element.appendChild(details);
        }
    };

    const createTable = (data) => {
        // ... (this function remains the same as before) ...
        const table = document.createElement('table');
        const thead = document.createElement('thead');
        const tbody = document.createElement('tbody');
        const headers = Object.keys(data[0]);
        const headerRow = document.createElement('tr');
        headers.forEach(headerText => {
            const th = document.createElement('th');
            th.textContent = headerText;
            headerRow.appendChild(th);
        });
        thead.appendChild(headerRow);
        data.forEach(rowData => {
            const row = document.createElement('tr');
            headers.forEach(header => {
                const td = document.createElement('td');
                if (header === 'timestamp') {
                    td.textContent = new Date(rowData[header]).toLocaleString();
                } else {
                    td.textContent = rowData[header];
                }
                row.appendChild(td);
            });
            tbody.appendChild(row);
        });
        table.appendChild(thead);
        table.appendChild(tbody);
        return table;
    };

    // --- Event Handlers ---

    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const question = messageInput.value.trim();
        if (!question) return;

        const userMessage = { role: 'user', content: question };
        chatHistory[activeChatId].messages.push(userMessage);
        appendMessage(userMessage.role, userMessage.content);
        
        if (chatHistory[activeChatId].messages.length === 1) {
            chatHistory[activeChatId].title = question;
            renderChatHistory();
        }

        messageInput.value = '';
        appendMessage('bot', 'loading');

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question: question })
            });

            chatWindow.removeChild(chatWindow.lastChild);

            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.error || `HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            // Store the sql_query in the message object
            const botMessage = { role: 'bot', content: result.data, sql_query: result.sql_query };
            chatHistory[activeChatId].messages.push(botMessage);
            appendMessage(botMessage.role, botMessage.content, botMessage.sql_query);
            
        } catch (error) {
            console.error('Error fetching from API:', error);
            const errorMessage = { role: 'bot', content: `Error: ${error.message}` };
            chatHistory[activeChatId].messages.push(errorMessage);
            appendMessage(errorMessage.role, errorMessage.content);
        }

        saveChats();
    });

    newChatBtn.addEventListener('click', startNewChat);
    deleteChatBtn.addEventListener('click', deleteActiveChat); // Attach event listener

    // --- Initial Load ---
    loadChats();
});