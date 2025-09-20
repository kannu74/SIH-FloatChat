document.addEventListener("DOMContentLoaded", () => {
  // Get references to all the necessary HTML elements
  const chatWindow = document.getElementById("chat-window");
  const chatForm = document.getElementById("chat-form");
  const messageInput = document.getElementById("message-input");
  const newChatBtn = document.getElementById("new-chat-btn");
  const deleteChatBtn = document.getElementById("delete-chat-btn");
  const chatHistoryEl = document.getElementById("chat-history");
  const welcomeCard = document.getElementById("welcome-card");

  let chatHistory = {};
  let activeChatId = null;

  // --- Core Functions for Chat Management ---
  const loadChats = () => {
    chatHistory = JSON.parse(localStorage.getItem("floatChatHistory")) || {};
    const chatIds = Object.keys(chatHistory);
    if (chatIds.length === 0) {
      startNewChat();
    } else {
      activeChatId =
        localStorage.getItem("floatChatActiveId") ||
        chatIds[chatIds.length - 1];
      if (!chatHistory[activeChatId]) {
        activeChatId = chatIds[chatIds.length - 1];
      }
      renderChatHistory();
      renderActiveChat();
    }
  };

  const saveChats = () => {
    localStorage.setItem("floatChatHistory", JSON.stringify(chatHistory));
    localStorage.setItem("floatChatActiveId", activeChatId);
  };

  const startNewChat = () => {
    const newChatId = `chat_${Date.now()}`;
    chatHistory[newChatId] = { id: newChatId, title: "New Chat", messages: [] };
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
      localStorage.removeItem("floatChatActiveId");
      saveChats();
      loadChats();
    }
  };

  // --- Rendering Functions to Display Content ---
  const renderChatHistory = () => {
    chatHistoryEl.innerHTML = "";
    Object.values(chatHistory).forEach((chat) => {
      const sessionEl = document.createElement("div");
      sessionEl.classList.add("chat-session");
      if (chat.id === activeChatId) sessionEl.classList.add("active");
      sessionEl.textContent = chat.title;
      sessionEl.addEventListener("click", () => switchChat(chat.id));
      chatHistoryEl.appendChild(sessionEl);
    });
  };

  const renderActiveChat = () => {
    chatWindow.innerHTML = ""; // Clear previous messages

    // Put the welcome card back if needed
    chatWindow.appendChild(welcomeCard);

    const activeChat = chatHistory[activeChatId];
    if (activeChat) {
      activeChat.messages.forEach((msg) => appendMessage(msg.role, msg, false)); // false = don't animate old messages
    }
    toggleWelcomeCard();
  };

  const appendMessage = (role, messageData, animate = true) => {
    const messageEl = document.createElement("div");
    messageEl.classList.add("message", `${role}-message`);
    if (animate) {
      messageEl.classList.add("new-message");
      setTimeout(() => messageEl.classList.remove("new-message"), 1200);
    }

    if (messageData.content === "loading") {
      const indicator = document.createElement("div");
      indicator.classList.add("thinking-indicator");
      const loader = document.createElement("div");
      loader.classList.add("loader");
      const text = document.createElement("span");
      text.textContent = "Orca AI is thinking...";
      indicator.appendChild(loader);
      indicator.appendChild(text);
      messageEl.appendChild(indicator);
    } else {
      renderResponse(messageEl, messageData);
    }

    chatWindow.appendChild(messageEl);
    chatWindow.scrollTop = chatWindow.scrollHeight;
    toggleWelcomeCard();
  };

  const renderResponse = (element, messageData) => {
    const { content, sql_query, visualization } = messageData;

    if (visualization === "text") {
      element.textContent = content;
    } else if (Array.isArray(content) && content.length > 0) {
      const plotContainer = document.createElement("div");
      switch (visualization) {
        case "line_chart":
          renderLineChart(plotContainer, content);
          break;
        case "map":
          renderMap(plotContainer, content);
          break;
        case "scatter_plot":
          renderScatterPlot(plotContainer, content);
          break;
        case 'bar_chart':
          renderBarChart(plotContainer, content); 
          break;
        case 'histogram':
          renderHistogram(plotContainer, content);
          break;
        case 'time_series':
          renderTimeSeries(plotContainer, content);
          break;
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
      const details = document.createElement("details");
      const summary = document.createElement("summary");
      summary.textContent = "View SQL Query";
      const pre = document.createElement("pre");
      pre.textContent = sql_query;
      details.appendChild(summary);
      details.appendChild(pre);
      element.appendChild(details);
    }
  };

  // --- Visualization and Table Functions ---
  const renderBarChart = (element, data) => {
    // Intelligently find which column has text and which has numbers
    let categoryKey = '';
    let valueKey = '';
    for (const key in data[0]) {
        if (typeof data[0][key] === 'string') {
            categoryKey = key;
        } else if (typeof data[0][key] === 'number') {
            valueKey = key;
        }
    }

    // If we couldn't find the keys, exit gracefully
    if (!categoryKey || !valueKey) {
        element.textContent = "Could not render bar chart due to unexpected data format.";
        return;
    }

    const categories = data.map(row => row[categoryKey]);
    const values = data.map(row => row[valueKey]);

    Plotly.newPlot(element, [{
        x: categories, // Text labels on the x-axis
        y: values,     // Numerical values on the y-axis
        type: 'bar',
        marker: { color: 'cyan' }
    }], {
        title: `Count of Measurements per Project`, // Updated title
        xaxis: { 
            title: 'Project Name',
            tickangle: -45 // Rotate labels to prevent overlap
        },
        yaxis: { title: 'Number of Measurements' },
        margin: { b: 150 }, // Add bottom margin for rotated labels
        paper_bgcolor: '#2a2a2a',
        plot_bgcolor: '#2a2a2a',
        font: { color: '#e0e0e0' }
    });
};
    const renderHistogram = (element, data) => {
    const key = Object.keys(data[0])[0];
    const values = data.map(row => row[key]);

    Plotly.newPlot(element, [{
        x: values,
        type: 'histogram',
        marker: { 
            color: 'cyan',
            // Add a line to create a border around each bar
            line: {
                color: '#121212', // A dark color matching the background
                width: 1
            }
        }
    }], {
        title: `Distribution of ${key}`,
        xaxis: { title: key },
        yaxis: { title: 'Frequency' },
        paper_bgcolor: '#2a2a2a',
        plot_bgcolor: '#2a2a2a',
        font: { color: '#e0e0e0' }
    });
};
    const renderTimeSeries = (element, data) => {
        // Assumes data has 'timestamp' and one other measurement key
        const valueKey = Object.keys(data[0]).find(k => k !== 'timestamp');
        const timestamps = data.map(row => row.timestamp);
        const values = data.map(row => row[valueKey]);

        Plotly.newPlot(element, [{
            x: timestamps,
            y: values,
            mode: 'lines+markers',
            type: 'scatter'
        }], {
            title: `Trend of ${valueKey} Over Time`,
            xaxis: { title: 'Timestamp' },
            yaxis: { title: valueKey },
            paper_bgcolor: '#2a2a2a',
            plot_bgcolor: '#2a2a2a',
            font: { color: '#e0e0e0' }
        });
    };
  const renderLineChart = (element, data) => {
    const x_values = data.map((row) => row.temperature ?? row.salinity);
    const y_values = data.map((row) => row.pressure);
    const x_axis_title = data[0].temperature ? "Temperature (°C)" : "Salinity";
    Plotly.newPlot(
      element,
      [{ x: x_values, y: y_values, mode: "lines+markers", type: "scatter" }],
      {
        title: `${x_axis_title} Profile`,
        xaxis: { title: x_axis_title, side: "top" },
        yaxis: { title: "Pressure (Depth)", autorange: "reversed" },
        paper_bgcolor: "#2a2a2a",
        plot_bgcolor: "#2a2a2a",
        font: { color: "#e0e0e0" },
      }
    );
  };

  const renderMap = (element, data) => {
    Plotly.newPlot(
      element,
      [
        {
          type: "scattergeo",
          lon: data.map((r) => r.longitude),
          lat: data.map((r) => r.latitude),
          text: data.map((r) => `Float ID: ${r.float_id || ""}`),
          mode: "markers",
          marker: { size: 8, color: "cyan" },
        },
      ],
      {
        title: "Float Locations",
        geo: {
          projection: { type: "natural earth" },
          bgcolor: "#2a2a2a",
          landcolor: "#3a3a3a",
          subunitcolor: "#555",
        },
        paper_bgcolor: "#2a2a2a",
        plot_bgcolor: "#2a2a2a",
        font: { color: "#e0e0e0" },
      }
    );
  };

  // Find and replace this specific function in your main.js file
const renderScatterPlot = (element, data) => {
    // --- CORRECTED, MORE ROBUST CHECK ---
    // This now checks if the keys exist, which works even if the value is 0.
    if (!('salinity' in data[0]) || !('temperature' in data[0]) || !('pressure' in data[0])) {
        element.textContent = "Error: To create a scatter plot, the data must include salinity, temperature, and pressure.";
        return;
    }
    // ------------------------------------

    const plotData = [{
        x: data.map((row) => row.salinity),
        y: data.map((row) => row.temperature),
        mode: 'markers',
        type: 'scatter',
        marker: {
            color: data.map((row) => row.pressure),
            colorscale: 'Viridis',
            showscale: true,
            colorbar: { title: 'Pressure (Depth)' },
        },
    }];
    const layout = {
        title: 'Temperature vs. Salinity (T-S Diagram)',
        xaxis: { title: 'Salinity' },
        yaxis: { title: 'Temperature (°C)' },
        paper_bgcolor: '#2a2a2a',
        plot_bgcolor: '#2a2a2a',
        font: { color: '#e0e0e0' },
    };
    Plotly.newPlot(element, plotData, layout);
};
  const createTable = (data) => {
    const table = document.createElement("table");
    const thead = document.createElement("thead");
    const tbody = document.createElement("tbody");
    const headers = Object.keys(data[0]);
    const headerRow = document.createElement("tr");
    headers.forEach((headerText) => {
      const th = document.createElement("th");
      th.textContent = headerText;
      headerRow.appendChild(th);
    });
    thead.appendChild(headerRow);
    data.forEach((rowData) => {
      const row = document.createElement("tr");
      headers.forEach((header) => {
        const td = document.createElement("td");
        td.textContent =
          header === "timestamp"
            ? new Date(rowData[header]).toLocaleString()
            : rowData[header];
        row.appendChild(td);
      });
      tbody.appendChild(row);
    });
    table.appendChild(thead);
    table.appendChild(tbody);
    return table;
  };

  // --- Event Handlers ---
  chatForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const question = messageInput.value.trim();
    if (!question) return;

    const userMessage = { role: "user", content: question };
    chatHistory[activeChatId].messages.push(userMessage);
    appendMessage(userMessage.role, userMessage);

    if (chatHistory[activeChatId].messages.length === 1) {
      chatHistory[activeChatId].title = question;
      renderChatHistory();
    }

    messageInput.value = "";
    appendMessage("bot", { content: "loading" });

    const historyForApi = chatHistory[activeChatId].messages
      .slice(0, -1)
      .map((msg) => {
        let content =
          typeof msg.content === "string"
            ? msg.content
            : "User asked for a visualization.";
        return { role: msg.role, content: content };
      });

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: question,
          chat_history: historyForApi,
        }),
      });
      chatWindow.removeChild(chatWindow.lastChild);
      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.error || `HTTP error! status: ${response.status}`);
      }
      const result = await response.json();
      const botMessage = {
        role: "bot",
        content: result.data,
        sql_query: result.sql_query,
        visualization: result.visualization,
      };
      chatHistory[activeChatId].messages.push(botMessage);
      appendMessage(botMessage.role, botMessage);
    } catch (error) {
      console.error("Error fetching from API:", error);
      const errorMessage = { role: "bot", content: `Error: ${error.message}` };
      chatHistory[activeChatId].messages.push(errorMessage);
      appendMessage(errorMessage.role, errorMessage);
    }
    saveChats();
  });

  newChatBtn.addEventListener("click", startNewChat);
  deleteChatBtn.addEventListener("click", deleteActiveChat);

  // --- Welcome Card Feature ---
  function toggleWelcomeCard() {
    // Checks if there are any message elements (excluding the welcome card itself)
    const hasMessages = chatWindow.querySelector(".message");
    if (welcomeCard) {
      welcomeCard.style.display = hasMessages ? "none" : "flex";
    }
  }

  // This makes sure the welcome card is shown or hidden when messages are added or removed
  const observer = new MutationObserver(() => {
    // We need a small delay to let the DOM update after clearing
    setTimeout(toggleWelcomeCard, 0);
  });
  observer.observe(chatWindow, { childList: true });

  // --- Initial Load ---
  loadChats();
});
