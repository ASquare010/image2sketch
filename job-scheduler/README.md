# What is Image to Sketch job-scheduler

    Job-scheduler provides queue for image2sketch service

# Dependent services

**This must be in docker-compose.yml other can be commented out**

- image2sketch
- image2sketch_network

# How to Run

`docker-compose up --build`

# How to use job-scheduler with Postman

- Run UI at `http//:localhost:5050`
- Use the endpoint `http://localhost:5050/generate_sketch` using `POST` method to submit the job
  - Request: `{ "imageUrl": "https://example.com/image.jpg" }`
  - Response: `{"uuid": "uuid", "message": "Message"}`
- Use the endpoint `http://localhost:5050/get_results` using `POST` method to get the results
  - Request: `{ "uuid": "uuid" }`
  - Response: `{"status": "status", "result": {"ZipFileUrl": "SomeURl"}}`

# To check check the status of the Image to Sketch

- Use the endpoint `http://localhost:5050/` using `GET` method
  - Response {"status": "success", "flask_response": response.text,"flask_status_code": response.status_code}