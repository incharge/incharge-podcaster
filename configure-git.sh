# Configure git
#!/usr/bin/env bash

# The default branch is main in modern projects
git config --global init.defaultBranch main

# Set the pull strategy
git config --global pull.rebase false

# Check that the git email is configured so commits are attributed to the correct user and not "noreply"
git config --get user.email > /dev/null || {
	echo Set your git email e.g: echo git config --global user.email "my@email"
}
# Check that the git user name is configured
git config --get user.name > /dev/null || {
	echo Set your git user name e.g: echo git config --global user.name "My Name"
}
