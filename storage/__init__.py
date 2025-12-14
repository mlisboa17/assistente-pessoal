"""
☁️ Storage Package
Armazenamento em nuvem (Google Drive, OneDrive)
"""
from .cloud_storage import CloudStorageManager, GoogleDriveManager, OneDriveManager, get_cloud_storage

__all__ = ['CloudStorageManager', 'GoogleDriveManager', 'OneDriveManager', 'get_cloud_storage']
