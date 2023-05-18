import logging
from typing import List, Optional, Dict, Set
import os
import re
import shutil
import fnmatch

from librarian.exceptions import InvalidProjectException
from librarian.syncer.data import Bucket
from librarian.syncer import sync_buckets

logger = logging.getLogger(__name__)

STUDIO_PROJECT_FILENAME = ".studio_project"

class LibraryService:

    def __init__(self, library_path:str, workspace_path:str, file_names:List[str]):
        self.library_path = library_path
        self.workspace_path = workspace_path
        self.file_names = file_names

    def get_sync_state(self, project_path) -> Dict:
        sync_state = dict()
        for file in self.file_names:
            file_path = os.path.join(project_path, file)
            if not os.path.exists(file_path):
                continue
            if os.path.isfile(file_path):
                sync_state[file_path] = os.path.getmtime(file_path)
            if os.path.isdir(file_path):
                sync_state[file_path] = Bucket(file_path).files
        return sync_state

    def to_project_path(self, project_name:str) -> str:
        return os.path.join(self.library_path, project_name)

    def is_project(self, project_name:str) -> bool:
        # check if project name corresponds to a valid project in the library.
        return project_name is not None and os.path.exists(os.path.join(self.library_path, project_name, STUDIO_PROJECT_FILENAME))
    
    def copy_files(self, source, destination):
        # copy contents from files. (replace destination if exist)
        for file in self.file_names:
            source_file_path = os.path.join(source, file)
            destination_file_path = os.path.join(destination, file)

            # clear existing files
            if os.path.exists(destination_file_path):
                if os.path.isfile(destination_file_path):
                    os.remove(destination_file_path)
                if os.path.isdir(destination_file_path):
                    shutil.rmtree(destination_file_path)

            if not os.path.exists(source_file_path):
                continue

            if os.path.isfile(source_file_path):
                shutil.copy(source_file_path, destination_file_path)
            if os.path.isdir(source_file_path):
                shutil.copytree(source_file_path, destination_file_path)

    # CRUD operations.
    # create
    def create_project(self, project_name:str, source_project_path=None):
        if source_project_path is None:
            source_project_path = self.workspace_path

        # create project to library from workspace.
        logger.info(f"Creating project {project_name}.")
        
        # create project path if necessary (within the library)
        project_path = self.to_project_path(project_name)

        # check if super directory is a project (if so, raise error).
        target_dir = self.library_path
        for level in re.split(r'[\/\\]', project_name):
            if not os.path.exists(target_dir):
                pass
            if os.path.exists(os.path.join(target_dir, STUDIO_PROJECT_FILENAME)):
                raise FileExistsError("Project is being created in another project directory.")
            target_dir = os.path.join(target_dir, level)

        metadata_path = os.path.join(project_path, STUDIO_PROJECT_FILENAME)
        # check if metadata exists.
        if os.path.exists(metadata_path):
            raise FileExistsError(f"Project {project_name} exists.")

        os.makedirs(project_path, exist_ok=True)
        # add metadata
        with open(metadata_path, "w") as writer:
            writer.write("")

        # copy contents from files.
        self.copy_files(source_project_path, project_path)

    def copy_project(self, source_project_name, destination_project_name:str=None) -> Optional[str]:
        if source_project_name == destination_project_name:
            raise KeyError("Destination of copy cannot be source.")

        if not self.is_project(source_project_name):
            raise InvalidProjectException(source_project_name)

        if destination_project_name is None:
            destination_project_name = source_project_name + "-copy"
            while self.is_project(destination_project_name):
                destination_project_name += "-copy"

        source_project_path = self.to_project_path(source_project_name)

        if self.is_project(destination_project_name):
            confirmation = input("A project already exists with this name. Override? (y/n): ")
            if confirmation != "y":
                return None
            destination_project_path = self.to_project_path(destination_project_name)
            self.copy_files(source_project_path, destination_project_path)
            return destination_project_name
        else:
            self.create_project(destination_project_name, source_project_path=source_project_path)
            return destination_project_name

    # get
    def list_projects(self, pattern=None) -> List[str]:
        # list projects in library (that fit optional pattern argument).
        library_path = self.library_path
        projects = list()
        for dirpath, dirnames, filenames in os.walk(library_path):
            if STUDIO_PROJECT_FILENAME in filenames:
                rel_path = os.path.relpath(dirpath, library_path)
                if pattern is None or fnmatch.fnmatch(rel_path, pattern):
                    projects.append(os.path.relpath(dirpath, self.library_path))
        return projects
    
    def transfer(self, source:str, destinations:Set[str], folders:Set[str]):
        source_path = self.to_project_path(source)
        destination_paths = list(map(self.to_project_path, destinations))
        for folder in folders:
            folder_from_source = os.path.join(source_path, folder)
            if not os.path.exists(folder_from_source):
                logger.info(f"Skipping folder {folder_from_source} which does not exist.")
                continue
            if not os.path.isdir(folder_from_source):
                logger.error(f'target {folder_from_source} is not directory.')
                continue
            for dest_path in destination_paths:
                folder_from_dest = os.path.join(dest_path, folder)
                if os.path.exists(folder_from_dest) and not os.path.isdir(folder_from_dest):
                    logger.warning(f'Target {folder_from_dest} exists but is not a directory: skipping.')
                    continue
                os.makedirs(folder_from_dest, exist_ok=True)
                shutil.copytree(folder_from_source, folder_from_dest, dirs_exist_ok=True)
        return

    # update
    def pull_project(self, from_project_name):
        # pull changes from library to workspace (aka. load project).
        logger.info(f"Pulling from project {from_project_name}.")
        if not self.is_project(from_project_name):
            raise InvalidProjectException(from_project_name)
        project_path = self.to_project_path(from_project_name)
        self.copy_files(project_path, self.workspace_path)

    def push_project(self, to_project_name):
        # push changes from workspace to library.
        logger.info(f"Pushing project {to_project_name}.")
        if not self.is_project(to_project_name):
            raise InvalidProjectException(to_project_name)
        project_path = self.to_project_path(to_project_name)
        self.copy_files(self.workspace_path, project_path)

    def get_sync_state(self):
        new_state = dict()
        for file in self.file_names:
            workspace_file_path = os.path.join(self.workspace_path, file)
            if os.path.isdir(workspace_file_path):
                new_state[file] = Bucket(path=workspace_file_path).files
        return new_state

    def sync(self, project_name, previous_state:Dict=None, last_sync_time=None) -> Dict:
        # sync between library and workspace and returns the final state as output.
        new_state = dict()
        for file in self.file_names:
            workspace_file_path = os.path.join(self.workspace_path, file)
            library_file_path = os.path.join(self.library_path, project_name, file)

            workspace_file_exists = os.path.exists(workspace_file_path)
            library_file_exists = os.path.exists(library_file_path)
            
            # file doesn't exist.
            if not (workspace_file_exists or library_file_exists):
                continue

            # file only exists in one place (copy to other).
            if not workspace_file_exists or not library_file_exists:
                if workspace_file_exists:
                    source_path = workspace_file_path
                    dest_path = library_file_path
                else:
                    source_path = library_file_path
                    dest_path = workspace_file_path

                mtime = os.path.getmtime(source_path)

                # modification detected after last sync --> copy file instead of delete
                if mtime > last_sync_time:
                    dname = os.path.dirname(dest_path)
                    os.makedirs(dname, exist_ok=True)

                    if os.path.isfile(source_path):
                        shutil.copy2(source_path, dest_path)
                    elif os.path.isdir(source_path):
                        shutil.copytree(source_path, dest_path)
                
                # no updates since last sync --> delete both files
                else:
                    if os.path.isfile(source_path):
                        os.remove(source_path)
                    elif os.path.isdir(source_path):
                        shutil.rmtree(source_path)

            # file exist in both workspace and library.
            if os.path.isfile(workspace_file_path):
                # use most recently updated file.
                w_time = os.path.getmtime(workspace_file_path)
                l_time = os.path.getmtime(library_file_path)
                if max(w_time, l_time) <= last_sync_time:
                    pass
                elif w_time > l_time:
                    shutil.copy2(workspace_file_path, library_file_path)
                elif l_time > w_time:
                    shutil.copy2(library_file_path, workspace_file_path)
                
                new_state[file] = os.path.getmtime(workspace_file_path)

            if os.path.isdir(workspace_file_path):
                workspace_file_bucket = Bucket(workspace_file_path)
                library_file_bucket = Bucket(library_file_path)
                previous_file_state = Bucket(files=previous_state.get(file)) if previous_state is not None and file in previous_state else None
                sync_buckets(workspace_file_bucket, library_file_bucket, previous_state=previous_file_state, last_sync_time=last_sync_time)
                new_state[file] = Bucket(path=workspace_file_path).files
        return new_state

    # delete
    def delete_project(self, project_name, safe=True) -> bool:
        # delete project from library.
        logger.info(f"Deleting project {project_name}.")
        if not self.is_project(project_name):
            raise InvalidProjectException(project_name)
        if safe:
            confirmation = input(f"Delete project {project_name}? (y/n): ")
            if confirmation != "y":
                return False
        shutil.rmtree(os.path.join(self.library_path, project_name))
        return True

    # delete multiple projects
    def delete_projects(self, project_names, safe=True) -> bool:
        # check if all the projects are valid.
        for name in project_names:
            if not self.is_project(name):
                raise InvalidProjectException(name)
        
        if safe:
            print("Delete the following projects?\n-----")
            for name in project_names:
                print(f"- {name}")
            print("-----")
            confirmation = input(f"Confirm (y/n): ")
            if confirmation!= "y":
                return False
        
        for name in project_names:
            self.delete_project(name, safe=False)
        return True
