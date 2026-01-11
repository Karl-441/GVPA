import os
from utils.logger import logger
import git
from core.code_analyzer import code_analyzer

class GitAnalyzer:
    def __init__(self, repo_path="."):
        self.repo_path = repo_path
        try:
            self.repo = git.Repo(repo_path, search_parent_directories=True)
        except git.InvalidGitRepositoryError:
            self.repo = None
            logger.warning("No valid Git repository found.")

    def get_commit_history(self, limit=10):
        if not self.repo: return []
        commits = []
        for commit in self.repo.iter_commits(max_count=limit):
            commits.append({
                "hexsha": commit.hexsha,
                "message": commit.message.strip(),
                "author": commit.author.name,
                "date": commit.committed_datetime.isoformat()
            })
        return commits

    def compare_commits(self, current_analysis, commit_hash):
        """
        Compare current analysis with analysis of a previous commit.
        Returns a merged analysis dict suitable for CodeGraphBuilder, 
        with '_status' fields ('added', 'removed', 'unchanged').
        """
        if not self.repo: return None
        
        logger.info(f"Comparing current state with commit {commit_hash}...")
        
        prev_analysis = self._analyze_commit(commit_hash)
        if not prev_analysis:
            return None
            
        return self._merge_analyses(current_analysis, prev_analysis)

    def _analyze_commit(self, commit_hash):
        import tempfile
        import shutil
        
        commit = self.repo.commit(commit_hash)
        temp_dir = tempfile.mkdtemp(prefix="gvpa_git_")
        
        try:
            # Checkout to temp dir
            for blob in commit.tree.traverse():
                if blob.type == 'blob':
                    # Filter extensions
                    if not any(blob.path.endswith(ext) for ext in code_analyzer.parsers.keys()):
                        continue
                        
                    dest_path = os.path.join(temp_dir, blob.path)
                    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                    with open(dest_path, "wb") as f:
                        blob.stream_data(f)
            
            # Run Analysis
            # Use ProjectCodeAnalyzer (renamed from ProjectAnalyzer in imports usually, check main.py usage)
            from core.project_analyzer import ProjectCodeAnalyzer
            analyzer = ProjectCodeAnalyzer()
            result = analyzer.analyze_project(temp_dir) # Use analyze_project, not analyze_structure
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing commit {commit_hash}: {e}")
            return None
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def _merge_analyses(self, current, previous):
        """
        Merge two analyses into one, marking nodes/edges as added/removed.
        """
        merged = {
            "functions": [],
            "calls": []
        }
        
        # Nodes
        curr_nodes = {n["name"]: n for n in current.get("functions", [])}
        prev_nodes = {n["name"]: n for n in previous.get("functions", [])}
        
        all_node_names = set(curr_nodes.keys()) | set(prev_nodes.keys())
        
        for name in all_node_names:
            node = {}
            status = "unchanged"
            
            if name in curr_nodes and name not in prev_nodes:
                status = "added"
                node = curr_nodes[name].copy()
            elif name in prev_nodes and name not in curr_nodes:
                status = "removed"
                node = prev_nodes[name].copy()
            else:
                node = curr_nodes[name].copy() # Prefer current data
                
            node["_status"] = status
            merged["functions"].append(node)
            
        # Edges
        # Edge identity is (source, target)
        curr_edges = {(e["source"], e["target"]): e for e in current.get("calls", [])}
        prev_edges = {(e["source"], e["target"]): e for e in previous.get("calls", [])}
        
        all_edges = set(curr_edges.keys()) | set(prev_edges.keys())
        
        for (s, t) in all_edges:
            edge = {}
            status = "unchanged"
            
            if (s, t) in curr_edges and (s, t) not in prev_edges:
                status = "added"
                edge = curr_edges[(s, t)].copy()
            elif (s, t) in prev_edges and (s, t) not in curr_edges:
                status = "removed"
                edge = prev_edges[(s, t)].copy()
            else:
                edge = curr_edges[(s, t)].copy()
                
            edge["_status"] = status
            merged["calls"].append(edge)
            
        return merged

git_analyzer = GitAnalyzer()
