# Librarian

> Manage Koikatsu projects by managing the movement of Koikatsu `UserData` folders.

## Installation

Setup virtual environment and install repository:
```bash
pip install git+https://github.com/pain-text-format/librarian.git
```

### Setup
Configure the Librarian to work with the `UserData` file between the Koikatsu game directory and some `[library]` directory of choice.

```bash
librarian --library [library-path] --workspace [koikatsu-path]
```
For example:
```bash
librarian --library ./my_library --workspace "C:/Program Files/Koikatsu Party"
```
Librarian data is stored in `.librarian.yaml`.

## Usage
Copy the `UserData` game folder to `$LIBRARY/hello-world/UserData`.
```bash
librarian create hello-world
```
This creates the following folder structure:
```
- $LIBRARY
    - hello-world
        - UserData
            - audio
            - bg
            - cap
            - ...
        - .studio_project
```
The folder `hello-world` is called a 'project'. Notice it contains a `.studio_project` file. By definition, any folder in the library that directly contains such a file is considered a project.

This library project is now *assigned* to the game directory, a.k.a the *workspace*. At **most** one project can be assigned to the workspace at any given time. A workspace can have *no* projects assigned. Assignment allows the user to perform `push` or `pull` actions: syncing features described [below](#pushpull-from-assigned-projects).

When a new project is created (e.g. `librarian create hello-universe`), the Librarian will *unassign* `hello-world` and assign `hello-universe`. To see which project is currently assigned to the workspace, execute
```bash
librarian
```
List all projects:
```bash
librarian list
# Retrieved Librarian data.
# -----
# - project-1
# - project-2
# - ...
# -----
```
To assign a different project, execute
```
librarian assign [project-name]
```

### Features
* Wildcarding is supported with the `-p` flag (e.g. `librarian list -p hello-*` or `librarian delete -p hello-*`)
* Folder structure is supported (e.g. `librarian create path/to/project-name`)

Delete a project:
```bash
librarian delete --name [project-name]
```
Load a project:
```bash
librarian load [project-name]
```

## Push/Pull from Assigned Projects
The following commands work only if a project is assigned to the workspace.

Copy an updated `UserData` folder from the game directory to the assigned project location with
```bash
librarian push
```
This will delete the `UserData` folder in the assigned project directory.

Similarly, load the `UserData` folder from the assigned project directory to the game directory with
```bash
librarian pull
```

## Applications
You may have multiple projects organized like so:
```
- $LIBRARY
    - genre-1
        - story-1
            - chapter-1
                - UserData
                - .studio_project
            - chapter-2
                - UserData
                - .studio_project
            - ...
    - genre-2
        ...
    - gallery
        - theme-1
```
View projects within a scope with `librarian list`:
```bash
librarian list -p genre-1/*
# response
# ------
# - genre-1\story-1\chapter-1
# - genre-1\story-1\chapter-2
# - ...
```
Save your workspace to the assigned project with `librarian push`, then load another ongoing project:
```bash
librarian load genre-1/story-1/chapter-1
```