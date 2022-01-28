class Result:
    def __init__(self):
        self.penalty = 0
        self.messages = []
        self.comments = []
        self.custom = {} 

    def __iadd__(self, other):
        self.penalty += other.penalty
        self.messages += other.messages
        self.comments += other.messages
        self.custom = {**self.custom, **other.custom}
        return self

    def __add__(self, other):
        res = deepcopy(self)
        res += other
        return res

    def __str__(self):
        return f"<Result penalty: {self.penalty} comments: {'. '.join(self.comments)}>"

    def render_penalty(self, suffix=''):
        if self.penalty == 0:
            return "c"
        return f"-{self.penalty}{suffix}"

    def render_comments(self, end='.'):
        return " ".join((c + end for c in set(self.comments)))

    def render_messages(self):
        return "\n".join(set(self.messages))

