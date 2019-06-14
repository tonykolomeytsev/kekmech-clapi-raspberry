import npyscreen
import curses
import re


class ClapiTUI(npyscreen.StandardApp):
    def onStart(self):
        self.main_form = self.addForm("MAIN", MainForm, name="Clapi TUI")



class LogBox(npyscreen.BoxTitle):
    _real_height = None
    _contained_widget = npyscreen.MultiLineEdit


    
class InputBox(npyscreen.BoxTitle):
    _contained_widget = npyscreen.MultiLineEdit
    
    def when_value_edited(self):
        self.parent.parentApp.queue_event(npyscreen.Event("event_value_edited"))



class MainForm(npyscreen.FormBaseNew):
    def create(self):
        y, x = self.useable_space()
        
        devices_list = list(map(lambda x: str(x.id), api.core.devices)) if api.core.devices else []
        # DEVICES LIST
        self.dev_list = self.add(npyscreen.BoxTitle, name="Devices", \
			  values=devices_list, \
              rely=2, max_width=x // 3 - 5, max_height=y-6)#, max_height=7)
        
        # STATUS BOX
        #self.status_box = self.add(InputBox, name="Clapi Status", \
		#	  editable=False, \
        #      rely=9, max_width=x // 3 - 5, max_height=y-13, value=str(y-9))
        
        # MESSAGES LOG
        self.log_box = self.add(LogBox, name="Message Log", footer="log.2019.06.14.txt", \
              relx=x // 3, rely=2, max_height=y-9, editable=False)
        self.log_box._real_height = y-9
        
        # INPUT BOX
        self.input_box = self.add(InputBox, relx=x // 3, rely=y-7,\
			  max_height=3, name="Input")
        
        # HELP
        self.add(npyscreen.FixedText, rely=y-3, max_height=1, \
              value="Exit: Ctrl+Q    Status: Ctrl+S    Nav: Tab\Shift+Tab")
        
        # HANDLERS
        new_handlers = { "^Q": self.exit_func }
        self.add_handlers(new_handlers)
        self.add_event_hander("event_value_edited", self.on_message)
        
    def on_message(self, event):
        text = self.input_box.value
        ch = text[-1] if len(text) > 0 else ' '
        if ch == "\n":
            process_cmd(text)
    
    def exit_func(self, event):
        exit(0)



api = None # clapi instance
clapiTUI = None
log_lines = []

def start(clapi_instance):
    global clapiTUI
    global api
    api = clapi_instance
    api.start()
    
    clapiTUI = ClapiTUI()
    clapiTUI.run()



def process_cmd(cmd):
    
    lb = clapiTUI.main_form.log_box
    ib = clapiTUI.main_form.input_box
    current_device_id = clapiTUI.main_form.dev_list.get_value()
    current_device = clapiTUI.main_form.dev_list.values[current_device_id]
    
    try:
        # LOGIC
        chain = re.split(r'\s+' ,cmd.strip().upper())
        
        cmd_code = int(chain[1], 16)
        cmd_code_txt = chain[1]
        if len(chain) > 2:
            cmd_args = [float(chain[i]) for i in range(2, len(chain))]
        else:
            cmd_args = []
        
        if chain[0] == "R":
            cmd_type = "REQUEST"
            getattr(api, current_device).request_async(cmd_code)\
                .args(*cmd_args)\
                .callback(callback_add_response).execute()
                
        if chain[0] == "P":
            cmd_type = "PUSH"
            getattr(api, current_device).push_async(cmd_code)\
                .args(*cmd_args).execute()
                
        if chain[0] == "LP":
            cmd_type = "LONG_POLL"
            getattr(api, current_device).long_poll_async(cmd_code)\
                .args(*cmd_args)\
                .callback(callback_add_response).execute()
        
        text_to_print = '{} {} {}'.format(cmd_type,cmd_code_txt,cmd_args)
    except:
        text_to_print = 'Error while parsing command {} for {}\n'.format(cmd, current_device)
    
    # VIEW
    log_lines.append(text_to_print)
    update_value(lb)
    ib.value = ""
    ib.display()



def callback_add_response(data):
    lb = clapiTUI.main_form.log_box
    log_lines.append("RESPONSE")
    beautify(data)
    update_value(lb)


def update_value(lb):
    h = lb._real_height-2
    if h < len(log_lines):
        lb.value = "\n".join(log_lines[-h:])
    else:
        lb.value = "\n".join(log_lines)
    lb.display()


def beautify(data):
    log_lines.append("{")
    for k,v in data.items():
        log_lines.append("    {}: {}".format(k,v))
    log_lines.append("}")
