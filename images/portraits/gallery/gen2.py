import requests, json, time, os
API_KEY = os.environ.get('LEONARDO_API_KEY')
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
MODEL_ID = "de7d3faf-762f-48e0-b3b7-9d0ac3a3fcf3"

breeds = [
    {"name": "golden-retriever", "prompt": "An expressive oil painting of a Golden Retriever with visible painterly brushstrokes and rich impasto texture. Warm earth tones with bold pops of crimson. Gallery-quality canvas texture, museum lighting, Renaissance-inspired fine art."},
    {"name": "french-bulldog", "prompt": "An expressive oil painting of a French Bulldog with visible painterly brushstrokes and rich impasto texture. Warm earth tones with bold pops of teal. Gallery-quality canvas texture, museum lighting, Renaissance-inspired fine art."},
    {"name": "maine-coon", "prompt": "An expressive oil painting of a majestic Maine Coon cat with visible painterly brushstrokes. Warm earth tones with bold pops of emerald. Gallery-quality canvas texture, museum lighting, Renaissance-inspired fine art."},
]

for i, breed in enumerate(breeds):
    print(f"[{i+1}] {breed['name']}...", end=" ", flush=True)
    payload = {
        "modelId": MODEL_ID,
        "prompt": breed["prompt"],
        "num_images": 1,
        "width": 1024,
        "height": 1024,
        "presetStyle": "DYNAMIC"
    }
    try:
        resp = requests.post("https://cloud.leonardo.ai/api/rest/v1/generations", headers=HEADERS, json=payload, timeout=30)
        data = resp.json()
        if "sdGenerationJob" in data:
            job_id = data["sdGenerationJob"]["generationId"]
            for _ in range(30):
                time.sleep(4)
                check = requests.get(f"https://cloud.leonardo.ai/api/rest/v1/generations/{job_id}", headers=HEADERS, timeout=15)
                check_data = check.json()
                if "generations_by_pk" in check_data:
                    gen = check_data["generations_by_pk"]
                    if gen.get("status") == "COMPLETE":
                        images = gen.get("generated_images", [])
                        if images and images[0].get("url"):
                            img_resp = requests.get(images[0]["url"], timeout=30)
                            if img_resp.status_code == 200:
                                with open(f"{breed['name']}-v2.jpg", "wb") as f:
                                    f.write(img_resp.content)
                                print(f"✅ {len(img_resp.content)//1024}KB")
                                break
                        print("❌ No images")
                        break
                    elif gen.get("status") == "FAILED":
                        print("❌ Failed")
                        break
            else:
                print("⏱️ Timeout")
        else:
            print(f"❌ No job: {json.dumps(data)[:100]}")
    except Exception as e:
        print(f"❌ {e}")
    time.sleep(3)
print("Done")
