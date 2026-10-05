# aamas-paper-template [![Build Status](https://travis-ci.org/furushchev/aamas-paper-template.svg)](https://travis-ci.org/furushchev/aamas-paper-template)

Latex template for AAMAS Conference

based on:

- http://www.acm.org/publications/proceedings-template
- http://celweb.vuse.vanderbilt.edu/aamas18/submissions/
- http://celweb.vuse.vanderbilt.edu/static/files/aamas18-latex-template.zip


### 1. Prerequisities

```bash
# only for ubuntu 12.04
$ sudo apt-add-repository ppa:texlive-backports/ppa
$ sudo apt-get update
```

### 2. Edit LaTeX files

### 3. Make pdf

```bash
$ make
```

### 4. Release pdf

- Install [Travis Command Line Tool](https://github.com/travis-ci/travis.rb#installation)
- Enable Travis

    ```bash
    travis enable
    travis setup releases --force
    ```

- After `travis` command, configuration like below will be appended to `.travis.yml`.

    ```yaml
    deploy:
      provider: releases
      api_key: "GITHUB OAUTH TOKEN"
      file: main.pdf
      skip_cleanup: true
      on:
        tags: true
    ```

**NOTE** Please make sure you have `skip_cleanup` and `on: tags` is `true`


- Push your tag by `git push --tags`. Then you can watch pdf in github releases.

### Optional. cleaning

```bash
$ make clean
# or
$ make wipe
```
