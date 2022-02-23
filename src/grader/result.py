class Result:
    def __init__(self):
        self.penalty = 0
        self.messages = []
        self.comments = []
        self.custom = {} 

    def __iadd__(self, other):
        self.penalty += other.penalty
        self.messages += other.messages
        self.comments += other.comments
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
        if int(self.penalty) == self.penalty:
            self.penalty = int(self.penalty)
        return f"-{self.penalty}{suffix}"

    def render_comments(self, end='.'):
        return " ".join((c + end for c in dict.fromkeys(self.comments)))

    def render_messages(self):
        return "\n".join(dict.fromkeys(self.messages))

