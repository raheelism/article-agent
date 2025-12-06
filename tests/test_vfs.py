import pytest
from app.core.vfs import VFS

def test_vfs_basic_operations():
    vfs = VFS()
    
    # Test Write
    vfs.write_file("test.txt", "Hello World", {"source": "manual"})
    
    # Test Exists
    assert vfs.exists("test.txt")
    assert not vfs.exists("fake.txt")
    
    # Test Read
    content = vfs.read_file("test.txt")
    assert content == "Hello World"
    
    # Test Get File (metadata)
    file_obj = vfs.get_file("test.txt")
    assert file_obj.metadata["source"] == "manual"
    
    # Test List
    assert "test.txt" in vfs.list_files()

def test_vfs_overwrite():
    vfs = VFS()
    vfs.write_file("test.txt", "v1")
    vfs.write_file("test.txt", "v2")
    assert vfs.read_file("test.txt") == "v2"
