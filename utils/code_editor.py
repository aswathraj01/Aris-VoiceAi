import os

def write_to_file(filename, content):
    with open(filename, "w") as f:
        f.write(content)
    return f"Written to {filename}"

def append_to_file(filename, content):
    with open(filename, "a") as f:
        f.write("\n" + content + "\n")
    return f"Code appended to {filename}"

def replace_line(filename, line_number, new_content):
    with open(filename, "r") as f:
        lines = f.readlines()

    if 0 <= line_number < len(lines):
        lines[line_number] = new_content + "\n"
        with open(filename, "w") as f:
            f.writelines(lines)
        return f"Line {line_number + 1} replaced."
    else:
        return "Invalid line number."

def open_in_vscode(filepath):
    os.system(f"code {filepath}")