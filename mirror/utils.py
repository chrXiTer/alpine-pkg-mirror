
import urllib.request

def get_file(url, filename, timeout=60):
    opener = urllib.request.build_opener(urllib.request.HTTPHandler)
    request = urllib.request.Request(url)
    request.get_method = lambda: 'GET'
    try:
        response = opener.open(request, timeout=timeout)
        if response.code == 200:
            with open(filename, 'wb') as target:
                while True:
                    data = response.read(64000)
                    if not data:
                        break
                    target.write(data)

    except urllib.request.HTTPError as err:
        print({
                "code": err.getcode(),
                "error_msg": err.msg,
                "headers": dict(err.headers.items()),
                "body": '\n'.join(err.readlines())
        })
