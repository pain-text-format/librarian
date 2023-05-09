class InvalidProjectException(Exception):
    def __init__(self, project_name):
        super().__init__(f"\"{project_name}\" is invalid project or doesn't exist.")

class FolderCollisionException(Exception):
    def __init__(self):
        super().__init__("The library and workspace cannot be assigned the same directory.")