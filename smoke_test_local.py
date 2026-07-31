import subprocess
import glob
import os

failed = []
files = glob.glob("*/src/pardus_*.py")
for f in files:
    print(f"Testing {f}...")
    env = os.environ.copy()
    env["QT_QPA_PLATFORM"] = "offscreen"
    try:
        # Run the app with timeout 5s
        subprocess.run(["py", f], env=env, timeout=5, check=True)
    except subprocess.TimeoutExpired:
        print(f"  OK (timeout 5s reached)")
    except subprocess.CalledProcessError as e:
        print(f"  FAILED with exit code {e.returncode}")
        failed.append(f)
    except Exception as e:
        print(f"  FAILED: {e}")
        failed.append(f)

if failed:
    print(f"\nFailed files: {failed}")
else:
    print("\nAll files passed GUI smoke test.")
