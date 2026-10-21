import os, runpy
base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "parcial2")
os.chdir(base)
runpy.run_path(os.path.join(base, "app.py"), run_name="__main__")
