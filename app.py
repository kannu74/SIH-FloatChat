from flask import render_template
from backend.api.main import app

# This new route will serve the HTML frontend for our chat application.
# It tells Flask to find 'index.html' in the 'templates' folder.
@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    # The app will now serve both the API and the frontend.
    app.run(debug=True)
