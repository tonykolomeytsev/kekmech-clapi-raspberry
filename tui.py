import npyscreen
import curses
import re
import clapi as api



tui = None # TUI instance here



class ClapiTUI(npyscreen.StandardApp):
    def onStart(self):
        self.offset = 0
        self.main_form = self.addForm("MAIN", MainFrame, name="Clapi TUI") # view
        self.data = ClapiTUIData()

    def process_cmd(self, cmd):
        log_view = self.main_form.log_view
        input_view = self.main_form.input_view
        current_device = self.data.current_device
        
        def callback_add_response(data):
            self.data.log("RESPONSE\n" + self.beautify_json(data))
            self.scroll_end()
        
        try:
            # LOGIC
            chain = re.split(r'\s+' ,cmd.strip().upper())
            
            cmd_code = int(chain[1], 16)
            cmd_args = [float(chain[i]) for i in range(2, len(chain))] if len(chain) > 2 else []
            
            if chain[0] == "R":
                cmd_type = "REQUEST"
                getattr(api, current_device)\
                    .request_async(cmd_code)\
                    .args(*cmd_args)\
                    .callback(callback_add_response)\
                    .execute()
                    
            if chain[0] == "P":
                cmd_type = "PUSH"
                getattr(api, current_device)\
                    .push_async(cmd_code)\
                    .args(*cmd_args)\
                    .execute()
            
            text_to_print = '{} {} {}'.format(cmd_type, chain[1], cmd_args)
        except:
            text_to_print = 'Error while parsing command {} for {}\n{}\n'.format(cmd, current_device,chain)
        
        # VIEW
        self.data.log(text_to_print)
        self.clear_view()

    def clear_view(self):
        self.scroll_end()
        self.main_form.input_view.value = ""
        self.main_form.input_view.display()

    def scroll_end(self):
        self.offset = 0
        self.main_form.log_view.value = self.data.scrolled_lines(
            offset=self.offset,
            lines_count=self.main_form.log_view._real_height - 2)
        self.main_form.log_view.display()
        
    def scroll_up(self):
        h = self.main_form.log_view._real_height - 2
        self.offset += 1 if len(self.data.log_lines) - self.offset > h else 0
        self.main_form.log_view.value = self.data.scrolled_lines(
            offset=self.offset,
            lines_count=h)
        self.main_form.log_view.display()
        
    def scroll_down(self):
        h = self.main_form.log_view._real_height - 2
        self.offset -= 1 if self.offset > 0 else 0
        self.main_form.log_view.value = self.data.scrolled_lines(
            offset=self.offset,
            lines_count=h)
        self.main_form.log_view.display()

    def beautify_json(self, data):
        response = "{\n"
        for k,v in data.items():
            response += "    {}: {}\n".format(k,v)
        response += "}"
        return response
    
    def check_current_device(self):
        self.data.check_current_device()
        self.main_form.log_view.name = "Log of {} device".format(self.data.current_device)
        self.main_form.log_view.display()

    def exit(self):
        exit(0)



class LogView(npyscreen.BoxTitle):
    _real_height = None
    _contained_widget = npyscreen.MultiLineEdit


    
class InputView(npyscreen.BoxTitle):
    _contained_widget = npyscreen.MultiLineEdit
    
    def when_value_edited(self):
        self.parent.parentApp.queue_event(npyscreen.Event("event_value_edited"))



class MainFrame(npyscreen.FormBaseNew):
    def create(self):
        y, x = self.useable_space()
        
        # TODO: split data and view
        devices_list = list(map(lambda x: str(x.id), api.core.devices)) if api.core.devices else []
        
        # DEVICES LIST
        self.dev_list = self.add(npyscreen.BoxTitle,
            name="Devices",
		    values=devices_list,
            rely=2,
            max_width=x // 3 - 5,
            max_height=y - 6)
        
        # MESSAGES LOG
        self.log_view = self.add(LogView, 
            name="Log", 
            footer="unsaved",
            relx=x // 3, 
            rely=2, 
            max_height=y - 9, 
            editable=False)
        
        self.log_view._real_height = y - 9 # = max_height (for scrolling)
        
        # INPUT BOX
        self.input_view = self.add(InputView, 
            relx=x // 3, 
            rely=y-7,
			max_height=3, 
            name="Input (press Enter to send)")
        
        # HELP
        self.add(npyscreen.FixedText, 
            rely=y - 3, 
            max_height=1,
            value="Exit: Ctrl+Q    Status: Ctrl+S    Nav: Tab\Shift+Tab")
        
        # HANDLERS
        new_handlers = { 
            "^Q": self.exit_func,
            curses.ascii.alt(chr(curses.KEY_UP)): self.on_scroll_up,
            curses.ascii.alt(chr(curses.KEY_DOWN)): self.on_scroll_down
        }
        self.add_handlers(new_handlers)
        self.add_event_hander("event_value_edited", self.on_message)
        
    def on_message(self, event):
        text = self.input_view.value
        if '\n' in text:
            tui.process_cmd(text.replace('\n', ''))
        tui.check_current_device()
        
    
    def exit_func(self, event):
        tui.exit()
    
    def on_scroll_up(self, event):
        tui.on_scroll_up()
        
    def on_scroll_down(self, event):
        tui.on_scroll_down()

    def get_devices_list():
        pass



class ClapiTUIData():
    
    def __init__(self):
        self.log_lines = list()
        self.current_device = None
        self.current_device_id = None

    def save_log_to(self, path_to_txt):
        pass

    def log(self, lines:str):
        self.log_lines += lines.split("\n")

    def scrolled_lines(self, offset:int, lines_count:int):
        if lines_count < len(self.log_lines):
            start = -lines_count-offset
            end = -offset
            return "\n".join(self.log_lines[start:end]) if end != 0 else "\n".join(self.log_lines[start:])
        else:
            return "\n".join(self.log_lines)
    
    def check_current_device(self):
        self.current_device_id = tui.main_form.dev_list.get_value()
        self.current_device = tui.main_form.dev_list.values[self.current_device_id]



def start(clapi_instance):
    global tui
    api.start()
    tui = ClapiTUI()
    tui.run()



if __name__=="__main__":
    print("For use clapi with TUI run clapi.py from terminal, not tui.py :)")






