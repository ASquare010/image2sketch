import os, uuid, shutil, subprocess
import gradio as gr


UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER","src/uploads")
RESULT_FOLDER = os.getenv("RESULT_FOLDER","src/results/semi_unpair/dir_free/")
DATASET_FOLDER = os.getenv("DATASET_FOLDER ","src/datasets/ref_unpair/")
GRADIO_SERVER_PORT = os.getenv("GRADIO_SERVER_PORT", 8073)

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

def copy_files(source_files, target_folder):
    """
    Copies files manually from source to target folder.
    :param source_files: List of file paths to copy.
    :param target_folder: Path to the destination folder.
    """
    os.makedirs(target_folder, exist_ok=True)

    for file in source_files:
        file_name = os.path.basename(file)
        target_file_path = os.path.join(target_folder, file_name)

        with open(file, 'rb') as source:
            with open(target_file_path, 'wb') as target:
                target.write(source.read())

def save_image(image, file_path, name_uuid):
    """
    Saves the uploaded image to the specified path.
    """
    os.makedirs(file_path, exist_ok=True)
    full_file_path = os.path.join(file_path, f"{name_uuid}.png")
    image.save(full_file_path)

def process_uploaded_file(image):

    name_uuid = str(uuid.uuid4())
    source_dir_b = os.path.join(DATASET_FOLDER, 'testB')
    source_dir_c = os.path.join(DATASET_FOLDER, 'testC')
    target_folder_a = os.path.join(UPLOAD_FOLDER, name_uuid, 'testA')
    target_folder_b = os.path.join(UPLOAD_FOLDER, name_uuid, 'testB')
    target_folder_c = os.path.join(UPLOAD_FOLDER, name_uuid, 'testC')

    os.makedirs(target_folder_a, exist_ok=True)
    os.makedirs(target_folder_b, exist_ok=True)
    os.makedirs(target_folder_c, exist_ok=True)

    save_image(image, target_folder_a, name_uuid)

    read_files_testB = [f'{source_dir_b}/dummy_image.png']
    read_files_testC = [f'{source_dir_c}/styleA.png', f'{source_dir_c}/styleB.png', f'{source_dir_c}/styleC.png']

    copy_files(read_files_testB, target_folder_b)
    copy_files(read_files_testC, target_folder_c)

    root_folder = os.path.join(UPLOAD_FOLDER, name_uuid)
    
    return  root_folder, name_uuid

def get_output_image_path(name_uuid):
    return [ 
        os.path.join(RESULT_FOLDER, 'styleA.png',f'{name_uuid}.png'),
        os.path.join(RESULT_FOLDER, 'styleB.png',f'{name_uuid}.png'),
        os.path.join(RESULT_FOLDER, 'styleC.png',f'{name_uuid}.png')
    ]

def process_image(image):

    root_folder, name_uuid = process_uploaded_file(image)

    # Run the command to process the image
    command = [
        "python3", "src/test_dir.py",
        "--name", "semi_unpair",
        "--model", "unpaired",
        "--epoch", "100",
        "--dataroot", root_folder,
    ]

    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
        shutil.rmtree(root_folder)
    except subprocess.CalledProcessError as e:
        return f"Error: Command failed: {str(e)}"

    files = get_output_image_path(name_uuid)

    if all(os.path.exists(file) for file in files):
        return files[0], files[1], files[2]
    else:
        print("Error: Output files not found.")
        return None, None, None

    
interface = gr.Interface(
    fn=process_image,
    inputs=gr.Image(type="pil"),
    outputs=[
        gr.Image(label="Sketch 1"),
        gr.Image(label="Sketch 2"),
        gr.Image(label="Sketch 3")
    ],
    title="Image2Sketch",
    description="Upload an image to process and get three output images."
)

if __name__ == "__main__":
    interface.launch(server_name="0.0.0.0",share=True,server_port=int(GRADIO_SERVER_PORT))