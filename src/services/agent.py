import json
import re
import logging
from typing import Dict, List, Any, Optional

from src.services.gmail import GmailAgent
from src.services.github import GithubService
from src.services.openai import OpenAIService

logging.basicConfig(level = logging.INFO)
logger = logging.getLogger(__name__)

class AgentService:
    def __init__(self, gmail_agent=None, github_agent=None, openai_agent=None):
        self.gmail_agent = gmail_agent if gmail_agent else GmailAgent()
        self.github_agent = github_agent if github_agent else GithubService()
        self.openai_agent = openai_agent if openai_agent else OpenAIService()

    async def process_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        plan = await self.openai_agent.create_action_plan(query, context)
        result_data = {
            "emails": [],
            "email_contents": {},
            "github_repos": [],
            "repository_alerts": {},
            "repository_issues": {},
            "repository_structures": {},
            "errors": []
        }

        actions_taken = []
        extracted_repo_names = []

        for step in plan.get("steps", []):
            step_type = step.get("type")
            params = step.get("params", {})

            try:
                if step_type == "search_gmail":
                    search_query = params.get("query")
                    max_results = params.get("max_results", 10)
                     
                    if not search_query:
                        result_data["errors"].append(f"Missing 'query' parameter for {step_type}")
                        continue
                    
                    print(f"Searching Gmail with query: {search_query}")
                    actions_taken.append(f"Searching Gmail with query: {search_query}")
                    emails = await self.gmail_agent.search_emails(search_query, max_results)
                    result_data["emails"] = emails

                    extracted_repo_names = self._extract_repo_info_from_emails(emails)
                    if extracted_repo_names:
                        logger.info(f"Extracted repository names: {extracted_repo_names}")
                        actions_taken.append(f"Extracted repository names: {', '.join(extracted_repo_names)}")
                    else:
                        logger.warning("No repository names were extracted from emails")
                        actions_taken.append("No repository names were extracted from emails")
                
                elif step_type == "get_email_content":
                    email_id = params.get("email_id")

                    if not email_id:
                        result_data["errors"].append(f"Missing 'email_id' parameter for {step_type}")
                        continue
                    
                    email_id = self._clean_email_id(email_id)

                    print(f"Getting email content for ID: {email_id}")
                    actions_taken.append(f"Getting email content for ID: {email_id}")
                    email_content = await self.gmail_agent.get_email_content(email_id)
                    result_data["email_contents"][email_id] = email_content
                    
                elif step_type == "search_github_repos":
                    search_query = params.get("query")
                    max_results = params.get("max_results", 5)
                    
                    if not search_query:
                        result_data["errors"].append(f"Missing 'query' parameter for {step_type}")
                        continue
                    
                    print(f"Searching GitHub repositories with query: {search_query}")
                    actions_taken.append(f"Searching GitHub repositories with query: {search_query}")
                    repos = await self.github_agent.search_repositories(search_query, max_results)
                    result_data["github_repos"] = repos
                    
                elif step_type == "get_repo_alerts":
                    repo_name = params.get("repo_name")
                    
                    # Skip if repo_name is "extracted_from_email" but no repositories were actually extracted
                    if repo_name == "extracted_from_email" and not extracted_repo_names:
                        error_msg = "No repository names were extracted from emails to get alerts for"
                        print(error_msg)
                        actions_taken.append(error_msg)
                        result_data["errors"].append(error_msg)
                        continue
                    
                    # If repo_name is not provided, use extracted repository names
                    if not repo_name and extracted_repo_names:
                        for extracted_repo in extracted_repo_names:
                            print(f"Getting repository alerts for: {extracted_repo}")
                            actions_taken.append(f"Getting repository alerts for: {extracted_repo}")
                            alerts = await self.github_agent.get_repository_alerts(extracted_repo)

                            if alerts and len(alerts) > 0 and "error" in alerts[0]:
                                error_msg = f"Error getting alerts for {extracted_repo}: {alerts[0].get('message', 'Unknown error')}"
                                print(error_msg)
                                actions_taken.append(error_msg)
                                result_data["errors"].append(error_msg)
                            else:
                                result_data["repository_alerts"][extracted_repo] = alerts
                    elif repo_name:
                        print(f"Getting repository alerts for: {repo_name}")
                        actions_taken.append(f"Getting repository alerts for: {repo_name}")
                        alerts = await self.github_agent.get_repository_alerts(repo_name)
                        
                        if alerts and len(alerts) > 0 and "error" in alerts[0]:
                            error_msg = f"Error getting alerts for {repo_name}: {alerts[0].get('message', 'Unknown error')}"
                            print(error_msg)
                            actions_taken.append(error_msg)
                            result_data["errors"].append(error_msg)
                        else:
                            result_data["repository_alerts"][repo_name] = alerts
                    else:
                        result_data["errors"].append(f"Missing 'repo_name' parameter for {step_type} and no repository names extracted from emails")
                        
                elif step_type == "get_repo_issues":
                    repo_name = params.get("repo_name")
                    state = params.get("state", "open")

                    # Skip if repo_name is "extracted_from_email" but no repositories were actually extracted
                    if repo_name == "extracted_from_email" and not extracted_repo_names:
                        error_msg = "No repository names were extracted from emails to get issues for"
                        print(error_msg)
                        actions_taken.append(error_msg)
                        result_data["errors"].append(error_msg)
                        continue

                    if not repo_name and extracted_repo_names:
                        for extracted_repo in extracted_repo_names:
                            print(f"Getting repository issues for: {extracted_repo}")
                            actions_taken.append(f"Getting repository issues for: {extracted_repo}")
                            issues = await self.github_agent.get_repository_issues(extracted_repo, state)
                            
                            if issues and len(issues) > 0 and "error" in issues[0]:
                                error_msg = f"Error getting issues for {extracted_repo}: {issues[0].get('message', 'Unknown error')}"
                                print(error_msg)
                                actions_taken.append(error_msg)
                                result_data["errors"].append(error_msg)
                            else:
                                result_data["repository_issues"][extracted_repo] = issues
                    elif repo_name:
                        print(f"Getting repository issues for: {repo_name}")
                        actions_taken.append(f"Getting repository issues for: {repo_name}")
                        issues = await self.github_agent.get_repository_issues(repo_name, state) 

                        if issues and len(issues) > 0 and "error" in issues[0]:
                            error_msg = f"Error getting issues for {repo_name}: {issues[0].get('message', 'Unknown error')}"
                            print(error_msg)
                            actions_taken.append(error_msg)
                            result_data["errors"].append(error_msg)
                        else:
                            result_data["repository_issues"][repo_name] = issues
                    else:
                        result_data["errors"].append(f"Missing 'repo_name' parameter for {step_type} and no repository names extracted from emails")
                        
                elif step_type == "get_repo_structure":
                    repo_name = params.get("repo_name")
                    max_depth = params.get("max_depth", 3)
                    
                    # Skip if repo_name is "extracted_from_email" but no repositories were actually extracted
                    if repo_name == "extracted_from_email" and not extracted_repo_names:
                        error_msg = "No repository names were extracted from emails to get structure for"
                        print(error_msg)
                        actions_taken.append(error_msg)
                        result_data["errors"].append(error_msg)
                        continue
                    
                    if not repo_name and extracted_repo_names:
                        logger.info(f"No repo_name provided, using extracted names: {extracted_repo_names}")
                        for extracted_repo in extracted_repo_names:
                            logger.info(f"Getting repository structure for: {extracted_repo}")
                            print(f"Getting repository structure for: {extracted_repo}")
                            actions_taken.append(f"Getting repository structure for: {extracted_repo}")
                            structure = await self.github_agent.get_repository_structure(extracted_repo, max_depth)
                            
                            if structure and "error" in structure:
                                error_msg = f"Error getting structure for {extracted_repo}: {structure.get('message', 'Unknown error')}"
                                logger.error(error_msg)
                                print(error_msg)
                                actions_taken.append(error_msg)
                                result_data["errors"].append(error_msg)
                            else:
                                result_data["repository_structures"][extracted_repo] = structure
                    elif repo_name:
                        logger.info(f"Using provided repo_name: {repo_name}")
                        print(f"Getting repository structure for: {repo_name}")
                        actions_taken.append(f"Getting repository structure for: {repo_name}")
                        structure = await self.github_agent.get_repository_structure(repo_name, max_depth)
                        
                        if structure and "error" in structure:
                            error_msg = f"Error getting structure for {repo_name}: {structure.get('message', 'Unknown error')}"
                            logger.error(error_msg)
                            print(error_msg)
                            actions_taken.append(error_msg)
                            result_data["errors"].append(error_msg)
                        else:
                            result_data["repository_structures"][repo_name] = structure
                    else:
                        error_msg = f"Missing 'repo_name' parameter for {step_type} and no repository names extracted from emails"
                        logger.error(error_msg)
                        print(error_msg)
                        actions_taken.append(error_msg)
                        result_data["errors"].append(error_msg)
                        
                elif step_type == "get_repo_contents":
                    repo_name = params.get("repo_name")
                    path = params.get("path", "")
                    
                    # Skip if repo_name is "extracted_from_email" but no repositories were actually extracted
                    if repo_name == "extracted_from_email" and not extracted_repo_names:
                        error_msg = "No repository names were extracted from emails to get contents for"
                        print(error_msg)
                        actions_taken.append(error_msg)
                        result_data["errors"].append(error_msg)
                        continue
                    
                    if not repo_name and extracted_repo_names:
                        for extracted_repo in extracted_repo_names:
                            print(f"Getting repository contents for: {extracted_repo}, path: {path}")
                            actions_taken.append(f"Getting repository contents for: {extracted_repo}, path: {path}")
                            contents = await self.github_agent.get_repository_contents(extracted_repo, path)
                            
                            if contents and len(contents) > 0 and "error" in contents[0]:
                                error_msg = f"Error getting contents for {extracted_repo}: {contents[0].get('message', 'Unknown error')}"
                                print(error_msg)
                                actions_taken.append(error_msg)
                                result_data["errors"].append(error_msg)
                            else:
                                key = f"{extracted_repo}:{path}" if path else extracted_repo
                                if "repository_contents" not in result_data:
                                    result_data["repository_contents"] = {}
                                result_data["repository_contents"][key] = contents
                    elif repo_name:
                        print(f"Getting repository contents for: {repo_name}, path: {path}")
                        actions_taken.append(f"Getting repository contents for: {repo_name}, path: {path}")
                        contents = await self.github_agent.get_repository_contents(repo_name, path)
                        
                        if contents and len(contents) > 0 and "error" in contents[0]:
                            error_msg = f"Error getting contents for {repo_name}: {contents[0].get('message', 'Unknown error')}" 
                            print(error_msg)
                            actions_taken.append(error_msg)
                            result_data["errors"].append(error_msg)
                        else:
                            key = f"{repo_name}:{path}" if path else repo_name
                            if "repository_contents" not in result_data:
                                result_data["repository_contents"] = {}
                            result_data["repository_contents"][repo_name] = contents
                    else:
                        result_data["errors"].append(f"Missing 'repo_name' parameter for {step_type} and no repository names extracted from emails")
                        
                else:
                    result_data["errors"].append(f"Unknown step type: {step_type}")
                    actions_taken.append(f"Unknown step type: {step_type}")
                    
            except Exception as e:
                error_message = f"Error processing {step_type}: {str(e)}"
                print(error_message)
                result_data["errors"].append(error_message)
                actions_taken.append(error_message)
        
        actions_taken.append("Generating response")
        response = await self.openai_agent.generate_response(query, result_data)
        
        return {
            "query": query,
            "plan": plan,
            "data": result_data,
            "response": response,
            "actions_taken": actions_taken
        }
    
    def _clean_email_id(self, email_id: str) -> str:
        email_id = re.sub(r'[<>]', '', email_id)
        email_id = re.sub(r'email_id_from_search_results', '', email_id)
        email_id = re.sub(r'[^\w\-]', '', email_id)
        
        return email_id
    
    def _extract_repo_info_from_emails(self, emails: List[Dict[str, Any]]) -> List[str]:
        repos = []

        repo_patterns = [
            r'([a-zA-Z0-9\-_]+)/([a-zA-Z0-9\-_]+)',
            r'([a-zA-Z0-9\-_]+) / ([a-zA-Z0-9\-_]+)',
            r'repository ([a-zA-Z0-9\-_]+)/([a-zA-Z0-9\-_]+)',
            r'([a-zA-Z0-9\-_]+)\'s repository ([a-zA-Z0-9\-_]+)',
            r'Dependabot alerts? for ([a-zA-Z0-9\-_]+)/([a-zA-Z0-9\-_]+)',
            r'Dependabot alerts? for ([a-zA-Z0-9\-_]+) / ([a-zA-Z0-9\-_]+)'
        ]
        
        for email in emails:
            subject = email.get("subject", "")
            snippet = email.get("snippet", "")

            logger.info(f"Extracting repo info from email - Subject: {subject}")
            logger.info(f"Snippet: {snippet}")

            for text in [subject, snippet]:
                for pattern in repo_patterns:
                    matches = re.findall(pattern, text)
                    for match in matches:
                        if isinstance(match, tuple) and len(match) == 2:
                            username, repo = match
                            username = username.strip()
                            repo = repo.strip()
                            repo_name = f"{username}/{repo}"
                            logger.info(f"Found repository: {repo_name} (from pattern: {pattern})")
                            repos.append(repo_name)
                        elif isinstance(match, str):
                            repo_name = match.strip()
                            logger.info(f"Found repository: {repo_name} (from pattern: {pattern})")
                            repos.append(repo_name)
            
            account_repo_match = re.search(r'([a-zA-Z0-9\-_]+)\'s personal account ([a-zA-Z0-9\-_]+) / ([a-zA-Z0-9\-_]+)', snippet)
            if account_repo_match:
                username = account_repo_match.group(2).strip()
                repo = account_repo_match.group(3).strip()
                repo_name = f"{username}/{repo}"
                logger.info(f"Found repository from personal account pattern: {repo_name}")
                repos.append(repo_name)
                
            dependabot_match = re.search(r'\[GitHub\] (?:Your )?Dependabot alerts? (?:summary )?for ([a-zA-Z0-9\-_]+)/([a-zA-Z0-9\-_]+)', subject)
            if dependabot_match:
                username = dependabot_match.group(1).strip()
                repo = dependabot_match.group(2).strip()
                repo_name = f"{username}/{repo}"
                logger.info(f"Found repository from Dependabot alert subject: {repo_name}")
                repos.append(repo_name)
                
        clean_repos = []
        for repo in set(repos):
            clean_repo = repo.replace(" ", "")
            clean_repos.append(clean_repo)
            
        logger.info(f"Final extracted repositories: {clean_repos}")
        return clean_repos
    
                
                
                                
                            
                    
                    
                    
                                
                