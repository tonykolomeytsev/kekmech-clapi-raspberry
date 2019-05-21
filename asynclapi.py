from threading import Thread, Lock
import json

# должна быть очередь из тасков, которые отправляются на МК. При этом некоторые таски не удаляются после выполнения
# например таск опроса дальномеров работает все время и только между запросами на дальномеры будут отправляться другие команды
# вот это реально боевые условия, посмотрим на скорость работы этого всего


class TaskPool():

    task_thread = None
    subscribers_thread = None
    tasks = list()
    subscribers = dict()
    task_lock = Lock()
    subscribers_lock = Lock()
    serial_lock = Lock()

    def __init__(self, serial_wrapper):
        self.serial_wrapper = serial_wrapper

    # главный входной метод, остальные лучше не запускать самостоятельно
    # добавление таска на выполнение, если все таски уже были выполнены и поток завершился,
    # создадим новый поток для выполнения тасков 
    # скорее всего в продакшене будут использованы бесконечные таски, которые не удаляются, а значит и поток
    # не будет завершаться
    def push_task(self, task):
        self.task_lock.acquire()
        self.tasks.append(task)
        if not self.task_thread.isAlive():
            self.task_thread = Thread(target=task_loop, daemon=False)
        self.task_lock.release()
    
    # добавление подписчика с колбэком, если всем подписчикам уже были отправлены сообщения и поток завершился,
    # создадим новый поток для рассылки подписчикам
    def push_subscriber(self, subscriber):
        self.subscribers_lock.acquire()
        self.subscribers.append(subscriber)
        if not self.subscribers_thread.isAlive():
            self.subscribers_thread = Thread(target=inbox_loop, daemon=False)
        self.subscribers_lock.release()
    
    # мейнлуп для выполнения тасков
    # если таск, это сообщение, то отправляем
    # если таск это запрос, то обрабатываем его отдельно
    # если таск помечен как бесконечный, то в конце возвращаем его обратно в список тасков
    def task_loop(self):
        while len(tasks):
            self.task_lock.acquire()
            cur_task = self.tasks.pop(0) # берем из начала

            if isinstance(cur_task, Push):
                self.serial_lock.acquire()
                self.serial_wrapper.push(cur_task.code, cur_task.args)
                self.serial_lock.release()
            
            if isinstance(cur_task, Request):
                self.process_request(cur_task)
            
            if cur_task.is_infinite:
                self.tasks.append(cur_task) # добавляем в конец
            self.task_lock.release()
    
    # обработка поступившего в список тасков запроса
    # реггистрируем подписчика и после этого шлем сообщение
    def process_request(self, request):
        self.serial_lock.acquire()
        self.push_subscriber(request)
        self.serial_wrapper.push(request.code, request.args)
        self.serial_lock.release()
        
    # мейнлуп для ожидания входящих сообщений
    # входящих сообщений не может прийти больше, чем зарегистрировано подписчиков (в том случае если все работает правильно)
    # если сообщение пришло без идентификационного номера (номер команды, на которую отвечают), то ВСЁ ПЛОХО
    def inbox_loop(self):
        while len(self.subscribers):
            self.subscribers_lock.acquire() # тут один лок внутри другого, это плохо
            self.serial_lock.acquire()
            response = json.loads(serial_wrapper.pull())
            self.serial_lock.release()
            code = response.get('code', -1)
            if code == -1:
                print('Response to the void:', response) # отвечать без идентификационного номера нельзя
                self.subscribers = []
                break
            else:
                target = subscribers.get(code, None)
                if target: # в теории подписчик по-любому должен быть, но на всякий случай надо перестраховаться
                    target.callback(response)
                    subscribers.pop(code, None)
                
            self.subscribers_lock.release()
    
    def reset():
        self.subscribers = dict()
        self.tasks = list()



class Task():
    
    is_infinite=False


        
class Push(Task):
    def __init__(self, code:int, *args):
        self.code = code
        self.args = args

class Request(Task):
    def __init__(self, callback, code:int, *args):
        self.code = code
        self.callback = callback
        self.args = args


        



