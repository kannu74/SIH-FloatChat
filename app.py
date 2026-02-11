from dotenv import load_dotenv
# Load environment variables FIRST, before any other imports that might need them.
load_dotenv()

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
# This imports the FastAPI app object from your API file.
# That object already contains the /api/chat route.
from backend.api.main import app 

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# This new route serves the main HTML page for your user interface.
@app.get('/')
async def index():
    return FileResponse('templates/index.html')

# This block runs the FastAPI server with uvicorn.
if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)