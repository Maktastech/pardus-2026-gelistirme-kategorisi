import urllib.request, json

try:
    req = urllib.request.Request('https://api.github.com/repos/Maktastech/pardus-2026-gelistirme-kategorisi/actions/runs', headers={'User-Agent': 'Mozilla/5.0'})
    res = urllib.request.urlopen(req)
    data = json.loads(res.read())
    run = data['workflow_runs'][0]
    
    jobs_url = run['jobs_url']
    req_jobs = urllib.request.Request(jobs_url, headers={'User-Agent': 'Mozilla/5.0'})
    res_jobs = urllib.request.urlopen(req_jobs)
    data_jobs = json.loads(res_jobs.read())
    for job in data_jobs['jobs']:
        if job['conclusion'] == 'failure':
            job_id = job['id']
            print(f"Failed job ID: {job_id}")
            log_url = f"https://api.github.com/repos/Maktastech/pardus-2026-gelistirme-kategorisi/actions/jobs/{job_id}/logs"
            print(f"Fetching log from: {log_url}")
            try:
                req_log = urllib.request.Request(log_url, headers={'User-Agent': 'Mozilla/5.0'})
                res_log = urllib.request.urlopen(req_log)
                print(res_log.read().decode('utf-8'))
            except Exception as e:
                print(f"Error fetching job log: {e}")
except Exception as e:
    print(f"Error: {e}")
