#!/bin/bash
export WORKON_HOME=%(env_path)s
%(activate_path)s

# colors
PS1="\[\e[0;36m\](`basename \"$VIRTUAL_ENV\"`)\[\e[0m\] $_OLD_VIRTUAL_PS1"

# set a fancy prompt (non-color, unless we know we "want" color)
case "$TERM" in
    xterm-color) color_prompt=yes;;
esac

# enable color support of ls and also add handy aliases
if [ -x /usr/bin/dircolors ]; then
    test -r ~/.dircolors && eval "$(dircolors -b ~/.dircolors)" || eval "$(dircolors -b)"
    alias ls='ls --color=auto'
    #alias dir='dir --color=auto'
    #alias vdir='vdir --color=auto'

    alias grep='grep --color=auto'
    alias fgrep='fgrep --color=auto'
    alias egrep='egrep --color=auto'
fi

#alias gst='git status '
alias gc='git commit '
alias gca='git commit -a '
alias ga='git add '
alias gco='git checkout '
alias gb='git branch '
alias gm='git merge '
alias gt='git status'

cd %(project_name)s
