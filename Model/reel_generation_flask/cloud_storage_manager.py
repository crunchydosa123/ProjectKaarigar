"""
Cloud Storage Manager for Project Kaarigar
Handles uploading generated videos to Google Cloud Storage
"""

import os
from google.cloud import storage
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict
import json


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
        self.client = storage.Client()
        self.bucket = self.client.bucket(bucket_name)
        print(f"☁️  CloudStorageManager initialized: {bucket_name}")
    
    def upload_video(self, local_video_path: str, video_type: str = "generated", 
                     metadata: Optional[Dict] = None) -> Optional[Dict]:
        """
        Upload video to Google Cloud Storage
        
        Args:
            local_video_path: Path to local video file
            video_type: Type of video ('text', 'image', 'generated')
            metadata: Optional metadata to store with video
            
        Returns:
            Dict with cloud_path, public_url, or None if failed
        """
        try:
            # Validate file exists
            if not os.path.exists(local_video_path):
                print(f"❌ Video file not found: {local_video_path}")
                return None
            
            # Get file info
            file_size = os.path.getsize(local_video_path)
            file_size_mb = file_size / (1024 * 1024)
            video_name = Path(local_video_path).name
            
            # Generate cloud storage path with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if video_type == "text":
                cloud_path = f"media/{self.brand_id}/processed/videos/text_{timestamp}/{video_name}"
            elif video_type == "image":
                cloud_path = f"media/{self.brand_id}/processed/videos/image_{timestamp}/{video_name}"
            else:
                cloud_path = f"media/{self.brand_id}/processed/videos/generated_{timestamp}/{video_name}"
            
            # Create blob and upload
            blob = self.bucket.blob(cloud_path)
            
            # Set metadata if provided
            if metadata:
                blob.metadata = metadata
            
            # Upload file
            blob.upload_from_filename(
                local_video_path,
                content_type="video/mp4"
            )
            
            # Make blob public
            blob.make_public()
            
            # Generate public URL
            public_url = blob.public_url
            
            print(f"✅ Video uploaded to GCS successfully!")
            print(f"   📁 Cloud Path: gs://{self.bucket_name}/{cloud_path}")
            print(f"   📊 File Size: {file_size_mb:.2f} MB")
            print(f"   🔗 Public URL: {public_url}")
            
            return {
                "success": True,
                "cloud_path": cloud_path,
                "public_url": public_url,
                "bucket": self.bucket_name,
                "file_size_mb": round(file_size_mb, 2),
                "video_name": video_name,
                "timestamp": timestamp
            }
            
        except Exception as e:
            print(f"❌ Cloud Storage Error: {str(e)}")
            return None
    
    def list_videos(self) -> Optional[Dict]:
        """
        List all videos in cloud storage for this brand
        
        Returns:
            Dict with list of videos or None if failed
        """
        try:
            prefix = f"media/{self.brand_id}/processed/videos/"
            blobs = self.client.list_blobs(self.bucket_name, prefix=prefix)
            
            videos = []
            for blob in blobs:
                if blob.name.endswith('.mp4'):
                    size_mb = blob.size / (1024 * 1024)
                    videos.append({
                        "name": Path(blob.name).name,
                        "path": blob.name,
                        "cloud_url": f"gs://{self.bucket_name}/{blob.name}",
                        "public_url": blob.public_url,
                        "size_mb": round(size_mb, 2)
                    })
            
            return {
                "success": True,
                "bucket": self.bucket_name,
                "brand_id": self.brand_id,
                "total_videos": len(videos),
                "videos": sorted(videos, key=lambda x: x['name'])
            }
            
        except Exception as e:
            print(f"❌ Error listing videos: {str(e)}")
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
            blob.delete()
            
            print(f"✅ Video deleted from cloud: {cloud_path}")
            return True
            
        except Exception as e:
            print(f"❌ Error deleting video: {str(e)}")
            return False
    
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
            from datetime import timedelta
            
            if cloud_path.startswith("gs://"):
                cloud_path = cloud_path.replace(f"gs://{self.bucket_name}/", "")
            
            blob = self.bucket.blob(cloud_path)
            url = blob.generate_signed_url(
                version="v4",
                expiration=timedelta(hours=expiration_hours),
                method="GET"
            )
            
            return url
            
        except Exception as e:
            print(f"❌ Error generating signed URL: {str(e)}")
            return None