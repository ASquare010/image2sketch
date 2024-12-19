from celery import Celery
import os, requests

# --------------------------------------------------------Initialize the FastAPI, Celery and Redis---------------------------------------------------
REDIS_PORT = os.getenv('REDIS_PORT', 6379)
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', f'redis://localhost:{REDIS_PORT}/0')
CELERY_BACKEND_URL = os.getenv('CELERY_BACKEND_URL', f'redis://localhost:{REDIS_PORT}/1')
IMAGE2SKETCH_URL = os.getenv('IMAGE2SKETCH_URL', 'http://image2sketch:5000')

celery_app = Celery('tasks', broker=CELERY_BROKER_URL, backend=CELERY_BACKEND_URL)


# --------------------------------------------------------Celery Worker Task Function--------------------------------------------------------
@celery_app.task
def process_image_task(imageUrl):
    try:
        response = requests.post(f"{IMAGE2SKETCH_URL}/process_image", json={"imageUrl": imageUrl}, timeout=60*2)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Failed to process image, status code: {response.status_code}, response: {response.text}"}
    except requests.RequestException as e:
        return {"error": str(e)}
