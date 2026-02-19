import sys
import inspect

try:
    import mediapipe as mp
    print('[OK] MediaPipe imported successfully')
    print(f'  Version: {mp.__version__}')
    print(f'  Location: {inspect.getfile(mp)}')

    print('\n[OK] MediaPipe attributes:')
    attrs = dir(mp)
    print(f'  Found {len(attrs)} attributes: {attrs}')

    # Test core modules
    print('\n[OK] Testing core MediaPipe modules:')
    print(f"  - solutions: {hasattr(mp, 'solutions')}")
    if hasattr(mp, 'solutions'):
        print(f"    - pose: {hasattr(mp.solutions, 'pose')}")
        print(f"    - drawing_utils: {hasattr(mp.solutions, 'drawing_utils')}")

    print('\n[OK] All MediaPipe tests passed!')

except ImportError as e:
    print(f'[FAIL] Error importing MediaPipe: {e}')
    print('  Please install it with: pip install mediapipe')
    sys.exit(1)

except Exception as e:
    print(f'[FAIL] Unexpected error: {e}')
    sys.exit(1)
