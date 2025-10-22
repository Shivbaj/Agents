"""
Utility functions for file handling
"""
import os
import hashlib
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from loguru import logger

from src.config.settings import get_settings


def ensure_directory_exists(directory_path: str) -> None:
    """Ensure a directory exists, create it if it doesn't"""
    Path(directory_path).mkdir(parents=True, exist_ok=True)


def get_file_hash(file_path: str) -> Optional[str]:
    """Get MD5 hash of a file"""
    try:
        with open(file_path, 'rb') as f:
            file_hash = hashlib.md5()
            for chunk in iter(lambda: f.read(4096), b""):
                file_hash.update(chunk)
            return file_hash.hexdigest()
    except Exception as e:
        logger.error(f"Failed to get file hash: {str(e)}")
        return None


def validate_file_extension(filename: str, allowed_extensions: List[str]) -> bool:
    """Check if file extension is allowed"""
    if not filename:
        return False
    
    extension = filename.lower().split('.')[-1] if '.' in filename else ''
    return extension in [ext.lower() for ext in allowed_extensions]


def get_file_size_mb(file_path: str) -> float:
    """Get file size in MB"""
    try:
        size_bytes = os.path.getsize(file_path)
        return size_bytes / (1024 * 1024)
    except Exception:
        return 0.0


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to remove potentially dangerous characters"""
    # Remove path separators and other potentially dangerous characters
    dangerous_chars = ['/', '\\', '..', '<', '>', ':', '"', '|', '?', '*']
    
    sanitized = filename
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, '_')
    
    return sanitized


def save_uploaded_file(file_content: bytes, filename: str, upload_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Save uploaded file to disk
    
    Returns:
        Dictionary with file information including path, size, hash, etc.
    """
    settings = get_settings()
    upload_directory = upload_dir or settings.upload_dir
    
    # Ensure upload directory exists
    ensure_directory_exists(upload_directory)
    
    # Sanitize filename
    safe_filename = sanitize_filename(filename)
    
    # Add timestamp to avoid conflicts
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    name, ext = os.path.splitext(safe_filename)
    unique_filename = f"{name}_{timestamp}{ext}"
    
    # Full file path
    file_path = os.path.join(upload_directory, unique_filename)
    
    try:
        # Save file
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        # Get file information
        file_info = {
            'original_filename': filename,
            'saved_filename': unique_filename,
            'file_path': file_path,
            'size_bytes': len(file_content),
            'size_mb': len(file_content) / (1024 * 1024),
            'hash': hashlib.md5(file_content).hexdigest(),
            'upload_time': datetime.now(),
            'success': True
        }
        
        logger.info(f"File saved successfully: {unique_filename} ({file_info['size_mb']:.2f} MB)")
        return file_info
        
    except Exception as e:
        logger.error(f"Failed to save file {filename}: {str(e)}")
        return {
            'original_filename': filename,
            'error': str(e),
            'success': False
        }


def cleanup_old_files(directory: str, max_age_days: int = 7) -> int:
    """
    Clean up files older than specified days
    
    Returns:
        Number of files deleted
    """
    if not os.path.exists(directory):
        return 0
    
    deleted_count = 0
    cutoff_time = datetime.now().timestamp() - (max_age_days * 24 * 60 * 60)
    
    try:
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            
            if os.path.isfile(file_path):
                file_mtime = os.path.getmtime(file_path)
                
                if file_mtime < cutoff_time:
                    os.remove(file_path)
                    deleted_count += 1
                    logger.info(f"Deleted old file: {filename}")
        
        logger.info(f"Cleanup complete: {deleted_count} files deleted from {directory}")
        return deleted_count
        
    except Exception as e:
        logger.error(f"Failed to cleanup files in {directory}: {str(e)}")
        return 0


def get_directory_size(directory: str) -> Dict[str, Any]:
    """Get total size and file count of a directory"""
    if not os.path.exists(directory):
        return {'size_bytes': 0, 'size_mb': 0, 'file_count': 0}
    
    total_size = 0
    file_count = 0
    
    try:
        for dirpath, dirnames, filenames in os.walk(directory):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if os.path.exists(filepath):
                    total_size += os.path.getsize(filepath)
                    file_count += 1
        
        return {
            'size_bytes': total_size,
            'size_mb': total_size / (1024 * 1024),
            'file_count': file_count
        }
        
    except Exception as e:
        logger.error(f"Failed to get directory size for {directory}: {str(e)}")
        return {'size_bytes': 0, 'size_mb': 0, 'file_count': 0}


def read_file_safely(file_path: str, max_size_mb: float = 10.0) -> Optional[str]:
    """
    Safely read a text file with size limit
    
    Args:
        file_path: Path to the file
        max_size_mb: Maximum file size in MB to read
        
    Returns:
        File content as string or None if failed
    """
    try:
        # Check file size first
        size_mb = get_file_size_mb(file_path)
        if size_mb > max_size_mb:
            logger.warning(f"File {file_path} is too large: {size_mb:.2f} MB")
            return None
        
        # Read file
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
            
    except Exception as e:
        logger.error(f"Failed to read file {file_path}: {str(e)}")
        return None