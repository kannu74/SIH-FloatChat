document.addEventListener('DOMContentLoaded', () => {
    // Get references to all the necessary HTML elements
    const chatWindow = document.getElementById('chat-window');
    const chatForm = document.getElementById('chat-form');
    const messageInput = document.getElementById('message-input');
    const newChatBtn = document.getElementById('new-chat-btn');
    const deleteChatBtn = document.getElementById('delete-chat-btn');
    const chatHistoryEl = document.getElementById('chat-history');
    const welcomeCard = document.getElementById('welcome-card');

    let chatHistory = {};
    let activeChatId = null;

    // --- Core Functions for Chat Management ---

    const loadChats = () => {
        chatHistory = JSON.parse(localStorage.getItem('floatChatHistory')) || {};
        const chatIds = Object.keys(chatHistory);
        if (chatIds.length === 0) {
            startNewChat();
        } else {
            activeChatId = localStorage.getItem('floatChatActiveId') || chatIds[chatIds.length - 1];
            if (!chatHistory[activeChatId]) {
                activeChatId = chatIds[chatIds.length - 1];
            }
            renderChatHistory();
            renderActiveChat();
        }
    };

    const saveChats = () => {
        localStorage.setItem('floatChatHistory', JSON.stringify(chatHistory));
        localStorage.setItem('floatChatActiveId', activeChatId);
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
        saveChats();
    };

    const deleteActiveChat = () => {
        const chatIds = Object.keys(chatHistory);
        if (chatIds.length <= 1) {
            alert("Cannot delete the last chat.");
            return;
        }
        if (confirm("Are you sure you want to delete this chat?")) {
            delete chatHistory[activeChatId];
            localStorage.removeItem('floatChatActiveId');
            saveChats();
            loadChats();
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
            activeChat.messages.forEach(msg => appendMessage(msg.role, msg));
        }
        toggleWelcomeCard();
    };

    const appendMessage = (role, messageData) => {
        const messageEl = document.createElement('div');
        messageEl.classList.add('message', `${role}-message`, 'new-message');
        setTimeout(() => messageEl.classList.remove('new-message'), 1200);

        if (messageData.content === 'loading') {
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
            renderResponse(messageEl, messageData);
        }
        
        chatWindow.appendChild(messageEl);
        chatWindow.scrollTop = chatWindow.scrollHeight;
    };
    
    const renderResponse = (element, messageData) => {
        const { content, sql_query, visualization } = messageData;
        
        if (Array.isArray(content) && content.length > 0) {
            const plotContainer = document.createElement('div');
            switch (visualization) {
                case 'line_chart':
                    renderLineChart(plotContainer, content);
                    break;
                case 'map':
                    renderMap(plotContainer, content);
                    break;
                case 'scatter_plot':
                    renderScatterPlot(plotContainer, content);
                    break;
                case 'table':
                default:
                    plotContainer.appendChild(createTable(content));
                    break;
            }
            element.appendChild(plotContainer);
        } else if (Array.isArray(content) && content.length === 0) {
            element.textContent = "Query returned no results.";
        } else {
            element.textContent = content;
        }

        if (sql_query) {
            const details = document.createElement('details');
            const summary = document.createElement('summary');
            summary.textContent = 'View SQL Query';
            const pre = document.createElement('pre');
            pre.textContent = sql_query;
            details.appendChild(summary);
            details.appendChild(pre);
            element.appendChild(details);
        }
    };

    // --- Visualization and Table Functions ---

    const renderLineChart = (element, data) => {
        const x_values = data.map(row => row.temperature ?? row.salinity);
        const y_values = data.map(row => row.pressure);
        const x_axis_title = data[0].temperature ? 'Temperature (°C)' : 'Salinity';
        
        Plotly.newPlot(element, [{ x: x_values, y: y_values, mode: 'lines+markers', type: 'scatter' }], {
            title: `${x_axis_title} Profile`,
            xaxis: { title: x_axis_title, side: 'top' },
            yaxis: { title: 'Pressure (Depth)', autorange: 'reversed' },
            paper_bgcolor: '#2a2a2a', plot_bgcolor: '#2a2a2a', font: { color: '#e0e0e0' }
        });
    };

    const renderMap = (element, data) => {
        Plotly.newPlot(element, [{
            type: 'scattergeo', lon: data.map(r => r.longitude), lat: data.map(r => r.latitude),
            text: data.map(r => `Float ID: ${r.float_id || ''}`), mode: 'markers',
            marker: { size: 8, color: 'cyan' }
        }], {
            title: 'Float Locations', geo: { projection: { type: 'natural earth' },
            bgcolor: '#2a2a2a', landcolor: '#3a3a3a', subunitcolor: '#555' },
            paper_bgcolor: '#2a2a2a', plot_bgcolor: '#2a2a2a', font: { color: '#e0e0e0' }
        });
    };

    // --- Find and replace this specific function in your main.js file ---
    const renderScatterPlot = (element, data) => {
        // Add a check to ensure the required data columns are present
        if (!data[0].salinity || !data[0].temperature || !data[0].pressure) {
            element.textContent = "Error: To create a scatter plot, the data must include salinity, temperature, and pressure.";
            return;
        }

        const plotData = [{
            x: data.map(row => row.salinity),
            y: data.map(row => row.temperature),
            mode: 'markers',
            type: 'scatter',
            marker: {
                color: data.map(row => row.pressure),
                colorscale: 'Viridis',
                showscale: true,
                colorbar: {
                    title: 'Pressure (Depth)'
                }
            }
        }];
        const layout = {
            title: 'Temperature vs. Salinity (T-S Diagram)',
            xaxis: { title: 'Salinity' },
            yaxis: { title: 'Temperature (°C)' },
            paper_bgcolor: '#2a2a2a',
            plot_bgcolor: '#2a2a2a',
            font: { color: '#e0e0e0' }
        };
        Plotly.newPlot(element, plotData, layout);
    };

    const createTable = (data) => {
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
                td.textContent = (header === 'timestamp') ? new Date(rowData[header]).toLocaleString() : rowData[header];
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
        appendMessage(userMessage.role, userMessage);
        
        if (chatHistory[activeChatId].messages.length === 1) {
            chatHistory[activeChatId].title = question;
            renderChatHistory();
        }

        messageInput.value = '';
        appendMessage('bot', { content: 'loading' });

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
            const botMessage = { role: 'bot', content: result.data, sql_query: result.sql_query, visualization: result.visualization };
            chatHistory[activeChatId].messages.push(botMessage);
            appendMessage(botMessage.role, botMessage);
            
        } catch (error) {
            console.error('Error fetching from API:', error);
            const errorMessage = { role: 'bot', content: `Error: ${error.message}` };
            chatHistory[activeChatId].messages.push(errorMessage);
            appendMessage(errorMessage.role, errorMessage);
        }

        saveChats();
    });

    newChatBtn.addEventListener('click', startNewChat);
    deleteChatBtn.addEventListener('click', deleteActiveChat);

    // --- Welcome Card Feature ---
    function toggleWelcomeCard() {
        const hasMessages = chatWindow.querySelector(".message");
        if (welcomeCard) {
            welcomeCard.style.display = hasMessages ? "none" : "flex";
        }
    }

    const observer = new MutationObserver(toggleWelcomeCard);
    observer.observe(chatWindow, { childList: true });

    // --- Initial Load ---
    loadChats();
});