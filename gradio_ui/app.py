import requests, zipfile, os, tempfile, json
import gradio as gr
from uuid import uuid4

# Environment Variables
IMAGE2SKETCH_URL = os.getenv("IMAGE2SKETCH_URL", "http://image2sketch:5000")
IMAGE2SKETCH_JOB_URL = os.getenv("IMAGE2SKETCH_JOB_URL", "http://image2sketch-job-scheduler:5050")
GRADIO_SERVER_PORT = os.getenv("GRADIO_SERVER_PORT", 8073)

# ----------------------------------------------------- Helper Functions -----------------------------------------------------

def gr_generate_sketch(image_url):
    response = requests.post(
        f"{IMAGE2SKETCH_JOB_URL}/generate_sketch",
        json={"imageUrl": image_url},
    )
    if response.status_code == 200:
        data = response.json()
        return f"Task submitted successfully! Your UUID is: {data['uuid']}"
    else:
        return f"Error: {response.json().get('error', 'Unknown error occurred.')}"


def gr_get_results(uuid):
    response = requests.post(
        f"{IMAGE2SKETCH_JOB_URL}/get_results",
        json={"uuid": uuid},
    )
    try:
        data = response.json()
    except ValueError:
        return "Error: Invalid JSON response."

    if isinstance(data, list):
        return "Error: Unexpected response format (list instead of dictionary)."

    if response.status_code == 200:
        if data.get("status") == "Task completed successfully." and "result" in data:
            return data["result"]  # Return the ZIP file URL
        else:
            return f"Status: {data.get('status', 'Unknown status')}"
    elif response.status_code == 202:
        return f"Status: {data.get('status', 'Task is in progress')}"
    elif response.status_code == 404:
        return "Error: UUID not found."
    else:
        error_message = data.get("error", "Unknown error occurred.")
        return f"Error: {error_message}"


def gr_download_and_display(data_json):
    try:
        data_json = json.loads(str(data_json).replace("'", '"'))
    except json.JSONDecodeError:
        return "Invalid input data. Please provide a valid JSON."

    try:
        temp_dir = tempfile.mkdtemp()
        zip_url = f"{IMAGE2SKETCH_URL}{data_json['zipFileUrl']}"
        zip_path = os.path.join(temp_dir, f"{uuid4()}_images.zip")

        response = requests.get(zip_url, stream=True)
        if response.status_code == 200:
            with open(zip_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
        else:
            return f"Failed to download ZIP file: {response.status_code}"

        extract_dir = os.path.join(temp_dir, "extracted_images")
        os.makedirs(extract_dir, exist_ok=True)
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(extract_dir)

        image_files = [
            os.path.join(extract_dir, file)
            for file in os.listdir(extract_dir)
            if file.lower().endswith((".png", ".jpg", ".jpeg"))
        ]

        return image_files if image_files else "No images found in the ZIP file."

    except requests.exceptions.RequestException as req_err:
        return f"Request error: {str(req_err)}"
    except zipfile.BadZipFile:
        return "Error: The ZIP file is corrupted."
    except Exception as e:
        return f"An unexpected error occurred: {str(e)}"


# ----------------------------------------------------- Define Gradio Interface -----------------------------------------------------

with gr.Blocks() as ui:
    gr.Markdown("# Image2Sketch API Interface")

    with gr.Tab("Post Job"):
        with gr.Row():
            image_input = gr.Image(label="Upload Image", type="filepath")
            input_url = gr.Textbox(label="Image URL (Optional)", value="")
            output_message = gr.Textbox(label="Job UUID", interactive=False)
        generate_button = gr.Button("Generate Sketch")
        generate_button.click(
            lambda image, url: gr_generate_sketch(url if url else f"file://{image}"),
            inputs=[image_input, input_url],
            outputs=output_message,
        )

    with gr.Tab("Get Results and Display"):
        with gr.Row():
            input_uuid = gr.Textbox(label="UUID")
            data_json = gr.Textbox(label="ZIP File URL", interactive=False)
        get_zip_button = gr.Button("Check Job Status")
        get_zip_button.click(gr_get_results, inputs=input_uuid, outputs=data_json)

        with gr.Row():
            images_display = gr.Gallery(label="Extracted Images", columns=4, height=600)
        download_button = gr.Button("Download and Show Images")
        download_button.click(gr_download_and_display, inputs=data_json, outputs=images_display)

if __name__ == "__main__":
    ui.launch(server_name="0.0.0.0", server_port=int(GRADIO_SERVER_PORT))
