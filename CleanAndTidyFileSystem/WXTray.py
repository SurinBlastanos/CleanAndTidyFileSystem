import wx.adv
import wx
import os, time, ctypes, threading
from selenium import webdriver
TRAY_TOOLTIP = 'Name' 
TRAY_ICON = 'icon.png' 


def create_menu_item(menu, label, func):
    item = wx.MenuItem(menu, -1, label)
    menu.Bind(wx.EVT_MENU, func, id=item.GetId())
    menu.Append(item)
    return item

class OtherFrame(wx.Frame): # This class inherits from the wx.Frame class
    def __init__(self, title, parent=None):
        wx.Frame.__init__(self, parent=parent, title=title)
        self.Show()

class TaskBarIcon(wx.adv.TaskBarIcon):
    def __init__(self, frame): 
        self.frame = frame 
        super(TaskBarIcon, self).__init__()  
        self.set_icon(TRAY_ICON) 
        self.Bind(wx.adv.EVT_TASKBAR_LEFT_DOWN, self.on_left_down) 
        self.frame_number = 0

    def CreatePopupMenu(self):
        menu = wx.Menu()
        create_menu_item(menu, 'Maximise', self.on_hello)
        menu.AppendSeparator()
        create_menu_item(menu, 'Minimise', self.on_min)
        menu.AppendSeparator()
        create_menu_item(menu, 'Exit', self.on_exit)
        return menu

    def on_min(self, event):
        driver.set_window_position(1000,1000)

    def set_icon(self, path):
        icon = wx.Icon(path)
        self.SetIcon(icon, TRAY_TOOLTIP)

    def on_left_down(self, event):      
        print ('Tray icon was left-clicked.')

    def on_hello(self, event):
        driver.set_window_position(0,0)

    def on_exit(self, event):
        wx.CallAfter(self.Destroy)
        self.frame.Destroy()

class App(wx.App):
    def OnInit(self):
        frame=wx.Frame(None)
        self.SetTopWindow(frame)
        TaskBarIcon(frame)
        return True

def main():
    app = App(False)
    app.MainLoop()

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()  # Returns true if the program has administrator access
    except:
        return False

def startScanner():
    os.system('python scanner.py')


if __name__ == '__main__':
    if is_admin():
        print("hello")
    else:
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    x = threading.Thread(target=startScanner, args=())
    x.start()
    time.sleep(10)
    driver = webdriver.Edge('msedgedriver.exe')
    driver.get('http://localhost:8000/main.html')
    main()
