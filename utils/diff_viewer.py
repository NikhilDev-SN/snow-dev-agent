import difflib


def generate_diff(old_script, new_script):

    diff = difflib.unified_diff(
        old_script.splitlines(),
        new_script.splitlines(),
        lineterm=""
    )

    return "\n".join(diff)