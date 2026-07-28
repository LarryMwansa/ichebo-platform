import requests

session = requests.Session()
response = session.get('http://localhost:8000/accounts/login/')
csrf_token = session.cookies.get('csrftoken')

login_data = {
    'login': 'architect@ics.test',
    'password': 'Architect123!',
    'csrfmiddlewaretoken': csrf_token,
}
res_login = session.post('http://localhost:8000/accounts/login/', data=login_data, headers={'Referer': 'http://localhost:8000/accounts/login/'})

res_target = session.get('http://localhost:8000/channel/')
print("Status:", res_target.status_code)
if res_target.status_code == 500:
    import re
    # Extract the traceback from the Django debug page
    match = re.search(r'<textarea id="traceback_area" .*?>(.*?)</textarea>', res_target.text, re.DOTALL)
    if match:
        print(match.group(1).strip())
    else:
        # Just print the head of the exception title
        match_title = re.search(r'<h1>([^<]+)</h1>', res_target.text)
        if match_title:
            print("Exception:", match_title.group(1))
            match_exc = re.search(r'<pre class="exception_value">([^<]+)</pre>', res_target.text)
            if match_exc:
                print("Value:", match_exc.group(1))
