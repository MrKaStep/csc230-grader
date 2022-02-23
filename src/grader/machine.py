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


def get_local_machine():
    return local


def with_machine_rule(cls):
    old_init = cls.__init__
    def new_init(self, config):
        old_init(self, config)
        if "machine" not in config:
            machine_type = "local"
        else:
            machine_type = config["machine"]["type"]

        if machine_type == "local":
            self.machine = get_local_machine()
        elif machine_type == "remote":
            self.machine = get_remote_machine_with_password(config["machine"]["host"], config["machine"]["user"])
        else:
            raise ValueError(f"Invalid machine type: {config['machine']['type']}")
        self.machine_type = machine_type
    cls.__init__ = new_init

    old_apply = cls.apply
    def new_apply(self, project):
        with self.machine.tempdir() as tempdir:
            project_path = tempdir / "project"
            copy(project.root, project_path)

            with self.machine.cwd(project_path):
                session = self.machine.session()
                session.run(f"cd {project_path}")

            return old_apply(self, project, session)
    cls.apply = new_apply
        

    # old_del = cls.__del__
    # def new_del(self):
    #     if self.machine_type == "remote":
    #         self.machine.close()
    #     old_del(self)
    # cls.__del__ = new_del

    return cls

