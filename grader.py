#!/usr/bin/env python3
import argparse
import json
import os
import re
import sys
import tempfile
import time

from collections import defaultdict

from contextlib import contextmanager

from functools import partial

from termcolor import colored

from plumbum import path, local, FG, BG, RETCODE, TF
from plumbum import SshMachine
from plumbum.machines.paramiko_machine import ParamikoMachine

from elftools.elf.elffile import ELFFile
from elftools.elf.sections import SymbolTableSection
from elftools.elf.enums import ENUM_ST_INFO_TYPE

from contextlib import ExitStack


STUDENTS = [id.strip() for id in open("students", "r")]
SUBMISSIONS_DIR = local.cwd / "submissions"
DATA_DIR = local.cwd / "data"

REVIEWS = defaultdict(lambda: {})
REVIEWS_PATH = ".reviews.json"


def move_subs():
    current = local.cwd
    all_subs = current / "Project-1"
    my_subs = current / "submissions"
    for student in STUDENTS:
        path.utils.copy(all_subs / student, my_subs / student)


def run(student, source_name, tests):
    gcc = local["gcc"]
    gcc = gcc["-g", "-Wall", "-std=c99", f"{source_name}.c", "-o", source_name]

    printed = False
    def print_header():
        nonlocal printed
        if not printed:
            print(colored(f"{student}:\n", "green"))
        printed = True

    def print_footer():
        nonlocal printed
        if printed:
            print("----------\n")

    with local.cwd(SUBMISSIONS_DIR / student):
        retcode, out, err = gcc.run(retcode=None)
        if err:
            print_header()
            if retcode:
                print(colored(err, "red"))
                print_footer()
                return
            else:
                print(colored(err, "yellow"))

        binary = local[f"./{source_name}"]
        output_file = local.cwd / "out"
        
        for input_file, expected_file in tests:
            try:
                retcode = ((binary < input_file) > output_file) & RETCODE(timeout=1)
                if retcode:
                    print_header()
                    print(f"{input_file.basename}: failed with exit code {retcode}")
                    continue

                diff_retcode = local["diff"][expected_file, output_file] & RETCODE

                if diff_retcode:
                    print_header()
                    print(f"{expected_file.basename}: output differs")
            except:
                print_header()
                print(f"{input_file.basename}: process timed out")

    print_footer()


def persist_reviews():
    with open(local.path(REVIEWS_PATH), "w") as f:
        json.dump(REVIEWS, f)


def load_reviews():
    global REVIEWS
    if local.path(REVIEWS_PATH).exists():
        with open(REVIEWS_PATH, "r") as f:
            REVIEWS = defaultdict(lambda: {}, json.load(f))


def run_all_tests():
    for student in STUDENTS:
        # run(student, "style", [(local.path("/dev/null"), DATA_DIR / "expected-s.txt")])
        run(student, "textbox", [
            (DATA_DIR / f"input-t{i}.txt", DATA_DIR / f"expected-t{i}.txt") for i in range(1, 5)
        ])


def convert_reviews_to_tsv():
    load_reviews()
    with open("reviews.tsv", "w") as f:
        for student in STUDENTS:
            f.write(REVIEWS[student]["compilation"] + '\t' + REVIEWS[student]["makefile"] + "\n")


def session_manager(template_path):
    with open(template_path, "r") as f:
        template = f.read()

    @contextmanager
    def manager(student, review_path, *args):
        session = template.replace("STUDENT_ID", student).replace("REVIEW_PATH", review_path)
        for i, arg in enumerate(args):
            session = session.replace(f"CUSTOM_ARG_{i + 1}", arg)
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".grading_session", delete=False)
        f.write(session)
        f.flush()
        try:
            yield f
        finally:
            f.close()

    return manager


def create_tempfiles(texts):
    files = []
    for text in texts:
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".grading")
        f.write(text)
        f.flush()
        files.append(f)

    return files
        

def find_magic_number(line):
    if line.strip().startswith("//") or line.strip().startswith("#define") or line.strip().startswith("/*") and line.strip().endswith("*/"):
        return None

    pattern = "(?<=[^a-zA-Z0-9_])[0-9]+"
    matches = re.findall(pattern, line)
    for m in matches:
        n = int(m)
        if n != 0 and n != 1:
            return n
    return None




def analyze_code(source_path):
    if not os.path.exists(source_path):
        return {
            "messages": [],
            "has_newline": True,
        }

    with open(source_path) as f:
        s = f.read()

    messages = []

    tabs = s.count('\t')
    if tabs > 0:
        messages.append(f"Found {tabs} hard tabs in {os.path.basename(source_path)}")

    carriages = s.count('\r')
    if carriages > 0:
        messages.append(f"Found {carriages} wrong line endings in {os.path.basename(source_path)}")
        s = s.replace('\r', '\n')

    comment = False
    for i, line in enumerate(s.split('\n')):
        if "/*" in line:
            comment = True
        if "*/" in line:
            comment = False
        if comment:
            continue

        n = find_magic_number(line)
        if n:
            messages.append(f"Magic number at {os.path.basename(source_path)}:{i+1}: {n}")

    return {
        "messages": messages,
        "has_newline": s.endswith('\n')
    }


def get_symbols(source_path):
    assert source_path.endswith(".c")
    basename = os.path.basename(source_path)

    clang = local["clang"]

    obj_path = source_path[:-1] + 'o'

    try:
        clang("-o", obj_path, "-c", source_path)
    except:
        return {"symbols": [], "messages": [f"{basename}: compilation failed"]}

    with open(obj_path, "rb") as f:
        elf = ELFFile(f)

        symtab = elf.get_section_by_name(".symtab")

        if not symtab:
            return {
                "messages": [f"{basename}: .symtab not found"],
            }

        num_symbols = symtab.num_symbols()

        messages = []
        symbols = []

        for i in range(num_symbols):
            symbol = symtab.get_symbol(i)
            symbol_type = symbol["st_info"]["type"]
            if symbol_type == "STT_FUNC":
                symbols.append(symbol.name)
                # messages.append(f"{basename}: symbol '{symbol.name}' with type {symbol_type} found")

        os.remove(obj_path)
        return {"symbols": symbols, "messages": messages}


def get_symbol_comments(code_path, symbols):
    in_comment = False
    proper_comment = False
    comment_just_ended = False

    report_flag = False

    level = 0
    param_tags = 0
    return_tags = 0

    comments = {}
    found_symbols = []
    messages = []

    with open(code_path, "r") as f:
        for l in f:
            line = l.strip()
            if line.count("reportFlags") > 0:
                report_flag = True
            if line.startswith("//"):
                continue

            if len(line) == 0:
                continue

            if not in_comment and line.startswith("/*"):
                report_flag = False
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

                            if comment_just_ended and not report_flag:
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

                report_flag = False
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

    has_file_comment = False
    has_author_tag = False
    has_file_tag = False
    with open(code_path, "r") as f:
        c = f.read().strip()
        has_file_comment = (c.startswith("/*"))
        has_author_tag = (c.count("@author") > 0)
        has_file_tag = (c.count("@file") == 1)

    return {
        "comments": comments,
        "symbols": found_symbols,
        "has_file_comment": has_file_comment,
        "has_author_tag": has_author_tag,
        "has_file_tag": has_file_tag,
        "messages": messages,
    }



def check_comments(source_path):
    assert source_path.endswith(".c")
    basename = os.path.basename(source_path)
    if not os.path.exists(source_path):
        return {"messages": [f"{basename} does not exist"]}

    header_path = source_path[:-1] + "h"

    if not os.path.exists(header_path):
        header_path = None

    explanation = []
    messages = []

    symbols_res = get_symbols(source_path)
    messages += symbols_res["messages"]
    symbols = symbols_res["symbols"]


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
    missing_file_comments = 0
    missing_file_tags = 0
    duplicate_comments = 0

    def update_file_comment_stats(res, path):
        nonlocal missing_file_tags
        nonlocal missing_file_comments
        if not res["has_file_comment"]:
            missing_file_comments += 1
            c = f"{os.path.basename(path)}: missing file comment"
            # messages.append(c)
            explanation.append(c)
        else:
            if not res["has_author_tag"]:
                missing_file_tags += 1
                c = f"{os.path.basename(path)}: missing @author tag"
                # messages.append(c)
                explanation.append(c)
            if not res["has_file_tag"]:
                missing_file_tags += 1
                c = f"{os.path.basename(path)}: missing @file tag"
                # messages.append(c)
                explanation.append(c)

    update_file_comment_stats(source_res, source_path)
    if header_path:
        update_file_comment_stats(header_res, header_path)

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
        "missing_file_comments": missing_file_comments,
        "missing_file_tags": missing_file_tags,
        "duplicate_comments": duplicate_comments,
        "messages": messages,
    }




def expand_message(message):
    macros = {
        # Formatting and magic numbers
        "CURLY1": "Incorrect curly bracket placement in function definitions",
        "CURLY2": "Incorrect curly bracket placement in control structures",
        "ASCII!": "No need to define ASCII codes, it only hurts readability. Use literals",
        "LIMITS": "No need to define LONG_MIN and LONG_MAX: they are defined in limits.h",
        # Block comments
        "HEADER": "For functions that have a prototype in the header, the comment should be in the header, not the source",
        "DUPLICATE": "Don't duplicate comments in both source AND header",
        "TOP": "File comments should start at the very top of the file",
    }

    for k, v in macros.items():
        message = message.replace(k, v)

    return message


def review():
    parser = argparse.ArgumentParser()
    parser.add_argument("-S", "--session", required=True)

    args = parser.parse_args()

    session = session_manager(args.session)
    
    load_reviews()
    vim = local["vim"]

    for student in STUDENTS:
        if student not in REVIEWS:
            with tempfile.NamedTemporaryFile(mode="w+t", suffix=".grading") as message:
                with session(student, message.name) as s:
                    sources = [SUBMISSIONS_DIR / student / base_name for base_name in [
                        "input.c",
                        "list.c",
                        "pattern.c",
                        "match.c"
                    ]]

                    score = 0
                    explanation = []
                    comments = []

                    # Comments grading
                    misplaced_comments = 0
                    missing_comments = 0
                    missing_tags = 0
                    missing_file_comments = 0
                    missing_file_tags = 0
                    duplicate_comments = 0

                    for source in sources:
                        res = check_comments(source)
                        comments += res["messages"]
                        if "explanation" not in res:
                            continue

                        explanation += res["explanation"]

                        misplaced_comments += res["misplaced_comments"]
                        missing_comments += res["missing_comments"]
                        missing_tags += res["missing_tags"]
                        missing_file_comments += res["missing_file_comments"]
                        missing_file_tags += res["missing_file_tags"]
                        duplicate_comments += res["duplicate_comments"]

                    misplaced_penalty = min(1, 0.5 * misplaced_comments)
                    if misplaced_comments:
                        explanation.append("HEADER")
                    missing_comment_penalty = min(10, missing_comments)
                    missing_tag_penalty = min(5, missing_tags * 0.5)
                    if duplicate_comments:
                        explanation.append("DUPLICATE")

                    missing_file_penalty = min(5, missing_file_comments + missing_file_tags * 0.5)

                    penalty = min(10, misplaced_penalty + missing_comment_penalty + missing_tag_penalty + missing_file_penalty)
                    score = round(-penalty, 1)
                    if round(score) == score:
                        score = int(score)
    
                    # Style grading

                    # missing_newlines = 0
                    # for source in sources:
                    #     res = analyze_code(source)
                    #     comments += res["messages"]
                    #     missing_newlines += 0 if res["has_newline"] else 1


                    # if missing_newlines > 2:
                    #     score -= 1
                    #     explanation.append("Missing newlines at the end of files")
                    # elif missing_newlines > 0:
                    #     score -= 0.5
                    #     explanation.append("Some missing newlines at the end of files")

                    message.write(f"{score if score != 0 else ''} {'. '.join(explanation)}\n\n" + '\n'.join(comments))
                    message.flush()


                    vim["-S", s.name] & FG
                    message.seek(0)
                    commenting = (message.read().split("\n"))[0] 
                    commenting = expand_message(commenting)
                    REVIEWS[student]["commenting"] = commenting
                    persist_reviews()


# TODO(mrkastep): rewrite with makefile?
def test_compilation(rem, source_files, cflags, ldflags):
    for s in source_files:
        assert s.endswith('.c')
        if not (rem.cwd / s).exists():
            return {
                "results": {
                    s: (0, "", "") for s in (source_files + ["linker"])
                },
                "failed": True,
                "messages": [f"{s} does not exist"],
            }

    # gcc = rem["gcc"]
    object_files = [s[:-1] + 'o' for s in source_files]

    compilation_failed = False
    compilation_results = {}

    session = rem.session()
    session.run(f"cd {rem.cwd}")

    compilation_results["linker"] = (0, "", "")

    for s, o in zip(source_files, object_files):
        args = cflags + ['-o', o, "-c", s]
        # print(' '.join(args))
        # retcode, out, err = gcc.run(args, retcode=None)
        retcode, out, err = session.run(' '.join(["gcc"] + args), retcode=None)
        if retcode:
            compilation_failed = True
        compilation_results[s] = (retcode, out, err)

    if not compilation_failed:
        args = object_files + ldflags + ['-o', "a.out"]
        # print(' '.join(args))
        # retcode, out, err = gcc.run(args, retcode=None)
        retcode, out, err = session.run(' '.join(["gcc"] + args), retcode=None)
        if retcode:
            compilation_failed = True
        compilation_results["linker"] = (retcode, out, err)

    rm = rem["rm"]["-f"]
    rm("a.out", *object_files)

    return {
        "results": compilation_results,
        "failed": compilation_failed,
        "messages": [],
    }


def review_compilation(vim_session, student, outputs):
    vim = local["vim"]
    with tempfile.NamedTemporaryFile(mode="w+t", suffix=".grading") as message:
        with ExitStack() as stack:
            files = [stack.enter_context(f).name for f in create_tempfiles(outputs)]
            with vim_session(student, message.name, *files) as s:
                vim["-S", s.name] & FG
                message.seek(0)
                compilation = (message.read().split("\n"))[0] 
                compilation = expand_message(compilation)
                REVIEWS[student]["compilation"] = compilation
                persist_reviews()


def get_built_files(make_output):
    files = []
    for l in make_output.strip().split('\n'):
        args = l.strip().split()
        found = False
        for i, arg in enumerate(args):
            if arg == '-o':
                assert i < len(args) - 1
                files.append(args[i + 1])
                found = True
                break

        if not found:
            if '-c' in args:
                source_count = 0
                source = None
                for arg in args:
                    if arg.endswith(".c"):
                        source_count += 1
                        source = arg
                if source_count == 1:
                    files.append(source[:-1] + 'o')

    return set(files)



def test_makefile(rem):
    with ExitStack() as stack:
        print(rem.cwd)
        initial_file_count = len(rem.cwd.list())
        session = rem.session()
        session.run(f"cd {rem.cwd}")

        stack.callback(partial(session.run, "rm -f *.o tour"))

        retcode, out, err = session.run("make", retcode=None)


        if retcode:
            return {
                "fail": "error",
                "retcode": retcode,
                "out": out,
                "err": err,
            }

        if not rem.path("tour").exists():
            return {
                "fail": "exists",
                "retcode": retcode,
                "out": out,
                "err": err,
            }

        expected_files = set(["map.o", "input.o", "tour.o", "tour"])

        for l in out.strip().split("\n"):
            if not l.strip().startswith("gcc"):
                return {
                    "fail": f"weird_not_gcc: '{l}'",
                    "retcode": retcode,
                    "out": out,
                    "err": err,
                }

            if "tour" in l.split() and l.count("tour.c") > 0:
                return {
                    "fail": f"weird_direct_source: '{l}'",
                    "retcode": retcode,
                    "out": out,
                    "err": err,
                }


        found_files = get_built_files(out)
        if found_files != expected_files:
            return {
                "fail": f"weird_mismatched_files: {list(found_files)}",
                "retcode": retcode,
                "out": out,
                "err": err,
            }

        time.sleep(2)
        session.run("touch map.h")
        retcode, out, err = session.run("make", retcode=None)

        if retcode:
            return {
                "fail": "error",
                "retcode": retcode,
                "out": out,
                "err": err,
            }

        expected_files = set(["map.o", "tour.o", "tour"])
        found_files = get_built_files(out)
        if found_files != expected_files:
            return {
                "fail": f"select: rebuilt files {list(found_files)}",
                "retcode": retcode,
                "out": out,
                "err": err,
            }

        retcode, out, err = session.run("make clean", retcode=None)
        file_count = len(rem.cwd.list())
        if file_count != initial_file_count:
            return {
                "fail": f"clean: initial {initial_file_count}, final {file_count}",
                "retcode": retcode,
                "out": out,
                "err": err,
            }

        return {
            "fail": None
        }


def review_makefile(vim_session, student, res):
    explanation = f'{res["fail"]}\nstdout:\n{res["out"]}\nstderr:\n{res["err"]}'
    vim = local["vim"]
    with tempfile.NamedTemporaryFile(mode="w+t", suffix=".grading") as message:
        with create_tempfiles([explanation])[0] as f:
            with vim_session(student, message.name, f.name) as s:
                vim["-S", s.name] & FG
                message.seek(0)
                makefile = (message.read().split("\n"))[0] 
                makefile = expand_message(makefile)
                REVIEWS[student]["makefile"] = makefile
                persist_reviews()




def grade_compilation_and_makefile():
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--password_file")
    parser.add_argument("-s", "--session", required=True)
    parser.add_argument("-m", "--makefile-session", required=True)

    args = parser.parse_args()

    vim_session = session_manager(args.session)

    password = None
    if args.password_file is not None:
        with open(args.password_file, 'r') as f:
            password = f.read()

    rem = ParamikoMachine("remote.eos.ncsu.edu", user="skalini", password=password.strip())
    rem.cwd.chdir(rem.cwd / "project4" / "submissions")

    source_files = ["input.c", "map.c", "tour.c"]
    cflags = ["-std=c99", "-Wall", "-D_GNU_SOURCE"]
    ldflags = ["-lm"]


    for student in STUDENTS:
        if student in REVIEWS and "compilation" in REVIEWS[student]:
            continue

        print(student)
        
        with rem.cwd(rem.cwd / student):
            res = test_compilation(rem, source_files, cflags, ldflags)

            need_review = False

            for s, report in res["results"].items():
                retcode, out, err = report
                if retcode or out.strip() or err.strip():
                    # print(s, retcode, out, sep='\n', end="==========\n")
                    need_review = True

            if need_review:
                review_compilation(vim_session, student, [f'stdout:\n{res["results"][s][1]}\nstderr:\n{res["results"][s][2]}' for s in source_files + ["linker"]])
            else:
                REVIEWS[student]["compilation"] = ""
                persist_reviews()


    make_vim_session = session_manager(args.makefile_session)
    for student in STUDENTS:
        if student in REVIEWS and "makefile" in REVIEWS[student]:
            continue
        
        print(student)
        with rem.cwd(rem.cwd / student):
            res = test_makefile(rem)
            if not res["fail"]:
                REVIEWS[student]["makefile"] = ""
                persist_reviews()
            else:
                review_makefile(make_vim_session, student, res)





    rem.close()



def main():
    load_reviews()
    convert_reviews_to_tsv()
    # review()

    # grade_compilation_and_makefile()


if __name__ == "__main__":
    main()
































