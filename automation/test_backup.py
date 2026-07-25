import os

def test_backup_script_exists():
    assert os.path.exists("backup.py")
