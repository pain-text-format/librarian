import os

class Bucket:
    def __init__(self, path=None, files=None): # path must exist.

        # generate from path.
        if path is not None and not os.path.exists(path):
            raise FileNotFoundError(path)
        elif path is not None:
            self.path = path
            self.files = dict()
            for root, _, filename in os.walk(path):
                for file in filename:
                    relative_path = os.path.join(root, file)[len(path) + 1:]
                    mtime = self.get_mtime(relative_path)
                    self.files[relative_path] = mtime
        # generate from input
        else:
            self.path = path
            self.files = files

    def get_path(self, filename):
        return os.path.join(self.path, filename)
    
    def get_mtime(self, filename):
        return os.path.getmtime(self.get_path(filename))
