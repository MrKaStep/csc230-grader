from grader.rules.rule import construct_rule
from grader.project import Project
from grader.review.reviewer import construct_reviewer

import grader.storage as storage

import argparse
import json
from plumbum import local



class ReviewApp:
    def __init__(self, config, rule_config, project_config):
        self.rule = construct_rule({"name": "compound", "config": rule_config})
        self.project_config = project_config
        self.project_root_template = config["project_root_template"]
        self.tag = config["review_tag"]

        self.reviewer = construct_reviewer(config["reviewer"]["name"], config["reviewer"]["config"])

        storage.init_storage(config["storage_path"])

        with open(config["students_list"]) as f:
            self.students = [l.strip() for l in f]

    def _project_root(self, student_id):
        return local.path(self.project_root_template.replace("STUDENT_ID", student_id))

    def do_review(self, student_id):
        project = Project(self.project_config, self._project_root(student_id))

        res = self.rule(project)
        review = self.reviewer(project, res)

        storage.add_review(student_id, self.tag, review)

    def review_all(self):
        for student_id in self.students:
            if storage.has_review(student_id, self.tag):
                continue
            self.do_review(student_id)


def handle_review(args):
    with open(args.config) as f:
        config = json.load(f)

    with open(args.rule_config) as f:
        rule_config = json.load(f)

    with open(args.project_config) as f:
        project_config = json.load(f)

    review_app = ReviewApp(config, rule_config, project_config)
    review_app.review_all()


def handle_export(args):
    with open(args.config) as f:
        config = json.load(f)

    storage.init_storage(config["storage_path"])
    reviews = storage.get_reviews()
    tags = set()
    with open(config["students_list"]) as f:
        students = [l.strip() for l in f]

    for student in students:
        for tag in reviews.get(student, {}):
            tags.add(tag)


    with open(args.file, "w") as f:
        for student in students:
            values = [student]
            for tag in tags:
                values.append(reviews.get(student, {}).get(tag, {}))
            f.write('\t'.join(values) + '\n')



def run():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", required=True)

    handlers = {
        "review": handle_review,
        "export": handle_export,
    }

    subparsers = parser.add_subparsers(title="actions", dest="action")
    review_parser = subparsers.add_parser("review", add_help=False)

    review_parser.add_argument("-r", "--rule-config", required=True)
    review_parser.add_argument("-p", "--project-config", required=True)

    export_parser = subparsers.add_parser("export", add_help=False)
    export_parser.add_argument("-f", "--file", required=True)

    args = parser.parse_args()


    handlers[args.action](args)

