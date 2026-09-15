class HookRegistry:
    def __init__(self):
        self.listeners = {}

    def register(self, hook_name, func):
        if hook_name not in self.listeners:
            self.listeners[hook_name] = []
        if func not in self.listeners[hook_name]:
            self.listeners[hook_name].append(func)

    def execute(self, hook_name, data, **kwargs):
        """
        Executes all registered functions for a hook in order.
        Each function must return the modified `data`.
        """
        if hook_name in self.listeners:
            for func in self.listeners[hook_name]:
                data = func(data, **kwargs)
        return data

registry = HookRegistry()
