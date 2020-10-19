#!/usr/bin/python3

# The code for changing pages was derived from: http://stackoverflow.com/questions/7546050/switch-between-two-frames-in-tkinter
# License: http://creativecommons.org/licenses/by-sa/3.0/   


'''
------Import necessary packages--------
'''
import tkinter as tk
from tkinter import ttk
from tkinter import *
from tkinter import messagebox
import traceback
import cv2
from PIL import ImageTk,Image
from password_keypad import NumPad
from normal_keypad import KeyPad
import RPi.GPIO as GPIO
import time
import Scale_Final
import Dimension_V1
#import Length_Width
import Scale_Final_Reset
import time
from multiprocessing import Process, Queue
#import ColorTest
#from ColorTest import *
'''
---------------Initiate LED lights and GPIO pins--------------
'''

#Open folders the contain initial light setting
g = open("Green_Light", 'r')
green = g.read()
g.close()

b = open("Blue_Light", 'r')
blue = b.read()
b.close()

w = open("White_Light", 'r')
white = w.read()
w.close()

r = open("Red_Light", 'r')
red = r.read()
r.close()

left = open("Left_Light", 'r')
left_val = left.read()
left.close()

right = open("Right_Light", 'r')
right_val = right.read()
right.close()

# Configure the Pi to use the BCM (Broadcom) pin names, rather than the pin positions
GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.OUT)
GPIO.setup(18, GPIO.OUT)
GPIO.setup(27, GPIO.OUT)
GPIO.setup(22, GPIO.OUT)
GPIO.setup(23, GPIO.OUT)
GPIO.setup(24, GPIO.OUT)
GPIO.setup(12, GPIO.OUT)

global WEIGHT
# Start Pulse Width Modulation (PWM) on the red, green and blue channels to 
# control the brightness of the LEDs.
# Follow this link for more info on PWM: http://en.wikipedia.org/wiki/Pulse-width_modulation
pwmRed = GPIO.PWM(17, 500)
pwmRed.start(0)

pwmGreen = GPIO.PWM(18, 500)
pwmGreen.start(0)

pwmBlue = GPIO.PWM(27, 500)
pwmBlue.start(0)

pwmWhite = GPIO.PWM(22, 500)
pwmWhite.start(0)

LeftRing = GPIO.PWM(23, 500)
LeftRing.start(int(left_val))

RightRing = GPIO.PWM(24, 500)
RightRing.start(int(right_val))

GPIO.output( 12 , 0)

global Measurment

m = open("Measurment_Standard", 'r')
Measurment = m.read()
m.close()


'''
--------Initiate GUI, this class creates tkinter frames to be switched between-----
'''
class Photobooth(tk.Tk):

    def __init__(self, *args, **kwargs):
        
        tk.Tk.__init__(self, className = 'Photobooth', *args, **kwargs)

        '''
        ----Initiate size of application, will automatically fill space of screen
        '''
        self.attributes('-fullscreen', True)
        #w, h = self.winfo_screenwidth(), self.winfo_screenheight()
        #w = 800 #image.width()
        #h = 580#image.height()
        #self.geometry("%dx%d+0+0" % (w, h))

        self.page = None
        
        #initiate 'container' which will 
        self.container = tk.Frame(self)
        
        '''create Menu bar'''
        menu = Menu(self)
        self.config(menu=menu)
        file = Menu(menu)
        file.add_command(label = 'Exit', command = self.exit_app)
        #file.add_command(label = 'Christmas', command = lambda: self.show_frame(idle_mode))
        menu.add_cascade(label='File', menu = file)

        self.container.pack(side="top", fill="both", expand = True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)
        
        self.weight_job = None
        self.job = None 
        self.red = 1
        self.count = 0
        
        self.idle = self.after(60 * 1000 * 15, lambda: self.show_frame(idle_mode))
        
        self.frames = {}

        self.bind('<Button>', self.checkTopLevel)

        #create list of frames, each frame is a new 'Page' on the GUI
        for F in (Dimensions, MainMenu, Options, Scale_Setup, LedPage, idle_mode):

            frame = F(self.container, self)
            
            self.frames[F] = frame

            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(Dimensions)

    #Raise the current frame to display 'page'
    def show_frame(self, cont):

        frame = self.frames[cont]
        frame.tkraise()

        #On the "Dimensions" page, turn all the LED lights white
        if cont == Dimensions or cont == Options or cont == Scale_Setup:
            pwmRed.ChangeDutyCycle(0)
            pwmGreen.ChangeDutyCycle(0)
            pwmBlue.ChangeDutyCycle(0)
            pwmWhite.ChangeDutyCycle(100)
            LeftRing.ChangeDutyCycle(0)
            RightRing.ChangeDutyCycle(0)
            GPIO.output( 12 , 1)
#             if cont == Dimensions:
#                 self.show_weight()
            
        #Else return the LED lights to their proper color
        elif cont == MainMenu or cont == LedPage:
            #color.set(1)
            if self.job is not None:
                self.after_cancel(self.job)
                
            if self.weight_job is not None:
                self.after_cancel(self.weight_job)
            g = open("Green_Light", 'r')
            green = g.read()
            g.close()

            b = open("Blue_Light", 'r')
            blue = b.read()
            b.close()

            w = open("White_Light", 'r')
            white = w.read()
            w.close()

            r = open("Red_Light", 'r')
            red = r.read()
            r.close()            
            
            left = open("Left_Light", 'r')
            left_val = left.read()
            left.close()

            right = open("Right_Light", 'r')
            right_val = right.read()
            right.close()

            pwmRed.ChangeDutyCycle(int(red))
            pwmGreen.ChangeDutyCycle(int(green))
            pwmBlue.ChangeDutyCycle(int(blue))
            pwmWhite.ChangeDutyCycle(int(white))
            LeftRing.ChangeDutyCycle(int(left_val))
            RightRing.ChangeDutyCycle(int(right_val))
            
            GPIO.output( 12 , 0)
    
        elif cont == idle_mode:
            #ColorTest.change()
            pwmBlue.ChangeDutyCycle(0)
            pwmWhite.ChangeDutyCycle(0)
            pwmGreen.ChangeDutyCycle(0)
            pwmRed.ChangeDutyCycle(0)
            LeftRing.ChangeDutyCycle(0)
            RightRing.ChangeDutyCycle(0)
            #self.xmas_lights()

    def queue_display(self, Q):
        
        info = int(Scale_Final.get_weight2())
        Q.put(info)
    
    def show_weight(self):
        self.count+=1
        
        Q = Queue()
        display_weight = Process(target = self.queue_display, args = (Q, ))
        display_weight.start()
        display_weight.join()
        display_weight.terminate()
        WEIGHT.set(Q.get())
        #self.weight += 1

        self.weight_job = self.after(2000, self.show_weight)

    
    def xmas_lights(self):
        
        
        if self.red == 1:
            pwmRed.ChangeDutyCycle(100)
            pwmGreen.ChangeDutyCycle(0)
            #green = 1
            self.red = 0
            #time.sleep(2)
        elif self.red == 0:
            pwmGreen.ChangeDutyCycle(100)
            pwmRed.ChangeDutyCycle(0)
            self.red = 1
            #green = 0
            #time.sleep(2)
            
        self.job = self.after(2000, self.xmas_lights)
    
    '''
    -------Exit function in the menu bar, if password is entered program will end-----
    '''
    def exit_app(self):
        #If toplevel does not already exist make one
        if self.page == None or not tk.Toplevel.winfo_exists(self.page):
            self.page = Toplevel()
            self.numpad = NumPad(self.page)
            enter = tk.Button(self.page, text = "Enter/Exit", width =6, height=2, command = self.check)
            enter.place(rely=(5/6))
            self.page.attributes('-topmost', 'true')
            self.page.mainloop()
            
        #If toplevel already exists, detroy the old one and make a new one    
        elif tk.Toplevel.winfo_exists(self.page) == 1:
            self.page.destroy()
            self.page = Toplevel()
            self.numpad = NumPad(self.page)
            enter = tk.Button(self.page, text = "Enter/Exit", width =6, height=2, command = self.check)
            enter.place(rely=(5/6))
            self.page.attributes('-topmost', 'true')
            self.page.mainloop()

    #Check the password      
    def check(self):
        if self.numpad.password == '1234':
            if self.job is not None:
                self.after_cancel(self.job)
                
            if self.weight_job is not None:
                self.after_cancel(self.weight_job)
            exit()
        else:
            messagebox.showinfo('Password', "Wrong!")
            self.page.destroy()

    #If anywhere else on the page is touched, toplevel will destroy itself
    def checkTopLevel(self, event):
        self.after_cancel(self.idle)
        self.idle = self.after(60 *1000 * 15, lambda: self.show_frame(idle_mode))
        if event is not None:
            if self.page == None or not tk.Toplevel.winfo_exists(self.page):
                None
            elif tk.Toplevel.winfo_exists(self.page) == 1:
                self.page.destroy()

'''
---------This class contains the Dimensions Frame.----------
'''     
class Dimensions(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent, background = 'white')
#         print('self', self)
#         print('parent', parent)
#         print('controller ', controller)
#         print(self.__init__(parent, controller))
        '''
        -------Create all of the buttons and Labels-----
        '''
        logo = tk.PhotoImage(file="radwell.gif")
        BGlabel = tk.Label(self,image=logo,  borderwidth=0)
        BGlabel.image = logo
        BGlabel.place(x=0, y=0)
        
        self.button = tk.Button(self)
        self.button.place(relx=0.55, rely=0.1, relheight = .12)
        self.button.configure(text='''Photo Station''', font = 40)
        self.button.configure(command=lambda: controller.show_frame(MainMenu))

        self.add=None
        self.pic = None
        
        setting_pic = tk.PhotoImage(file="Preferences.gif")
        self.settings = tk.Button(self, image = setting_pic)
        self.settings.image = setting_pic
        self.settings.place(relx=0.9, rely=0.1, anchor = CENTER)
        self.settings.configure(command=lambda: controller.show_frame(Options))

        self.Reset = tk.Button(self)
        self.Reset.place(relx=0.05, rely=0.3)
        self.Reset.configure(font="TkTextFont")
        self.Reset.configure(text='''Clear''', font = 26)
        self.Reset.configure(command = self.Reset_Func)
     
        self.Measure = tk.Button(self)
        self.Measure.place(relx=0.9, rely=0.85, relwidth = .15, relheight = .2, anchor = CENTER)
        self.Measure.configure(font="TkTextFont")
        self.Measure.configure(text='''Measure''')
        self.Measure.configure(command=self.measure)

        self.Tare = tk.Button(self)
        self.Tare.place(relx=0.1, rely=0.85, relwidth = .165, relheight = .15, anchor = CENTER)
        self.Tare.configure(font="TkTextFont")
        self.Tare.configure(text='''Zero Weight & \nHeight Laser ''')
        self.Tare.configure(command=self.Zero)

        self.LENGTH = tk.Text(self)
        self.LENGTH.place(relx=0.3, rely=0.9, relheight=0.05, relwidth=0.09)
        self.LENGTH.configure(background="white")
        self.LENGTH.configure(font="TkTextFont")
        self.LENGTH.configure(selectbackground="#c4c4c4")
        self.LENGTH.configure(wrap="word")
        self.LENGTH.config(state=NORMAL)
        
        self.Length_Label = tk.Label(self)
        self.Length_Label.place(relx=0.2, rely=0.9, height=29, width=56)
        self.Length_Label.configure(text='''Length:''', bg = 'white')

        self.Width = tk.Text(self)
        self.Width.place(relx=0.5, rely=0.9, relheight=0.05, relwidth=0.09)
        self.Width.configure(background="white")
        self.Width.configure(font="TkTextFont")
        self.Width.configure(selectbackground="#c4c4c4")
        self.Width.configure(wrap="word")
        
        self.Width_Label = tk.Label(self)
        self.Width_Label.place(relx=0.4, rely=0.9, height=29, width=56)
        self.Width_Label.configure(text='''Width:''', bg = 'white')

        self.Height = tk.Text(self)
        self.Height.place(relx=0.7, rely=0.9, relheight=0.05, relwidth=0.09)
        self.Height.configure(background="white")
        self.Height.configure(font="TkTextFont")
        self.Height.configure(selectbackground="#c4c4c4")
        self.Height.configure(wrap="word")

        self.Height_Label = tk.Label(self)
        self.Height_Label.place(relx=0.6, rely=0.9, height=29, width=56)
        self.Height_Label.configure(text='''Height:''', bg = 'white')

        self.Weight = tk.Text(self)
        self.Weight.place(relx=0.1, rely=0.6, relheight=0.05, relwidth=0.09)
        self.Weight.configure(background="white")
        self.Weight.configure(font="TkTextFont")
        self.Weight.configure(selectbackground="#c4c4c4")
        self.Weight.configure(wrap="word")

        self.Weight_Label = tk.Label(self)
        self.Weight_Label.place(relx=0.05, rely=0.5, height=29, width=56)
        self.Weight_Label.configure(text='''Weight:''', bg = 'white')


        self.Weight.bind('<Button>', self.add_in)
        self.Width.bind('<Button>', self.add_in)
        self.Height.bind('<Button>', self.add_in)
        self.LENGTH.bind('<Button>', self.add_in)

        global WEIGHT
        WEIGHT = tk.IntVar()
#         cont = tk.Label(self, textvariable = WEIGHT)
#         cont.place(relx=0.15, rely=0.5, height=29, width=56)
# 
#         self.TimerInterval = 2000
#         #self.weight = 0
#         #self.get_weight()
    

    '''
    -----------Reset all values and picture---------
    '''
    def Reset_Func(self):

        if self.pic == None:
            self.LENGTH.delete(0.0, tk.END)
            self.Width.delete(0.0, END)
            self.Height.delete(0.0, END)
            self.Weight.delete(0.0, END)
        elif self.pic is not None:
            self.pic.destroy()
            self.LENGTH.delete(0.0, tk.END)
            self.Width.delete(0.0, END)
            self.Height.delete(0.0, END)
            self.Weight.delete(0.0, END)

    '''
    -----------These functions manually add values into the text widgets----------
    '''
    def add_in(self, event):

        #If toplevel doesnt exist create one
        if self.add == None or not tk.Toplevel.winfo_exists(self.add):
            self.add = Toplevel()
            self.add_numpad = KeyPad(self.add)
            enter = tk.Button(self.add, text = "Enter/Exit", width =6, height = 2, command = lambda: self.add_text(event))
            enter.place(rely=(5/6))
            self.add.attributes('-topmost', 'true')
            self.add.mainloop()
        #If toplevel already exists destroy it and create one   
        elif tk.Toplevel.winfo_exists(self.add):
            self.add.destroy()
            self.add = Toplevel()
            self.add_numpad = KeyPad(self.add)
            enter = tk.Button(self.add, text = "Enter/Exit", width =6, height = 2, command = lambda: self.add_text(event))
            enter.place(rely=(5/6))
            self.add.attributes('-topmost', 'true')
            self.add.mainloop()
    
    #Add manually entered values
    def add_text(self, event):
        event.widget.delete(0.0, END)
        event.widget.insert(END, self.add_numpad.value)
        self.add.destroy()


    '''
    ------------This is the function called when 'measure' button is pressed--------
    '''
    def queue_L_W(self, q):
        try:
            i = Dimension_V1.get_Dimensions()
            q.put(i)
        except:
            pass
    
    def queue_weight(self, q):
        try:
            i = Scale_Final.get_weight()
            q.put(i)
        except:
            pass    

    def measure(self):
        t1 = time.time()
        global Measurment
        if Measurment == 'Metric':
            conv = 1
            weight_conv = 1
            suffix = ' mm'
            w_suffix = ' g'
            
        else:
            conv = 25.4
            weight_conv =  453.59237 #28.34952 (oz)
            suffix = ' in'
            w_suffix = ' lb'
        
        if self.pic == None:
            self.LENGTH.delete(0.0, tk.END)
            self.Width.delete(0.0, END)
            self.Height.delete(0.0, END)
            self.Weight.delete(0.0, END)
        elif self.pic is not None:
            self.pic.destroy()
            self.LENGTH.delete(0.0, tk.END)
            self.Width.delete(0.0, END)
            self.Height.delete(0.0, END)
            self.Weight.delete(0.0, END)


        '''
        --------Disable all the buttons while extracting data-----
        '''
        self.Measure.config(state=DISABLED)
        self.button.config(state=DISABLED)
        self.Reset.config(state=DISABLED)
        self.Tare.config(state=DISABLED)
        self.settings.config(state=DISABLED)
        
        '''
        Create progress bar to track data 
        '''

        progress_label = Label(self, text = "Please wait: Fetching data!", bg = 'white', font = 24)
        progress_label.place(relx = .5, rely = .2, anchor = CENTER)
        
        progress = ttk.Progressbar(self, orient = HORIZONTAL, mode = 'determinate')
        progress.place(relx = .5, rely = .25, anchor = CENTER, relwidth = .3)
        
        progress['value'] = 10
        progress.update()
      
        #q1 = Queue()
#         q2 = Queue()
#         #L_W_task = Process(target = self.queue_L_W, args = (q1, ))
#         Weight_task = Process(target = self.queue_weight, args = (q2, ))
#         
#         #L_W_task.start()
#         Weight_task.start()
#         
#         #L_W_task.join(7)
#         Weight_task.join(7)
#         
#         #L_W_task.terminate()
#         Weight_task.terminate() 

        #Get the length and width from Length_Width.py calling Start() function
        #Enter values into their text boxes
        #tk.Tk.report_callback_exception = self.show_error
        try:
            t2 = time.time()
            
            #L, W, H, minx, maxx, miny, maxy = q1.get(timeout = 1)
            
            L, W, H, minx, maxx, miny, maxy = Dimension_V1.get_Dimensions()
            #print("Got values successfully: ", L, W, H)
            #int(miny, maxy, minx, maxx)
            self.LENGTH.delete(0.0, END)
            self.LENGTH.insert(END, str("{:.2f}".format(L/conv)) + suffix)
            
            self.Width.delete(0.0, END)
            self.Width.insert(END, str("{:.2f}".format(W/conv)) + suffix)

            self.Height.delete(0.0, END)
            self.Height.insert(END, str("{:.2f}".format(H/conv)) + suffix)
            
            progress['value'] = 25
            progress.update()
        
            #Add the image the was just captured onto the page to be checked 
            image= cv2.imread('DisplayPic.jpg')#Image.open("/home/opencv/TestPicLeftStop.jpg")
            image = image[int(miny):int(maxy), int(minx):int(maxx)]
            
            yadjust = 250/(int(maxy)-int(miny))
            xadjust = 350/(int(maxx)-int(minx))
            #image = image[200:450, 200:550]
            image = cv2.resize(image, None, fx=xadjust, fy=yadjust, interpolation=cv2.INTER_AREA)
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            image = Image.fromarray(image)
            
            img = ImageTk.PhotoImage(image)
            self.pic = tk.Label(self, image = img,  borderwidth=0)
            self.pic.image = img
            self.pic.place(relx=0.5, rely=0.57, anchor = CENTER)
            
            print(time.time() - t2)
        except:
            messagebox.showerror('Exception', "Dimensions Camera Error!")
            pass
        
        #update progress bar
        progress['value'] = 50
        progress.update()
        
        #get the weight from Scale_final.py calling the get_weight() function
        try:
            t3 = time.time()
            #weight = q2.get(timeout = 1)
            weight = Scale_Final.get_weight()
            self.Weight.delete(0.0, END)
            self.Weight.insert(END, str("{:.2f}".format(weight/weight_conv)) + w_suffix)
            print(time.time() - t3)
        
        except:
            messagebox.showerror('Exception', "Scale Error!")
            pass
        
        progress['value'] = 75
        progress.update()

        #Update progress bar and destory
        progress['value'] = 100
        progress.update()
        progress.destroy()
        progress_label.destroy()

        '''
        --------Enable buttons once process complete-----
        '''
        self.Measure.config(state=NORMAL)
        self.button.config(state=NORMAL)
        self.Reset.config(state=NORMAL)
        self.Tare.config(state=NORMAL)
        self.settings.config(state=NORMAL)
        print(time.time() - t1)

    '''
    -------------Zero the Scale and Laser Distance Sensor----------
    '''
    def Zero(self):
        
        
        if self.pic == None:
            self.LENGTH.delete(0.0, tk.END)
            self.Width.delete(0.0, END)
            self.Height.delete(0.0, END)
            self.Weight.delete(0.0, END)
        elif self.pic is not None:
            self.pic.destroy()
            self.LENGTH.delete(0.0, tk.END)
            self.Width.delete(0.0, END)
            self.Height.delete(0.0, END)
            self.Weight.delete(0.0, END)

        '''
        --------Disable all the buttons while extracting data-----
        '''
        self.Measure.config(state=DISABLED)
        self.button.config(state=DISABLED)
        self.Reset.config(state=DISABLED)
        self.Tare.config(state=DISABLED)
        self.settings.config(state=DISABLED)    
        
        progress_label = Label(self, text = "Please wait: Zeroing Weight and Height", bg = 'white', font = 24)
        progress_label.place(relx = .5, rely = .2, anchor = CENTER)
        
        progress = ttk.Progressbar(self, orient = HORIZONTAL, mode = 'determinate')
        progress.place(relx = .5, rely = .25, anchor = CENTER, relwidth = .3)
        
        progress['value'] = 25
        progress.update()

        
        
        try:
            Zero_distance = int(Sensor_Distance.get_Distance())
            tare = open("Laser_distance", 'w')
            tare.write(str(Zero_distance))
            tare.close()
            self.Height.insert(END, 0)    

        except:
            messagebox.showerror('Exception', "Laser Sensor Error!")
            pass

        progress['value'] = 60
        progress.update()

        try:
            Scale_Final.Tare()
            #weight = Scale_Final.get_weight()
            self.Weight.delete(0.0, END)
            self.Weight.insert(END, 0)

        except:
            messagebox.showerror('Exception', "Scale Error!")
            pass
        
        self.LENGTH.insert(END, 0)
        self.Width.insert(END, 0)
        progress['value'] = 100
        progress.update()
        progress.destroy()
        progress_label.destroy()


        '''
        --------Enable buttons once process complete-----
        '''
        self.Measure.config(state=NORMAL)
        self.button.config(state=NORMAL)
        self.Reset.config(state=NORMAL)
        self.Tare.config(state=NORMAL)
        self.settings.config(state=NORMAL)


'''
------------Main Menu page---------------
'''    
class MainMenu(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent, background = 'white')

        self.controller = controller

        '''
        --------Create all of the widgets---------- 
        '''
        logo = tk.PhotoImage(file="radwell.gif")
        BGlabel = tk.Label(self,image=logo,  borderwidth=0)
        BGlabel.image = logo
        BGlabel.place(relx=0, rely=0)

        image= cv2.imread('Photobooth.png')#Image.open("/home/opencv/TestPicLeftStop.jpg")
        image = cv2.resize(image, None, fx=.6, fy=.6, interpolation=cv2.INTER_AREA)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(image)
        
        img = ImageTk.PhotoImage(image)
        pic = tk.Label(self, image = img,  borderwidth=0)
        pic.image = img
        pic.place(relx=0.5, rely=0.6, anchor = CENTER)

        Dim_button = tk.Button(self, text="Enter "
                               "\nPhoto Dimensioning",
                        command=lambda: controller.show_frame(Dimensions))

        Dim_button.place(relx=0.55, rely=0.1)
        
        setting_pic = tk.PhotoImage(file="Preferences.gif")
        self.settings = tk.Button(self, image = setting_pic, bg = 'white', bd =0)
        self.settings.image = setting_pic
        self.settings.place(relx=0.9, rely=0.1, anchor = CENTER)
        self.settings.configure(command=lambda: controller.show_frame(Options))

        self.scaleLeftRing = Scale(self, from_=100, to=0, highlightthickness = 0, length = 250,
              orient=VERTICAL, command=self.updateLeftRing, borderwidth = 5,
                              width = 50, bg = 'white', sliderlength=50)
        self.scaleLeftRing.place(relx=0.125, rely=0.6, anchor = CENTER)
        self.scaleLeftRing.set(left_val)
        
        self.scaleRightRing = Scale(self, from_=100, to=0, highlightthickness = 0, length = 250,
              orient=VERTICAL, command=self.updateRightRing, borderwidth = 5,
                              width = 50, bg = 'white', sliderlength=50)
        self.scaleRightRing.place(relx=0.825, rely=0.6, anchor = CENTER)
        self.scaleRightRing.set(right_val)

        left_ring= Label(self, text='Left Light', bg = 'white')
        left_ring.place(relx=0.15, rely=0.925, anchor = CENTER)
        
        right_ring= Label(self, text='Right Light', bg = 'white')
        right_ring.place(relx=0.85, rely=0.925, anchor = CENTER)

        self.var = IntVar()
        self.var.set(1)
        RadiobuttonleftON = Radiobutton(self, indicatoron = 0, anchor=W, text="ON", variable=self.var, value=1, command = self.SwitchLeft)
        RadiobuttonleftON.place(relx=.1, rely=.25, relwidth=.05)
        RadiobuttonleftOFF = Radiobutton(self, indicatoron = 0, anchor=W, text="OFF", variable=self.var, value=2, command = self.SwitchLeft)
        RadiobuttonleftOFF.place(relx=.15, rely=.25, relwidth=.05)

        self.var1 = IntVar()
        self.var1.set(1)
        RadiobuttonrightON = Radiobutton(self, indicatoron = 0, anchor=W, text="ON", variable=self.var1, value=1, command = self.SwitchRight)
        RadiobuttonrightON.place(relx=.8, rely=.25, relwidth=.05)
        RadiobuttonrightOFF = Radiobutton(self, indicatoron = 0, anchor=W, text="OFF", variable=self.var1, value=2, command = self.SwitchRight)
        RadiobuttonrightOFF.place(relx=.85, rely=.25, relwidth=.05)
        
#         global color
#         color = IntVar()
#                
#         color.set(1)
#         Blue_Button = Radiobutton(self, indicatoron = 0, anchor=CENTER, text="Blue", variable=color, value=1, command = self.SwitchColor)
#         Blue_Button.place(relx=.35, rely=.83, relheight = .125, relwidth=.15)
#         White_Button = Radiobutton(self, indicatoron = 0, anchor=CENTER, text="White", variable=color, value=2, command = self.SwitchColor)
#         White_Button.place(relx=.5, rely=.83, relheight = .125, relwidth=.15)
# 
#     def SwitchColor(self):
#         if color.get() == 2:
#             pwmRed.ChangeDutyCycle(0)
#             pwmGreen.ChangeDutyCycle(0)
#             pwmBlue.ChangeDutyCycle(0)
#             pwmWhite.ChangeDutyCycle(100)
# 
#         else:
#             g = open("Green_Light", 'r')
#             green = g.read()
#             g.close()
# 
#             b = open("Blue_Light", 'r')
#             blue = b.read()
#             b.close()
# 
#             w = open("White_Light", 'r')
#             white = w.read()
#             w.close()
# 
#             r = open("Red_Light", 'r')
#             red = r.read()
#             r.close()            
# 
#             pwmRed.ChangeDutyCycle(int(red))
#             pwmGreen.ChangeDutyCycle(int(green))
#             pwmBlue.ChangeDutyCycle(int(blue))
#             pwmWhite.ChangeDutyCycle(int(white))
#       

    '''
    ---------functions called when widgets are activated--------
    '''
    def updateLeftRing(self, duty):
        LeftRing.ChangeDutyCycle(float(duty))
        leftfile = open("Left_Light", 'w')
        leftfile.write(str(duty))
        leftfile.close()

    def updateRightRing(self, duty):
        RightRing.ChangeDutyCycle(float(duty))
        rightfile = open("Right_Light", 'w')
        rightfile.write(str(duty))
        rightfile.close()

    def SwitchLeft(self):
        if self.var.get() == 2:
            self.scaleLeftRing.config(state=DISABLED)
            LeftRing.ChangeDutyCycle(0)
        else:
            self.scaleLeftRing.config(state=NORMAL)
            leftfile = open("Left_Light", 'r')
            _left_ = leftfile.read()
            leftfile.close()
            LeftRing.ChangeDutyCycle(float(_left_))
            
    def SwitchRight(self):
        if self.var1.get() == 2:
            self.scaleRightRing.config(state=DISABLED)
            RightRing.ChangeDutyCycle(0)
        else:
            self.scaleRightRing.config(state=NORMAL)
            rightfile = open("Right_Light", 'r')
            _right_ = rightfile.read()
            rightfile.close()
            RightRing.ChangeDutyCycle(float(_right_))


'''
-------------Options page-----------------
'''
class Options(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent, background = 'white')

        self.controller = controller

        '''
        ----------Create widgets----------
        '''
        logo = tk.PhotoImage(file="radwell.gif")
        BGlabel = tk.Label(self,image=logo,  borderwidth=0)
        BGlabel.image = logo
        BGlabel.place(x=0, y=0)

#         label = tk.Label(self, text="Settings", bg="white")
#         label.place(relx=0.2, rely=0.3, anchor=CENTER)

        laser = tk.Label(self, text="Laser Distance Sensor Options:", bg="white")
        laser.place(relx=0.05, rely=0.65, anchor=W)
        
        self.Zero = tk.Button(self)
        self.Zero.place(relx=0.2, rely=0.75, anchor=CENTER)
        self.Zero.configure(font="TkTextFont")
        self.Zero.configure(text='''Zero Laser''')
        self.Zero.configure(command=self.Zero_Laser)       
        
        self.Zero_done = tk.Label(self, bg = 'white')
        self.Zero_done.place(relx = .35, rely = .75, anchor = CENTER)
        
        
        weight = tk.Label(self, text="Scale Options:", bg="white")
        weight.place(relx=0.05, rely=0.3, anchor=W)
        
        self.Reset_Scale = tk.Button(self)
        self.Reset_Scale.place(relx=0.2, rely=0.4, anchor=CENTER)
        self.Reset_Scale.configure(font="TkTextFont")
        self.Reset_Scale.configure(text='''Reset Scale''')
        self.Reset_Scale.configure(command=lambda: controller.show_frame(Scale_Setup))        
        
        self.Tare = tk.Button(self)
        self.Tare.place(relx=0.2, rely=0.5, anchor=CENTER)
        self.Tare.configure(font="TkTextFont")
        self.Tare.configure(text='''Zero Scale''')
        self.Tare.configure(command= self.Zero_Weight)              
        
        self.Tare_done = tk.Label(self, bg = 'white')
        self.Tare_done.place(relx = .35, rely = .5, anchor = CENTER)
        
        light = tk.Label(self, text="LED Options:", bg="white")
        light.place(relx=0.6, rely=0.3, anchor=W)

        self.Lights = tk.Button(self)
        self.Lights.place(relx=0.8, rely=0.4, anchor=CENTER)
        self.Lights.configure(font="TkTextFont")
        self.Lights.configure(text='''Adjust LED\n Color''')
        self.Lights.configure(command=lambda: self.LED_permission(controller))
 
        
        system = tk.Label(self, text="Measurment System Option:", bg="white")
        system.place(relx=0.6, rely=0.65, anchor=W)

        self.var = IntVar()
        m = open('Measurment_Standard', 'r')
        metric_start = m.read()
        m.close()
        
        if metric_start == 'Metric':
            self.var.set(1)
        else:
            self.var.set(2)
            
        MetricSystem = Radiobutton(self, text="Metric System", font = 30, variable=self.var, value=1, command = self.SwitchLeft)
        MetricSystem.place(relx=.7, rely=.75, anchor = W)#, relwidth=.05)
        ImperialSystem = Radiobutton(self, text="Imperial System", font = 30, variable=self.var, value=2, command = self.SwitchLeft)
        ImperialSystem.place(relx=.7, rely=.85, anchor = W)#, relwidth=.05)
     
        self.button = tk.Button(self)
        self.button.place(relx=0.6, rely=0.05, relwidth = .18 )
        self.button.configure(text='''Enter\n Photo Station''')
        self.button.configure(command=lambda: controller.show_frame(MainMenu))
        
        Dim_button = tk.Button(self, text="Enter "
                               "Photo\n Dimensioning",
                        command=lambda: controller.show_frame(Dimensions))

        Dim_button.place(relx=0.8, rely=0.05, relwidth = .18)
        
        self.led_page = None
    
        self.bind('<Button>', self.clear_labels)
        self.Lights.bind('<Button>', self.clear_labels)
        self.Reset_Scale.bind('<Button>', self.clear_labels)
        Dim_button.bind('<Button>', self.clear_labels)
        self.button.bind('<Button>', self.clear_labels)
        

    '''
    ----------Functions used when widgets are activated
    '''
    def clear_labels(self, event):
        self.Tare_done.config(text = '')
        self.Zero_done.config(text = '')
    
    
    def SwitchLeft(self):
        global Measurment
        if self.var.get() == 2:
            file = open('Measurment_Standard', 'w')
            Measurment = 'Imperial'
            file.write(Measurment)
            file.close()
        else:
            file = open('Measurment_Standard', 'w')
            Measurment = 'Metric'
            file.write(Measurment)
            file.close()

  
    #Ask permission to visit LED page, if password is correct visit page
    def LED_permission(self, controller):
        
        #If toplevel doesnt exist create one
        if self.led_page == None or not tk.Toplevel.winfo_exists(self.led_page):
            self.led_page = Toplevel()
            self.led_numpad = NumPad(self.led_page)
            enter = tk.Button(self.led_page, text = "Enter/Exit", width =6, height = 2, command = lambda: self.check(controller))
            enter.place(rely=(5/6))
            self.led_page.attributes('-topmost', 'true')
            self.led_page.mainloop()
        #If toplevel already exists destroy it and create one   
        elif tk.Toplevel.winfo_exists(self.led_page):
            self.led_page.destroy()
            self.led_page = Toplevel()
            self.led_numpad = NumPad(self.led_page)
            enter = tk.Button(self.led_page, text = "Enter/Exit", width =6, height = 2, command = lambda: self.check(controller))
            enter.place(rely=(5/6))
            self.led_page.attributes('-topmost', 'true')
            self.led_page.mainloop()

    def check(self, controller):
        if self.led_numpad.password == '1234':
            controller.show_frame(LedPage)
            self.led_page.destroy()
        else:
            self.led_page.destroy()

    #Take the laser distance and store it in a file to be used for a zero
    def Zero_Laser(self):
        try:
            Zero_distance = int(Sensor_Distance.get_Distance())
            tare = open("Laser_distance", 'w')
            tare.write(str(Zero_distance))
            tare.close()
        except:
            messagebox.showerror('Exception', "Laser Sensor Error!")
            pass
        
        self.Zero_done.config(text = "Done!")
        
    def Zero_Weight(self):
        
        self.Tare.config(state = DISABLED)
        self.Zero.config(state = DISABLED)
        self.Reset_Scale.config(state = DISABLED)
        self.Lights.config(state = DISABLED)
        self.update_idletasks()
        
        try:
            Scale_Final.Tare()

        except:
            messagebox.showerror('Exception', "Scale Error!")
            pass
        self.Tare_done.config(text="Done!")
        self.Tare.config(state = ACTIVE)
        self.Zero.config(state = ACTIVE)
        self.Reset_Scale.config(state = ACTIVE)
        self.Lights.config(state = ACTIVE)

class Scale_Setup(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent, background = 'white')

        self.controller = controller
        self.parent = parent
        
        '''
        -------------Create Widgets-----------------
        '''
        logo = tk.PhotoImage(file="radwell.gif")
        BGlabel = tk.Label(self,image=logo,  borderwidth=0)
        BGlabel.image = logo
        BGlabel.place(x=0, y=0)

        self.label = tk.Label(self, text="Please Clear Scale for reset", bg="white")
        self.label.place(relx=0.5, rely=0.4, anchor=CENTER)
        
        self.Back_button = tk.Button(self, text="Return", font = 30,
                        command=lambda: controller.show_frame(Options))

        self.Back_button.place(relx=0.9, rely=0.1, anchor=CENTER)

        self.button = tk.Button(self, text="Begin",
                        command=self.start)
        
        self.button.place(relx=0.5, rely=0.6, anchor=CENTER)
        
        self.manual_value = None
        
        self.Back_button.bind('<Button>', self.re_init)
        
        self.Scale = Scale_Final_Reset.Scale()
    
    def re_init(self, event):
        self.button.config( text="Begin",
                        command=self.start, state= ACTIVE)
        self.label.config(text = "Please Clear Scale for reset")
        
    def start(self):
        
        progress = ttk.Progressbar(self, orient = HORIZONTAL, mode = 'determinate')
        progress.place(relx = .5, rely = .5, anchor = CENTER, relwidth = .3)
        progress['value'] = 30
        
        self.update_idletasks()
        
        self.label.config(text = "Setting up, please keep scale clear")
        self.button.config(state= DISABLED)

        progress['value'] = 40
        
        self.update_idletasks()
  
        text = self.Scale.setup()  
        
        if text == "Error":
            messagebox.showerror('Exception', "Scale is not working!")
        
        data = self.Scale.get_data()
        
        progress['value'] = 60
        self.update_idletasks()
  
        self.label.config(text = "Place known weight onto scale and press 'OK'")
        
        progress.destroy()
        self.button.config(state= ACTIVE, text = "OK", command = lambda: self.place_weight(data))
        
        
                
    def place_weight(self, data):
        
        #self.label.config(text = "Setting up, please keep scale clear")
        self.button.config(state= DISABLED)
            
        progress = ttk.Progressbar(self, orient = HORIZONTAL, mode = 'determinate')
        progress.place(relx = .5, rely = .5, anchor = CENTER, relwidth = .3)
        progress['value'] = 30
        self.update_idletasks()
        
        data = self.Scale.Weight_on_Scale(data)
 
        progress['value'] = 50
        self.label.config(text = "Enter known weight (in grams) and press Enter")
        self.update_idletasks()
        
        
        progress.destroy()
        #If toplevel doesnt exist create one
        if self.manual_value == None or not tk.Toplevel.winfo_exists(self.manual_value):
            self.manual_value = Toplevel()
            self.numpad = KeyPad(self.manual_value)
            enter = tk.Button(self.manual_value, text = "Enter", width =6, height = 2, command = lambda: self.add_weight(data))
            enter.place(rely=(5/7))
            inst = tk.Label(self.manual_value, text = "Enter known weight (in grams)\n Press Enter", font = 30).grid(row = 7, column = 0, columnspan=3)
            self.manual_value.attributes('-topmost', 'true')
            self.manual_value.mainloop()
        #If toplevel already exists destroy it and create one   
        elif tk.Toplevel.winfo_exists(self.manual_value):
            self.manual_value.destroy()
            self.manual_value = Toplevel()
            self.numpad = KeyPad(self.manual_value)
            enter = tk.Button(self.manual_value, text = "Enter", width =6, height = 2, command = lambda: self.add_weight(data))
            enter.place(rely=(5/7))
            inst = tk.Label(self.manual_value, text = "Enter known weight (in grams)\n Press Enter", font = 30).grid(row = 7, column = 0, columnspan=3)
            self.manual_value.attributes('-topmost', 'true')
            self.manual_value.mainloop()
            
        

    def add_weight(self, data):
      
        self.label.config(text = "Finishing Calibration")
        self.button.config(state= DISABLED)
      
        progress = ttk.Progressbar(self, orient = HORIZONTAL, mode = 'determinate')
        progress.place(relx = .5, rely = .5, anchor = CENTER, relwidth = .3)
        progress['value'] = 30
        self.update_idletasks()
  
        weight = self.numpad.value
        
        self.manual_value.destroy()
        
        progress['value'] = 30
        self.update_idletasks()
        
        final_weight = self.Scale.Manual_Entry(data, weight)
        
        progress['value'] = 60
        self.update_idletasks()
        
        progress.destroy()
        
        self.label.config(text = ("Current weight on the scale is \n" + str(final_weight)+ ' g'))
        
        
'''
--------------LED page ----------------
'''
class LedPage(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent, background = 'white')

        self.controller = controller

        '''
        -------------Create Widgets-----------------
        '''
        logo = tk.PhotoImage(file="radwell.gif")
        BGlabel = tk.Label(self,image=logo,  borderwidth=0)
        BGlabel.image = logo
        BGlabel.place(x=0, y=0)

        self.button = tk.Button(self)
        self.button.place(relx=0.9, rely=0.1, anchor=CENTER)
        self.button.configure(text='''Return''', font = 30)
        self.button.configure(command=lambda: controller.show_frame(Options))

        red_label= Label(self, text='Red', bg = 'white')
        red_label.place(relx=0.3, rely=0.35)
        green_label= Label(self, text='Green', bg = 'white')
        green_label.place(relx=0.3, rely=0.5)
        blue_label= Label(self, text='Blue', bg = 'white')
        blue_label.place(relx=0.3, rely=0.65)
        white_label= Label(self, text='White', bg = 'white')
        white_label.place(relx=0.3, rely=0.8)
        
        # Create the sliders and position them in a grid layout
        # the 'command' attribute specifys a method to call when
        # a slider is moved
        scaleRed = Scale(self, from_=0, to=100, highlightthickness = 0, length = 200,
              orient=HORIZONTAL, command=self.updateRed, borderwidth = 5,
                              width = 30, bg = 'white')
        scaleRed.place(relx=0.4, rely=0.3)
        scaleRed.set(red)
        
        scaleGreen = Scale(self, from_=0, to=100, highlightthickness = 0, length = 200,
              orient=HORIZONTAL, command=self.updateGreen, borderwidth = 5,
                              width = 30, bg = 'white')
        scaleGreen.place(relx=0.4, rely=0.45)
        scaleGreen.set(green)
        
        scaleBlue = Scale(self, from_=0, to=100, highlightthickness = 0, length = 200,
              orient=HORIZONTAL, command=self.updateBlue, borderwidth = 5,
                              width = 30, bg = 'white')
        scaleBlue.place(relx=0.4, rely=0.6)
        scaleBlue.set(blue)
        
        scaleWhite = Scale(self, from_=0, to=100, highlightthickness = 0, length = 200,
              orient=HORIZONTAL, command=self.updateWhite, borderwidth = 5,
                              width = 30, bg = 'white')
        scaleWhite.place(relx=0.4, rely=0.75)
        scaleWhite.set(white)

    # These methods called whenever a slider moves
    def updateRed(self, duty):   
        # change the led brightness to match the slider
        pwmRed.ChangeDutyCycle(float(duty))
        redfile = open("Red_Light", 'w')
        redfile.write(str(duty))
        redfile.close()
    def updateGreen(self, duty):
        pwmGreen.ChangeDutyCycle(float(duty))
        greenfile = open("Green_Light", 'w')
        greenfile.write(str(duty))
        greenfile.close()   
    def updateBlue(self, duty):
        pwmBlue.ChangeDutyCycle(float(duty))
        bluefile = open("Blue_Light", 'w')
        bluefile.write(str(duty))
        bluefile.close()
    def updateWhite(self, duty):
        pwmWhite.ChangeDutyCycle(float(duty))
        whitefile = open("White_Light", 'w')
        whitefile.write(str(duty))
        whitefile.close()
  
  
  
class idle_mode(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent, background = 'white')

        self.controller = controller

        '''
        ----------Create widgets----------
        '''
        logo = tk.PhotoImage(file="radwell.gif")
        BGlabel = tk.Label(self,image=logo,  borderwidth=0)
        BGlabel.image = logo
        BGlabel.place(x=0, y=0)
        
        self.message = tk.Label(self, text = "Idle Mode: Please Return", bg = 'white', font = 40)
        self.message.place(relx = .5, rely = .5, anchor = CENTER)
        
        self.button = tk.Button(self)
        self.button.place(relx=0.5, rely=0.7, anchor=CENTER)
        self.button.configure(text='''Return''', font = 40)
        self.button.configure(command=lambda: controller.show_frame(MainMenu))

'''
Create instance of class, try it and run main loop. When quit turn off all the GPIO
pins and clean up application 
'''
app = Photobooth()
try:
    app.mainloop()
finally:
    GPIO.output(17, 0)
    GPIO.output(18, 0)
    GPIO.output(27, 0)
    GPIO.output(22, 0)
    GPIO.output(23, 0)
    GPIO.output(24, 0)
    GPIO.output(12, 0)

    GPIO.cleanup()
    print("Clean")
