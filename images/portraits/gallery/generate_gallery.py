import requests
import json
import time
import os

API_KEY = os.environ.get('LEONARDO_API_KEY')
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

# Phoenix 1.0 model
MODEL_ID = "de7d3faf-762f-48e0-b3b7-9d0ac3a3fcf3"

breeds = [
    {
        "name": "golden-retriever",
        "prompt": "An expressive oil painting of a Golden Retriever with visible painterly brushstrokes and rich impasto texture. Warm earth tones — burnt sienna, ochre, deep umber — with bold pops of crimson and ultramarine. Loose, expressive brushwork in the style of modern impressionist digital painting. Gallery-quality canvas texture, museum lighting, intimate portrait composition. Renaissance-inspired, highly detailed, professional fine art."
    },
    {
        "name": "french-bulldog", 
        "prompt": "An expressive oil painting of a French Bulldog with visible painterly brushstrokes and rich impasto texture. Warm earth tones — burnt sienna, ochre, deep umber — with bold pops of teal and violet. Loose, expressive brushwork in the style of modern impressionist digital painting. Gallery-quality canvas texture, museum lighting, intimate portrait composition. Renaissance-inspired, highly detailed, professional fine art."
    },
    {
        "name": "maine-coon",
        "prompt": "An expressive oil painting of a majestic Maine Coon cat with visible painterly brushstrokes and rich impasto texture. Warm earth tones — burnt sienna, ochre, deep umber — with bold pops of emerald and gold. Loose, expressive brushwork in the style of modern impressionist digital painting. Gallery-quality canvas texture, museum lighting, intimate portrait composition. Renaissance-inspired, highly detailed, professional fine art."
    },
    {
        "name": "german-shepherd",
        "prompt": "An expressive oil painting of a German Shepherd with visible painterly brushstrokes and rich impasto texture. Warm earth tones — burnt sienna, ochre, deep umber — with bold pops of sapphire and amber. Loose, expressive brushwork in the style of modern impressionist digital painting. Gallery-quality canvas texture, museum lighting, intimate portrait composition. Renaissance-inspired, highly detailed, professional fine art."
    },
    {
        "name": "siamese-cat",
        "prompt": "An expressive oil painting of a Siamese cat with visible painterly brushstrokes and rich impasto texture. Warm earth tones — burnt sienna, ochre, deep umber — with bold pops of ruby and cream. Loose, expressive brushwork in the style of modern impressionist digital painting. Gallery-quality canvas texture, museum lighting, intimate portrait composition. Renaissance-inspired, highly detailed, professional fine art."
    },
    {
        "name": "labrador",
        "prompt": "An expressive oil painting of a Chocolate Labrador with visible painterly brushstrokes and rich impasto texture. Warm earth tones — burnt sienna, ochre, deep umber — with bold pops of copper and jade. Loose, expressive brushwork in the style of modern impressionist digital painting. Gallery-quality canvas texture, museum lighting, intimate portrait composition. Renaissance-inspired, highly detailed, professional fine art."
    }
]

print(f"Generating {len(breeds)} portraits with Phoenix 1.0...")
print(f"Using API key: {API_KEY[:8]}...")
print()

for i, breed in enumerate(breeds):
    print(f"[{i+1}/{len(breeds)}] Generating {breed['name']}...", end=" ", flush=True)
    
    payload = {
        "modelId": MODEL_ID,
        "prompt": breed["prompt"],
        "num_images": 1,
        "width": 1024,
        "height": 1024,
        "presetStyle": "PHOTOGRAPHY",
        "photoReal": True,
        "photoRealVersion": "v2"
    }
    
    try:
        resp = requests.post(
            "https://cloud.leonardo.ai/api/rest/v1/generations",
            headers=HEADERS,
            json=payload,
            timeout=30
        )
        data = resp.json()
        
        if "sdGenerationJob" in data:
            job_id = data["sdGenerationJob"]["generationId"]
            print(f"Job: {job_id}")
            
            # Poll for completion
            for attempt in range(30):
                time.sleep(3)
                check = requests.get(
                    f"https://cloud.leonardo.ai/api/rest/v1/generations/{job_id}",
                    headers=HEADERS,
                    timeout=15
                )
                check_data = check.json()
                
                if "generations_by_pk" in check_data:
                    gen = check_data["generations_by_pk"]
                    status = gen.get("status", "unknown")
                    
                    if status == "COMPLETE":
                        images = gen.get("generated_images", [])
                        if images:
                            img_url = images[0].get("url")
                            if img_url:
                                img_resp = requests.get(img_url, timeout=30)
                                if img_resp.status_code == 200:
                                    with open(f"{breed['name']}.jpg", "wb") as f:
                                        f.write(img_resp.content)
                                    print(f" ✅ Saved ({len(img_resp.content)//1024}KB)")
                                else:
                                    print(f" ❌ Download failed: {img_resp.status_code}")
                            break
                        else:
                            print(f" ❌ No images in response")
                            break
                    elif status == "FAILED":
                        print(f" ❌ Generation failed")
                        break
                else:
                    print(f" ❌ Invalid poll response")
                    break
            else:
                print(f" ⏱️ Timeout")
        else:
            print(f" ❌ No job created: {json.dumps(data)[:200]}")
    except Exception as e:
        print(f" ❌ Error: {e}")
    
    if i < len(breeds) - 1:
        time.sleep(5)

print()
print("Done! Listing generated files:")
for f in os.listdir("."):
    if f.endswith(".jpg"):
        size = os.path.getsize(f) // 1024
        print(f"  {f} ({size}KB)")
