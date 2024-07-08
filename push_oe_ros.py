#!/usr/bin/env python3

# gitpython
import git

# python-gitlab
import gitlab

import os
import sys

GITLAB_ENABLE_DEBUG = 0
GITLAB_PARENT_GROUP = "github"
GIT_MIRROR_DIR = os.path.join(os.getcwd(), "git-mirror")

GITLAB_SERVER = os.environ.get('GITLAB_SERVER', 'https://gitlab.com')
GITLAB_TOKEN = os.environ.get('GITLAB_TOKEN')

def check_gitlab_groups(gitlab_url, access_token, groups):
    gl = gitlab.Gitlab(url=gitlab_url, private_token=access_token)

    gl.auth()

    if GITLAB_ENABLE_DEBUG:
        gl.enable_debug()

    parent_group = gl.groups.get(GITLAB_PARENT_GROUP)
    # print(f"Parent Group {parent_group.name} with id {parent_group.id}")

    subgroups = parent_group.subgroups.list()
    subgroup_list = [x.name for x in subgroups]

    for group in groups:
        if group not in subgroup_list:
            try:
                gl.groups.create({'name': group, 'path': group, 'parent_id': parent_group.id})
            except Exception as e:
                print(f"Failed to create group {parent_group}/{group} on GitLab: {str(e)}")

def push_to_gitlab(gitlab_url, access_token, repos):
    gl = gitlab.Gitlab(url=gitlab_url, private_token=access_token)

    gl.auth()

    if GITLAB_ENABLE_DEBUG:
        gl.enable_debug()

    parent_group = gl.groups.get(GITLAB_PARENT_GROUP)
    subgroups = parent_group.subgroups.list()

    # for subgroup in subgroups:
    #     print(subgroup)

    for org_name, repo_name in repos:
        repo_base = repo_name.rsplit(".git", 1)[0]

        project = None
        project_path = '/'.join((GITLAB_PARENT_GROUP, org_name, repo_base))

        try:
            # group = gl.groups.get(group_id)
            project = gl.projects.get(project_path)

        except Exception as e:
            # print(f"Failed to get project for {project_path}: {str(e)}")

            group_id = next(x.id for x in subgroups if x.name == org_name )

            try:
                print(f"Creating new project {project_path}")
                project = gl.projects.create({'name': repo_base, 'namespace_id': group_id, 'auto_devops_enabled': False, 'visibility': 'public'})
            except Exception as e:
                print(f"Failed to create project for {project_path}: {str(e)}")

        if hasattr(project, 'name'):
            print(f"Project is {project.name}")
        else:
            print(f"Project name is not set")

        if hasattr(project, 'ssh_url_to_repo'):
            print(f"Project ssh url is {project.ssh_url_to_repo}")
        else:
            print(f"Project ssh url is not set")

        repo = git.Repo(os.path.join(mirror_dir, org_name, repo_name))

        if repo.head.ref not in repo.heads:
            print(f"Skipping {project.name} it is empty")
            continue

        if "gitlab" in repo.remotes:
           repo.delete_remote("gitlab")
        repo.create_remote("gitlab", project.ssh_url_to_repo)
        
        repo.remotes.gitlab.push(push_option=['ci.skip'], all=True)
        repo.remotes.gitlab.push(push_option=['ci.skip'], tags=True)

        

if __name__ == "__main__":
    all_orgs = []
    all_repos = []

    if not GITLAB_TOKEN:
        print("Please set the GITLAB_TOKEN env variable.")
        sys.exit(1)

    gitlab_url = GITLAB_SERVER
    access_token = GITLAB_TOKEN
    mirror_dir = GIT_MIRROR_DIR

    # Check that all groups exist first
    for org_name in os.listdir(mirror_dir):
        all_orgs.extend([org_name])

    check_gitlab_groups(gitlab_url, access_token, all_orgs)
        
    for org_name in os.listdir(mirror_dir):
        for repo_name in os.listdir(os.path.join(mirror_dir, org_name)):
            all_repos.append([org_name, repo_name])

    push_to_gitlab(gitlab_url, access_token, all_repos)
