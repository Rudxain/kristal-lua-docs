#!/usr/bin/env python3
from typing import Final
import os
import subprocess
import re

# I wrote this script almost entirely using copilot bc i dont know python
# so it might be a mess or doing bad things but it works

# git clone the repository at https://github.com/KristalTeam/Kristal.git using the subprocess module, or update it if it already exists
subprocess.call(['git', 'submodule', 'update', '--init', '--remote', "Kristal"])

SRC_PATH = os.path.join("Kristal", "src")

ignore: Final = [
    os.path.join("engine", "loadthread.lua"),
    os.path.join("engine", "loadstate.lua"),
    os.path.join("utils", "graphics.lua"),
    os.path.join("teststate.lua"),

    # TODO: Should be accessible, but as variables of Kristal
    os.path.join("engine", "menu", "menu.lua"),
    os.path.join("engine", "shaders.lua"),
    os.path.join("engine", "overlay.lua"),
]

copy: Final = [
    os.path.join("engine", "vars.lua"),
    os.path.join("engine", "statevars.lua"),
    os.path.join("engine", "vendcust.lua"),
]

scripts: list[str] = []
copy_scripts: list[str] = []

# Loop through the files recursively inside the "Kristal/src" directory, excluding the "lib" directory
for root, dirs, files in os.walk(SRC_PATH, topdown=False):
    for name in files:
        # Get the path of the file relative to the "Kristal/src" directory
        path = os.path.join(root, name)[len(SRC_PATH) + 1:]
        # If the file is a .lua file, and it's not in the "lib" directory, add it to the scripts list
        if path.endswith(".lua") and not path.startswith("lib"+os.path.sep):
            if path in copy:
                copy_scripts.append(path)
            elif not path in ignore:
                scripts.append(path)

# If we have a "library" folder, delete it and all of its contents
if os.path.exists("library"):
    for root, dirs, files in os.walk("library", topdown=False):
        for name in files:
            os.remove(os.path.join(root, name))
        for name in dirs:
            os.rmdir(os.path.join(root, name))
    os.rmdir("library")

# Create a new "library" folder
os.mkdir("library")

event_calls: list[str | None] = []

# Now we read each script file and process it
for script in scripts:
    functions: list[tuple[str | None, str | None]] = []
    classes: list[tuple[str | None, str | None]] = []
    aliases: list[str | None] = []

    # Read the script file
    with open(os.path.join(SRC_PATH, script)) as f:
        data = f.read()

        print(f"Processing {script}...")

        # Find all functions in the script file, and add them to the functions list
        for match in re.finditer(r"((?:^---.*$\n)+)?^function (\S+\(.*\))", data, flags=re.M):
            functions.append((match.group(1), match.group(2)))

        # Find the first class definition in the script file, and add it to the classes list
        for match in re.finditer(r"((?:^---.*$\n)+)?^local ([^\s,]+)(?:, super)? = (?:(?:Class)|(?:{}))", data, flags=re.M):
            classes.append((match.group(1), match.group(2)))
            break

        # Find all events being called
        for match in re.finditer(r"Kristal\.(?:(?:callEvent)|(?:modCall))\(\"(\S+)\"", data):
            if not match.group(1) in event_calls:
                event_calls.append(match.group(1))

        # Find standalone documentation comments (usually aliases)
        for match in re.finditer(r"((?:^---.*$[\r\n]*)+)$(?!\n\S)", data, flags=re.M):
            aliases.append(match.group(1))

    # Create a new file in the "library" folder matching the script file name, creating the directory if it doesn't exist
    os.makedirs(os.path.join("library", os.path.dirname(script)), exist_ok=True)
    with open(os.path.join("library", script), "w") as f:
        # Write the script file name as a comment
        normal_path = script.replace("\\", "/")
        f.write(f"""--[[
    Generated from {os.path.join(SRC_PATH, script)}

    Source: https://github.com/KristalTeam/Kristal/blob/main/src/{normal_path}
]]""")

        f.write("\n\n---@meta\n\n")

        # Write the classes
        for class_ in classes:
            if class_[0] != None:
                # Write the documentation comments, if any exist
                f.write(class_[0])
            # Write the class definition
            f.write(f"{class_[1]} = {{}}\n\n")

        # Write the aliases
        for alias in aliases:
            assert alias != None
            if alias.startswith("---@diagnostic"):
                continue
            f.write(alias)
            f.write("\n\n")

        # Write the functions
        for function in functions:
            assert function[1] != None
            # Ignore love callbacks
            if "love." in function[1]:
                continue
            if function[0] != None:
                # Write the documentation comments, if any exist
                f.write(function[0])
            # Write the function definition
            f.write(f"function {function[1]} end\n\n")

# Also process each file that should be directly copied
for script in copy_scripts:
    print(f"Copying {script}...")

    # Read the contents of the script
    f = open(os.path.join(SRC_PATH, script), "r")
    script_text = f.read()
    f.close()

    # Create a new file in the "library" folder matching the script file name, creating the directory if it doesn't exist
    os.makedirs(os.path.join("library", os.path.dirname(script)), exist_ok=True)
    with open(os.path.join("library", script), "w") as f:
        # Write the script file name as a comment
        normal_path = script.replace("\\", "/")
        f.write(
f"""--[[
    Generated from {os.path.join(SRC_PATH, script)}

    Source: https://github.com/KristalTeam/Kristal/blob/main/src/{normal_path}
]]""")

        # Append the meta annotation to the file
        f.write("\n\n---@meta\n\n")

        # Copy the script to the output file
        f.write(script_text)


# Temp solution to Mod global
# TODO: Document these manually?

with open(os.path.join("library", "mod.lua"), "w") as f:
    f.write(
"""--[[
    Generated from Kristal mod event calls
]]""")

    f.write("\n\n---@meta\n\n")
    f.write("Mod = {}\n\n")

    for event in event_calls:
        f.write(f"function Mod:{event}(...) end\n\n")
