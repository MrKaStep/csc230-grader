import getpass
from plumbum import local
from plumbum.machines.paramiko_machine import ParamikoMachine
from plumbum.path.utils import copy

def _once(f):
    res = None
    def wrapped(*args, **kwargs):
        nonlocal res
        if res is None:
            res = f(*args, **kwargs)
        return res
    return wrapped

@_once
def get_remote_machine_with_password(host, user):
    password = getpass.getpass(prompt=f"Password for {user}@{host}: ", stream=None)

    rem = ParamikoMachine(host, user=user, password=password)
    return rem


@_once
def get_remote_machine(host, user, keyfile):
    rem = ParamikoMachine(host, user=user, keyfile=keyfile)
    return rem


def get_local_machine():
    return local


def with_machine_rule(cls):
    old_init = cls.__init__
    def new_init(self, config):
        if "machine" not in config:
            machine_type = "local"
        else:
            machine_type = config["machine"]["type"]

        if machine_type == "local":
            self.machine = get_local_machine()
            self.files_to_copy = None
        elif machine_type == "remote":
            if "keyfile" in config["machine"]:
                self.machine = get_remote_machine(config["machine"]["host"], config["machine"]["user"], config["machine"]["keyfile"])
            else:
                self.machine = get_remote_machine_with_password(config["machine"]["host"], config["machine"]["user"])

            self.files_to_copy = config["machine"].get("files_to_copy")
        else:
            raise ValueError(f"Invalid machine type: {config['machine']['type']}")
        self.machine_type = machine_type
        old_init(self, config)
    cls.__init__ = new_init

    old_apply = cls.apply
    def new_apply(self, project):
        with self.machine.tempdir() as tempdir:
            project_path = tempdir / "project"
            project_path.mkdir()
            existing_files = set([f.name for f in project.root.list()])
            if self.files_to_copy:
                for fname in self.files_to_copy:
                    if fname in existing_files:
                        copy(project.root / fname, project_path / fname)
            else:
                for f in project.files():
                    if f.name in existing_files:
                        copy(f.path, project_path / f.name)

            with self.machine.cwd(project_path):
                self.session = self.machine.session()
                self.session.run(f"cd {project_path}")
                return old_apply(self, project)
    cls.apply = new_apply
        
    return cls

