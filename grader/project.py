from plumbum.path.base import Path

class File:
    def __init__(self, filename: str, type: str, root: Path):
        self.name = filename
        self.type = type
        self.path = root / filename
        self.contents = None
        self.lines = None

    def read(self):
        if not self.contents:
            with open(self.path) as f:
                self.contents = f.read()
        return self.contents

    def readlines(self):
        if not self.lines:
            with open(self.path) as f:
                self.lines = f.readlines()
        return self.lines

    def __str__(self):
        return f"<File {self.path}>"


class Module:
    def __init__(self, config: dict, root: Path):
        self.root = root

        name = None
        if "source" in config:
            self.source = File(config["source"], "source", root)
            name = config["source"][:-2]
        else:
            self.source = None

        if "header" in config:
            self.header = File(config["header"], "header", root)
            name = config["header"][:-2]
        else:
            self.header = None

        if "name" in config:
            name = config["name"]

        if not name:
            raise ValueError("unable to determine module name")

        self.name = name

    def files(self):
        if self.source:
            yield self.source
        if self.header:
            yield self.header

    def __str__(self):
        return f"<Module {self.name} at {self.root}>"



class Project:
    def __init__(self, config: dict, root: Path):
        self.modules = {}
        self.root = root
        for module in config["modules"]:
            m = Module(module, root)
            self.modules[m.name] = m
    
    def files(self):
        for m in self.modules.values():
            yield from m.files()

    def __str__(self):
        return f"<Project {self.root}>"
