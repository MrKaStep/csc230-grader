from .rule import rule

from grader.project import Project, File
from grader.result import Result
from grader.rules.decorators import occurence_counter, per_source_file, per_module, binary_rule
from grader.util import get_symbols


def get_symbol_comments(code_path, symbols):
    in_comment = False
    proper_comment = False
    comment_just_ended = False

    level = 0
    param_tags = 0
    return_tags = 0

    comments = {}
    found_symbols = []
    messages = []

    with open(code_path, "r") as f:
        for l in f:
            line = l.strip()
            if line.startswith("//"):
                continue

            if len(line) == 0:
                continue

            if not in_comment and line.startswith("/*"):
                in_comment = True
                proper_comment = (line == "/**")


            if in_comment:
                param_tags += line.count("@param")
                return_tags += line.count("@return")
            else:
                if level == 0:
                    for s in symbols:
                        if line.count(f"{s}(") == 1 or line.count(f"{s} (") == 1:
                            found_symbols.append(s)

                            if comment_just_ended:
                                param_count = line.count(",") + 1
                                if line.count("()") != 0 or line.count("( )") != 0 or line.count("( void )") != 0 or line.count("(void)") != 0:
                                    param_count = 0

                                tokens = line.split()
                                return_type = "void" if (tokens[0] == "void" or tokens[1] == "void") else "type"

                                comments[s] = {
                                    "param_count": param_count,
                                    "param_tags": param_tags,
                                    "return_tags": return_tags,
                                    "return_type": return_type,
                                }

                level += line.count("{") - line.count("}")

                comment_just_ended = False
                param_tags = 0
                return_tags = 0
                in_comment = False
                proper_comment = False
                
            if line.endswith("*/"):
                in_comment = False
                comment_just_ended = True
                if line.startswith("/*"):
                    comment_just_ended = False

    return {
        "comments": comments,
        "symbols": found_symbols,
        "messages": messages,
    }


def check_comments(source_path, header_path):
    assert source_path.endswith(".c")
    if not source_path.exists():
        return {"messages": [f"{source_path.name} does not exist"]}

    explanation = []
    messages = []

    symbols = get_symbols(source_path)

    header_res = get_symbol_comments(header_path, symbols) if header_path else None
    source_res = get_symbol_comments(source_path, symbols)

    # messages.append(f"{os.path.basename(source_path)}: {source_res}")
    messages += source_res["messages"]
    if header_res:
        # messages.append(f"{os.path.basename(header_path)}: {header_res}")
        messages += header_res["messages"]
    
    misplaced_comments = 0
    missing_comments = 0
    missing_tags = 0
    duplicate_comments = 0


    for symbol in symbols:
        comment = None
        if header_res and symbol in header_res["comments"]:
            comment = header_res["comments"][symbol]

        if symbol in source_res["comments"]:
            if header_res and symbol in header_res["symbols"]:
                c = f"{symbol}: comment in source instead of a header"
                misplaced_comments += 1
                # messages.append(c)

            if comment is None:
                comment = source_res["comments"][symbol]
            else:
                source_comment = source_res["comments"][symbol]
                source_tag_count = source_comment["param_tags"] + source_comment["return_tags"]
                tag_count = comment["param_tags"] + comment["return_tags"]
                if source_tag_count > tag_count:
                    comment = source_comment

                if source_tag_count == tag_count and tag_count > 0:
                    duplicate_comments += 1 


        if not comment:
            missing_comments += 1
            c = f"{symbol}: missing comment"
            # messages.append(c)
            explanation.append(c)
        else:
            missing_tags_delta = 0
            if comment["return_type"] != "void" and comment["return_tags"] == 0:
                missing_tags_delta += 1
                c = f"{symbol}: missing @return tag"
                # messages.append(c)
                explanation.append(c)

            if comment["param_count"] > comment["param_tags"]:
                missing_tags_delta += comment["param_count"] - comment["param_tags"]
                c = f"{symbol}: missing {comment['param_count'] - comment['param_tags']} @param tag(s)"
                # messages.append(c)
                explanation.append(c)

            missing_tags += min(2, missing_tags_delta)

    return {
        "explanation": explanation,
        "misplaced_comments": misplaced_comments,
        "missing_comments": missing_comments,
        "missing_tags": missing_tags,
        "duplicate_comments": duplicate_comments,
        "messages": messages,
    }


@rule
@per_source_file(annotate_comments=True)
class FileCommentRule:
    def __init__(self, config):
        self.comment_penalty = config.get("missing_comment_penalty", 1)
        self.tag_penalty = config.get("tag_penalty", 0.5)

    def apply(self, f: File):
        res = Result()
        with open(f.path, "r") as code:
            c = code.read().strip()
            if not c.startswith("/*"):
                res.penalty += self.comment_penalty
                res.comments.append("Missing file comment")
            else:
                if not c.count("@author") > 0:
                    res.penalty += self.tag_penalty
                    res.comments.append("Missing @author tag")
                if not c.count("@file") == 1:
                    res.penalty += self.tag_penalty
                    res.comments.append("Missing @file tag")
        return res


@rule
@per_module(annotate_comments=False)
class FunctionCommentsRule:
    def __init__(self, config):
        self.duplicate_comments_penalty = config.get("duplicate_comments_penalty", 0)
        self.comment_penalty = config.get("missing_comment_penalty", 1)
        self.comment_penalty_limit = config.get("missing_comment_penalty_limit", 10)
        self.tag_penalty = config.get("missing_tag_penalty", 0.5)
        self.tag_penalty_limit = config.get("missing_tag_penalty_limit", 5)

    def apply(self, module):
        res = Result()
        check = check_comments(module.sources[0].path, module.header.path if module.header else None)
        res.comments += check["explanation"]
        res.messages += check["messages"]

        res.penalty += min(self.comment_penalty_limit, self.comment_penalty * check["missing_comments"])
        res.penalty += min(self.tag_penalty_limit, self.tag_penalty * check["missing_tags"])

        return res

@rule
@occurence_counter
@per_module(annotate_comments=False)
class MisplacedCommentsRule:
    def __init__(self, config):
        pass

    def apply(self, module):
        res = Result()
        check = check_comments(module.sources[0].path, module.header.path if module.header else None)

        res.penalty = check["misplaced_comments"]

        if res.penalty:
            res.comments.append("For functions that have a prototype in the header, the comment should be in the header, not the source")

        return res
