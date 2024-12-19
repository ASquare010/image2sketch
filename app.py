import os, uuid, shutil, subprocess,requests,zipfile
from flask import Flask, send_from_directory, jsonify,request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

app.config['UPLOAD_FOLDER'] = 'src/uploads'
app.config['RESULT_FOLDER'] = 'src/results/semi_unpair/dir_free/'
app.config['DATASET_FOLDER'] = 'src/datasets/ref_unpair/'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['RESULT_FOLDER'], exist_ok=True)

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

def download_image_and_save(image_url, file_path,name_uuid):
    """
    Downloads an image from the given URL and saves it to the specified file path.

    Args:
        image_url (str): The URL of the image to download.
        file_path (str): The path to save the downloaded image.
    """
    response = requests.get(image_url)
    if response.status_code == 200:
        full_file_path = os.path.join(file_path, f"{name_uuid}.png")
        with open(full_file_path, "wb") as file:
            file.write(response.content)

def process_uploaded_file(image_url):
    """
    Handles the processing and organization of an uploaded file, including saving the file and copying associated 
    resources into organized folders.

    Args:
        file (FileStorage): The uploaded file object, typically obtained from a web form submission.

    Returns:
        tuple: 
            - root_folder (str): The root folder path where all processed files and folders are stored.
            - name_uuid (str): The unique identifier for the uploaded file batch.
    """
    name_uuid = str(uuid.uuid4())
    source_dir_b = os.path.join(app.config['DATASET_FOLDER'], 'testB')
    source_dir_c = os.path.join(app.config['DATASET_FOLDER'], 'testC')
    target_folder_a = os.path.join(app.config['UPLOAD_FOLDER'], name_uuid, 'testA')
    target_folder_b = os.path.join(app.config['UPLOAD_FOLDER'], name_uuid, 'testB')
    target_folder_c = os.path.join(app.config['UPLOAD_FOLDER'], name_uuid, 'testC')

    os.makedirs(target_folder_a, exist_ok=True)
    os.makedirs(target_folder_b, exist_ok=True)
    os.makedirs(target_folder_c, exist_ok=True)

    download_image_and_save(image_url, target_folder_a, name_uuid)

    read_files_testB = [f'{source_dir_b}/dummy_image.png']
    read_files_testC = [f'{source_dir_c}/styleA.png', f'{source_dir_c}/styleB.png', f'{source_dir_c}/styleC.png']

    copy_files(read_files_testB, target_folder_b)
    copy_files(read_files_testC, target_folder_c)

    root_folder = os.path.join(app.config['UPLOAD_FOLDER'], name_uuid)
    
    return  root_folder, name_uuid

def get_output_image_path(name_uuid):
    styleA_path = os.path.join(app.config['RESULT_FOLDER'], 'styleA.png',f'{name_uuid}.png')
    styleB_path = os.path.join(app.config['RESULT_FOLDER'], 'styleB.png',f'{name_uuid}.png')
    styleC_path = os.path.join(app.config['RESULT_FOLDER'], 'styleC.png',f'{name_uuid}.png')
    
    return [styleA_path, styleB_path, styleC_path]

def create_zip_from_files(files, name_uuid):
    zip_file_path = os.path.join(app.config['RESULT_FOLDER'], f'{name_uuid}_styles.zip')

    with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        count = 1
        for file in files:
            base_name, ext = os.path.splitext(os.path.basename(file))
            new_name = f"{base_name}_{count}{ext}"
            zip_file.write(file, new_name)
            count += 1
    return zip_file_path

def delete_files(files):
    """Deletes the specified files from the filesystem."""
    try:
        for file in files:
            if os.path.exists(file):
                os.remove(file)  
            else:
                print(f"File not found: {file}")
    except Exception as e:
        print(f"Error deleting files: {str(e)}")
        raise

def download_image(image_url):
    """
    Downloads an image from the given URL.

    Args:
        image_url (str): URL of the image to download.

    Returns:
        bytes: The binary content of the image, or None if the download failed.
    """
    try:
        response = requests.get(image_url, stream=True)
        response.raise_for_status()  
        return response.content
    except requests.RequestException as e:
        print(f"Error downloading image: {e}")
        return None

@app.route("/")
def home():
    return "Flask App is Running!", 200

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['RESULT_FOLDER'], filename)

@app.post("/process_image")
def process_job():

    imageUrl = request.json.get('imageUrl')
    root_folder, name_uuid = process_uploaded_file(imageUrl)

    command = [
        # r"D:\Git\image2sketch\.venv\Scripts\python.exe", "src/test_dir.py",
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
        print({'error': f'Command failed: {str(e)}\n{e.stderr}'}), 500
        
    files = get_output_image_path(name_uuid)

    if all(os.path.exists(file) for file in files):
        zip_file_path = create_zip_from_files(files, name_uuid)
        delete_files(files)  
        zip_file_url = f'/download/{os.path.basename(zip_file_path)}'
        return jsonify({'zipFileUrl': zip_file_url}), 200
    else:
        return jsonify({'error': 'Output files not found'}), 404
    
   
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

