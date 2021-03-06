from .reviewer import reviewer
from .decorators import with_csc230_render

from grader.project import Project
from grader.result import Result
from grader.util import create_tempfile, create_file

from contextlib import ExitStack
from enum import Enum

from tempfile import TemporaryDirectory

from plumbum import local
from plumbum.cmd import touch
from plumbum.path.utils import delete, copy

import os
import sys
import socket


class VscodeCommand(Enum):
    START = 1
    REVIEW = 2
    STOP = 3

WELCOME_MESSAGE = """Hi! This is a sample project you can use to set up your editor layout. It contains all the
files expected from a student, as well as some extra files (`review.txt`, `messages.txt`). You can also create and
open your own files that you expect to be created (i.e. `COMPILATION_linker`) generated by `CompilationRule`, they
will be picked up when running on an actual project. Enjoy!
"""


@reviewer
@with_csc230_render
class VscodeReviewer:
    def __init__(self, config):
        review_filename = config.get("review_filename", "review.txt")
        messages_filename = config.get("messages_filename", "messages.txt")

        self._dir = TemporaryDirectory()
        self.dir = local.path(self._dir.name)

        self.project_path = self.dir / "project"
        self.review_path = self.project_path / review_filename
        self.messages_path = self.project_path / messages_filename

        sock_path = self.dir / "sock"
        sock = socket.socket(socket.AF_UNIX)
        sock.bind(sock_path)
        sock.listen(1)

        dummy_project_path = config["dummy_project"]
        self._prepare_project_dir(dummy_project_path)
        
        with create_tempfile(WELCOME_MESSAGE, suffix=".md") as welcome_file:
            vscode = local["code"].with_env(GRADER_WORKDIR=self.dir)
            vscode("-n", self.dir, welcome_file.name)

            self.vscode_sock, _ = sock.accept()

            assert self._get_message() == VscodeCommand.START

        self.review_file.close()

    def __del__(self):
        self._send_string("__stop")

    def _get_message(self):
        raw_message = int.from_bytes(self.vscode_sock.recv(1), sys.byteorder)
        return VscodeCommand(raw_message)

    def _send_string(self, s):
        b = bytes(s, "ascii")
        self.vscode_sock.send(b)

    def _prepare_project_dir(self, project_path, result=None):
        delete(self.project_path)
        copy(project_path, self.project_path)

        if result is None:
            result = Result()
            result.penalty = 1
            result.comments = ["This is an example review"]
            result.messages = [f"Example message {i}" for i in range(1, 4)]
            result.custom = {"EXAMPLE_CUSTOM_NAME": "Example custom contents"}
        review, messages = self.render_result(result)
        
        self.review_file = create_file(self.review_path, review, mode="w+")
        create_file(self.messages_path, messages)

        for name, contents in result.custom.items():
            create_file(self.project_path / name, contents)


    def _get_review(self):
        assert self.review_file is not None
        self.review_file.seek(0)
        review = self.review_file.read()
        review = review.split('\n')[0]
        
        return review


    def review(self, project: Project, result: Result):
        self._prepare_project_dir(project.root, result)
        self._send_string(project.root.name)
        assert self._get_message() == VscodeCommand.REVIEW
        return self._get_review()



