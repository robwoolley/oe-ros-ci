# Overview

This is a CI/CD pipeline for building OpenEmbedded with ROS.  This involves 
adapting the existing Yocto Project and ROS infrastructure and tools to work
together.

Process (XXX)
1. [rosdep](https://github.com/ros-infrastructure/rosdep): The rosdep tool
   is used to cache a list of packages for each ROS distro.
2. [rosdistro_build_cache](https://github.com/ros-infrastructure/rosdistro/blob/master/scripts/rosdistro_build_cache): 
   The rosdistro_build_cache tool uses the rosdep cache with its manifest
   providers to download the package.xml files for each package.
3. [superflore-gen-oe-recipes](https://github.com/ros-infrastructure/superflore/blob/master/superflore/generators/bitbake/run.py): The
   superflore-gen-oe-recipes tool uses the rosdep cache and invokes
   rosdistro_build_cache to get the Catkin package.xml files which it saves to a new branch in meta-ros.

The meta-ros Yocto Layer has 2 scripts to help automate this process:

1. [ros-generate-cache.sh](https://github.com/ros/meta-ros/blob/master/scripts/ros-generate-cache.sh): Calls rosdistro_build_cache
2. [ros-generate-recipes.sh](https://github.com/ros/meta-ros/blob/master/scripts/ros-generate-recipes.sh): Calls rosdep update and superflore-gen-oe-recipes

## rosdep

One may use Docker with the [container images provided by Open Robotics (OSRF)](https://github.com/osrf/docker_images) to run rosdep.

Start by pulling the ros2 development container and running it.

```
docker pull osrf/ros2:devel
docker run -it --rm osrf/ros2:devel
```

From inside the container install some useful packages with apt:

```
apt-get update
apt-get install -y python3.10-venv vim wget
```

Create a work directory
```
mkdir /work
cd /work
```

Clone the superflore git repository and install it inside a Python virtual environment which includes rosdep.

```
git clone https://github.com/ros-infrastructure/superflore.git
cd superflore
python3 -m venv venv
source venv/bin/activate
python3 ./setup.py install
cd ..
```

Create a custom rosdep directory for 20-default.list
```
export ROS_HOME=/work/roshome
export ROSDEP_SOURCE_PATH=/work/rosdep
rosdep init
rosdep update
```

The cache files are stored in /work/roshome/rosdep/

Clone the rosdistro repository and point the 20-default.list to it.
```
git clone https://github.com/ros/rosdistro

ROSDISTRO_URL="https://raw.githubusercontent.com/ros/rosdistro/master/rosdep"

sed -i -e "s|${ROSDISTRO_URL}|file:///work/rosdistro/rosdep|" ${ROSDEP_SOURCE_PATH}/20-default.list
```

## superflore

```
cd /work/rosdistro
ROS_DISTRO=humble

ROS_DISTRO_RELEASE_DATE=$(git tag --list "${ROS_DISTRO}/*" | sort | tail -n1)
echo ${ROS_DISTRO_RELEASE_DATE}

ROSDISTRO_COMMIT=$(git rev-parse ${ROS_DISTRO_RELEASE_DATE})
echo ${ROSDISTRO_COMMIT}

ROS_DISTRO_RELEASE_DATE_ONLY=$(echo ${ROS_DISTRO_RELEASE_DATE} | cut -d/ -f2)
echo ${ROS_DISTRO_RELEASE_DATE_ONLY}
```

## ros-generate-cache.sh

Grabs the package.xml files from the ros2-gbp

```
cd /work
git clone https://github.com/ros/meta-ros.git
cd meta-ros
```

Export GITHUB_USER with your GitHub username and GITHUB_PASSWORD with your personal access token.  This helps prevent GitHub from rate limiting the accesses.

```
export GITHUB_USER=<USER>
export GITHUB_PASSWORD=<TOKEN>
```

Set your git configuration for your name and e-mail address for the commits created by superflore.
```
git config --global user.email "you@example.com"
git config --global user.name "Your Name"
```

Run the script using the variables set in the previous section.
```
sh scripts/ros-generate-cache.sh ${ROS_DISTRO} ${ROS_DISTRO_RELEASE_DATE_ONLY} /work/rosdistro/ ${ROSDISTRO_COMMIT}
```

```
sh scripts/ros-generate-recipes.sh ${ROS_DISTRO}
```

```
# scripts/rename-bbappend.sh <ROS_DISTRO_LAYER> <SYNC_COMMIT_ID>
scripts/rename-bbappend.sh meta-ros2-humble <SYNC_COMMIT_ID>
```




# Git Mirror Workspace Setup
```
$ python3 -m venv .venv
$ source .venv/bin/activate
$ which python3
/opt/projects/oe_ros_wg/oe-ros-ci/.venv/bin/python3
```

```
$ python3 -m pip install --upgrade pip
Requirement already satisfied: pip in ./.venv/lib/python3.11/site-packages (23.0.1)
Collecting pip
  Downloading pip-24.0-py3-none-any.whl (2.1 MB)
     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 2.1/2.1 MB 250.7 kB/s eta 0:00:00
Installing collected packages: pip
  Attempting uninstall: pip
    Found existing installation: pip 23.0.1
    Uninstalling pip-23.0.1:
      Successfully uninstalled pip-23.0.1
Successfully installed pip-24.0
$ python3 -m pip --version
pip 24.0 from /opt/projects/oe_ros_wg/oe-ros-ci/.venv/lib/python3.11/site-packages/pip (python 3.11)
```

```
$ python3 -m pip install -r requirements.txt
```

## Running clone_oe_ros.py

source .venv/bin/activate

export GITHUB_USERNAME="<USERNAME>"
export GITHUB_ACCESS_TOKEN="ghp_<GITHUB_TOKEN>"

python3 clone_oe_ros.py

## Running push_oe_ros.py

source .venv/bin/activate

export GITLAB_SERVER="https://<GITLAB_SERVER>/"
export GITLAB_TOKEN="glpat-<GITLAB_TOKEN>"
python3 push_oe_ros.py

