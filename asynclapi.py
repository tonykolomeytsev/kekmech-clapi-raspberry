from threading import Thread, Lock
import json

# должна быть очередь из тасков, которые отправляются на МК. При этом некоторые таски не удаляются после выполнения
# например таск опроса дальномеров работает все время и только между запросами на дальномеры будут отправляться другие команды
# вот это реально боевые условия, посмотрим на скорость работы этого всего


class TaskPool():

    task_thread = None # поток, отправляющий таски по очереди
    subscribers_thread = None # поток, принимающий входящие сообщения и сообщающий о них подписчикам
    tasks = list() # очередь из тасков
    subscribers = dict() # список подписчиков (CODE -> LISTENER) где CODE - код команды, на которую ожидается ответ
    task_lock = Lock() # локер для потокобезопасного обращения к списку тасков
    subscribers_lock = Lock() # локер для потокобезопасного обращения к списку подписчиков
    serial_lock = Lock() # локер для потокобезопасного обращения к экземпляру Serial

    def __init__(self, serial_wrapper):
        self.serial_wrapper = serial_wrapper

    # Добавление таска на выполнение. Главный входной метод, остальные лучше не запускать самостоятельно. 
    # Если все таски уже были выполнены и поток завершился, создадим новый поток для выполнения тасков.
    # Скорее всего в продакшене будут использованы бесконечные таски, которые не удаляются, а значит и поток
    # не будет завершаться
    def push_task(self, task):
        self.task_lock.acquire()
        self.tasks.append(task)
        if not self.task_thread or not self.task_thread.isAlive():
            self.task_thread = Thread(target=self.task_loop, daemon=False)
            self.task_thread.start()
        self.task_lock.release()
    
    # Добавление подписчика с колбэком. 
    # Если всем подписчикам уже были отправлены сообщения и поток завершился,
    # создадим новый поток для рассылки
    # Если подписчик с таким кодом уже дожидается сообщения в данный момент, то вернем True
    def push_subscriber(self, subscriber) -> bool:
        self.subscribers_lock.acquire()
        already_subscribed = (subscriber.code in self.subscribers) # вдруг ответа уже кто-то дожидается в данный момент
        self.subscribers[subscriber.code] = subscriber
        if not self.subscribers_thread or not self.subscribers_thread.isAlive():
            self.subscribers_thread = Thread(target=self.inbox_loop, daemon=False)
            self.subscribers_thread.start()
        self.subscribers_lock.release()
        return already_subscribed
    
    # Мейнлуп для выполнения тасков
    # Если таск, это сообщение, то отправляем
    # Если таск это запрос, то обрабатываем его отдельно в функции process_request()
    # Если таск помечен как бесконечный, то в конце возвращаем его обратно в список тасков
    def task_loop(self):
        while len(self.tasks):
            self.task_lock.acquire()
            cur_task = self.tasks.pop(0) # берем из начала

            if isinstance(cur_task, Push):
                self.serial_lock.acquire()
                self.serial_wrapper.push(cur_task.code, list(cur_task.args[0]))
                self.serial_lock.release()
            
            if isinstance(cur_task, Request):
                self.process_request(cur_task)
            
            if cur_task.is_infinite:
                self.tasks.append(cur_task) # добавляем в конец очереди
            self.task_lock.release()
    
    # Обработка поступившего в список тасков запроса
    # Регистрируем подписчика и после этого шлем команду
    # Если ранее была отправлена команда, на которую не пришел ответ, то подписчика
    # нового регистрируем вместо старого, но повторно команду не отправляем (ибо если уж зависать, так навсегда)
    def process_request(self, request):
        self.serial_lock.acquire()
        already_subscribed = self.push_subscriber(request)
        #if not already_subscribed:
        self.serial_wrapper.push(request.code, list(request.args[0]))
        self.serial_lock.release()
        
    # мейнлуп для ожидания входящих сообщений
    # входящих сообщений не может прийти больше, чем зарегистрировано подписчиков (в том случае если все работает правильно)
    # если сообщение пришло без идентификационного номера (номер команды, на которую отвечают), то ВСЁ ПЛОХО
    def inbox_loop(self):
        while len(self.subscribers):
            self.subscribers_lock.acquire() # тут один лок внутри другого, это плохо
            self.serial_lock.acquire()
            response = json.loads(self.serial_wrapper.pull())
            self.serial_lock.release()
            code = response.get('code', -1)
            if code == -1:
                print('Response to the void (response without CODE):', response) # отвечать без идентификационного номера нельзя
                self.subscribers = []
                break
            else:
                target = self.subscribers.get(code, None)
                if target: # в теории подписчик по-любому должен быть, но на всякий случай надо перестраховаться
                    if target.callback:
                        target.callback(response)
                    self.subscribers.pop(code, None)
                
            self.subscribers_lock.release()
    
    def reset(self):
        self.subscribers = dict()
        self.tasks = list()
        if (self.task_lock.locked()): self.task_lock.release()
        if (self.subscribers_lock.locked()): self.subscribers_lock.release()
        if (self.serial_lock.locked()): self.serial_lock.release()
    
    def __str__(self):
        response =  '\n\n  task_thread: '
        response += 'active' if self.task_thread and self.task_thread.isAlive() else 'stopped'
        for t in self.tasks:
            response += "\n[task] {}".format(t)
        
        response += '\n\n  subscribers_thread: '
        response += 'active' if self.subscribers_thread and self.subscribers_thread.isAlive() else 'stopped'
        for s in self.subscribers.itervalues():
            response += "\n[subscriber] {}".format(s)
        return response



class Task():
    _code = None
    _args = None

    def code(self, control_code:int):
        self._code = control_code
        return self

    def args(self, *control_args):
        self._args = control_args[0]
        return self
    
    def execute(self):
        return self



class Push(Task):
    def __str__(self):
        return "push {} with args {}".format(self.code, str(self.args))



class CallbackTask(Task):
    _callback = None

    def callback(self, control_callback):
        self._callback = control_callback
        return self
    
    def execute_async(self):
        return self



class Request(CallbackTask):
    def __str__(self):
        return "request {} with args {} callback {}".format(self._code, str(self._args), str(self._callback))



class LongPoll(CallbackTask):
    def __str__(self):
        return "long-poll {} with args {} callback {}".format(self._code, str(self._args), str(self._callback))
        
