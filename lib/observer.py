class Subscriber:
    def notify(self, obj, param, value):
        pass
        # print("{} has changed {} to {}".format(obj, param, value))

class Notifier:
    def __setattr__(self, name, value):
        super().__setattr__(name, value)
        for subscriber in getattr(self, '_subscribers', []):
            subscriber.notify(self, name, value)

    def subscribe(self, obj):
        if not getattr(self, "_subscribers", None):
            self._subscribers = []
        self._subscribers.append(obj)