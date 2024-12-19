from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from uuid import uuid4
import redis, uvicorn, requests
from worker import process_image_task, REDIS_PORT, IMAGE2SKETCH_URL

# --------------------------------------------------------Initialize the FastAPI, Celery and Redis---------------------------------------------------
app = FastAPI()
redis_client = redis.StrictRedis(host='localhost', port=int(REDIS_PORT), db=2, decode_responses=True)

# ---------------------------------------------------------Celery Task Function--------------------------------------------------------
class ImageRequest(BaseModel):
    imageUrl: str

class UUIDRequest(BaseModel):
    uuid: str

# ----------------------------------------------------------API Endpoints-------------------------------------------------------------

@app.get("/test_flask")
async def proxy_to_flask():
    try:
        # Call the Flask app's "/" endpoint
        response = requests.get(f"{IMAGE2SKETCH_URL}/", timeout=10)
        
        # Return the response from Flask
        return {
            "status": "success",
            "flask_response": response.text,
            "flask_status_code": response.status_code
        }
    except requests.RequestException as e:
        # Handle errors during the request
        raise HTTPException(status_code=500, detail=f"Failed to reach Flask app: {str(e)}")

@app.post("/generate_sketch")
def generate_sketch(request: ImageRequest, background_tasks: BackgroundTasks):
    imageUrl = request.imageUrl
    uuid = str(uuid4())

    task = process_image_task.delay(imageUrl)
    redis_client.set(uuid, task.id)

    return JSONResponse(content={"uuid": uuid, "message": f"Task submitted. UUID: {uuid}"}, status_code=200)


@app.post("/get_results")
def get_results(request: UUIDRequest):
    uuid = request.uuid
    task_id = redis_client.get(uuid)

    if not task_id:
        return JSONResponse(content={"error": "UUID not found."}, status_code=404)

    task = process_image_task.AsyncResult(task_id)

    if task.state == 'PENDING':
        return JSONResponse(content={"status": "Task is still in the queue."}, status_code=202)
    elif task.state == 'STARTED':
        return JSONResponse(content={"status": "Task is currently being processed."}, status_code=202)
    elif task.state == 'SUCCESS':
        redis_client.delete(uuid)
        return JSONResponse(content={"status": "Task completed successfully.", "result": task.result}, status_code=200)
    elif task.state == 'FAILURE':
        return JSONResponse(content={"status": "Task failed.", "error": str(task.info)}, status_code=500)

    return JSONResponse(content={"status": "Unknown state."}, status_code=500)



# ----------------------------------------------------------Run FastAPI---------------------------------------------------------------
if __name__ == "__main__":
    uvicorn.run(app, port=5050)
