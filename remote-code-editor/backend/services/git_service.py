"""
Git服务模块
提供Git操作的核心逻辑
"""
import os
import asyncio
import subprocess
import requests
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from git import Repo, GitCommandError, InvalidGitRepositoryError
from git.exc import NoSuchPathError
from django.conf import settings


class GitService:
    """Git服务类"""
    
    def __init__(self, workspace_path: str):
        """
        初始化Git服务
        
        Args:
            workspace_path: 工作目录根路径
        """
        self.workspace = Path(workspace_path).resolve() if workspace_path else None
        self.repo: Optional[Repo] = None
        self._git_configured = None
        if self.workspace:
            self._init_repo()
    
    def _init_repo(self):
        """初始化或打开Git仓库"""
        if not self.workspace:
            self.repo = None
            return
        try:
            # 尝试打开现有仓库
            self.repo = Repo(self.workspace)
        except (InvalidGitRepositoryError, NoSuchPathError):
            # 不是Git仓库，repo为None
            self.repo = None
    
    def is_git_repo(self) -> bool:
        """检查当前工作目录是否是Git仓库"""
        return self.repo is not None
    
    def check_git_config(self) -> Dict:
        """
        检查Git配置状态
        
        Returns:
            配置状态信息
        """
        try:
            # 检查git命令是否可用
            result = subprocess.run(['git', '--version'], capture_output=True, text=True)
            if result.returncode != 0:
                return {
                    'configured': False,
                    'error': 'Git未安装或不可用'
                }
            
            # 检查用户名配置
            name_result = subprocess.run(
                ['git', 'config', '--global', 'user.name'],
                capture_output=True,
                text=True
            )
            
            # 检查邮箱配置
            email_result = subprocess.run(
                ['git', 'config', '--global', 'user.email'],
                capture_output=True,
                text=True
            )
            
            user_name = name_result.stdout.strip() if name_result.returncode == 0 else ''
            user_email = email_result.stdout.strip() if email_result.returncode == 0 else ''
            
            if not user_name or not user_email:
                return {
                    'configured': False,
                    'error': 'Git未配置用户信息',
                    'hint': '请运行以下命令配置Git:\ngit config --global user.name "Your Name"\ngit config --global user.email "your.email@example.com"'
                }
            
            return {
                'configured': True,
                'user_name': user_name,
                'user_email': user_email
            }
            
        except Exception as e:
            return {
                'configured': False,
                'error': f'检查Git配置失败: {str(e)}'
            }
    
    async def clone(self, repo_url: str) -> Dict:
        """
        克隆远程仓库（使用系统配置的Git凭据）
        
        Args:
            repo_url: 仓库URL
        
        Returns:
            克隆结果信息
        """
        try:
            # 检查Git配置
            config_status = self.check_git_config()
            if not config_status['configured']:
                return {
                    'success': False,
                    'error': config_status.get('error', 'Git未配置'),
                    'hint': config_status.get('hint', '')
                }
            
            # 获取仓库名称
            repo_name = repo_url.split('/')[-1].replace('.git', '')
            clone_path = self.workspace / repo_name
            
            # 如果目录已存在，报错
            if clone_path.exists():
                return {
                    'success': False,
                    'error': f'目录已存在: {repo_name}'
                }
            
            # 执行克隆（使用系统Git凭据）
            def _clone():
                # Git会自动使用配置的credential helper
                Repo.clone_from(repo_url, clone_path)
                return Repo(clone_path)
            
            # 在线程池中执行（避免阻塞）
            loop = asyncio.get_event_loop()
            self.repo = await loop.run_in_executor(None, _clone)
            
            return {
                'success': True,
                'message': f'成功克隆仓库: {repo_name}',
                'path': str(clone_path.relative_to(self.workspace))
            }
            
        except GitCommandError as e:
            error_msg = str(e)
            # 判断是否是认证错误
            if 'Authentication failed' in error_msg or 'could not read Username' in error_msg:
                return {
                    'success': False,
                    'error': '认证失败，请配置Git凭据',
                    'hint': '请运行以下命令配置Git凭据存储:\ngit config --global credential.helper store\n然后手动克隆一次仓库以保存凭据'
                }
            return {
                'success': False,
                'error': f'克隆失败: {error_msg}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'克隆失败: {str(e)}'
            }
    
    async def get_status(self) -> Dict:
        """
        获取Git状态
        
        Returns:
            状态信息
        """
        if not self.is_git_repo():
            return {
                'is_repo': False,
                'message': '当前目录不是Git仓库'
            }
        
        try:
            # 获取当前分支
            current_branch = self.repo.active_branch.name
            
            # 获取所有分支
            branches = [b.name for b in self.repo.branches]
            
            # 获取远程仓库信息
            remotes = [{'name': r.name, 'url': r.url} for r in self.repo.remotes]
            
            # 获取更改的文件
            changed_files = []
            
            # 未暂存的更改
            for item in self.repo.index.diff(None):
                changed_files.append({
                    'path': item.a_path,
                    'status': 'M'  # 修改
                })
            
            # 已暂存但未提交的更改
            for item in self.repo.index.diff('HEAD'):
                if item.a_path not in [f['path'] for f in changed_files]:
                    changed_files.append({
                        'path': item.a_path,
                        'status': 'M'  # 修改
                    })
            
            # 未跟踪的文件
            for path in self.repo.untracked_files:
                changed_files.append({
                    'path': path,
                    'status': 'A'  # 新增
                })
            
            return {
                'is_repo': True,
                'branch': current_branch,
                'branches': branches,
                'remotes': remotes,
                'changed_files': changed_files,
                'has_changes': len(changed_files) > 0
            }
            
        except Exception as e:
            return {
                'is_repo': False,
                'error': str(e)
            }
    
    async def switch_branch(self, branch_name: str) -> Dict:
        """
        切换分支
        
        Args:
            branch_name: 分支名称
        
        Returns:
            操作结果
        """
        if not self.is_git_repo():
            return {
                'success': False,
                'error': '不是Git仓库'
            }
        
        try:
            # 检查是否有未提交的更改
            if self.repo.is_dirty():
                return {
                    'success': False,
                    'error': '有未提交的更改，请先提交或暂存'
                }
            
            # 切换分支
            self.repo.git.checkout(branch_name)
            
            return {
                'success': True,
                'message': f'已切换到分支: {branch_name}',
                'branch': branch_name
            }
            
        except GitCommandError as e:
            return {
                'success': False,
                'error': f'切换分支失败: {str(e)}'
            }
    
    async def commit(self, message: str, files: Optional[List[str]] = None) -> Dict:
        """
        提交更改
        
        Args:
            message: 提交信息
            files: 要提交的文件列表（None表示提交所有更改）
        
        Returns:
            操作结果
        """
        if not self.is_git_repo():
            return {
                'success': False,
                'error': '不是Git仓库'
            }
        
        try:
            if files:
                # 添加指定文件
                self.repo.index.add(files)
            else:
                # 添加所有更改
                self.repo.git.add(A=True)
            
            # 提交
            commit = self.repo.index.commit(message)
            
            return {
                'success': True,
                'message': f'提交成功: {message}',
                'commit_hash': commit.hexsha[:7]
            }
            
        except GitCommandError as e:
            return {
                'success': False,
                'error': f'提交失败: {str(e)}'
            }
    
    async def push(self, remote: str = 'origin', branch: Optional[str] = None) -> Dict:
        """
        推送到远程仓库
        
        Args:
            remote: 远程仓库名称
            branch: 分支名称（None表示当前分支）
        
        Returns:
            操作结果
        """
        if not self.is_git_repo():
            return {
                'success': False,
                'error': '不是Git仓库'
            }
        
        try:
            if branch is None:
                branch = self.repo.active_branch.name
            
            origin = self.repo.remote(remote)
            origin.push(branch)
            
            return {
                'success': True,
                'message': f'推送成功: {remote}/{branch}'
            }
            
        except GitCommandError as e:
            return {
                'success': False,
                'error': f'推送失败: {str(e)}'
            }
    
    async def pull(self, remote: str = 'origin', branch: Optional[str] = None) -> Dict:
        """
        从远程仓库拉取
        
        Args:
            remote: 远程仓库名称
            branch: 分支名称（None表示当前分支）
        
        Returns:
            操作结果
        """
        if not self.is_git_repo():
            return {
                'success': False,
                'error': '不是Git仓库'
            }
        
        try:
            if branch is None:
                branch = self.repo.active_branch.name
            
            origin = self.repo.remote(remote)
            origin.pull(branch)
            
            return {
                'success': True,
                'message': f'拉取成功: {remote}/{branch}'
            }
            
        except GitCommandError as e:
            return {
                'success': False,
                'error': f'拉取失败: {str(e)}'
            }
    
    async def get_commit_history(self, limit: int = 20) -> Dict:
        """
        获取提交历史
        
        Args:
            limit: 限制返回的提交数量
        
        Returns:
            提交历史列表
        """
        if not self.is_git_repo():
            return {
                'success': False,
                'error': '不是Git仓库'
            }
        
        try:
            commits = []
            for commit in self.repo.iter_commits(max_count=limit):
                commits.append({
                    'hash': commit.hexsha[:7],
                    'message': commit.message.strip(),
                    'author': commit.author.name,
                    'date': commit.committed_datetime.isoformat()
                })
            
            return {
                'success': True,
                'commits': commits
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def list_git_repos(self, search_path: Optional[str] = None) -> Dict:
        """
        搜索并列出Git仓库
        
        Args:
            search_path: 搜索路径（None表示用户主目录）
        
        Returns:
            Git仓库列表
        """
        import os
        from pathlib import Path
        
        try:
            # 确定搜索路径
            if search_path:
                base_path = Path(search_path).resolve()
            else:
                # 默认从用户主目录开始搜索
                base_path = Path.home()
            
            git_repos = []
            
            # 递归搜索Git仓库（限制搜索深度避免性能问题）
            def find_git_repos(path: Path, depth: int = 0, max_depth: int = 3):
                """递归查找Git仓库"""
                if depth > max_depth:
                    return
                
                try:
                    # 检查当前目录是否是Git仓库
                    git_dir = path / '.git'
                    if git_dir.exists() and git_dir.is_dir():
                        # 找到Git仓库
                        try:
                            repo = Repo(path)
                            # 获取远程仓库信息
                            remote_url = ''
                            if repo.remotes:
                                remote_url = repo.remotes[0].url
                            
                            # 计算相对路径（兼容Python 3.8）
                            try:
                                relative_path = str(path.relative_to(base_path))
                            except ValueError:
                                relative_path = str(path)
                            
                            git_repos.append({
                                'name': path.name,
                                'path': str(path),
                                'relative_path': relative_path,
                                'branch': repo.active_branch.name if not repo.head.is_detached else 'detached',
                                'remote_url': remote_url,
                                'is_dirty': repo.is_dirty()
                            })
                            return  # 不再递归子目录
                        except Exception:
                            pass
                    
                    # 递归搜索子目录
                    for item in path.iterdir():
                        if item.is_dir() and not item.name.startswith('.'):
                            # 跳过一些常见的非代码目录
                            if item.name in ['node_modules', '__pycache__', 'venv', '.venv', 'env', 'build', 'dist', 'target']:
                                continue
                            find_git_repos(item, depth + 1, max_depth)
                
                except (PermissionError, OSError):
                    pass
            
            # 执行搜索
            find_git_repos(base_path)
            
            return {
                'success': True,
                'repos': git_repos,
                'search_path': str(base_path)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def list_github_repos(self, github_token: Optional[str] = None, 
                                  repo_type: str = 'all') -> Dict:
        """
        获取GitHub用户的仓库列表
        
        Args:
            github_token: GitHub Personal Access Token（可选，使用环境变量）
            repo_type: 仓库类型 ('all', 'owner', 'public', 'private', 'member')
        
        Returns:
            GitHub仓库列表
        """
        try:
            # 获取GitHub Token
            token = github_token or getattr(settings, 'GITHUB_TOKEN', None)
            
            if not token:
                return {
                    'success': False,
                    'error': '未配置GitHub Token',
                    'hint': '请在环境变量中设置GITHUB_TOKEN或在前端输入'
                }
            
            # 调用GitHub API
            headers = {
                'Authorization': f'token {token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            # 获取用户仓库列表
            url = f'https://api.github.com/user/repos?type={repo_type}&sort=updated&per_page=100'
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 401:
                return {
                    'success': False,
                    'error': 'GitHub Token无效或已过期',
                    'hint': '请检查GitHub Personal Access Token是否正确，确保有repo权限'
                }
            
            if response.status_code != 200:
                return {
                    'success': False,
                    'error': f'GitHub API请求失败: {response.status_code}'
                }
            
            repos_data = response.json()
            
            # 解析仓库信息
            repos = []
            private_count = 0
            public_count = 0
            
            for repo in repos_data:
                if repo['private']:
                    private_count += 1
                else:
                    public_count += 1
                    
                repos.append({
                    'id': repo['id'],
                    'name': repo['name'],
                    'full_name': repo['full_name'],
                    'description': repo.get('description', ''),
                    'html_url': repo['html_url'],
                    'clone_url': repo['clone_url'],
                    'ssh_url': repo['ssh_url'],
                    'language': repo.get('language', ''),
                    'stars': repo['stargazers_count'],
                    'forks': repo['forks_count'],
                    'is_private': repo['private'],
                    'is_fork': repo['fork'],
                    'updated_at': repo['updated_at'],
                    'default_branch': repo['default_branch']
                })
            
            return {
                'success': True,
                'repos': repos,
                'stats': {
                    'total': len(repos),
                    'private': private_count,
                    'public': public_count
                }
            }
            
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': 'GitHub API请求超时'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'获取GitHub仓库失败: {str(e)}'
            }
