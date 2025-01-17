import os
import sys

def usage():
    print("Usage: python decorate_with_symlinks.py <source_root> <destination_root> [search_string] [replace_string] [--relative] [--on-exists=<value>]")
    print("")
    print("  source_root       - The root directory of the source repo (e.g., X)")
    print("  destination_root  - The root directory of the destination repo (e.g., Y)")
    print("  search_string     - (optional) The string to search for in the file paths")
    print("  replace_string    - (optional) The string to replace 'search_string' with in the file paths")
    print("  --relative        - (optional) Flag to create relative symlinks (default is absolute symlinks)")
    print("  --on-exists       - (optional) Specifies the action when a file already exists at the destination:")
    print("                      'fail' (default), 'skip', 'replace', or 'ask'")
    print("")
    print("Description:")
    print("  This script will create symlinks in the destination directory (Y) pointing to files in the source directory (X).")
    print("  It will replace 'search_string' with 'replace_string' in the destination paths only, leaving the source paths unchanged.")
    print("  If a symlink destination already exists, it will follow the behavior specified by --on-exists.")
    print("")
    print("Example:")
    print("  python decorate_with_symlinks.py /path/to/X /path/to/Y ..git .git --relative --on-exists=ask")
    sys.exit(1)

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

def get_on_exists_behavior(option_value):
    """ Parse and validate the on-exists option. """
    valid_values = ['fail', 'skip', 'replace', 'ask']
    if option_value not in valid_values:
        print(f"Invalid value for --on-exists: {option_value}. Valid values are: {', '.join(valid_values)}.")
        sys.exit(1)
    return option_value

def handle_existing_file_behavior(action, target_file, src, dest):
    """ Handle the behavior when the destination file already exists. """
    if action == 'fail':
        print(f"File already exists: {target_file}. Exiting.")
        sys.exit(1)
    elif action == 'skip':
        print(f"Skipping file: {target_file}")
        return False
    elif action == 'replace':
        print(f"Replacing existing file: {target_file}")
        remove_existing_file(target_file)
    elif action == 'ask':
        user_choice = input(f"File {target_file} already exists. Do you want to replace? (y/n): ")
        if user_choice.lower() == 'y':
            print(f"Replacing file: {target_file}")
            remove_existing_file(target_file)
        else:
            print(f"Skipping file: {target_file}")
            return False
    return True

# Main function for the symlink decorating logic
def decorate_symlinks(source_root, dest_root, search_string='', replace_string='', relative_symlink=False, on_exists='fail'):
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
        print(f"Using relative paths for source and destination.")
    else:
        print(f"Using absolute paths for source and destination.")

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
                if not handle_existing_file_behavior(on_exists, target_file, file_with_correct_git, target_file):
                    continue

            # Create the symlink
            create_symlink(file_path, target_file, relative_symlink)

    print("Decorating process complete!")

def main():
    if len(sys.argv) < 3:
        usage()

    source_root = sys.argv[1]
    dest_root = sys.argv[2]
    search_string = sys.argv[3] if len(sys.argv) > 3 else ''
    replace_string = sys.argv[4] if len(sys.argv) > 4 else ''
    relative_symlink = '--relative' in sys.argv
    on_exists = 'fail'  # Default behavior

    # Check for --on-exists argument
    for arg in sys.argv:
        if arg.startswith('--on-exists='):
            on_exists = get_on_exists_behavior(arg.split('=')[1])

    decorate_symlinks(source_root, dest_root, search_string, replace_string, relative_symlink, on_exists)

if __name__ == "__main__":
    main()