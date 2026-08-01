import httpx

url = "https://smart-loading-backend.onrender.com/api/v1/plans"
headers = {"X-API-KEY": "unikl_demo_secret_2026"}

response = httpx.get(url, headers=headers)
plans = response.json()
if plans:
    plan_id = plans[0]['id']
    steps_url = f"{url}/{plan_id}/steps"
    steps_res = httpx.get(steps_url, headers=headers)
    print("Steps:", steps_res.text)
