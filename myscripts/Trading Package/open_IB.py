import subprocess
import pyautogui
from datetime import datetime, time
import time as t
import threading

def background_calculation():
    # here goes some long calculation
	dt = datetime.now()
	ib_open_time = time(8,20)
	current_time = time(datetime.now().hour,datetime.now().minute)
	#target_time = datetime(2020, 7, 29, 18, 25, 00)
	target_time = time(ib_open_time.hour,ib_open_time.minute)
	
	hourmin = time(target_time.hour,target_time.minute)
	
	while current_time < hourmin or (current_time > time(15,0) and current_time <= time(23,59,59)):
		current_time = time(datetime.now().hour,datetime.now().minute,datetime.now().second)
		print(current_time)
		t.sleep(3)
	

	subprocess.Popen('C:\\Jts\\tws.exe')

	#Wait for App to open
	t.sleep(10)
	print("10 secs passed")

	pyautogui.typewrite('esond9648')
	pyautogui.press('tab')
	pyautogui.write('Ep2LatRl1Interactive')
	t.sleep(3)
	pyautogui.press('enter')
	t.sleep(60)
	pyautogui.press('enter')
	
	
def main():
    thread = threading.Thread(target=background_calculation)
    thread.start()

    # wait here for the result to be available before continuing
    thread.join()

if __name__ == '__main__':
    main()

