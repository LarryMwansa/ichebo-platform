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

res = session.get('http://localhost:8000/channel/?view=library&tenant_id=374509f0-a655-488d-a817-334668ae5609')
if 'video-upload-file-library-direct' in res.text:
    print("Found video-upload-file-library-direct!")
else:
    print("NOT FOUND: video-upload-file-library-direct")

if 'IcheboVideoUpload.init(\'-library-direct\')' in res.text:
    print("Found init script!")
else:
    print("NOT FOUND: init script")

if 'ichebo_video_uploader.js' in res.text:
    print("Found JS include!")
else:
    print("NOT FOUND: JS include")
