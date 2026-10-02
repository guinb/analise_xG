from curl_cffi import requests

url = "https://api.sofascore.com/api/v1/team/1963"
print(f"Testing {url} with curl_cffi impersonate='chrome124'...")

r = requests.get(url, impersonate="chrome124")
print(f"Status: {r.status_code}")
if r.status_code == 200:
    team = r.json().get("team", {})
    print(f"Success! Team: {team.get('name')} (Country: {team.get('country', {}).get('name')})")
else:
    print(f"Response: {r.text[:200]}")
