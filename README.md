<h1 align="center">Orca AI - Conversational Interface for ARGO Data</h1>
<p align="center">
  Orca AI is an end-to-end conversational system for ARGO float data. It enables users to query, explore, and visualize oceanographic information using natural language through an AI-powered backend, a PostgreSQL/ChromaDB pipeline, and a responsive frontend chat interface.
</p>

---

<h2>📋 Project Overview</h2>
<ul>
  <li>⚡ <b>Data Pipeline:</b> Ingests ARGO NetCDF (<code>.nc</code>) files, processes them, and stores data in PostgreSQL and ChromaDB for AI retrieval.</li>
  <li>🧠 <b>AI Backend:</b> Uses Flask and Gemini API to translate questions into SQL queries, execute them, and return results.</li>
  <li>💬 <b>Frontend Chat:</b> Responsive dark-themed interface with multiple sessions, localStorage context memory, SQL inspection, and dynamic data tables.</li>
</ul>

---

<h2>📂 Project Structure</h2>
<pre><code>
orca-ai/
├── backend/
│   ├── api/
│   │   └── main.py
│   ├── data_processing/
│   │   └── processor.py
│   ├── database/
│   │   └── setup_db.py
│   └── llm/
│       └── rag_handler.py
├── data/
│   └── raw/
├── db/
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── main.js
├── templates/
│   └── index.html
├── app.py
├── docker-compose.yml
├── requirements.txt
├── run_ingestion.py
└── .env
</code></pre>

---

<h2>🚀 Installation</h2>
<h3>1. Prerequisites</h3>
<ul>
  <li>Git</li>
  <li>Python 3.8+ and pip</li>
  <li><a href="https://docs.docker.com/desktop/install/" target="_blank">Docker Desktop</a></li>
</ul>

<h3>2. Clone and Set Up</h3>
<pre><code>git clone &lt;https://github.com/kannu74/SIH-FloatChat&gt;
cd orca-ai

# Create and activate virtual environment
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
</code></pre>

<h3>3. Configure Environment</h3>
<pre><code>POSTGRES_USER=argo_user
POSTGRES_PASSWORD=your_secure_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=argo_db
GOOGLE_API_KEY=your_google_api_key
</code></pre>

<h3>4. Start Database</h3>
<pre><code>docker-compose up -d
</code></pre>

<h3>5. Ingest Data</h3>
<ul>
  <li>Download ARGO <code>.nc</code> files from 
    <a href="ftp://ftp.ifremer.fr/ifremer/argo/geo/indian_ocean/" target="_blank">Indian Ocean Repository</a> 
    and place them in <code>data/raw/</code>.
  </li>
</ul>
<pre><code>python backend/database/setup_db.py
python run_ingestion.py
</code></pre>

---

<h2>🧠 Run Backend API</h2>
<pre><code>python app.py
</code></pre>
<p>Server runs at: <code>http://127.0.0.1:5000</code></p>

<h3>Test Endpoint</h3>
<pre><code>curl -X POST -H "Content-Type: application/json" \
-d "{\"question\":\"Show me the 5 most recent temperature and salinity measurements\"}" \
http://127.0.0.1:5000/api/chat
</code></pre>

---

<h2>💬 Launch Full App</h2>
<pre><code>docker-compose up -d
python app.py
</code></pre>
<p>Visit: <code>http://127.0.0.1:5000</code></p>

---

<h2>✨ Features</h2>
<ul>
  <li>Multiple chat sessions with sidebar navigation.</li>
  <li>Context memory using <code>localStorage</code>.</li>
  <li>Dynamic table rendering of data in chat.</li>
  <li>Collapsible SQL query viewer and session deletion.</li>
  <li>Spinner indicator while AI processes queries.</li>
</ul>

---

<h2>🐳 Useful Docker Commands</h2>
<pre><code># Check container status
docker-compose ps

# View database logs
docker-compose logs -f db

# Stop and remove containers
docker-compose down
</code></pre>

---

<h2>🔧 Troubleshooting</h2>
<ul>
  <li>If <code>"data": []</code> is returned, re-run <code>python run_ingestion.py</code> to reload data.</li>
  <li>Ensure Docker is running and .env variables are correctly set.</li>
</ul>
<h4>Please note that the we have used <b>Gemini</b> and <b>Chat GPT</b> LLMs for almost 70-80% of the coding</h4>
