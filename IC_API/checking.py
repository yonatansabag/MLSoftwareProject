# import requests
# import time
# from celery.result import AsyncResult
# from app import celery

# url = 'http://127.0.0.1:5000/classify'
# files = {'image': open('C:/Users/yonat/OneDrive - Technion/Desktop/temp/uploads/flag.png', 'rb')}
# response = requests.post(url, files=files)
# print(response.json())

from app import celery

@celery.task
def simple_task():
    return 'Task completed successfully'

# Run the simple task
result = celery.send_task('tasks.simple_task')
print(result.status)
print(result.result)  # Check if it completes successfully

