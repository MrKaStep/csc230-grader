import json
import os

from copy import deepcopy

class ReviewStorage:
    def __init__(self, path):
        self.path = path
        if os.path.exists(self.path):
            with open(self.path) as f:
                self.data = json.load(f)
        else:
            self.data = {}

    def _persist(self):
        with open(self.path, "w") as f:
            json.dump(self.data, f, indent='\t')

    def _has_review(self, student_id, tag):
        return tag is not None and student_id in self.data and tag in self.data[student_id]

    def _add_review(self, student_id, tag, review):
        if tag is None:
            return
        if student_id not in self.data:
            self.data[student_id] = {}
        self.data[student_id][tag] = review
        self._persist()

    def _delete_review(self, student_id, tag):
        if tag is None:
            return
        if self.has_review(student_id, tag):
            del self.data[student_id][tag]
        self.persist()

    def _get_reviews(self, tag):
        if tag is None:
            return deepcopy(self.data)
        return {s: r[tag] for s, r in self.data.items()}

    def _get_review(self, student_id, tag):
        if tag is None:
            return deepcopy(self.data[student_id])
        return self.data[student_id][tag]


_instance = None


def _get_instance():
    global _instance
    if _instance is None:
        raise RuntimeError("Review storage not initialized")
    return _instance


def init_storage(path):
    global _instance
    if _instance is not None:
        raise RuntimeError("Review storage already initialized")
    _instance = ReviewStorage(path)


def has_review(student_id, tag):
    return _get_instance()._has_review(student_id, tag)


def add_review(student_id, tag, review):
    _get_instance()._add_review(student_id, tag, review)


def delete_review(student_id, tag):
    _get_instance()._delete_review(student_id, tag)


def get_reviews(tag=None):
    return _get_instance()._get_reviews(tag)

def get_review(student_id, tag=None):
    return _get_instance()._get_review(student_id, tag)

