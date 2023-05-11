import os
from librarian.syncer.data import Bucket
import shutil

def copy_most_recent(bucket_a:Bucket, bucket_b:Bucket, path:str):
    path_in_a = os.path.join(bucket_a.path, path)
    path_in_b = os.path.join(bucket_b.path, path)
    if bucket_a.files[path] > bucket_b.files[path]:
        shutil.copy(path_in_a, path_in_b)
    if bucket_a.files[path] < bucket_b.files[path]:
        shutil.copy(path_in_b, path_in_a)
    return

def copy_one_way(src_bucket:Bucket, target_bucket:Bucket, path:str):
    src_path = os.path.join(src_bucket.path, path)
    target_path = os.path.join(target_bucket.path, path)
    target_directory = os.path.dirname(target_path)
    os.makedirs(target_directory, exist_ok=True)
    shutil.copy(src_path, target_path)


"""
File sync expected behavior:
* Modifications, additions and deletions from one folder are transferred to the other (if the other folder is unchanged).
* Modification overrides deletion: if a file is modified in one folder and deleted in another folder, the modified file will be copied to the latter (instead of being deleted).
* The most recent modification is prioritized: if the same file is modified in both folders, the file modified most recently takes priority.
* The algorithm treats the `UserData` folders like "buckets", i.e. it doesn't recognize folder structures and will not delete folders.
"""

def sync_buckets(bucket_a:Bucket, bucket_b:Bucket, previous_state:Bucket=None, last_sync_time:int=None):
    # sync buckets A and B so they are equal in bucket objects.
    
    if previous_state is None:
        previous_state = bucket_a
    if last_sync_time is None:
        last_sync_time = 0

    paths_a = set(bucket_a.files.keys())
    paths_b = set(bucket_b.files.keys())
    paths_0 = set(previous_state.files.keys())

    # demorgans law
    # undeleted (but possibly modified)
    undeleted_paths = paths_a.intersection(paths_b).intersection(paths_0)

    # deleted from exactly one bucket (undeleted one is possibly modified)
    deleted_in_one_bucket = paths_a.intersection(paths_0).difference(paths_b).union(
        paths_b.intersection(paths_0).difference(paths_a)
    )
    # added to both buckets (possibly different)
    added_in_two_buckets = paths_a.intersection(paths_b).difference(paths_0)
    # added to exactly one bucket
    added_in_one_bucket = paths_a.difference(paths_b).difference(paths_0).union(
        paths_b.difference(paths_a).difference(paths_0)
    )
    # deleted from both buckets (no action needed)
    deleted = paths_0.difference(paths_a).difference(paths_b)

    # apply updates.
    for path in undeleted_paths:
        if max(bucket_a.files[path], bucket_b.files[path]) <= last_sync_time:
            continue
        copy_most_recent(bucket_a, bucket_b, path)

    for path in deleted_in_one_bucket:
        # check if undeleted one is modified.
        if path in paths_a:
            if bucket_a.files[path] > last_sync_time:
                copy_one_way(bucket_a, bucket_b, path)
                continue
            else:
                os.remove(os.path.join(bucket_a.path, path))
        if path in paths_b:
            if bucket_b.files[path] > last_sync_time:
                copy_one_way(bucket_b, bucket_a, path)
                continue
            else:
                os.remove(os.path.join(bucket_b.path, path))
    
    for path in added_in_two_buckets:
        copy_most_recent(bucket_a, bucket_b, path)

    for path in added_in_one_bucket:
        if path in paths_a:
            copy_one_way(bucket_a, bucket_b, path)
        else:
            copy_one_way(bucket_b, bucket_a, path)