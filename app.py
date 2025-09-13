from dotenv import load_dotenv
# Load environment variables FIRST, before any other imports that might need them.
load_dotenv()

from flask import render_template
# This imports the Flask app object from your API file.
# That object already contains the /api/chat route.
from backend.api.main import app 

# This new route serves the main HTML page for your user interface.
@app.route('/')
def index():
    return render_template('index.html')

# This block runs the Flask development server.
if __name__ == '__main__':
    app.run(debug=True)