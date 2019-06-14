"""
Дополнение к библиотеке Clapi, добавляющее асинхронные запросы к устройствам.
Внешний вид API максимально приближен к API запросов HTTP.
Прямой вызов функций и классов из этого файла предусмотрен только для дебага,
для всех остальных случаев лучше использовать Clapi, который всё сделает за вас.
"""

from threading import Thread, Lock
import json
import time

# должна быть очередь из тасков, которые отправляются на МК. При этом некоторые таски не удаляются после выполнения
# например таск опроса дальномеров работает все время и только между запросами на дальномеры будут отправляться другие команды
# вот это реально боевые условия, посмотрим на скорость работы этого всего


class TaskPool():

    def __init__(self, serial_wrapper):
        self.serial_wrapper = serial_wrapper
        self.running = True
        self.main_thread = None # поток, отправляющий таски по очереди
        self.tasks = list() # очередь из тасков
        self.subscribers = dict() # список подписчиков (CODE -> LISTENER) где CODE - код команды, на которую ожидается ответ
        self.task_lock = Lock() # локер для потокобезопасного обращения к списку тасков

    # Добавление таска на выполнение. 
    def push_task(self, task):
        self.task_lock.acquire()
        self.tasks.append(task)
        # если поток по каким-то причинам мертв, то создадим и запустим его
        if not self.main_thread or not self.main_thread.isAlive():
            self.main_thread = Thread(target=self.main_loop, daemon=False) # daemon=True for force terminating
            self.main_thread.start()
        self.task_lock.release()

    # Добавление подписчика (слушателя) входящих сообщений
    def push_subscriber(self, s):
        self.subscribers[s._code] = s
    
    # Мейнлуп для выполнения тасков
    # Сначала обрабатываем входящие сообщения, потом отправляем
    def main_loop(self):
        while self.running:
            self.task_lock.acquire()
            # принимаем все входящие сообщения
            self.process_input()
            if len(self.tasks):
                self.process_output()
            else:
                time.sleep(0) # аналог thread.yield() в других языках
            self.task_lock.release()
    
    # Обрабатываем все входящие сообщения.
    # Если пришел ответ на LongPoll, сообщаем о нем подписчику и заново добавляем LongPoll в список тасков
    def process_input(self):
        while self.serial_wrapper.inWaiting():
            response = json.loads(self.serial_wrapper.pull())
            code = response.get('code', -1)
            if code == -1:
                print('Response to the void (response without CODE):', response) # отвечать без идентификационного номера нельзя
            else:
                target = self.subscribers.get(code, None)
                if target: # в теории подписчик по-любому должен быть, но на всякий случай надо перестраховаться
                    if target._callback: # в теории по-любому будет callback, но мы то знаем ;)
                        target._callback(response)
                    self.subscribers.pop(code, None)
                    if isinstance(target, LongPoll): # если выполненный таск был long-poll, то заново добавляем его в список тасков
                        self.push_task(target)

    # Берем из начала очереди таск, делаем с ним что нужно. В очередь никого не возвращаем.
    # LongPoll будет возвращен в очередь в методе process_input() после того как на этот таск придет ответ.
    def process_output(self):
        cur_task = self.tasks.pop(0) # берем из начала

        if isinstance(cur_task, Push):
            self.serial_wrapper.push(cur_task._code, list(cur_task._args))
        
        if isinstance(cur_task, Request) or isinstance(cur_task, LongPoll):
            self.push_subscriber(cur_task) # добавляем подписчика
            self.serial_wrapper.push(cur_task._code, list(cur_task._args))

    def reset(self):
        self.subscribers = dict()
        self.tasks = list()
        if (self.task_lock.locked()): self.task_lock.release()
    
    def __str__(self):
        response =  '\nmain_thread: '
        response += 'active' if self.main_thread and self.main_thread.isAlive() else 'stopped'
        if len(self.tasks):
            for t in self.tasks:
                response += "\n[task] {}".format(t)
        else:
            response += "\nno tasks"
        if len(self.subscribers):
            for s in self.subscribers.values():
                response += "\n[subscriber] {}".format(s)
        else:
            response += "\nno subscribers"
        return response



class Task():

    def __init__(self, control_code, *control_args):
        self._code = control_code
        self._args = control_args
        self._executor = None

    def code(self, control_code:int):
        self._code = control_code
        return self

    def args(self, *control_args):
        self._args = control_args
        return self
    
    def execute(self):
        if self._executor:
            self._executor(self)



class Push(Task):

    def __str__(self):
        return "Push(code={}, args={})".format(self._code, str(self._args))



class CallbackTask(Task):
    
    def __init__(self):
        self._callback = None

    def callback(self, control_callback):
        self._callback = control_callback
        return self



class Request(CallbackTask):
    def __str__(self):
        return "Request(code={}, args={}, callback={})".format(self._code, str(self._args), str(self._callback))



class LongPoll(CallbackTask):
    def __str__(self):
        return "LongPoll(code={}, args={}, callback={})".format(self._code, str(self._args), str(self._callback))
        
