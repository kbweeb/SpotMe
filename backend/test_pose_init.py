import traceback
import pose

try:
    p = pose.PoseDetector()
    print('backend', getattr(p, 'backend', None))
except Exception:
    traceback.print_exc()
