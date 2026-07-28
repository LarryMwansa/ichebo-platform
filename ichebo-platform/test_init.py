import requests

session = requests.Session()
response = session.get('http://localhost:8000/accounts/login/')
csrf_token = session.cookies.get('csrftoken')

login_data = {
    'login': 'architect@ics.test',
    'password': 'Architect123!',
    'csrfmiddlewaretoken': csrf_token,
}
session.post('http://localhost:8000/accounts/login/', data=login_data, headers={'Referer': 'http://localhost:8000/accounts/login/'})

req_body = {
    'title': 'Test Video',
    'filename': 'test.mp4',
    'file_size_bytes': 1024,
    'content_type': 'video/mp4',
    'tenant_id': '06467f45c13641f8be4e132943503fef'
}
res = session.post('http://localhost:8000/api/media/upload/init/', json=req_body, headers={'X-CSRFToken': csrf_token, 'Referer': 'http://localhost:8000/channel/'})
print(res.status_code)
print(res.text)
