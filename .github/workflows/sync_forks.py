# sync_forks.py

import os
import shutil
from github import Github
from github.GithubException import GithubException

def needs_update(repo, branch_name):
    try:
        fork_commit = repo.get_branch(branch_name).commit.sha
        upstream_commit = repo.parent.get_branch(branch_name).commit.sha
        return fork_commit != upstream_commit
    except GithubException:
        print(f"无法获取 {repo.name} 的 {branch_name} 分支信息，假定需要更新")
        return True

def sync_branch(repo, branch_name):
    print(f"同步 {repo.name} 的 {branch_name} 分支")
    repo_path = os.getcwd()
    try:
        parent = repo.parent
        repo_path = os.path.join(repo_path, repo.name)
        # 创建一个临时克隆
        os.system(f"git clone --quiet https://{os.environ['GITHUB_TOKEN']}@github.com/{repo.full_name}.git")
        os.chdir(repo.name)

        # 添加上游远程并获取
        os.system(f"git remote add upstream https://github.com/{parent.full_name}.git")
        os.system("git fetch upstream")

        # 同步所有分支
        for branch in repo.get_branches():
            os.system(f"git checkout {branch.name}")
            os.system(f"git rebase upstream/{branch.name}")
            os.system(f"git push -f origin {branch.name}")

        # 同步所有标签
        os.system("git fetch --tags upstream")
        os.system("git push --tags origin")

        # 返回并清理
        os.chdir('..')
        shutil.rmtree(repo.name)
    except GithubException as e:
        if e.status == 403 and "Repository access blocked" in str(e):
            print(f"仓库 {repo.name} 访问被阻止，跳过")
        else:
            print(f"处理仓库 {repo.name} 时发生错误: {str(e)}")
    except Exception as e:
        print(f"处理仓库 {repo.name} 时发生未预期的错误: {str(e)}")
    finally:
        if os.path.exists(repo_path):
            shutil.rmtree(repo_path)    
    print(f"{repo.name} 同步完成")

def main():
    g = Github(os.environ['GITHUB_TOKEN'])
    user = g.get_user()

    for repo in user.get_repos():
        try: 
            if repo.fork:
                print(f"检查 {repo.name}")
                if not repo.permissions.push:
                    print(f"没有 {repo.name} 的推送权限，跳过")
                    continue
                
                for branch in repo.get_branches():
                    if needs_update(repo, branch.name):
                        sync_branch(repo, branch.name)
                    else:
                        print(f"{repo.name} 的 {branch.name} 分支已是最新，无需更新")
                
                print(f"{repo.name} 处理完成")
        except GithubException as e:
            if e.status == 403 and "Repository access blocked" in str(e):
                print(f"仓库 {repo.name} 访问被阻止，跳过")
            else:
                print(f"处理仓库 {repo.name} 时发生错误: {str(e)}")
            continue
        except Exception as e:
            print(f"处理仓库 {repo.name} 时发生未预期的错误: {str(e)}")
            continue

    print("所有可访问的 fork 仓库检查/同步完成")

if __name__ == "__main__":
    main()
