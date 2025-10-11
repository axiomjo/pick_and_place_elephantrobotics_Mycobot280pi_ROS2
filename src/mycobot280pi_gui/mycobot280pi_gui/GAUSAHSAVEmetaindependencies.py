import os
import re

def create_codebase_map(root_dir, output_filename="codebase_map.txt"):
    """
    Reads all Python files in the given directory, notes their path, 
    and prints their content, with a focus on import statements.
    
    Args:
        root_dir (str): The root directory of the project.
        output_filename (str): The name of the output file.
    """
    
    # Directories to ignore (customize this list for your project)
    ignore_dirs = ['__pycache__', '.git', '.vscode', 'venv', 'build', 'dist', 'node_modules']
    
    with open(output_filename, 'w') as outfile:
        print(f"Starting analysis in: {root_dir}")
        print(f"Output file: {output_filename}\n")
        
        # Walk through the directory structure
        for dirpath, dirnames, filenames in os.walk(root_dir):
            
            # Modify dirnames in place to skip ignored directories
            dirnames[:] = [d for d in dirnames if d not in ignore_dirs]
            
            for filename in filenames:
                # Only process Python files
                if filename.endswith('.py'):
                    
                    full_path = os.path.join(dirpath, filename)
                    
                    # Skip the mapper script itself
                    if os.path.basename(full_path) == os.path.basename(__file__):
                        continue
                        
                    # Write file path header
                    outfile.write("=" * 60 + "\n")
                    outfile.write(f"# FILE: {full_path}\n")
                    outfile.write("=" * 60 + "\n\n")

                    try:
                        with open(full_path, 'r', encoding='utf-8') as infile:
                            content = infile.read()
                            
                            # Find all import statements
                            import_lines = []
                            for line in content.splitlines():
                                stripped_line = line.strip()
                                # Simple check for import lines
                                if stripped_line.startswith('import ') or stripped_line.startswith('from '):
                                    # Ignore relative imports of signals/slots if they are not the problem
                                    # if 'pyqtSignal' not in line and 'pyqtSlot' not in line: 
                                    import_lines.append(stripped_line)
                                
                            # Write the import section
                            outfile.write("### IMPORTS ###\n")
                            if import_lines:
                                outfile.write('\n'.join(import_lines) + '\n\n')
                            else:
                                outfile.write("(No primary imports found)\n\n")

                            # Write the rest of the file content
                            outfile.write("### FULL CONTENT ###\n")
                            outfile.write(content + '\n\n')
                            
                    except Exception as e:
                        outfile.write(f"!!! ERROR READING FILE: {e} !!!\n\n")

    print(f"\nAnalysis complete. Check {output_filename} for the map.")

# --- Execution ---
if __name__ == "__main__":
    # Assumes the script is run from the root of the project
    project_root = os.getcwd() 
    create_codebase_map(project_root)
