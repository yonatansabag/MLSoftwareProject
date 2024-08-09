import requests

# request_id = '521761'  # Replace with the request ID obtained from the /classify response
# url = 'http://127.0.0.1:5000/get_res'
# response = requests.post(url, json={'req_id': request_id})
# print(response.json())


from celery.result import AsyncResult

result = AsyncResult('872842')
print(result.status)
print(result.result)
