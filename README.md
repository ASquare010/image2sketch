# Greyscale Image Processor (Sketch Generator)

This repository takes an image as input and outputs a greyscale "sketch" of the image. It provides a web-based HTML endpoint for easy testing.

## Features

- Converts the image to a greyscale sketch.
- Downloads processed images as a ZIP file.
- Gpu docker container setup

# Architecture

![Alt text](assets/1.png)
![Alt text](assets/2.png)

# Ui Sample
**Gradio_Ui samples**
![Alt text](assets/3.png)
![Alt text](assets/4.png)

# Flask-endpoint API Endpoints

## 2. `/process` (POST)

- **Description**: Accepts an image file, processes it, and returns a URL to download the resulting `.zip` file.
- **Request**:
  - **Method**: `POST`
  - **Body**: `{"imageUrl": "https://example.com/image.jpg"}`
- **Response**:
  ```json
  { "zipFileUrl": "/download/<generated-zip-file-name>.zip" }
  ```

## Source

This repository is a clone of [https://github.com/Chanuku/semi_ref2sketch_code](https://github.com/Chanuku/semi_ref2sketch_code).

# Dependent services

**This must be in docker-compose.yml other can be commented out**

- image2sketch-job-scheduler
- image2sketch
- image2sketch_network

# How to Run

`docker-compose up --build`

## How to Run single Container

```bash
Run Docker Container:
- docker build -t img2sketch .
- docker run --gpus all -p 5000:5000 -it img2sketch
```