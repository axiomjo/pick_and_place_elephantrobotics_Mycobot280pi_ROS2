#!/usr/bin/env python3
import os
import argparse

def concatenate_files(directory, output_file, recursive=False, extensions=None, relative_path=False): # NEW argument
    """
    Scans a directory, reads specified files, and concatenates their content
    into a single output file, with a header for each file.

    Args:
        directory (str): The path to the directory to scan.
        output_file (str): The path to the file where content will be saved.
        recursive (bool): If True, search subdirectories as well.
        extensions (list): A list of file extensions to include (e.g., ['.py', '.txt']).
        relative_path (bool): If True, use relative file paths in headers.
        
    contoh command"
    
    python3 toolngeconcat.py -d src/mycobot280pi_robot -o planner.txt -r -e .py --relative 




    """
    print(f"Starting concatenation...")
    # Get the absolute path of the source directory to make relative paths clean
    start_dir = os.path.abspath(directory)
    print(f"Source directory: {start_dir}")
    print(f"Output file: {os.path.abspath(output_file)}")
    print(f"Recursive search: {'Yes' if recursive else 'No'}")
    print(f"Path style: {'Relative' if relative_path else 'Absolute'}") # NEW print statement
    if extensions:
        print(f"Filtering for extensions: {', '.join(extensions)}")

    try:
        with open(output_file, 'w', encoding='utf-8') as outfile:
            for dirpath, _, filenames in os.walk(directory):
                filenames.sort()
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)

                    if extensions:
                        if not any(filename.endswith(ext) for ext in extensions):
                            continue

                    # --- MODIFIED SECTION ---
                    if relative_path:
                        # Calculate path relative to the starting directory
                        header_path = os.path.relpath(filepath, directory)
                    else:
                        # Original behavior: get the full absolute path
                        header_path = os.path.abspath(filepath)
                    # --- END MODIFIED SECTION ---

                    outfile.write("==========\n")
                    outfile.write(f"{header_path}\n") # Use the determined path
                    outfile.write("======\n\n")

                    try:
                        with open(filepath, 'r', encoding='utf-8', errors='ignore') as infile:
                            content = infile.read()
                            outfile.write(content)
                    except Exception as e:
                        outfile.write(f"[Error reading file: {e}]\n")
                    
                    outfile.write("\n\n=====\n\n")

                if not recursive:
                    break
        
        print(f"\nSuccessfully concatenated files into '{output_file}'")

    except FileNotFoundError:
        print(f"Error: The directory '{directory}' does not exist.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def main():
    """Main function to parse arguments and run the script."""
    parser = argparse.ArgumentParser(
        description="Concatenate all files in a directory into a single file with headers.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument('-d', '--directory', required=True, help="The source directory to scan for files.")
    parser.add_argument('-o', '--output', required=True, help="The name of the output file.")
    parser.add_argument('-r', '--recursive', action='store_true', help="Include files in subdirectories.")
    parser.add_argument('-e', '--extensions', nargs='+', help="Optional: space-separated list of file extensions to include (e.g., .py .txt)")
    # NEW ARGUMENT FOR RELATIVE PATHS
    parser.add_argument(
        '--relative',
        action='store_true',
        help="Use file paths relative to the source directory in headers."
    )
    
    args = parser.parse_args()
    concatenate_files(args.directory, args.output, args.recursive, args.extensions, args.relative)

if __name__ == "__main__":
    main()
