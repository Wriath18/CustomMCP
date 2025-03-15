import os
import logging
from typing import Dict, List, Any, Optional
from github import Github, GithubException, Auth

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GithubService:

    def __init__(self):
        self.client = None
        self.username = os.getenv("GITHUB_USERNAME")
        self.access_token = os.getenv("GITHUB_ACCESS_TOKEN")

    async def get_client(self) -> Github:
        if self.client is None:
            if not self.access_token:
                raise ValueError("GitHub API credentials not properly configured. Please set GITHUB_ACCESS_TOKEN environment variable.")
            
            try:
                auth = Auth.Token(self.access_token)
                self.client = Github(auth=auth)

                user = self.client.get_user()
                logger.info(f"Successfully authenticated as {user.login}")
            except Exception as e:
                logger.error(f"Error initializing GitHub client: {str(e)}")
                raise ValueError(f"Failed to initialize GitHub client: {str(e)}")
        return self.client
    
    async def check_status(self) -> Dict[str, Any]:
        try:
            client = await self.get_client()
            user = client.get_user()
            return {
                "status" : "connected",
                "usrename" : user.login,
                "name" : user.name,
                "repos_count" : user.public_repos + user.owned_private_repos
            }
        except Exception as e:
            logger.error(f"GitHub service status check failed: {str(e)}")
            return {
                "status" : "error",
                "message" : str(e)
            }
        
    
    async def search_repositories(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        try:
            client = await self.get_client()
            logger.info(f"Searching GitHub repositories with query: {query}")

            if query.lower() == "my repositories" and self.username:
                repos = client.get_user().get_repos()
            else:
                repos = client.search_repositories(query)
            
            repo_list = []
            count = 0

            for repo in repos:
                if count >= max_results:
                    break

                repo_data = {
                    "name": repo.full_name,
                    "description": repo.description,
                    "url": repo.html_url,
                    "stars": repo.stargazers_count,
                    "forks": repo.forks_count,
                    "open_issues": repo.open_issues_count,
                    "language": repo.language,
                    "created_at": repo.created_at.isoformat() if repo.created_at else None,
                    "updated_at": repo.updated_at.isoformat() if repo.updated_at else None
                }

                repo_list.append(repo_data)
                count += 1
            
            logger.info(f"Found {len(repo_list)} repositories matching query: {query}")
            return repo_list
        
        except GithubException as e:
            logger.error(f"GitHub API error during repository search: {str(e)}")
            return [{
                "error": "GitHub API error",
                "message": f"An error occurred while searching for repositories with query '{query}'.",
                "status_code": getattr(e, 'status', None),
                "details": str(e)
            }]
        except Exception as e:
            logger.error(f"Unexpected error during repository search: {str(e)}")
            return [{
                "error": "Unexpected error",
                "message": f"An unexpected error occurred while searching for repositories.",
                "details": str(e)
            }]
        
    
    async def get_repository_alerts(self, repo_name: str) -> List[Dict[str, Any]]:
        try:
            client = await self.get_client()
            logger.info(f"Getting security alerts for repository: {repo_name}")

            try:
                repo = client.get_repo(repo_name)
                alerts = []

                try:
                    vulnerability_alerts = repo.get_vulnerability_alert()
                    if hasattr(vulnerability_alerts, '__iter__'):
                        for alert in vulnerability_alerts:
                            try:
                                alert_data = {
                                    "package": alert.dependency.package.name if hasattr(alert, 'dependency') and hasattr(alert.dependency, 'package') else "Unknown",
                                    "severity": alert.security_advisory.severity if hasattr(alert, 'security_advisory') else "Unknown",
                                    "summary": alert.security_advisory.summary if hasattr(alert, 'security_advisory') else "Unknown",
                                    "description": alert.security_advisory.description if hasattr(alert, 'security_advisory') else "Unknown",
                                    "published_at": alert.security_advisory.published_at.isoformat() if hasattr(alert, 'security_advisory') and alert.security_advisory.published_at else None,
                                    "url": alert.security_advisory.permalink if hasattr(alert, 'security_advisory') else None
                                    
                                }
                                alerts.append(alert_data)
                            except Exception as e:
                                alerts.append({
                                    "package": "Unknown",
                                    "severity": "Unknown",
                                    "summary": "Alert details not accessible",
                                    "description": "The alert information could not be retrieved due to API limitations or permissions",
                                    "published_at": None,
                                    "url": None
                                })
                    else:
                        alerts.append({
                            "package": "Unknown",
                            "severity": "Unknown",
                            "summary": "Repository vulnerability alerts status",
                            "description": f"Vulnerability alerts are {'enabled' if vulnerability_alerts else 'disabled'} for this repository",
                            "published_at": None,
                            "url": None
                        })
                except GithubException as e:
                    alerts.append({
                         "package": "Unknown",
                        "severity": "Unknown",
                        "summary": "Could not access vulnerability alerts",
                        "description": f"Error accessing vulnerability alerts: {str(e)}",
                        "published_at": None,
                        "url": None
                    })

                logger.info(f"Retrieved {len(alerts)} alerts for repository {repo_name}")
                return alerts
            
            except GithubException as e:
                # Handle specific GitHub API errors
                if e.status == 404:
                    logger.error(f"Repository not found: {repo_name}. Error: {str(e)}")
                    return [{
                        "error": "Repository not found",
                        "message": f"The repository '{repo_name}' does not exist or you don't have access to it.",
                        "status_code": 404,
                        "details": str(e)
                    }]
                elif e.status == 403:
                    logger.error(f"Permission denied for repository: {repo_name}. Error: {str(e)}")
                    return [{
                        "error": "Permission denied",
                        "message": f"You don't have permission to access the repository '{repo_name}'.",
                        "status_code": 403,
                        "details": str(e)
                    }]
                else:
                    logger.error(f"GitHub API error for repository {repo_name}: {str(e)}")
                    return [{
                        "error": "GitHub API error",
                        "message": f"An error occurred while accessing the repository '{repo_name}'.",
                        "status_code": e.status,
                        "details": str(e)
                    }]
                
        except Exception as e:
            logger.error(f"Unexpected error accessing repository alerts for {repo_name}: {str(e)}")
            return [{
                "error": "Unexpected error",
                "message": f"An unexpected error occurred while accessing alerts for repository '{repo_name}'.",
                "details": str(e)
            }]
        
    async def get_repository_issues(self, repo_name: str, state: str = "open") -> List[Dict[str, Any]]:
        try:
            client = await self.get_client()
            logger.info(f"Getting issues for repository: {repo_name}, state: {state}")

            try:
                repo = client.get_repo(repo_name)
                issues = repo.get_issues(state=state)

                issue_list = []
                for issue in issues:
                    issue_data = {
                        "number": issue.number,
                        "title": issue.title,
                        "state": issue.state,
                        "created_at": issue.created_at.isoformat(),
                        "updated_at": issue.updated_at.isoformat(),
                        "url": issue.html_url,
                        "body": issue.body,
                        "labels": [label.name for label in issue.labels]
                    }
                    issue_list.append(issue_data)

                logger.info(f"Retrieved {len(issue_list)} issues for repository {repo_name}")
                return issue_list
            
            except GithubException as e:
                # Handle specific GitHub API errors
                if e.status == 404:
                    logger.error(f"Repository not found: {repo_name}. Error: {str(e)}")
                    return [{
                        "error": "Repository not found",
                        "message": f"The repository '{repo_name}' does not exist or you don't have access to it.",
                        "status_code": 404,
                        "details": str(e)
                    }]
                elif e.status == 403:
                    logger.error(f"Permission denied for repository: {repo_name}. Error: {str(e)}")
                    return [{
                        "error": "Permission denied",
                        "message": f"You don't have permission to access the repository '{repo_name}'.",
                        "status_code": 403,
                        "details": str(e)
                    }]
                else:
                    logger.error(f"GitHub API error for repository {repo_name}: {str(e)}")
                    return [{
                        "error": "GitHub API error",
                        "message": f"An error occurred while accessing the repository '{repo_name}'.",
                        "status_code": e.status,
                        "details": str(e)
                    }]
                
        except Exception as e:
            logger.error(f"Unexpected error accessing repository issues for {repo_name}: {str(e)}")
            return [{
                "error": "Unexpected error",
                "message": f"An unexpected error occurred while accessing issues for repository '{repo_name}'.",
                "details": str(e)
            }]
        
    async def get_repository_contents(self, repo_name: str, path: str = "") -> List[Dict[str, Any]]:
        try:
            client = await self.get_client()
            logger.info(f"Getting contents for repository: {repo_name}, path: {path}")

            try:
                repo = client.get_repo(repo_name)
                contents = repo.get_contents(path)

                content_list = []
                for content in contents:
                    content_data =  {
                        "name": content.name,
                        "path": content.path,
                        "type": content.type,
                        "size": content.size,
                        "url": content.html_url
                    }
                    content_list.append(content_data)
                logger.info(f"Retrieved {len(content_list)} items from repository {repo_name}, path: {path}")
                return content_list
            
            except GithubException as e:
                # Handle specific GitHub API errors
                if e.status == 404:
                    logger.error(f"Repository or path not found: {repo_name}/{path}. Error: {str(e)}")
                    return [{
                        "error": "Repository or path not found",
                        "message": f"The repository '{repo_name}' or path '{path}' does not exist or you don't have access to it.",
                        "status_code": 404,
                        "details": str(e)
                    }]
                elif e.status == 403:
                    logger.error(f"Permission denied for repository: {repo_name}. Error: {str(e)}")
                    return [{
                        "error": "Permission denied",
                        "message": f"You don't have permission to access the repository '{repo_name}'.",
                        "status_code": 403,
                        "details": str(e)
                    }]
                else:
                    logger.error(f"GitHub API error for repository {repo_name}: {str(e)}")
                    return [{
                        "error": "GitHub API error",
                        "message": f"An error occurred while accessing the repository '{repo_name}'.",
                        "status_code": e.status,
                        "details": str(e)
                    }]
                
        except Exception as e:
            logger.error(f"Unexpected error accessing repository contents for {repo_name}: {str(e)}")
            return [{
                "error": "Unexpected error",
                "message": f"An unexpected error occurred while accessing contents for repository '{repo_name}'.",
                "details": str(e)
            }]
        
    async def get_repository_structure(self, repo_name: str, max_depth: int = 3) -> Dict[str, Any]:
        try:
            client = await self.get_client()
            logger.info(f"Getting repository structure for: {repo_name}")

            try:
                repo = client.get_repo(repo_name)
                repo_info = {
                    "name": repo.name,
                    "full_name": repo.full_name,
                    "description": repo.description,
                    "url": repo.html_url,
                    "default_branch": repo.default_branch,
                    "stars": repo.stargazers_count,
                    "forks": repo.forks_count,
                    "open_issues": repo.open_issues_count,
                    "language": repo.language,
                    "created_at": repo.created_at.isoformat() if repo.created_at else None,
                    "updated_at": repo.updated_at.isoformat() if repo.updated_at else None,
                    "structure": await self.get_directory_structure(repo, "", 1, max_depth)
                }

                logger.info(f"Successfully retrieved structure for repository {repo_name}")
                return repo_info
            
            except GithubException as e:
                # Handle specific GitHub API errors
                if e.status == 404:
                    logger.error(f"Repository not found: {repo_name}. Error: {str(e)}")
                    return {
                        "error": "Repository not found",
                        "message": f"The repository '{repo_name}' does not exist or you don't have access to it.",
                        "status_code": 404,
                        "details": str(e)
                    }
                elif e.status == 403:
                    logger.error(f"Permission denied for repository: {repo_name}. Error: {str(e)}")
                    return {
                        "error": "Permission denied",
                        "message": f"You don't have permission to access the repository '{repo_name}'.",
                        "status_code": 403,
                        "details": str(e)
                    }
                else:
                    logger.error(f"GitHub API error for repository {repo_name}: {str(e)}")
                    return {
                        "error": "GitHub API error",
                        "message": f"An error occurred while accessing the repository '{repo_name}'.",
                        "status_code": e.status,
                        "details": str(e)
                    }
                
        except Exception as e:
            logger.error(f"Unexpected error accessing repository {repo_name}: {str(e)}")
            return {
                "error": "Unexpected error",
                "message": f"An unexpected error occurred while accessing the repository '{repo_name}'.",
                "details": str(e)
            }
    async def get_directory_structure(self, repo, path: str, current_depth: int, max_depth: int) -> List[Dict[str, Any]]:
        if current_depth > max_depth:
            return [{"name": "...", "type": "max_depth_reached"}]
        
        try:
            contents = repo.get_contents(path)
            
            if not isinstance(contents, list):
                return [{
                    "name": contents.name,
                    "path": contents.path,
                    "type": contents.type,
                    "size": contents.size
                }]
            
            structure = []
            for content in contents:
                item = {
                    "name": content.name,
                    "path": content.path,
                    "type": content.type,
                    "size": content.size if content.type == "file" else None
                }
                
                if content.type == "dir" and current_depth < max_depth:
                    try:
                        item["contents"] = await self.get_directory_structure(
                            repo, content.path, current_depth + 1, max_depth
                        )
                    except GithubException as e:
                        item["contents"] = [{"error": str(e), "path": content.path}]
                
                structure.append(item)
            
            return structure

        except GithubException as e:
            logger.error(f"Error getting directory structure for path {path}: {str(e)}")
            return [{"error": str(e), "path": path}] 
                    