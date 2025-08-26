"""
Firebase Storage Client for Knowledge Extraction App
Handles all Firestore operations for video segments and collections
"""

import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import asdict
import uuid
import json

from google.cloud import firestore
from google.cloud.firestore import Query
from firebase_admin import storage

try:
    from .firebase_config import get_firebase_config
except ImportError:
    from storage.firebase_config import get_firebase_config

# Import VideoSegment - it might not be available in some contexts
try:
    from ..youtube_extractor import VideoSegment
except ImportError:
    try:
        from youtube_extractor import VideoSegment
    except ImportError:
        # VideoSegment might not be available, we'll handle this case
        VideoSegment = None


class FirebaseStorage:
    """Firebase storage client for video segments and knowledge extraction"""
    
    def __init__(self, credentials_path: str = None):
        """
        Initialize Firebase storage client
        
        Args:
            credentials_path: Path to Firebase service account key
        """
        self.config = get_firebase_config(credentials_path)
        self.db = self.config.get_firestore_client()
        self.bucket = self.config.get_storage_bucket()
        
        # Collection references
        self.videos_ref = self.db.collection('videos')
        self.segments_ref = self.db.collection('segments')  # Main collection for video segments with summaries
        self.collections_ref = self.db.collection('collections')
    
    def save_segment(self, segment: VideoSegment, tags: List[str] = None, user_notes: str = "") -> str:
        """
        Save a video segment to Firestore
        
        Args:
            segment: VideoSegment object
            tags: Optional list of tags
            user_notes: Optional user notes
            
        Returns:
            str: Document ID of saved segment
        """
        try:
            # Generate unique segment ID
            segment_id = str(uuid.uuid4())
            
            # Prepare segment data
            segment_data = {
                'segment_id': segment_id,
                'video_id': segment.video_id,
                'url': segment.url,
                'start_time': segment.start_time,
                'end_time': segment.end_time,
                'duration': segment.end_time - segment.start_time,
                'transcript': segment.transcript,
                'raw_segments': segment.raw_segments,
                'tags': tags or [],
                'user_notes': user_notes,
                'created_at': firestore.SERVER_TIMESTAMP,
                'updated_at': firestore.SERVER_TIMESTAMP,
                'character_count': len(segment.transcript),
                'segment_count': len(segment.raw_segments)
            }
            
            # Save to Firestore
            doc_ref = self.segments_ref.document(segment_id)
            doc_ref.set(segment_data)
            
            # Also update/create video document
            self._update_video_info(segment)
            
            print(f"✓ Segment saved with ID: {segment_id}")
            return segment_id
            
        except Exception as e:
            print(f"✗ Failed to save segment: {e}")
            raise
    
    def get_segment(self, segment_id: str) -> Optional[Dict]:
        """
        Retrieve a segment by ID
        
        Args:
            segment_id: Segment document ID
            
        Returns:
            Dict: Segment data or None if not found
        """
        try:
            doc = self.segments_ref.document(segment_id).get()
            if doc.exists:
                data = doc.to_dict()
                data['id'] = doc.id
                return data
            return None
            
        except Exception as e:
            print(f"✗ Failed to get segment {segment_id}: {e}")
            return None
    
    def get_video_segments(self, video_id: str) -> List[Dict]:
        """
        Get all segments for a specific video
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            List[Dict]: List of segment documents
        """
        try:
            query = self.segments_ref.where('video_id', '==', video_id)
            query = query.order_by('start_time')
            
            segments = []
            for doc in query.stream():
                data = doc.to_dict()
                data['id'] = doc.id
                segments.append(data)
            
            return segments
            
        except Exception as e:
            print(f"✗ Failed to get segments for video {video_id}: {e}")
            return []
    
    def search_segments(self, query: str = None, filters: Dict = None, limit: int = 50) -> List[Dict]:
        """
        Search segments with filters
        
        Args:
            query: Text to search in transcript (basic contains)
            filters: Dictionary of filters (tags, video_id, date_range)
            limit: Maximum results to return
            
        Returns:
            List[Dict]: Matching segment documents
        """
        try:
            # Start with base query
            firestore_query = self.segments_ref
            
            # Apply filters
            if filters:
                if 'video_id' in filters:
                    firestore_query = firestore_query.where('video_id', '==', filters['video_id'])
                
                if 'tags' in filters and filters['tags']:
                    firestore_query = firestore_query.where('tags', 'array_contains_any', filters['tags'])
                
                if 'min_duration' in filters:
                    firestore_query = firestore_query.where('duration', '>=', filters['min_duration'])
                
                if 'max_duration' in filters:
                    firestore_query = firestore_query.where('duration', '<=', filters['max_duration'])
            
            # Order and limit
            firestore_query = firestore_query.order_by('created_at', direction=Query.DESCENDING)
            firestore_query = firestore_query.limit(limit)
            
            # Execute query
            segments = []
            for doc in firestore_query.stream():
                data = doc.to_dict()
                data['id'] = doc.id
                
                # Basic text search in transcription (client-side filtering)
                if query and query.lower() not in data.get('transcription', '').lower():
                    continue
                
                segments.append(data)
            
            return segments
            
        except Exception as e:
            print(f"✗ Failed to search segments: {e}")
            return []
    
    def update_segment(self, segment_id: str, updates: Dict) -> bool:
        """
        Update a segment document
        
        Args:
            segment_id: Segment document ID
            updates: Dictionary of fields to update
            
        Returns:
            bool: True if successful
        """
        try:
            updates['updated_at'] = firestore.SERVER_TIMESTAMP
            
            doc_ref = self.segments_ref.document(segment_id)
            doc_ref.update(updates)
            
            print(f"✓ Segment {segment_id} updated")
            return True
            
        except Exception as e:
            print(f"✗ Failed to update segment {segment_id}: {e}")
            return False
    
    def delete_segment(self, segment_id: str) -> bool:
        """
        Delete a segment document
        
        Args:
            segment_id: Segment document ID
            
        Returns:
            bool: True if successful
        """
        try:
            self.segments_ref.document(segment_id).delete()
            print(f"✓ Segment {segment_id} deleted")
            return True
            
        except Exception as e:
            print(f"✗ Failed to delete segment {segment_id}: {e}")
            return False
    
    def create_collection(self, name: str, segment_ids: List[str], description: str = "") -> str:
        """
        Create a collection of segments
        
        Args:
            name: Collection name
            segment_ids: List of segment IDs to include
            description: Optional description
            
        Returns:
            str: Collection document ID
        """
        try:
            collection_id = str(uuid.uuid4())
            
            collection_data = {
                'collection_id': collection_id,
                'name': name,
                'description': description,
                'segment_ids': segment_ids,
                'segment_count': len(segment_ids),
                'created_at': firestore.SERVER_TIMESTAMP,
                'updated_at': firestore.SERVER_TIMESTAMP,
                'tags': []
            }
            
            doc_ref = self.collections_ref.document(collection_id)
            doc_ref.set(collection_data)
            
            print(f"✓ Collection '{name}' created with ID: {collection_id}")
            return collection_id
            
        except Exception as e:
            print(f"✗ Failed to create collection: {e}")
            raise
    
    def batch_save_segments(self, segments: List[VideoSegment], tags: List[str] = None) -> List[str]:
        """
        Save multiple segments in a batch operation
        
        Args:
            segments: List of VideoSegment objects
            tags: Optional list of tags to apply to all segments
            
        Returns:
            List[str]: List of document IDs
        """
        try:
            batch = self.db.batch()
            segment_ids = []
            
            for segment in segments:
                segment_id = str(uuid.uuid4())
                segment_ids.append(segment_id)
                
                segment_data = {
                    'segment_id': segment_id,
                    'video_id': segment.video_id,
                    'url': segment.url,
                    'start_time': segment.start_time,
                    'end_time': segment.end_time,
                    'duration': segment.end_time - segment.start_time,
                    'transcript': segment.transcript,
                    'raw_segments': segment.raw_segments,
                    'tags': tags or [],
                    'user_notes': '',
                    'created_at': firestore.SERVER_TIMESTAMP,
                    'updated_at': firestore.SERVER_TIMESTAMP,
                    'character_count': len(segment.transcript),
                    'segment_count': len(segment.raw_segments)
                }
                
                doc_ref = self.segments_ref.document(segment_id)
                batch.set(doc_ref, segment_data)
            
            # Execute batch
            batch.commit()
            
            print(f"✓ Batch saved {len(segments)} segments")
            return segment_ids
            
        except Exception as e:
            print(f"✗ Failed to batch save segments: {e}")
            raise
    
    def save_complete_segment(self, segment_data: Dict) -> str:
        """
        Save complete video segment with knowledge extraction to Firestore
        
        Args:
            segment_data: Complete segment data with transcript, summary, and extracted entities
            
        Returns:
            str: Document ID of saved segment
        """
        try:
            # Generate unique segment ID
            segment_id = str(uuid.uuid4())
            
            # Add segment ID and timestamps
            complete_data = {
                **segment_data,
                'segment_id': segment_id,
                'created_at': firestore.SERVER_TIMESTAMP,
                'updated_at': firestore.SERVER_TIMESTAMP
            }
            
            # Save to segments collection
            doc_ref = self.segments_ref.document(segment_id)
            doc_ref.set(complete_data)
            
            # Also update video info
            video_data = {
                'video_id': segment_data.get('video_id'),
                'last_segment_at': firestore.SERVER_TIMESTAMP,
                'segment_count': firestore.Increment(1)
            }
            
            video_ref = self.videos_ref.document(segment_data.get('video_id', 'unknown'))
            video_ref.set(video_data, merge=True)
            
            print(f"✓ Complete segment saved with ID: {segment_id}")
            return segment_id
            
        except Exception as e:
            print(f"✗ Failed to save complete segment: {e}")
            raise
    
    def get_complete_segment(self, segment_id: str) -> Optional[Dict]:
        """
        Retrieve a complete segment by ID
        
        Args:
            segment_id: Segment document ID
            
        Returns:
            Dict: Segment data or None if not found
        """
        try:
            doc = self.segments_ref.document(segment_id).get()
            if doc.exists:
                data = doc.to_dict()
                data['id'] = doc.id
                return data
            return None
            
        except Exception as e:
            print(f"✗ Failed to get segment {segment_id}: {e}")
            return None
    
    def search_segments(self, query: str = None, filters: Dict = None, limit: int = 20) -> List[Dict]:
        """
        Search video segments with filters
        
        Args:
            query: Text to search in transcript/summary (basic contains)
            filters: Dictionary of filters (tags, video_id, date_range, entities)
            limit: Maximum results to return
            
        Returns:
            List[Dict]: List of matching segment documents
        """
        try:
            # Start with base query
            firestore_query = self.segments_ref
            
            # Apply filters
            if filters:
                if 'video_id' in filters:
                    firestore_query = firestore_query.where('video_id', '==', filters['video_id'])
                
                if 'tags' in filters and filters['tags']:
                    firestore_query = firestore_query.where('tags', 'array_contains_any', filters['tags'])
                
                if 'min_duration' in filters:
                    firestore_query = firestore_query.where('duration', '>=', filters['min_duration'])
                
                if 'max_duration' in filters:
                    firestore_query = firestore_query.where('duration', '<=', filters['max_duration'])
                
                # Note: Entity count filters removed since we calculate entity counts on-demand
                # This reduces Firebase index requirements and storage costs
            
            # Order and limit
            firestore_query = firestore_query.order_by('created_at', direction=Query.DESCENDING)
            firestore_query = firestore_query.limit(limit)
            
            # Execute query
            segments = []
            for doc in firestore_query.stream():
                data = doc.to_dict()
                data['id'] = doc.id
                
                # Basic text search in summary and transcription (client-side filtering)
                if query:
                    search_text = f"{data.get('summary', '')} {data.get('transcription', '')}".lower()
                    if query.lower() not in search_text:
                        continue
                
                segments.append(data)
            
            return segments
            
        except Exception as e:
            print(f"✗ Failed to search segments: {e}")
            return []
    
    def get_segments_by_video(self, video_id: str) -> List[Dict]:
        """
        Get all segments for a specific video
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            List[Dict]: List of segment documents for the video
        """
        try:
            # Simple query without ordering to avoid index requirement
            query = self.segments_ref.where('video_id', '==', video_id)
            
            segments = []
            for doc in query.stream():
                data = doc.to_dict()
                data['id'] = doc.id
                segments.append(data)
            
            # Sort by created_at client-side
            segments.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            
            return segments
            
        except Exception as e:
            print(f"✗ Failed to get segments for video {video_id}: {e}")
            # Fallback: get all segments and filter client-side
            try:
                print("   Trying fallback method...")
                all_segments = []
                for doc in self.segments_ref.stream():
                    data = doc.to_dict()
                    if data.get('video_id') == video_id:
                        data['id'] = doc.id
                        all_segments.append(data)
                
                # Sort by created_at client-side
                all_segments.sort(key=lambda x: x.get('created_at', ''), reverse=True)
                return all_segments
                
            except Exception as fallback_error:
                print(f"✗ Fallback also failed: {fallback_error}")
                return []
    
    def update_complete_segment(self, segment_id: str, updates: Dict) -> bool:
        """
        Update a complete segment document
        
        Args:
            segment_id: Segment document ID
            updates: Dictionary of fields to update
            
        Returns:
            bool: True if successful
        """
        try:
            updates['updated_at'] = firestore.SERVER_TIMESTAMP
            
            doc_ref = self.segments_ref.document(segment_id)
            doc_ref.update(updates)
            
            print(f"✓ Segment {segment_id} updated")
            return True
            
        except Exception as e:
            print(f"✗ Failed to update segment {segment_id}: {e}")
            return False
    
    def delete_complete_segment(self, segment_id: str) -> bool:
        """
        Delete a complete segment document
        
        Args:
            segment_id: Segment document ID
            
        Returns:
            bool: True if successful
        """
        try:
            self.segments_ref.document(segment_id).delete()
            print(f"✓ Segment {segment_id} deleted")
            return True
            
        except Exception as e:
            print(f"✗ Failed to delete segment {segment_id}: {e}")
            return False
    
    def get_stats(self) -> Dict:
        """
        Get storage statistics
        
        Returns:
            Dict: Statistics about stored data
        """
        try:
            stats = {
                'total_segments': 0,
                'total_videos': 0,
                'total_collections': 0,
                'total_summaries': 0,
                'total_transcript_chars': 0,
                'total_knowledge_entities': 0,
                'latest_segment_date': None,
                'latest_summary_date': None
            }
            
            # Count segments
            segments = list(self.segments_ref.limit(1000).stream())
            stats['total_segments'] = len(segments)
            
            # Calculate total characters and find latest date
            for doc in segments:
                data = doc.to_dict()
                stats['total_transcript_chars'] += data.get('character_count', 0)
                
                created_at = data.get('created_at')
                if created_at and (not stats['latest_segment_date'] or created_at > stats['latest_segment_date']):
                    stats['latest_segment_date'] = created_at
            
            # Count unique videos
            video_ids = set()
            for doc in segments:
                video_ids.add(doc.to_dict().get('video_id'))
            stats['total_videos'] = len(video_ids)
            
            # Count collections
            collections = list(self.collections_ref.limit(100).stream())
            stats['total_collections'] = len(collections)
            
            # Count segments with summaries and knowledge entities
            # Note: segments collection now contains both raw segments and segments with summaries
            summary_segments = []
            for doc in self.segments_ref.limit(1000).stream():
                data = doc.to_dict()
                # Only count segments that have summary data (complete segments)
                if data.get('summary'):
                    summary_segments.append(data)
                    
            stats['total_summaries'] = len(summary_segments)
            
            # Calculate knowledge entity statistics on-demand
            for data in summary_segments:
                # Calculate entity counts from actual data
                entity_count = (
                    len(data.get('books', [])) +
                    len(data.get('people', [])) +
                    len(data.get('places', [])) +
                    len(data.get('facts', [])) +
                    len(data.get('topics', []))
                )
                stats['total_knowledge_entities'] += entity_count
                
                created_at = data.get('created_at')
                if created_at and (not stats['latest_summary_date'] or created_at > stats['latest_summary_date']):
                    stats['latest_summary_date'] = created_at
            
            return stats
            
        except Exception as e:
            print(f"✗ Failed to get stats: {e}")
            return {}
    
    def _update_video_info(self, segment: VideoSegment):
        """Update video document with basic info"""
        try:
            video_data = {
                'video_id': segment.video_id,
                'last_extracted_at': firestore.SERVER_TIMESTAMP,
                'segment_count': firestore.Increment(1)
            }
            
            # Use merge to avoid overwriting existing data
            video_ref = self.videos_ref.document(segment.video_id)
            video_ref.set(video_data, merge=True)
            
        except Exception as e:
            print(f"Warning: Failed to update video info: {e}")


# Convenience functions
def get_storage_client(credentials_path: str = None) -> FirebaseStorage:
    """
    Get Firebase storage client instance
    
    Args:
        credentials_path: Path to Firebase service account key
        
    Returns:
        FirebaseStorage: Storage client instance
    """
    return FirebaseStorage(credentials_path)


if __name__ == "__main__":
    # Test Firebase storage
    print("Testing Firebase Storage...")
    print("-" * 40)
    
    try:
        # Initialize storage client
        storage_client = get_storage_client()
        
        # Get statistics
        stats = storage_client.get_stats()
        print("Storage Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        print("✓ Firebase storage client working!")
        
    except Exception as e:
        print(f"✗ Error testing storage: {e}")
        print("\nPlease ensure:")
        print("1. Firebase is properly configured")
        print("2. Service account key is available")
        print("3. Required permissions are set")