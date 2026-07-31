import urllib.request, json, zipfile, io

try:
    req = urllib.request.Request('https://api.github.com/repos/Maktastech/pardus-2026-gelistirme-kategorisi/actions/runs', headers={'User-Agent': 'Mozilla/5.0'})
    res = urllib.request.urlopen(req)
    data = json.loads(res.read())
    run = data['workflow_runs'][0]
    logs_url = run['logs_url']

    print(f"Downloading logs from: {logs_url}")
    req_logs = urllib.request.Request(logs_url, headers={'User-Agent': 'Mozilla/5.0'})
    res_logs = urllib.request.urlopen(req_logs)
    with zipfile.ZipFile(io.BytesIO(res_logs.read())) as z:
        for filename in z.namelist():
            if "Smoke" in filename:
                print(f"--- Log: {filename} ---")
                print(z.read(filename).decode('utf-8'))
except urllib.error.HTTPError as e:
    print(f"HTTPError: {e.code} {e.reason}")
except Exception as e:
    print(f"Error: {e}")
