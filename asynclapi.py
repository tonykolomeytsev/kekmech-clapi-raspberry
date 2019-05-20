from threading import Thread
import json

# должна быть очередь из тасков, которые отправляются на МК. При этом некоторые таски не удаляются после выполнения
# например таск опроса дальномеров работает все время и только между запросами на дальномеры будут отправляться другие команды
# вот это реально боевые условия, посмотрим на скорость работы этого всего


class TaskPool():

    def __init__(self, *args, **kwargs):
        self.tasks = []
        return super().__init__(*args, **kwargs)

    def push_task(self, task):
        self.tasks += task

    def start(self):
        self.ithread = Thread(target=main_loop, daemon=False)
        self.ithread.start()
    
    def main_loop(self):
        while True:
            pass # делаем таски



class Task():

    # код команды и аргументы
    def __init__(self, infinite, code, *args):
        return super().__init__(*args, **kwargs)



