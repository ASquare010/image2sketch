import os, uuid, shutil, subprocess
import zipfile
from flask import Flask, request, jsonify, render_template,send_from_directory
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
app.config['UPLOAD_FOLDER'] = 'src/uploads'
app.config['RESULT_FOLDER'] = 'src/results/semi_unpair/dir_free/'
app.config['DATASET_FOLDER'] = 'src/datasets/ref_unpair/'

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['RESULT_FOLDER'], exist_ok=True)



def copy_files(source_files, target_folder):
    """
    Copies files manually from source to target folder.
    
    :param source_files: List of file paths to copy.
    :param target_folder: Path to the destination folder.
    """
    # Ensure the target directory exists
    os.makedirs(target_folder, exist_ok=True)

    for file in source_files:
        file_name = os.path.basename(file)
        target_file_path = os.path.join(target_folder, file_name)

        with open(file, 'rb') as source:
            with open(target_file_path, 'wb') as target:
                target.write(source.read())


def process_uploaded_file(file):
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
    # Generate a unique folder name
    name_uuid = str(uuid.uuid4())
    source_dir_b = os.path.join(app.config['DATASET_FOLDER'], 'testB')
    source_dir_c = os.path.join(app.config['DATASET_FOLDER'], 'testC')
    target_folder_a = os.path.join(app.config['UPLOAD_FOLDER'], name_uuid, 'testA')
    target_folder_b = os.path.join(app.config['UPLOAD_FOLDER'], name_uuid, 'testB')
    target_folder_c = os.path.join(app.config['UPLOAD_FOLDER'], name_uuid, 'testC')

    # Create the target folders
    os.makedirs(target_folder_a, exist_ok=True)
    os.makedirs(target_folder_b, exist_ok=True)
    os.makedirs(target_folder_c, exist_ok=True)

    # Save the uploaded file into the 'testA' folder
    file_extension = os.path.splitext(file.filename)[1] 
    unique_filename = name_uuid + file_extension
    file_path = os.path.join(target_folder_a, unique_filename)  # Save in testA folder
    file.save(file_path)

    # Define the files to read and copy to testB and testC folders
    read_files_testB = [f'{source_dir_b}/dummy_image.png']
    read_files_testC = [f'{source_dir_c}/styleA.png', f'{source_dir_c}/styleB.png', f'{source_dir_c}/styleC.png']

    copy_files(read_files_testB, target_folder_b)
    copy_files(read_files_testC, target_folder_c)

    root_folder = os.path.join(app.config['UPLOAD_FOLDER'], name_uuid)
    
    return  root_folder, name_uuid


def get_output_image_path(name_uuid):
    # Define the paths for the output images
    styleA_path = os.path.join(app.config['RESULT_FOLDER'], 'styleA.png',f'{name_uuid}.png')
    styleB_path = os.path.join(app.config['RESULT_FOLDER'], 'styleB.png',f'{name_uuid}.png')
    styleC_path = os.path.join(app.config['RESULT_FOLDER'], 'styleC.png',f'{name_uuid}.png')
    
    return [styleA_path, styleB_path, styleC_path]


def create_zip_from_files(files, name_uuid):
    # Create the ZIP file
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
                os.remove(file)  # Delete the file after zipping
            else:
                print(f"File not found: {file}")
    except Exception as e:
        print(f"Error deleting files: {str(e)}")
        raise


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['RESULT_FOLDER'], filename)

@app.route('/process', methods=['POST'])
def process():
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400

    uploaded_file = request.files['image']
    root_folder, name_uuid = process_uploaded_file(uploaded_file)

    # Run the image processing command
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
        return jsonify({'error': f'Command failed: {str(e)}\n{e.stderr}'}), 500
        
    files = get_output_image_path(name_uuid)

    if all(os.path.exists(file) for file in files):
        zip_file_path = create_zip_from_files(files, name_uuid)
        
        # Delete the image files after zipping
        try:
            delete_files(files)  # Delete the image files after zipping
        except Exception as e:
            return jsonify({'error': f"Failed to delete files: {str(e)}"}), 500
        
        zip_file_url = f'/download/{os.path.basename(zip_file_path)}'

        return jsonify({'zip_file_url': zip_file_url}), 200
    else:
        return jsonify({'error': 'Output images not found'}), 500
    
    
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
