import argparse
import os
import logging
from typing import List, Set

from librarian.controller import LibrarianController

logger = logging.getLogger(__name__)

def librarian_command_line():

    parser = argparse.ArgumentParser()
    parser.add_argument('--library', type=str, help='specify path to library')
    parser.add_argument('--workspace', type=str, help='specify path to workspace')
    parser.add_argument('--log', type=str, help='specify logging level', default='info')
    parser.add_argument('--sync_targets', nargs='+', default=[])

    subparsers = parser.add_subparsers(dest="command")

    create_parser = subparsers.add_parser('create', help='Create a project from current project.')
    create_parser.add_argument('project_name', type=str)

    copy_parser = subparsers.add_parser('copy', help='Copy a project in library.')
    copy_parser.add_argument('source_project_name', type=str)
    copy_parser.add_argument('destination_project_name', type=str, nargs='?')
    copy_parser.add_argument('--long', action='store_true', help='Specify full path of copy relative to library root directory.')

    assign_parser = subparsers.add_parser('assign', help='Assign current project to one in library.')
    assign_parser.add_argument('project_name', type=str)
    assign_parser.add_argument('--no-save', action='store_true', help='Do not save changes to current project before pulling new project.')
    
    transfer_parser = subparsers.add_parser('transfer', help='Transfer items from a source project to a destination.')
    transfer_parser.add_argument('-s', '--source', type=str)
    transfer_parser.add_argument('-d', '--destination', type=str, nargs='+', default=[])
    transfer_parser.add_argument('-g', '--groups', type=str, nargs="+", default=[], help='Folder groups to specify which folders to copy.')

    list_parser = subparsers.add_parser('list', help='List projects in the library.')
    list_parser.add_argument('-p', '--pattern', type=str)

    pull_parser = subparsers.add_parser('pull', help='Load linked project from library.')

    load_parser = subparsers.add_parser('load', help='Load project from library.')
    load_parser.add_argument('project_name', type=str)

    push_parser = subparsers.add_parser('push', help='Save current project to library.')

    sync_parser = subparsers.add_parser('sync', help='Sync current project with library.')

    delete_parser = subparsers.add_parser('delete', help='Delete a project or multiple projects.')
    delete_parser.add_argument('-n', '--names', type=str, nargs="+", default=[])
    delete_parser.add_argument('-p', '--pattern', type=str)

    parser.set_defaults()
    args = parser.parse_args()
    command = args.command

    # logging
    log_levels = {
        'debug': logging.DEBUG,
        'info': logging.INFO,
        'warning': logging.WARNING,
        'error': logging.ERROR,
    }
    log_level = args.log
    if isinstance(log_level, str) and log_level.lower() in log_levels:
        logging.basicConfig(level=log_levels[log_level.lower()])
    else:
        logger.warning(f"Invalid logging level selected: {log_level}")

    library_path = args.library
    workspace_path = args.workspace
    sync_targets = args.sync_targets

    if isinstance(library_path, str) and not os.path.exists(library_path):
        raise FileNotFoundError(library_path)
    if isinstance(workspace_path, str) and not os.path.exists(workspace_path):
        raise FileNotFoundError(workspace_path)

    controller = LibrarianController(library_path=library_path, workspace_path=workspace_path, sync_targets=sync_targets)

    if command == 'create':
        controller.create(args.project_name)

    if command == 'copy':
        controller.copy(
            args.source_project_name,
            args.destination_project_name,
            args.long
        )

    if command == 'assign':
        controller.assign(args.project_name, save_changes=not args.no_save)

    if command == 'transfer':
        source:str = args.source
        destination:List[str] = args.destination
        groups:Set[str] = args.groups
        controller.transfer(source, destination, groups)

    if command == 'pull':
        controller.pull()
    
    if command == 'push':
        controller.push()

    if command == 'sync':
        controller.sync()

    if command == 'load':
        controller.load_project(args.project_name)

    if args.command == 'list':
        controller.list_projects(args.pattern)

    if args.command == 'delete':
        controller.delete_projects(args.names, args.pattern)

    if args.command is None:
        controller.display_status()

    controller.update_sync_state()
    controller.update_metadata()