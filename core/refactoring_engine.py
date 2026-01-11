import os
import shutil
import re
from utils.logger import logger

class RefactoringEngine:
    def __init__(self):
        pass

    def generate_move_script(self, src_path, dst_path, project_root):
        """
        Generate a shell script to move a file and update imports.
        Returns the script content.
        """
        script = []
        
        # 1. Move Command
        if os.name == 'nt':
            # Windows
            cmd = f'move "{src_path}" "{dst_path}"'
        else:
            # Unix
            cmd = f'mv "{src_path}" "{dst_path}"'
        script.append(f"# 1. Move File\n{cmd}")
        
        # 2. Calculate Import Change
        # Need to convert paths to module dotted notation relative to project root
        try:
            rel_src = os.path.relpath(src_path, project_root)
            rel_dst = os.path.relpath(dst_path, project_root)
            
            # Assuming standard python structure
            module_src = rel_src.replace(os.sep, ".").replace(".py", "")
            module_dst = rel_dst.replace(os.sep, ".").replace(".py", "")
            
            script.append(f"\n# 2. Update Imports (Python)")
            script.append(f"# Changing: {module_src} -> {module_dst}")
            
            # Sed command for Unix or PowerShell replacement
            # Basic regex: "from old.module" -> "from new.module"
            # "import old.module" -> "import new.module"
            
            if os.name == 'nt':
                # PowerShell approach
                ps_cmd = f'''
Get-ChildItem -Path "{project_root}" -Recurse -Filter "*.py" | ForEach-Object {{
    (Get-Content $_.FullName).Replace('from {module_src}', 'from {module_dst}') | Set-Content $_.FullName
    (Get-Content $_.FullName).Replace('import {module_src}', 'import {module_dst}') | Set-Content $_.FullName
}}
'''
                script.append(ps_cmd)
            else:
                # Unix Sed
                sed_cmd = f"find {project_root} -name '*.py' -exec sed -i 's/from {module_src}/from {module_dst}/g' {{}} +"
                sed_cmd2 = f"find {project_root} -name '*.py' -exec sed -i 's/import {module_src}/import {module_dst}/g' {{}} +"
                script.append(sed_cmd)
                script.append(sed_cmd2)
                
        except Exception as e:
            logger.error(f"Error generating refactor script: {e}")
            script.append(f"# Error calculating imports: {e}")
            
        return "\n".join(script)

    def execute_move(self, src_path, dst_path, project_root, dry_run=True):
        """
        Execute the move operation.
        """
        if dry_run:
            return self.generate_move_script(src_path, dst_path, project_root)
            
        # TODO: Implement actual execution with safety checks
        # For now, we only support script generation as per safety guidelines
        return self.generate_move_script(src_path, dst_path, project_root)

refactoring_engine = RefactoringEngine()
