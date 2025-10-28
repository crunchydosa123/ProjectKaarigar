"""
Cloud Storage Manager for Project Kaarigar
Handles uploading generated videos to Google Cloud Storage
"""

import os
from google.cloud import storage
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CloudStorageManager:
    """Manages video uploads to Google Cloud Storage"""
    
    def __init__(self, bucket_name: str = "all_in_one_bucket", brand_id: str = "BRAND_123"):
        """
        Initialize Cloud Storage Manager
        
        Args:
            bucket_name: GCS bucket name
            brand_id: Brand ID for organizing videos
        """
        self.bucket_name = bucket_name
        self.brand_id = brand_id
        
        try:
            self.client = storage.Client()
            self.bucket = self.client.bucket(bucket_name)
            
            # Verify bucket exists
            if not self.bucket.exists():
                logger.warning(f"⚠️  Bucket {bucket_name} does not exist. It will be created on first upload.")
            
            logger.info(f"☁️  CloudStorageManager initialized: {bucket_name}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize CloudStorageManager: {str(e)}")
            raise
    
    def upload_video(self, local_video_path: str, video_type: str = "generated", 
                     metadata: Optional[Dict] = None) -> Optional[Dict]:
        """
        Upload video to Google Cloud Storage
        
        Args:
            local_video_path: Path to local video file
            video_type: Type of video ('text', 'image', 'generated', 'script')
            metadata: Optional metadata to store with video
            
        Returns:
            Dict with cloud_path, public_url, or None if failed
        """
        try:
            # Validate file exists
            if not os.path.exists(local_video_path):
                logger.error(f"❌ Video file not found: {local_video_path}")
                return None
            
            # Validate file is not empty
            file_size = os.path.getsize(local_video_path)
            if file_size == 0:
                logger.error(f"❌ Video file is empty: {local_video_path}")
                return None
            
            file_size_mb = file_size / (1024 * 1024)
            video_name = Path(local_video_path).name
            
            # Generate cloud storage path with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Map video types to paths
            video_type_paths = {
                "text": f"media/{self.brand_id}/processed/videos/text/{timestamp}/{video_name}",
                "image": f"media/{self.brand_id}/processed/videos/image/{timestamp}/{video_name}",
                "generated": f"media/{self.brand_id}/processed/videos/generated/{timestamp}/{video_name}",
                "script": f"media/{self.brand_id}/processed/videos/script/{timestamp}/{video_name}"
            }
            
            cloud_path = video_type_paths.get(
                video_type, 
                f"media/{self.brand_id}/processed/videos/other/{timestamp}/{video_name}"
            )
            
            # Create blob and upload
            blob = self.bucket.blob(cloud_path)
            
            # Set content type and cache control
            blob.content_type = "video/mp4"
            blob.cache_control = "public, max-age=3600"
            
            # Set metadata if provided
            if metadata:
                blob.metadata = metadata
            else:
                blob.metadata = {
                    "video_type": video_type,
                    "upload_timestamp": timestamp,
                    "brand_id": self.brand_id
                }
            
            # Upload file with progress logging
            logger.info(f"⬆️  Uploading video to GCS: {video_name} ({file_size_mb:.2f} MB)")
            
            blob.upload_from_filename(
                local_video_path,
                content_type="video/mp4",
                timeout=300  # 5 minutes timeout for large files
            )
            
            # Make blob public
            blob.make_public()
            
            # Generate public URL
            public_url = blob.public_url
            
            logger.info(f"✅ Video uploaded to GCS successfully!")
            logger.info(f"   📁 Cloud Path: gs://{self.bucket_name}/{cloud_path}")
            logger.info(f"   📊 File Size: {file_size_mb:.2f} MB")
            logger.info(f"   🔗 Public URL: {public_url}")
            
            return {
                "success": True,
                "cloud_path": cloud_path,
                "public_url": public_url,
                "bucket": self.bucket_name,
                "file_size_mb": round(file_size_mb, 2),
                "video_name": video_name,
                "timestamp": timestamp,
                "video_type": video_type
            }
            
        except Exception as e:
            logger.error(f"❌ Cloud Storage Error: {str(e)}")
            return None
    
    def list_videos(self, video_type: Optional[str] = None, limit: int = 100) -> Optional[Dict]:
        """
        List videos in cloud storage for this brand
        
        Args:
            video_type: Optional filter by video type ('text', 'image', 'generated', 'script')
            limit: Maximum number of videos to return
            
        Returns:
            Dict with list of videos or None if failed
        """
        try:
            if video_type:
                prefix = f"media/{self.brand_id}/processed/videos/{video_type}/"
            else:
                prefix = f"media/{self.brand_id}/processed/videos/"
            
            blobs = self.client.list_blobs(self.bucket_name, prefix=prefix, max_results=limit)
            
            videos = []
            for blob in blobs:
                if blob.name.endswith('.mp4'):
                    size_mb = blob.size / (1024 * 1024) if blob.size else 0
                    
                    # Extract video type from path
                    path_parts = blob.name.split('/')
                    extracted_type = path_parts[4] if len(path_parts) > 4 else "unknown"
                    
                    videos.append({
                        "name": Path(blob.name).name,
                        "path": blob.name,
                        "cloud_url": f"gs://{self.bucket_name}/{blob.name}",
                        "public_url": blob.public_url,
                        "size_mb": round(size_mb, 2),
                        "video_type": extracted_type,
                        "created": blob.time_created.isoformat() if blob.time_created else None,
                        "updated": blob.updated.isoformat() if blob.updated else None
                    })
            
            logger.info(f"📋 Found {len(videos)} video(s) in cloud storage")
            
            return {
                "success": True,
                "bucket": self.bucket_name,
                "brand_id": self.brand_id,
                "total_videos": len(videos),
                "videos": sorted(videos, key=lambda x: x.get('created', ''), reverse=True)
            }
            
        except Exception as e:
            logger.error(f"❌ Error listing videos: {str(e)}")
            return None
    
    def delete_video(self, cloud_path: str) -> bool:
        """
        Delete video from cloud storage
        
        Args:
            cloud_path: Cloud storage path (gs://bucket/path format or just path)
            
        Returns:
            True if deleted, False if failed
        """
        try:
            # Handle gs:// prefix
            if cloud_path.startswith("gs://"):
                cloud_path = cloud_path.replace(f"gs://{self.bucket_name}/", "")
            
            blob = self.bucket.blob(cloud_path)
            
            # Check if blob exists before deleting
            if not blob.exists():
                logger.warning(f"⚠️  Video not found in cloud: {cloud_path}")
                return False
            
            blob.delete()
            
            logger.info(f"✅ Video deleted from cloud: {cloud_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error deleting video: {str(e)}")
            return False
    
    def delete_videos_batch(self, cloud_paths: List[str]) -> Dict[str, bool]:
        """
        Delete multiple videos in batch
        
        Args:
            cloud_paths: List of cloud storage paths
            
        Returns:
            Dict mapping each path to deletion success status
        """
        results = {}
        for path in cloud_paths:
            results[path] = self.delete_video(path)
        
        successful = sum(1 for v in results.values() if v)
        logger.info(f"🗑️  Deleted {successful}/{len(cloud_paths)} video(s)")
        
        return results
    
    def generate_signed_url(self, cloud_path: str, expiration_hours: int = 24) -> Optional[str]:
        """
        Generate a signed URL for private videos
        
        Args:
            cloud_path: Cloud storage path
            expiration_hours: URL expiration time in hours
            
        Returns:
            Signed URL or None if failed
        """
        try:
            if cloud_path.startswith("gs://"):
                cloud_path = cloud_path.replace(f"gs://{self.bucket_name}/", "")
            
            blob = self.bucket.blob(cloud_path)
            
            # Check if blob exists
            if not blob.exists():
                logger.error(f"❌ Video not found: {cloud_path}")
                return None
            
            url = blob.generate_signed_url(
                version="v4",
                expiration=timedelta(hours=expiration_hours),
                method="GET"
            )
            
            logger.info(f"🔐 Generated signed URL (expires in {expiration_hours}h)")
            return url
            
        except Exception as e:
            logger.error(f"❌ Error generating signed URL: {str(e)}")
            return None
    
    def get_video_metadata(self, cloud_path: str) -> Optional[Dict]:
        """
        Get metadata for a specific video
        
        Args:
            cloud_path: Cloud storage path
            
        Returns:
            Dict with video metadata or None if failed
        """
        try:
            if cloud_path.startswith("gs://"):
                cloud_path = cloud_path.replace(f"gs://{self.bucket_name}/", "")
            
            blob = self.bucket.blob(cloud_path)
            blob.reload()  # Fetch latest metadata
            
            if not blob.exists():
                logger.error(f"❌ Video not found: {cloud_path}")
                return None
            
            size_mb = blob.size / (1024 * 1024) if blob.size else 0
            
            return {
                "name": Path(blob.name).name,
                "path": blob.name,
                "public_url": blob.public_url,
                "size_mb": round(size_mb, 2),
                "content_type": blob.content_type,
                "created": blob.time_created.isoformat() if blob.time_created else None,
                "updated": blob.updated.isoformat() if blob.updated else None,
                "metadata": blob.metadata if blob.metadata else {}
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting video metadata: {str(e)}")
            return None
    
    def video_exists(self, cloud_path: str) -> bool:
        """
        Check if video exists in cloud storage
        
        Args:
            cloud_path: Cloud storage path
            
        Returns:
            True if exists, False otherwise
        """
        try:
            if cloud_path.startswith("gs://"):
                cloud_path = cloud_path.replace(f"gs://{self.bucket_name}/", "")
            
            blob = self.bucket.blob(cloud_path)
            return blob.exists()
            
        except Exception as e:
            logger.error(f"❌ Error checking video existence: {str(e)}")
            return False