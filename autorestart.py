import subprocess
import time

CMD = [
    "python", "c:/tools/vxpcsys/main.py", "--cfg", "c:/tools/vxpcsys/cfg.json"
]
RELAX_TIME_S = 10

if __name__ == "__main__":
    while True:
        p = None
        try:
            p = subprocess.Popen(CMD)
        except:
            time.sleep(RELAX_TIME_S)

        if p is not None:
            while True:
                p.poll()
                if p.returncode is not None:
                    break
                time.sleep(RELAX_TIME_S)
