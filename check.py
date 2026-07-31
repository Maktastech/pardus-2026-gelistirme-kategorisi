import urllib.request, json

try:
    req = urllib.request.Request('https://api.github.com/repos/Maktastech/pardus-2026-gelistirme-kategorisi/actions/runs', headers={'User-Agent': 'Mozilla/5.0'})
    res = urllib.request.urlopen(req)
    data = json.loads(res.read())
    run = data['workflow_runs'][0]
    
    print(f"Status: {run['status']}")
    print(f"Conclusion: {run['conclusion']}")
    print(f"URL: {run['html_url']}")
    
    jobs_url = run['jobs_url']
    req_jobs = urllib.request.Request(jobs_url, headers={'User-Agent': 'Mozilla/5.0'})
    res_jobs = urllib.request.urlopen(req_jobs)
    data_jobs = json.loads(res_jobs.read())
    for job in data_jobs['jobs']:
        print(f"Job: {job['name']} - Status: {job['status']} - Conclusion: {job['conclusion']}")
        if job['status'] == 'completed':
            for step in job['steps']:
                if step['conclusion'] == 'failure':
                    print(f"  Step failed: {step['name']}")
except Exception as e:
    print(f"Error: {e}")
