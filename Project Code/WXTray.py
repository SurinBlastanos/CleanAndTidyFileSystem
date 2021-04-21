import wx.adv  # Used for system tray application
import wx  # Used to create UI in python
import os, time, ctypes, threading, sys  # os:run other python program time:sleeps the program ctypes:admin access threading:thread tasks sys: admin access
from selenium import webdriver  # Used to control the web browser
TRAY_TOOLTIP = 'Name'   # Name of the tray app
TRAY_ICON = 'icon.png'  # Path of the icon image


'''This functions creates a menu item that gets added to the tray app's menu
menu: menu object
label: what the menu item will say
func: the function that the menu option will execute'''
def create_menu_item(menu, label, func):
    item = wx.MenuItem(menu, -1, label)  # Setting the ID of the MenuItem to -1 tells wx to dynamically assign the best ID
    menu.Bind(wx.EVT_MENU, func, id=item.GetId())  # EVT_MENU is the event trigger for the function
    menu.Append(item)  # Adds the item to the menu
    return item


'''This class creates the taskbar app that we use to control the python Eel UI. It is a subclass of the base
TaskBarIcon class'''
class TaskBarIcon(wx.adv.TaskBarIcon):
    def __init__(self, frame): 
        self.frame = frame  # The frame is the window the taskbar icon is assigned to
        super(TaskBarIcon, self).__init__()  
        self.set_icon(TRAY_ICON)  # This sets the icon image
        self.Bind(wx.adv.EVT_TASKBAR_LEFT_DOWN, self.on_left_down)
        self.frame_number = 0

    '''This function creates the popup menu that appears then the icon is right clicked'''
    def CreatePopupMenu(self):
        menu = wx.Menu()
        create_menu_item(menu, 'Maximise', self.on_max)  # Creates a menu item and binds the on_max() method to
        menu.AppendSeparator()  # A line that makes the menu look better
        create_menu_item(menu, 'Minimise', self.on_min)
        menu.AppendSeparator()
        create_menu_item(menu, 'Exit', self.on_exit)
        return menu

    def on_left_down(self):
        print("Left click")
    '''You cannot properly hide an open web browser, so instead, this method pushes the window position out of
    the user's view when minimise is selected'''
    def on_min(self, event):
        driver.set_window_position(1000,1000)

    '''This method sets the icon image for the system tray app'''
    def set_icon(self, path):
        icon = wx.Icon(path)
        self.SetIcon(icon, TRAY_TOOLTIP)

    '''When the maximise button is pressed, this method returns the window position to a place where the user can
    see it'''
    def on_max(self, event):
        driver.set_window_position(0,0)

    '''When exit is clicked, this method destroys the system tray application'''
    def on_exit(self, event):
        wx.CallAfter(self.Destroy)
        self.frame.Destroy()


'''The base class for all wx applications'''
class App(wx.App):
    def OnInit(self):
        frame=wx.Frame(None)  # None means that there is no parent frame for this frame
        self.SetTopWindow(frame)  # Specifies this as the main window
        TaskBarIcon(frame)  # Creates the taskbar app
        return True

def main():
    app = App(False)  # False means that output isn't redirected by the app
    app.MainLoop()  # Starts the application

'''This function is used to ensure that the program runs with administrator permissions'''
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()  # Returns true if the program has administrator access
    except:
        return False

'''this function starts the scanner program that controls scanners and the web UI'''
def startScanner():
    os.system('python scanner.py')


if __name__ == '__main__':  # This only runs if this program is run directly
    if is_admin():
        print("Program is running")
    else:
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)  # Asks the user to give the program admin access
    x = threading.Thread(target=startScanner, args=())
    x.start()  # This is started in a thread because it is event-driven with no set termination, and we still need to run code in this program
    time.sleep(10)  # Gives the scanner program time to start the web UI
    driver = webdriver.Edge('msedgedriver.exe')  # Opens a browser tab that the program can control
    driver.get('http://localhost:8000/main.html')  # Navigates the browser tab to the web UI page
    main()  # Starts the system tray app
