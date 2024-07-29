class Prop:
    def __init__(self, name: str, value: str):
        self.name = name
        self.value = value

class Status:
    def __init__(self, value_int: int = None, value_str: str = None):
        self.value_int = value_int
        self.value_str = value_str

class Device:
    def __init__(self, name: str):
        self.name = name
        self.status: Status = Status()
        self.metadata: dict = {}
        self.props: list[Prop] = []
        self.cmds: dict = {}