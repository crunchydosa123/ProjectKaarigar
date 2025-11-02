import { useState, useEffect } from 'react';
import { usePage } from '@/contexts/PageContext';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { House, Youtube, Loader2, ExternalLink, Eye, ThumbsUp, MessageSquare, BarChart3, Upload, Check, Play } from 'lucide-react';
import { mediaAPI } from '@/lib/api';

//const BASE_URL = 'https://backend-557742533869.asia-south1.run.app';
const BASE_URL = '';

// API Helper
const youtubeAPI = {
  authStatus: async () => {
    const res = await fetch(`${BASE_URL}/api/youtube/auth/status`, {
      credentials: 'include'
    });
    return res.json();
  },
  
  startAuth: async () => {
    const res = await fetch(`${BASE_URL}/api/youtube/auth/start`, {
      credentials: 'include'
    });
    return res.json();
  },
  
  upload: async (data: any) => {
    const res = await fetch(`${BASE_URL}/api/youtube/upload`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(data)
    });
    return res.json();
  },
  
  getVideos: async () => {
    const res = await fetch(`${BASE_URL}/api/youtube/videos`, {
      credentials: 'include'
    });
    return res.json();
  },
  
  getAnalytics: async (days: number = 30) => {
    const res = await fetch(`${BASE_URL}/api/youtube/analytics/channel?days=${days}`, {
      credentials: 'include'
    });
    return res.json();
  }
};

const YouTubeShorts = () => {
  const { setCurrentPage } = usePage();
  const [connected, setConnected] = useState(false);
  const [channelInfo, setChannelInfo] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'upload' | 'videos' | 'analytics'>('upload');

  useEffect(() => {
    checkYouTubeConnection();
  }, []);

  const checkYouTubeConnection = async () => {
    try {
      setLoading(true);
      const result = await youtubeAPI.authStatus();
      if (result.success) {
        setConnected(result.connected);
        setChannelInfo(result.channel);
      }
    } catch (error) {
      console.error('Failed to check YouTube connection:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleConnectYouTube = async () => {
    try {
      const result = await youtubeAPI.startAuth();
      if (result.success) {
        // Open OAuth popup
        window.open(result.authorization_url, 'YouTube Auth', 'width=600,height=700');
        
        // Poll for connection
        const interval = setInterval(async () => {
          const status = await youtubeAPI.authStatus();
          if (status.success && status.connected) {
            setConnected(true);
            setChannelInfo(status.channel);
            clearInterval(interval);
          }
        }, 2000);
        
        // Stop polling after 2 minutes
        setTimeout(() => clearInterval(interval), 120000);
      }
    } catch (error) {
      console.error('Failed to connect YouTube:', error);
      alert('Failed to connect YouTube. Please try again.');
    }
  };

  if (loading) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-white">
        <Loader2 className="animate-spin h-8 w-8 text-red-600" />
      </div>
    );
  }

  if (!connected) {
    return (
      <div className="w-full h-full bg-cover bg-center flex flex-col" style={{ backgroundImage: "url('/white_bg.png')" }}>
        {/* Header */}
        <div className="w-full mt-10 flex justify-start items-center p-3">
          <button
            className="h-10 w-10 bg-gray-500 rounded-md flex justify-center items-center text-white"
            onClick={() => setCurrentPage("list-products")}
          >
            <House />
          </button>
          <div className="text-md font-bold ml-3">YouTube Shorts Manager</div>
        </div>

        {/* Connect YouTube */}
        <div className="flex-1 flex flex-col items-center justify-center p-6">
          <Youtube className="h-24 w-24 text-red-600 mb-6" />
          <h2 className="text-2xl font-bold mb-2">Connect Your YouTube Channel</h2>
          <p className="text-gray-600 text-center mb-8 max-w-md">
            Upload Shorts directly from your app and view analytics for your channel.
          </p>
          <Button onClick={handleConnectYouTube} className="bg-red-600 hover:bg-red-700">
            <Youtube className="mr-2 h-5 w-5" />
            Connect YouTube Account
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full h-full bg-cover bg-center flex flex-col overflow-y-auto" style={{ backgroundImage: "url('/white_bg.png')" }}>
      {/* Header */}
      <div className="w-full mt-10 flex justify-start items-center p-3">
        <button
          className="h-10 w-10 bg-gray-500 rounded-md flex justify-center items-center text-white"
          onClick={() => setCurrentPage("list-products")}
        >
          <House />
        </button>
        <div className="text-md font-bold ml-3">YouTube Shorts Manager</div>
      </div>

      {/* Channel Info */}
      {channelInfo && (
        <div className="mx-4 p-4 bg-white rounded-lg border flex items-center gap-3">
          <img src={channelInfo.thumbnail} alt="Channel" className="h-12 w-12 rounded-full" />
          <div className="flex-1">
            <div className="font-semibold">{channelInfo.title}</div>
            <div className="text-xs text-gray-500">
              {parseInt(channelInfo.subscribers).toLocaleString()} subscribers • {parseInt(channelInfo.videos).toLocaleString()} videos
            </div>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="flex border-b mx-4 mt-4">
        <button
          className={`px-4 py-2 font-medium ${activeTab === 'upload' ? 'border-b-2 border-red-600 text-red-600' : 'text-gray-600'}`}
          onClick={() => setActiveTab('upload')}
        >
          <Upload className="inline mr-1 h-4 w-4" /> Upload
        </button>
        <button
          className={`px-4 py-2 font-medium ${activeTab === 'videos' ? 'border-b-2 border-red-600 text-red-600' : 'text-gray-600'}`}
          onClick={() => setActiveTab('videos')}
        >
          <Youtube className="inline mr-1 h-4 w-4" /> Videos
        </button>
        <button
          className={`px-4 py-2 font-medium ${activeTab === 'analytics' ? 'border-b-2 border-red-600 text-red-600' : 'text-gray-600'}`}
          onClick={() => setActiveTab('analytics')}
        >
          <BarChart3 className="inline mr-1 h-4 w-4" /> Analytics
        </button>
      </div>

      {/* Tab Content */}
      <div className="flex-1 overflow-y-auto">
        {activeTab === 'upload' && <UploadTab />}
        {activeTab === 'videos' && <VideosTab />}
        {activeTab === 'analytics' && <AnalyticsTab />}
      </div>
    </div>
  );
};

// Upload Tab Component
const UploadTab = () => {
  const [uploadSource, setUploadSource] = useState<'local' | 'media' | null>(null);
  const [userVideos, setUserVideos] = useState<any[]>([]);
  const [loadingMedia, setLoadingMedia] = useState(false);
  const [selectedVideo, setSelectedVideo] = useState<any>(null);
  const [localFile, setLocalFile] = useState<File | null>(null);
  const [localFileUrl, setLocalFileUrl] = useState<string | null>(null);
  const [uploadingFile, setUploadingFile] = useState(false);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [tags, setTags] = useState('');
  const [privacy, setPrivacy] = useState('unlisted');
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<any>(null);

  const loadUserVideos = async () => {
    try {
      setLoadingMedia(true);
      const result = await mediaAPI.listMediaByType('videos');
      if (result.success) {
        setUserVideos(result.media);
      }
    } catch (error) {
      console.error('Failed to load videos:', error);
    } finally {
      setLoadingMedia(false);
    }
  };

  const handleSourceSelect = (source: 'local' | 'media') => {
    setUploadSource(source);
    if (source === 'media') {
      loadUserVideos();
    }
  };

  const handleLocalFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setLocalFile(file);
      setLocalFileUrl(URL.createObjectURL(file));
    }
  };

  const handleUploadLocalFile = async () => {
    if (!localFile) return;

    try {
      setUploadingFile(true);
      const uploadResult = await mediaAPI.uploadMedia({
        file: localFile,
        media_type: 'video',
        title: localFile.name
      });

      if (uploadResult.success) {
        // Set as selected video
        setSelectedVideo({
          id: uploadResult.media_id,
          public_url: uploadResult.public_url,
          title: localFile.name
        });
        alert('✅ Video uploaded to media library!');
      }
    } catch (error) {
      console.error('Failed to upload file:', error);
      alert('Failed to upload video. Please try again.');
    } finally {
      setUploadingFile(false);
    }
  };

  const handleUploadToYouTube = async () => {
    if (!selectedVideo || !title) {
      alert('Please select a video and provide a title');
      return;
    }

    try {
      setUploading(true);
      const result = await youtubeAPI.upload({
        video_url: selectedVideo.public_url,
        title,
        description,
        tags: tags.split(',').map((t: string) => t.trim()).filter((t: string) => t),
        privacy,
        is_short: true
      });

      if (result.success) {
        setUploadResult(result);
        setSelectedVideo(null);
        setLocalFile(null);
        setLocalFileUrl(null);
        setTitle('');
        setDescription('');
        setTags('');
      } else {
        alert(`Upload failed: ${result.error}`);
      }
    } catch (error) {
      console.error('Upload error:', error);
      alert('Upload failed. Please try again.');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="p-4 space-y-4">
      {uploadResult && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="font-semibold text-green-800 mb-2">✅ Video Uploaded Successfully!</div>
          <div className="space-y-2 text-sm">
            <a href={uploadResult.url} target="_blank" rel="noopener noreferrer" className="flex items-center text-blue-600 hover:underline">
              <ExternalLink className="h-4 w-4 mr-1" /> Watch on YouTube
            </a>
            <a href={uploadResult.studio_url} target="_blank" rel="noopener noreferrer" className="flex items-center text-blue-600 hover:underline">
              <ExternalLink className="h-4 w-4 mr-1" /> Edit in Studio
            </a>
          </div>
          <Button variant="outline" size="sm" className="mt-3" onClick={() => {
            setUploadResult(null);
            setUploadSource(null);
            setSelectedVideo(null);
            setLocalFile(null);
            setLocalFileUrl(null);
          }}>
            Upload Another
          </Button>
        </div>
      )}

      {/* Source Selection */}
      {!uploadSource && !uploadResult && (
        <div>
          <Label className="mb-3">Choose Video Source</Label>
          <div className="flex gap-3">
            <Button
              variant="outline"
              className="flex-1 h-24 flex flex-col items-center justify-center gap-2 hover:bg-blue-50"
              onClick={() => handleSourceSelect('local')}
            >
              <Upload className="h-8 w-8" />
              <span className="font-medium">Upload from Device</span>
              <span className="text-xs text-gray-500">Select a local video file</span>
            </Button>
            <Button
              variant="outline"
              className="flex-1 h-24 flex flex-col items-center justify-center gap-2 hover:bg-blue-50"
              onClick={() => handleSourceSelect('media')}
            >
              <Play className="h-8 w-8" />
              <span className="font-medium">From Media Library</span>
              <span className="text-xs text-gray-500">Use uploaded videos</span>
            </Button>
          </div>
        </div>
      )}

      {/* Local File Upload */}
      {uploadSource === 'local' && !selectedVideo && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <Label>Upload Video from Device</Label>
            <Button variant="ghost" size="sm" onClick={() => setUploadSource(null)}>
              Change Source
            </Button>
          </div>
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-6">
            <input
              type="file"
              accept="video/*"
              onChange={handleLocalFileChange}
              className="hidden"
              id="video-file-input"
            />
            <label
              htmlFor="video-file-input"
              className="flex flex-col items-center justify-center cursor-pointer"
            >
              {localFile ? (
                <div className="text-center space-y-2">
                  {localFileUrl && (
                    <video
                      src={localFileUrl}
                      className="max-h-32 rounded-lg mx-auto"
                      controls
                    />
                  )}
                  <p className="text-sm font-medium">{localFile.name}</p>
                  <p className="text-xs text-gray-500">{(localFile.size / 1024 / 1024).toFixed(2)} MB</p>
                  <Button
                    onClick={(e) => {
                      e.preventDefault();
                      handleUploadLocalFile();
                    }}
                    disabled={uploadingFile}
                    className="mt-2"
                  >
                    {uploadingFile ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Uploading to Library...
                      </>
                    ) : (
                      'Upload to Media Library'
                    )}
                  </Button>
                </div>
              ) : (
                <div className="text-center">
                  <Upload className="h-12 w-12 text-gray-400 mx-auto mb-3" />
                  <p className="text-sm font-medium">Click to select video</p>
                  <p className="text-xs text-gray-500 mt-1">MP4, MOV, AVI, etc.</p>
                </div>
              )}
            </label>
          </div>
        </div>
      )}

      {/* Media Library Selection */}
      {uploadSource === 'media' && !selectedVideo && (
        <div>
          <div className="flex items-center justify-between mb-2">
            <Label>Select a Video from Your Media</Label>
            <Button variant="ghost" size="sm" onClick={() => setUploadSource(null)}>
              Change Source
            </Button>
          </div>
          {loadingMedia ? (
            <div className="flex justify-center items-center py-8">
              <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
            </div>
          ) : userVideos.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <p>No videos found in your media library.</p>
              <p className="text-sm mt-2">Upload videos first from the Add Product page.</p>
            </div>
          ) : (
            <div className="grid grid-cols-2 gap-3 max-h-64 overflow-y-auto">
              {userVideos.map((video) => (
                <div
                  key={video.id}
                  onClick={() => setSelectedVideo(video)}
                  className={`relative border-2 rounded-lg overflow-hidden cursor-pointer transition-all ${
                    selectedVideo?.id === video.id
                      ? 'border-blue-500 ring-2 ring-blue-200'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <video
                    src={video.public_url}
                    className="w-full h-32 object-cover"
                    muted
                  />
                  <div className="absolute inset-0 bg-black bg-opacity-20 flex items-center justify-center">
                    <Play className="h-8 w-8 text-white" />
                  </div>
                  {selectedVideo?.id === video.id && (
                    <div className="absolute top-2 right-2 bg-blue-500 rounded-full p-1">
                      <Check className="h-4 w-4 text-white" />
                    </div>
                  )}
                  {video.title && (
                    <div className="absolute bottom-0 left-0 right-0 bg-black bg-opacity-70 text-white text-xs p-1 truncate">
                      {video.title}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* YouTube Upload Form */}
      {selectedVideo && (
        <>
          <div>
            <Label>Title *</Label>
            <Input
              placeholder="My Amazing YouTube Short"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
          </div>

          <div>
            <Label>Description</Label>
            <Textarea
              placeholder="Describe your video..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
            />
          </div>

          <div>
            <Label>Tags (comma-separated)</Label>
            <Input
              placeholder="shorts, viral, trending"
              value={tags}
              onChange={(e) => setTags(e.target.value)}
            />
          </div>

          <div>
            <Label>Privacy</Label>
            <Select value={privacy} onValueChange={setPrivacy}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="public">Public - Anyone can see</SelectItem>
                <SelectItem value="unlisted">Unlisted - Only people with link</SelectItem>
                <SelectItem value="private">Private - Only you</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <Button
            onClick={handleUploadToYouTube}
            disabled={uploading || !selectedVideo || !title}
            className="w-full bg-red-600 hover:bg-red-700"
          >
            {uploading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Uploading to YouTube...
              </>
            ) : (
              <>
                <Youtube className="mr-2 h-4 w-4" />
                Upload as YouTube Short
              </>
            )}
          </Button>
        </>
      )}
    </div>
  );
};

// Videos Tab Component
const VideosTab = () => {
  const [videos, setVideos] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadVideos();
  }, []);

  const loadVideos = async () => {
    try {
      setLoading(true);
      const result = await youtubeAPI.getVideos();
      if (result.success) {
        setVideos(result.videos);
      }
    } catch (error) {
      console.error('Failed to load videos:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader2 className="animate-spin h-8 w-8 text-red-600" />
      </div>
    );
  }

  if (videos.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center p-8 text-gray-500">
        <Youtube className="h-16 w-16 mb-4 opacity-50" />
        <p>No videos uploaded yet</p>
      </div>
    );
  }

  return (
    <div className="p-4 space-y-3">
      {videos.map((video) => (
        <div key={video.id} className="bg-white border rounded-lg overflow-hidden">
          <div className="flex gap-3 p-3">
            <img src={video.thumbnail} alt={video.title} className="w-32 h-20 object-cover rounded" />
            <div className="flex-1 min-w-0">
              <div className="font-medium text-sm line-clamp-2">{video.title}</div>
              <div className="text-xs text-gray-500 mt-1">
                {new Date(video.published_at).toLocaleDateString()}
              </div>
              <div className="flex gap-4 mt-2 text-xs text-gray-600">
                <span className="flex items-center">
                  <Eye className="h-3 w-3 mr-1" /> {video.views.toLocaleString()}
                </span>
                <span className="flex items-center">
                  <ThumbsUp className="h-3 w-3 mr-1" /> {video.likes.toLocaleString()}
                </span>
                <span className="flex items-center">
                  <MessageSquare className="h-3 w-3 mr-1" /> {video.comments.toLocaleString()}
                </span>
              </div>
            </div>
          </div>
          <div className="border-t px-3 py-2">
            <a
              href={video.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs text-blue-600 hover:underline flex items-center"
            >
              <ExternalLink className="h-3 w-3 mr-1" /> Watch on YouTube
            </a>
          </div>
        </div>
      ))}
    </div>
  );
};

// Analytics Tab Component
const AnalyticsTab = () => {
  const [analytics, setAnalytics] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState('30');

  useEffect(() => {
    loadAnalytics();
  }, [period]);

  const loadAnalytics = async () => {
    try {
      setLoading(true);
      const result = await youtubeAPI.getAnalytics(parseInt(period));
      if (result.success) {
        setAnalytics(result);
      }
    } catch (error) {
      console.error('Failed to load analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader2 className="animate-spin h-8 w-8 text-red-600" />
      </div>
    );
  }

  if (!analytics) {
    return (
      <div className="flex flex-col items-center justify-center p-8 text-gray-500">
        <BarChart3 className="h-16 w-16 mb-4 opacity-50" />
        <p>No analytics data available</p>
      </div>
    );
  }

  const summary = analytics.summary;

  return (
    <div className="p-4 space-y-4">
      {/* Period Selector */}
      <Select value={period} onValueChange={setPeriod}>
        <SelectTrigger>
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="7">Last 7 days</SelectItem>
          <SelectItem value="30">Last 30 days</SelectItem>
          <SelectItem value="90">Last 90 days</SelectItem>
        </SelectContent>
      </Select>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 gap-3">
        <div className="bg-white border rounded-lg p-4">
          <div className="text-xs text-gray-500 mb-1">Views</div>
          <div className="text-2xl font-bold">{summary.views.toLocaleString()}</div>
        </div>
        <div className="bg-white border rounded-lg p-4">
          <div className="text-xs text-gray-500 mb-1">Watch Time</div>
          <div className="text-2xl font-bold">{summary.watch_time_hours}h</div>
        </div>
        <div className="bg-white border rounded-lg p-4">
          <div className="text-xs text-gray-500 mb-1">Likes</div>
          <div className="text-2xl font-bold">{summary.likes.toLocaleString()}</div>
        </div>
        <div className="bg-white border rounded-lg p-4">
          <div className="text-xs text-gray-500 mb-1">Comments</div>
          <div className="text-2xl font-bold">{summary.comments.toLocaleString()}</div>
        </div>
      </div>

      {/* Subscribers */}
      <div className="bg-white border rounded-lg p-4">
        <div className="text-sm font-medium mb-3">Subscribers</div>
        <div className="grid grid-cols-3 gap-4 text-center">
          <div>
            <div className="text-green-600 font-bold text-lg">+{summary.subscribers_gained}</div>
            <div className="text-xs text-gray-500">Gained</div>
          </div>
          <div>
            <div className="text-red-600 font-bold text-lg">-{summary.subscribers_lost}</div>
            <div className="text-xs text-gray-500">Lost</div>
          </div>
          <div>
            <div className={`font-bold text-lg ${summary.net_subscribers >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {summary.net_subscribers >= 0 ? '+' : ''}{summary.net_subscribers}
            </div>
            <div className="text-xs text-gray-500">Net</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default YouTubeShorts;
