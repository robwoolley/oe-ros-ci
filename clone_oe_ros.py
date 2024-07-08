#!/usr/bin/env python3

import os
import sys

import urllib

# gitpython
import git

# pygithub
from github import Auth
from github import Github
from github import GithubException

GITHUB_USERNAME = os.environ.get('GITHUB_USERNAME', 'https://gitlab.com')
GITHUB_ACCESS_TOKEN = os.environ.get('GITHUB_ACCESS_TOKEN')

GIT_MIRROR_DIR = "git-mirror"

# Ignore the larger repositories that are no longer updated
ignore_list = [
    "https://github.com/ros-infrastructure/index.ros.org.git",
    "https://github.com/ros-infrastructure/www.ros.org.git",
    "https://github.com/osrf/opensplice.git",
    "https://github.com/osrf/rmf_demos.git",
    "https://github.com/osrf/uav_testing.git",
    "https://github.com/osrf/subt.git",
    "https://github.com/osrf/drake.git",
    "https://github.com/osrf/www.ros.org.git",
    "https://github.com/ros2-gbp/.github.git"
]

# Add individual repositories
add_list = [
    "https://github.com/agherzan/meta-raspberrypi.git",
    "https://github.com/raspberrypi/linux.git",
]

def get_all_github_repos(org_name):
    auth = Auth.Token(GITHUB_ACCESS_TOKEN)
    g = Github(auth=auth)
    org = g.get_organization(org_name)
    repos = org.get_repos()
    return [repo.clone_url for repo in repos]

def clone_repos(repos):
    total_repos = len(repos)
    for index, repo_url in enumerate(repos, start=1):
        _url = urllib.parse.urlparse(repo_url)

        _netloc = _url.netloc.split('@')[-1]
        _username = GITHUB_USERNAME
        _password = GITHUB_ACCESS_TOKEN
        _url = _url._replace(netloc=f'{_username}:{_password}@{_netloc}')
        # print(f"_url:{_url}")

        org_name = _url.path.split("/")[1]
        # print(f"org_name:{org_name}")
        if not len(org_name):
            sys.exit(f"ERROR: organization name is empty")

        repo_name = _url.path.split("/")[-1].rsplit(".git", 1)[0]
        # print(f"repo_name:{repo_name}")
        if not len(repo_name):
            sys.exit(f"ERROR: repository name is empty")

        repo_path = os.path.join(GIT_MIRROR_DIR,f"{org_name}/{repo_name}.git")
        # print(f"repo_path:{repo_path}")

        if not os.path.isdir(repo_path):
            print(f"Cloning repository {index}/{total_repos}: {repo_url}")
            repo = git.Repo.clone_from(
                url=f"{repo_url}",
                to_path=f"{repo_path}",
                bare=True,
                multi_options=['--mirror'])
                # mirror=True,
                # recursive=True)
        else:
            print(f"Updating repository {index}/{total_repos}: {repo_url}")
            repo = git.Repo(repo_path)

            origin = repo.remote("origin")
            if origin.url != repo_url:
                sys.exit(f"ERROR: {repo_path} does not originate from {repo_url}")
            
            old_sha = ""
            if repo.head.ref in repo.heads:
                old_sha = repo.head.commit.hexsha
                short_old_sha = repo.git.rev_parse(old_sha, short=8)

            repo.remotes.origin.update()

            new_sha = ""
            if repo.head.ref in repo.heads:
                new_sha = repo.head.commit.hexsha
                short_new_sha = repo.git.rev_parse(new_sha, short=8)
            
            # XXX: These print messages may not be accurate if an update is made on a non-default HEAD
            # if not new_sha:
            #     print(f"{repo_name}: Git repository is empty")
            # elif old_sha != new_sha:
            #     print(f"Updated from {short_old_sha} to {short_new_sha}")
            # else:
            #     print(f"{repo_name}: No update was necessary")

            repo.remotes.origin.fetch()

            # repo = git.Repo.init(repo_path, bare=True)
            # origin = repo.create_remote('origin', url=repo_url)
            # origin.fetch()
            # for branch_index, branch_ref in enumerate(repo.remote().refs, start=1):
            #     if branch_ref.name != 'HEAD':
            #         branch_name = branch_ref.name.split('/')[-1]
            #         print(f"Fetching branch {branch_name} ({branch_index}/{len(repo.remote().refs) - 1})")
            #         repo.create_head(branch_name, commit=branch_ref.commit)
            #         repo.heads[branch_name].set_tracking_branch(branch_ref)
                    # repo.heads[branch_name].checkout()

if __name__ == "__main__":

    if not GITHUB_ACCESS_TOKEN:
        print("Please set the GITHUB_ACCESS_TOKEN env variable.")
        sys.exit(1)

    github_orgs = ["WindRiverLinux23", "OpenEmbedded", "osrf", "ros", "ros-gbp", "ros2-gbp", "ros-infrastructure"]
    all_repos = []
    for org_name in github_orgs:
        repos = get_all_github_repos(org_name)
        all_repos.extend(repos)
    
    for repo in ignore_list:
        if repo in all_repos:
            all_repos.remove(repo)

    for repo in add_list:
        if repo not in all_repos:
            all_repos.extend([repo])

    clone_repos(all_repos)