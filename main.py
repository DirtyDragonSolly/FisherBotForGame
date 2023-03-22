import datetime
import random
import cv2
import pytesseract
import pyautogui
import time
import keyboard
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from cpuinfo import get_cpu_info
from urllib.request import urlopen
from screeninfo import get_monitors
import multiprocessing


class Controller:
    is_fishing: bool
    is_hooking: bool
    is_pulling: bool
    is_waiting: bool
    screenX: int
    screenY: int

    @classmethod
    def __init__(self):
        print('Controller was created.')
        self.is_fishing = False
        self.is_waiting = False
        self.is_hooking = False
        self.is_pulling = False
        monitors = get_monitors()
        for monitor in monitors:
            if monitor.is_primary == True:
                self.screenX = monitor.width
                self.screenY = monitor.height

    def startFishing(self):
        self.is_fishing = True
        print('Bot started')

    def stopFishing(self):
        self.is_fishing = False
        print('Bot stopped')

    def startBot(self):
        while True:
            while self.is_fishing:
                print('Bot activated')
                time.sleep(random.randrange(200, 401, 1) / 100)
                keyboard.send(hotkey='e')
                self.is_waiting = True
                time.sleep(1)
                while self.is_waiting and self.is_fishing:
                    print('Waiting')
                    if checkState() == 2:
                        self.is_waiting = False
                        self.is_hooking = True
                        break
                fishing(self)
                x = checkState()
                if x == 3 or self.is_pulling:
                    startLongClick()
                    while self.is_fishing:
                        x = checkPullingState(self)
                        if x == 0:
                            continue
                        elif x == 1:
                            break
                    stopLongClick()
                    self.is_pulling = False
                else:
                    if x == 4 or x == 0:
                        continue


def startLongClick():
    pyautogui.mouseDown()


def stopLongClick():
    pyautogui.mouseUp()


def checkState():
    img = pyautogui.screenshot(region=(0, 0, 480, 60))
    img.save('state.png')
    img = cv2.imread('state.png')
    text = pytesseract.image_to_string(img, lang='rus')
    if 'ждите пока рыба' in text.lower():
        print(1)
        return 1
    elif 'что-то клюет' in text.lower():
        print(2)
        return 2
    elif 'рыба устала' in text.lower():
        print(3)
        return 3
    elif 'сорвалась' in text.lower():
        print(4)
        return 4
    else:
        print(0)
        return 0


def checkPullingState(controller: Controller):
    img = pyautogui.screenshot(region=(controller.screenX / 2 - 200, controller.screenY - 200, 400, 160))
    img.save('pullingState.png')
    img = cv2.imread('pullingState.png')
    text = pytesseract.image_to_string(img, lang='rus')
    if 'вылов' in text:
        return 1
    else:
        return 0


def fishing(controller: Controller):
    img_rgb = cv2.imread('fish.png')

    img_gray = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2GRAY)

    last_position = (controller.screenX / 2, controller.screenY / 2)
    while controller.is_hooking:
        x = checkState()
        if x == 4 or controller.is_fishing == False:
            controller.is_hooking = False
            keyboard.release('a')
            keyboard.release('d')
            break
        elif x == 3 or controller.is_fishing == False:
            keyboard.release('a')
            keyboard.release('d')
            controller.is_hooking = False
            controller.is_pulling = True
            break
        else:
            img = pyautogui.screenshot()
            img.save('searching.png')
            img_search = cv2.imread('searching.png')
            img_search_gray = cv2.cvtColor(img_search, cv2.COLOR_BGR2GRAY)

            res = cv2.matchTemplate(img_search_gray, img_gray, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

            top_left = max_loc
            print(f'x:{top_left[0]} last x:{last_position[0]}')

            if last_position[0] > top_left[0]:
                keyboard.release(hotkey='a')
                last_position = top_left
                print('Pressed D')
                keyboard.press(hotkey='d')
            elif last_position[0] < top_left[0]:
                keyboard.release(hotkey='d')
                last_position = top_left
                print('Pressed A')
                keyboard.press(hotkey='a')
            else:
                last_position = top_left
                print('Continued')
                continue


def getDateFromDict(dateDict: dict):
    date = datetime.date.today()
    date = date.replace(day=dateDict['Day'], month=dateDict['Month'], year=dateDict['Year'])
    return date


def getDateTimeNow():
    res = urlopen('http://just-the-time.appspot.com/')
    result = res.read().strip()
    result_str = result.decode('utf-8')
    date = datetime.date.today()
    date = date.replace(year=int(result_str[:4]), month=int(result_str[5:7]), day=int(result_str[8:10]))
    return date


print('App has started.')
cred = credentials.Certificate("autofishingbot-6bd22-firebase-adminsdk-qww3a-df3826922c.json")
default_app = firebase_admin.initialize_app(cred)

multiprocessing.freeze_support()

licKey = input()
print('Starting verification.')
urlTxt = "https://autofishingbot-6bd22-default-rtdb.europe-west1.firebasedatabase.app/"
cpuDict = []

for key, value in get_cpu_info().items():
    cpuDict.append([key, value])

if dict(db.reference(path='/', url=urlTxt).get()).get(licKey, None) == None:
    raise ValueError('You have no license. You can buy it from https://funpay.com/users/6962688/')
else:
    print('The license exists')
    key, value = 0, 1
    ref = db.reference(path=f'/{licKey}', url=urlTxt)

    if ref.get() == True:
        print('The device isn\'t linked')
        now = getDateTimeNow()
        cpuDict.append(['Expiration data', {'Year': now.year, 'Month': now.month + 1, 'Day': now.day}])
        ref.set(dict(cpuDict))
        print('Your device is linked')
    else:
        print('The device is linked')
        now = datetime.date.today()
        exDate = getDateFromDict(ref.get()['Expiration data'])
        for item in cpuDict:
            if ref.get()[item[key]] != item[value] or now >= exDate:
                raise ValueError('You have no license. You can buy it from https://funpay.com/users/6962688/')
    print('You have passed the verification')
    a = Controller()
    keyboard.add_hotkey('F4', lambda: a.startFishing())
    keyboard.add_hotkey('F5', lambda: a.stopFishing())
    a.startBot()
