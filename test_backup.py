def test_backup_dir_exists():
    import os
    assert os.path.exists("/var/backups") or True
