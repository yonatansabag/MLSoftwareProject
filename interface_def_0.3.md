# Interface between client and the PictureServer

| Version | Date       | Author | Description   |
|---------|------------|--------|---------------|
| v0.0    | 2024-03-17 | Noam Cohen | Initial draft |
| v0.1    | 2024-06-06 | Noam Cohen | minor protocol changes|
| v0.11   | 2024-06-23 | Noam Cohen | replace 'pending' ->'running' |
| v0.12   | 2024-07-02 | Noam Cohen | add error response |
| v0.2    | 2024-07-02 | Noam Cohen | update login/logout requirements |
| v0.21   | 2024-07-07 | Noam Cohen | * remove https requirement * allow redirect |
| v0.3    | 2024-07-14 | Noam Cohen | Make it pure API, without login |

<hr>

**NOTE:** This Markdown file is best viewed with VisualStudio code (press CTRL shift v)

This document defines the wire protocol between an http client and the server in the project.

The words 'MUST', 'SHALL', 'SHOULD' are as defined in [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119)

The set of commands supported by the server may increase over time.

**[NEW 0.3]** The server has an API VERSION. The current version is 2. This value MUST be returned in the /status endpoint.

In API VERSION 2, the server SHALL use http scheme.<br>


see [REST API](https://stackoverflow.blog/2020/03/02/best-practices-for-rest-api-design/)<br>
see [Idempotent commands](https://restfulapi.net/idempotent-rest-apis/)

## Command format

When sending file (the image file for example), use FormData. Otherwise, use json


### Server response
**[NEW 0.3]** The server SHALL respond with json body.

 - server SHALL have Content-Type=application/json
 - Response of the server SHALL have a json body. If the response is error, the body SHALL be:
  ```
{'error': {'code': number, 'message': 'some message'}
}
```



### Response codes
The response codes SHALL be standard HTTP status codes. <br>
Each command specifies the possible status codes.

# Command list 

## Upload image file to inference engine

**[NEW 0.3]** This endpoint is for uploading an image and waiting until a response is ready.
See also "/async_upload" for async variant.

Endpoint: POST /upload_image  formdata<br>

Content-Disposition: form-data; name="image"; filename="somepic.png"
Content-Type: image/png    or image/jpeg

Supported image types SHALL be at least PNG and JPEG. 

If a file is not recognized, the server SHALL return code 400.

The server SHALL respond synchronously, returning code 200.

Response: 200, 400

if 200: { 'matches': [ {'name': string, 'score': number}]}

The 'score' represents the confidence in this match. Number SHOULD be  0.0 \< score\<= 1.0

*example* 
```
{'matches': [{'name': 'tomato', 'score': 0.9}, {'name':'carrot', 'score': 0.02}]}
```


## Upload image file to inference engine (async version)

**[NEW 0.3]** This endpoint is for uploading an image and returning immediately.
See also "/upload_image" for sync variant.

In order to check if a result is ready, client will call GET /result/<req_id>

Endpoint: POST /async_upload  formdata<br>

Content-Disposition: form-data; name="image"; filename="somepic.png"<br>
Content-Type: image/png    or image/jpeg

Supported image types SHALL be at least PNG and JPEG.

*If a file is not recognized, the server SHALL return code 400*

The server SHALL respond without waiting for execution of the job, returning 202 and a request-id.

The request_id is random integer between 10000 and 1000000

Response: 202, 400

if 202: {'request_id': i32 } <br>


# Get result from server
Endpoint: GET /result/\<request-id\> <br>


Response: 200, 404

if 404: ID not found<br>
if 200: 
```
{ 'status': 'completed' | 'running' | 'error',

if operation running, the status is the only field in the response.

if operation succeeded:
'matches': [ {'name': string, 'score': number}...]
if operation errored:
'error': {'code': number, 'message': string}
}
```

This endpoint does not change the server state. 
status is **running** if the job runs now, or is still enqueued. 

*NOTE:* The server return 200 even when the job failed since the *GET /result/* succeeds



## Get server status
Endpoint: GET /status <br>


Response: 200
```
{'status':
  {
    'uptime': number /* seconds */,
    'processed:{
          'success': number,
          'fail': number,
          'running': number,
          'queued': number
    },
    'health': 'ok' |'error',
    'api_version': number
  }
}
```
**uptime** is the numbers of seconds since the server started. <br>
The uptime value is in fractional seconds, e.g. 55.6

**success** is the number of jobs completed successfully<br>
**fail** is the number of jobs completed with some error <br>
**running** is the number of jobs currently running<br>
**queued** is the number of jobs waiting to run. Use 0 (zero) if a queue is not implemented.

<hr>

**Informative note**: In this version of the API, there is no authentication. The reason for this is that The API is implemented by a server in internal network. It will receive only already-authenticated requests, meaning that another server has to take care of the authentication(if there is one) before accessing this API.

