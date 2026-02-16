import os
import urllib.request
import urllib.error
import ssl

# Disable SSL verification
ssl._create_default_https_context = ssl._create_unverified_context

model_path = "pose_landmarker_lite.task"
model_urls = [
    "https://storage.googleapis.com/mediapipe-tasks/python/pose_landmarker/lite/pose_landmarker_lite.task",
    "https://storage.googleapis.com/mediapipe-tasks/video_landmarker/pose_landmarker_lite.task",
    "https://storage.googleapis.com/mediapipe-assets/pose_landmarker_lite.task",
]

print("Attempting to download MediaPipe pose model...")
for url in model_urls:
    try:
        print(f"\nTrying: {url}")
        response = urllib.request.urlopen(url, timeout=10)
        size = int(response.headers.get('Content-Length', 0))
        print(f"  Content-Length: {size}")
        
        with open(model_path, 'wb') as f:
            chunk_size = 8192
            downloaded = 0
            while True:
                chunk = response.read(chunk_size)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                print(f"  Downloaded: {downloaded}/{size} bytes", end='\r')
        
        final_size = os.path.getsize(model_path)
        print(f"\n✓ Model saved! Size: {final_size} bytes")
        break
    except Exception as e:
        print(f"  ✗ Failed: {e}")
else:
    print("\n✗ Could not download model")
