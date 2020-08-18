import subprocess
import time
import pyautogui
from datetime import datetime

print(datetime.now())
subprocess.Popen('C:\\Jts\\tws.exe')

#Wait for App to open
time.sleep(10)
print("10 secs passed")

pyautogui.typewrite('esond9648')
pyautogui.press('tab')
pyautogui.write('Ep2LatRl1Interactive')
time.sleep(3)
pyautogui.press('enter')
time.sleep(60)
pyautogui.press('enter')
