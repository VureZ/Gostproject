import sys, os
d = os.path.dirname(sys.executable)
print("Python dir:", d)
for f in os.listdir(d):
    if 'python' in f.lower():
        print(f"  {f}")
