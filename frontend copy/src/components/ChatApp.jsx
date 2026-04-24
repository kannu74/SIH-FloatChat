import { useEffect } from "react";

// load legacy JS (VERY IMPORTANT)
import "../legacy/static/js/main.js";
//import "../legacy/static/js/ui.js";

export default function ChatApp() {
  useEffect(() => {
    // initialize legacy scripts if they expose any init function
    if (window.initializeApp) {
      window.initializeApp();
    }
  }, []);

  return (
    <div className="container">
      {/* Sidebar */}
      <aside className="sidebar">
        <h1>
          <i className="fa fa-comments"></i> Orca AI
        </h1>

        <div className="sidebar-buttons">
          <button id="new-chat-btn">
            <i className="fa fa-plus"></i> New Chat
          </button>

          <button id="delete-chat-btn">
            <i className="fa fa-trash"></i> Delete Chat
          </button>
        </div>

        <nav id="chat-history"></nav>
      </aside>

      {/* Chat Interface */}
      <main className="chat-interface">
        <div id="welcome-card">
          <h2>Welcome to Orca AI</h2>
          <p>
            Click <strong>New Chat</strong> or type your question below to
            explore ARGO ocean data.
          </p>
        </div>

        <div id="chat-window"></div>

        <div id="avatar-container">AVATAR</div>

        <div className="chat-input-area">
          <form id="chat-form">
            <input
              type="text"
              id="message-input"
              placeholder="Ask about ARGO ocean data..."
              autoComplete="off"
              required
            />
            <button type="submit">Send</button>
          </form>
        </div>
      </main>
    </div>
  );
}