import npyscreen
import curses

class App(npyscreen.StandardApp):
    def onStart(self):
        self.addForm("MAIN", MainForm, name="Clapi TUI")

class LogBox(npyscreen.BoxTitle):
    _contained_widget = npyscreen.MultiLineEdit
    
class InputBox(npyscreen.BoxTitle):
    _contained_widget = npyscreen.MultiLineEdit
    
    def when_value_edited(self):
        self.parent.parentApp.queue_event(npyscreen.Event("event_value_edited"))

class MainForm(npyscreen.FormBaseNew):
    def create(self):
        y, x = self.useable_space()
        # DEVICES LIST
        self.add(npyscreen.BoxTitle, name="Devices", \
			  values=["nucleo", "arduino1", "arduino2"], \
              rely=2, max_width=x // 3 - 5, max_height=7)
        
        # STATUS BOX
        self.add(InputBox, name="Clapi Status", \
			  editable=False, \
              rely=9, max_width=x // 3 - 5, max_height=y-13)
        
        # MESSAGES LOG
        self.log_box = self.add(LogBox, name="Message Log", footer="log.2019.06.14.txt", \
              relx=x // 3, rely=2, max_height=y-9, editable=False)
              
        # INPUT BOX
        self.input_box = self.add(InputBox, relx=x // 3, rely=y-7,\
			  max_height=3, name="Input")
        
        # HELP
        self.add(npyscreen.FixedText, rely=y-3, max_height=1, \
              value="Exit: Ctrl+Q    Reconnect: Ctrl+R    Status: Ctrl+S    Nav: Tab\Shift+Tab")
        
        # HANDLERS
        new_handlers = { "^Q": self.exit_func }
        self.add_handlers(new_handlers)
        self.add_event_hander("event_value_edited", self.on_message)
        
    def on_message(self, event):
        text = self.input_box.value
        ch = text[-1] if len(text) > 0 else ' '
        if ch == "\n":
            self.log_box.value += "\n{}".format(text[0:len(text)-1])
            self.input_box.value = ""
            self.input_box.display()
            self.log_box.display()
    
    def exit_func(self, event):
        exit(0)

MyApp = App()
MyApp.run()
