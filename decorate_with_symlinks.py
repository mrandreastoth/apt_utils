"""
# ------------------------------------------------------------
# Script: decorate_with_symlinks.py
# Author: Andreas Toth
# Email: andreas.toth@xtra.co.nz
# Version: 2.0.1
# Date: 2025-01-18
#
# Description:
# This script replicates the hierarchy of files from a source directory as
# symlinks in a destination directory, preserving the original directory
# structure. It can optionally replace occurrences of a specified string with
# another specified string in constructing the destination path from the
# source path, allowing for transformations such as ../git/info/exclude to the
# symlinked file ./git/info/exclude, for example.
#
# The script supports the creation of both absolute and relative symlinks and
# handles cases where files or symlinks already exist in the destination with
# customisable options. There is also an option to delete files or symlinks that
# already exist in the destination.
#
# Empty directories are not replicated. Existing files and symlinks in the
# destination that are not part of the source set are left untouched.
#
# Usage:
# python decorate_with_symlinks.py <source_root> <destination_root>
#        [search_string] [replace_string] [--relative] [--mode=<value>]
#        [--on-exists=<value>]
#
# Options:
#   --mode            - (optional) Specifies the mode: 'create' (default) or 'delete'.
#   --on-exists       - (optional) Specifies the action when a file or symlink already exists at the destination:
#                       'ask' (default), 'fail', 'skip', or 'execute'.
#                       'ask' prompts the user for action (replace/delete, skip, or quit).
#
# ------------------------------------------------------------
"""

import os
import sys

def print_usage():
    """ Prints the usage instructions for the script. """
    print("Usage: python decorate_with_symlinks.py <source_root> <destination_root> [search_string] [replace_string] [--relative] [--mode=<value>] [--on-exists=<value>]")
    print("")
    print("  source_root       - The root directory of the source repo (e.g., X)")
    print("  destination_root  - The root directory of the destination repo (e.g., Y)")
    print("  search_string     - (optional) The string to search for in the file paths")
    print("  replace_string    - (optional) The string to replace 'search_string' with in the file paths")
    print("  --relative        - (optional) Flag to create relative symlinks (default is absolute symlinks)")
    print("  --mode            - (optional) Specifies the mode: 'create' (default) or 'delete'")
    print("  --on-exists       - (optional) Specifies the action when a file or symlink already exists:")
    print("                      'ask' (default), 'fail', 'skip', 'execute'")
    print("")
    print("Description:")
    print("  This script will create symlinks in the destination directory (Y) pointing to files in the source directory (X).")
    print("  If a symlink destination already exists, it will follow the behavior specified by --on-exists.")
    print("  The script can replace occurrences of 'search_string' in the destination path with 'replace_string'.")
    print("  Empty directories are not replicated, only files are symlinked.")
    print("")
    print("Example:")
    print("  python decorate_with_symlinks.py /path/to/X /path/to/Y ..git .git --relative --mode=create --on-exists=ask")

VALID_MODE_VALUES = ['create', 'delete']
DEFAULT_MODE_VALUE = 'create'

VALID_ACTION_VALUES = ['ask', 'fail', 'skip', 'execute']
DEFAULT_ACTION_VALUES = 'ask'

def convert_path_to_relative(src, dest_root):
    """ Convert the source path to a relative path from the destination root. """
    return os.path.relpath(src, dest_root)

def convert_path_to_absolute(path):
    """ Convert the given path to an absolute path. """
    return os.path.abspath(path)

def create_symlink(src, dest, relative=False):
    """ Create a symlink for files or directories with support for relative and absolute symlinks. """
    try:
        # Remove the existing file (whether it's a regular file or symlink)
        if os.path.exists(dest) or os.path.islink(dest):
            os.remove(dest)
            print(f"Removed existing file: {dest}")

        # If relative, convert the source path to relative
        if relative:
            src = os.path.relpath(src, os.path.dirname(dest))

        os.symlink(src, dest)  # Creates symlink for both files and directories

        print(f"Symlink created: {src} -> {dest}")
    except FileExistsError:
        print(f"Error: Symlink already exists: {dest}")
        return False
    except Exception as e:
        print(f"Error creating symlink: {e}")
        return False
    return True

def remove_existing_file(file_path):
    """ Remove a file if it exists. """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Removed existing file: {file_path}")
    except Exception as e:
        print(f"Error removing file {file_path}: {e}")

def create_directory(dir_path):
    """ Create directory if it doesn't exist. """
    try:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            print(f"Created directory: {dir_path}")
    except Exception as e:
        print(f"Error creating directory {dir_path}: {e}")

def replace_in_path(path, search, replace, is_destination=False):
    """ Replace a part of the path with a given string. """
    # Apply the replacement only to the destination path
    if is_destination:
        return path.replace(search, replace)

    return path

def validate_mode_value(mode_value):
    """ Validates the mode value to ensure it's within the allowed options. """
    if mode_value not in VALID_MODE_VALUES:
        print(f"Invalid mode: {mode_value}. Valid values are: {', '.join(VALID_MODE_VALUES)}.")
        sys.exit(1)

    return mode_value

def validate_action_value(action_value, error_text_override=""):
    """ Validates the action value to ensure it's within the allowed options. """
    if action_value not in VALID_ACTION_VALUES:
        if error_text_override != "":
            print(error_text_override)
        else:
            print(f"Invalid value for action: {action_value}. Valid values are: {', '.join(VALID_ACTION_VALUES)}.")

        sys.exit(1)

    if action_value not in VALID_ACTION_VALUES:
        sys.exit(1)

    return action_value

def validate_on_exists_action_value(action_value):
    """ Validates the on-exists' action value to ensure it's within the allowed options. """
    action_value = validate_action_value(action_value, f"Invalid value for --on-exists: {action_value}. Valid values are: {', '.join(VALID_ACTION_VALUES)}.")

    return action_value

def handle_existing_file_behavior(mode, action, target_file):
    """ Handle the behavior when the destination file already exists. """
    validate_mode_value(mode)
    validate_action_value(action)

    if action == 'fail':
        print(f"File already exists: {target_file}")
        return 'failed'

    if action == 'skip':
        print(f"Skipping file: {target_file}")
        return 'skipped'

    if action == 'ask':
        prompt_text = ""
        execute_choices = []
        invalid_text = ""

        while True:
            if mode == 'create':
                prompt_text = "Do you want to replace (r), skip (s), or fail (f)?"
                execute_choices = ['r', 'replace']
                invalid_text = "Please enter 'r' (replace), 's' (skip), or 'f' (fail)."
            else:
                assert mode == 'delete'

                prompt_text = "Do you want to delete (d), skip (s), or fail (f)?"
                execute_choices = ['d', 'delete']
                invalid_text = "Please enter 'd' (delete), 's' (skip), or 'f' (fail)."

            user_choice = input(f"File {target_file} exists. {prompt_text} ").lower()

            if user_choice in execute_choices:
                break # Let common execute action handling take over

            if user_choice in ['s', 'skip']:
                print(f"Skipping file: {target_file}")
                return 'skipped'

            if user_choice in ['f', 'Failed']:
                print("Failed operation.")
                return 'failed'

            print(f"Invalid input. {invalid_text}")

        if mode == 'create':
            print(f"Replacing file: {target_file}")
        else:
            assert mode == 'delete'
            print(f"Deleting file: {target_file}")
    else:
        assert action == 'execute'

    # Execute action
    remove_existing_file(target_file)
    return 'executed'

def decorate_symlinks(source_root, dest_root, search_string='', replace_string='', relative_symlink=False, mode=DEFAULT_MODE_VALUE, action=DEFAULT_ACTION_VALUES):
    """
    Replicates the source directory structure into the destination directory by creating symlinks.

    This function walks through all files in the source directory, creates the necessary directories in the destination,
    and creates symlinks for the files. It handles the replacement of a part of the path (if provided), and it also
    handles conflicts (e.g., when a file or symlink already exists at the destination) based on the action specified by
    the `--on-exists` option.

    Args:
        source_root (str): The root directory of the source directory to replicate.
        dest_root (str): The root directory of the destination where symlinks will be created.
        search_string (str, optional): The string to search for in the file paths to replace.
        replace_string (str, optional): The string to replace the search_string with in the destination paths.
        relative_symlink (bool, optional): Flag to indicate whether symlinks should be relative (default is absolute).
        mode (str, optional): Mode for symlink creation. Either 'create' (default) or 'delete'.
        action (str, optional): Action to take when a file exists at the destination. Options are 'ask', 'fail', 'skip', 'execute'.

    Returns:
        None: This function does not return a value, but performs operations such as creating symlinks, removing files, and printing output.

    Raises:
        SystemExit: If the source or destination root directories do not exist or if an invalid mode or action is provided.
    """
    validate_mode_value(mode)
    validate_action_value(action)

    # Ensure source and destination roots exist
    if not os.path.isdir(source_root):
        print("Source root does not exist. Exiting.")
        sys.exit(1)
    if not os.path.isdir(dest_root):
        print("Destination root does not exist. Exiting.")
        sys.exit(1)

    # Convert both source and destination paths to absolute first
    source_root = convert_path_to_absolute(source_root)
    dest_root = convert_path_to_absolute(dest_root)

    # If --relative is passed, convert both paths to relative paths based on current working directory
    if relative_symlink:
        source_root = convert_path_to_relative(source_root, os.getcwd())
        dest_root = convert_path_to_relative(dest_root, os.getcwd())

        print("Using relative paths for source and destination.")
    else:
        print("Using absolute paths for source and destination.")

    print(f"Using source root: {source_root}")
    print(f"Using destination root: {dest_root}")

    # Walk through the files in the source root
    for root, dirs, files in os.walk(source_root):
        for file in files:
            # Get the full source file path
            file_path = os.path.join(root, file)

            # Apply the search/replace to the destination file path
            file_with_correct_git = replace_in_path(file_path, search_string, replace_string, is_destination=True)

            # Get the relative path from the source root and target path
            relative_path = os.path.relpath(file_with_correct_git, source_root)
            target_file = os.path.join(dest_root, relative_path)

            # Ensure the target directory exists in the destination root
            target_dir = os.path.dirname(target_file)
            create_directory(target_dir)

            # Check if the file exists and handle based on the on-exists behavior
            if os.path.exists(target_file) or os.path.islink(target_file):
                action_result = handle_existing_file_behavior(mode, action, target_file)

                if action_result == 'failed':
                    print("Operation failed! Decorating process incomplete!")
                    return

                if action_result == 'skipped':
                    continue

            # Create the symlink
            if mode == 'create':
                create_symlink(file_path, target_file, relative_symlink)

    print("Decorating process complete!")

def main():
    """
    Main entry point of the script. Handles command-line arguments, validates input, and calls the decorate_symlinks function.

    This function parses the command-line arguments to retrieve the source and destination roots, optional search and replace strings,
    the mode of operation ('create' or 'delete'), and the action to take when a file exists at the destination. It ensures that the
    correct parameters are passed to the `decorate_symlinks` function and manages usage and error messages when the input is invalid.

    Command-line arguments:
        <source_root>       : Root directory of the source repo.
        <destination_root>  : Root directory of the destination repo.
        [search_string]     : (optional) String to search for in file paths.
        [replace_string]    : (optional) String to replace search_string with in the file paths.
        --relative          : (optional) Flag to create relative symlinks.
        --mode              : (optional) Specifies the mode of operation ('create' or 'delete').
        --on-exists         : (optional) Specifies the action to take when a file exists at the destination ('ask', 'fail', 'skip', 'execute').

    Returns:
        None: This function does not return a value but terminates the script execution if an error occurs.

    Calls:
        - decorate_symlinks: The main logic for replicating symlinks from source to destination.

    Raises:
        SystemExit: If required arguments are missing, or if the command-line arguments are invalid.
    """
    if len(sys.argv) < 3:
        print_usage()
        sys.exit(1)

    source_root = sys.argv[1]
    dest_root = sys.argv[2]
    search_string = sys.argv[3] if len(sys.argv) > 3 else ''
    replace_string = sys.argv[4] if len(sys.argv) > 4 else ''
    relative_symlink = '--relative' in sys.argv
    mode = DEFAULT_MODE_VALUE
    action = DEFAULT_ACTION_VALUES

    # Check for --mode argument
    for arg in sys.argv:
        if arg.startswith('--mode='):
            mode = validate_mode_value(arg.split('=')[1])

    # Check for --on-exists argument, i.e., action
    for arg in sys.argv:
        if arg.startswith('--on-exists='):
            action = validate_on_exists_action_value(arg.split('=')[1])

    decorate_symlinks(source_root, dest_root, search_string, replace_string, relative_symlink, mode, action)

if __name__ == "__main__":
    main()
