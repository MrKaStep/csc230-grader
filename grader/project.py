from plumbum.path.base import Path

from enum import Enum

class FileType(Enum):
    SOURCE = 0
    HEADER = 1
    INPUT = 2
    OUTPUT = 3
    README = 4
    EXTRA = 5

class File:
    def __init__(self, filename: str, type: FileType, root: Path):
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
            self.source = File(config["source"], FileType.SOURCE, root)
            name = config["source"][:-2]
        else:
            self.source = None

        if "header" in config:
            self.header = File(config["header"], FileType.HEADER, root)
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


class ResourceSet:
    def __init__(self, config: dict, root: Path):
        self.root = root
        self.template = config["template"]
        self.start = config["start_index"]
        self.count = config["count"]
        if "name" in config:
            self.name = config["name"]
        else:
            self.name = self.template[:self.template.rfind("-")]

    def files(self):
        for i in range(self.start, self.start + self.count):
            yield File(self.template.format(i), FileType.EXTRA, self.root)


class Project:
    def __init__(self, config: dict, root: Path):
        self.modules = {}
        self.resources = []
        self.misc = []
        self.root = root
        for module in config["modules"]:
            m = Module(module, root)
            self.modules[m.name] = m

        for resource_set_config in config.get("resources", []):
            self.resources.append(ResourceSet(resource_set_config, root))

        for filename in config.get("misc", []):
            self.misc.append(File(filename, FileType.EXTRA, root))

    def files(self):
        for m in self.modules.values():
            yield from m.files()
        for r in self.resources:
            yield from r.files()
        yield from self.misc
    
    def source_files(self):
        for m in self.modules.values():
            yield from m.files()

    def resource_set_files(self, name: str):
        for r in self.resources:
            if r.name == name:
                yield from r.files()

    def __str__(self):
        return f"<Project {self.root}>"

