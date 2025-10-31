import { usePage } from "@/contexts/PageContext";
import { House, LucideImagePlus, LucideVideo, Upload, Loader2, CheckCircle, XCircle, Trash2 } from "lucide-react";
import { useState, useRef, useEffect } from "react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { mediaAPI, type MediaItem } from "@/lib/api";

const UploadMedia = () => {
  const { setCurrentPage } = usePage();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [mediaType, setMediaType] = useState<"image" | "video">("image");
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<"idle" | "success" | "error">("idle");
  const [uploadMessage, setUploadMessage] = useState("");
  const [uploadedMedia, setUploadedMedia] = useState<MediaItem[]>([]);
  const [uploadedImages, setUploadedImages] = useState<MediaItem[]>([]);
  const [uploadedVideos, setUploadedVideos] = useState<MediaItem[]>([]);
  const [activeTab, setActiveTab] = useState<'all' | 'images' | 'videos'>('all');
  const [deletingMedia, setDeletingMedia] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setUploadStatus("idle");
      setUploadMessage("");
      
      // Auto-detect media type based on file type
      if (file.type.startsWith('image/')) {
        setMediaType("image");
      } else if (file.type.startsWith('video/')) {
        setMediaType("video");
      }
    }
  };

  const handleUpload = async () => {
    console.log("🔧 Frontend: Starting upload process...");
    
    if (!selectedFile) {
      console.log("🔧 Frontend: No file selected");
      setUploadStatus("error");
      setUploadMessage("Please select a file first");
      return;
    }

    if (!title.trim()) {
      console.log("🔧 Frontend: No title provided");
      setUploadStatus("error");
      setUploadMessage("Please enter a title for your media");
      return;
    }

    console.log("🔧 Frontend: Upload validation passed");
    console.log("🔧 Frontend: File:", selectedFile.name, "Type:", selectedFile.type, "Size:", selectedFile.size);
    console.log("🔧 Frontend: Media type:", mediaType);
    console.log("🔧 Frontend: Title:", title.trim());
    console.log("🔧 Frontend: Description:", description.trim());

    setUploading(true);
    setUploadStatus("idle");
    setUploadMessage("");

    try {
      console.log("🔧 Frontend: Calling mediaAPI.uploadMedia...");
      const response = await mediaAPI.uploadMedia({
        file: selectedFile,
        media_type: mediaType,
        title: title.trim(),
        description: description.trim()
      });

      console.log("🔧 Frontend: Upload response received:", response);

      if (response.success) {
        console.log("🔧 Frontend: Upload successful!");
        setUploadStatus("success");
        setUploadMessage("Media uploaded successfully!");
        
        // Reset form
        setSelectedFile(null);
        setTitle("");
        setDescription("");
        if (fileInputRef.current) {
          fileInputRef.current.value = "";
        }
        
        console.log("🔧 Frontend: Refreshing media list...");
        // Refresh media list
        loadMediaList();
      } else {
        console.error("🔧 Frontend: Upload failed:", response.error);
        setUploadStatus("error");
        setUploadMessage(response.error || "Upload failed");
      }
    } catch (error) {
      console.error("🔧 Frontend: Upload error:", error);
      console.error("🔧 Frontend: Error type:", typeof error);
      console.error("🔧 Frontend: Error message:", error instanceof Error ? error.message : String(error));
      setUploadStatus("error");
      setUploadMessage(error instanceof Error ? error.message : "Upload failed");
    } finally {
      setUploading(false);
      console.log("🔧 Frontend: Upload process completed");
    }
  };

  const handleDeleteMedia = async (mediaId: string, mediaTitle: string) => {
    console.log("🔧 Frontend: Starting delete process for media:", mediaId);
    
    if (!confirm(`Are you sure you want to delete "${mediaTitle}"? This action cannot be undone.`)) {
      console.log("🔧 Frontend: Delete cancelled by user");
      return;
    }
    
    setDeletingMedia(mediaId);
    
    try {
      console.log("🔧 Frontend: Calling mediaAPI.deleteMedia...");
      const response = await mediaAPI.deleteMedia(mediaId);
      console.log("🔧 Frontend: Delete response received:", response);
      
      if (response.success) {
        console.log("🔧 Frontend: Delete successful!");
        setUploadStatus("success");
        setUploadMessage(`"${mediaTitle}" deleted successfully!`);
        
        // Refresh media list
        console.log("🔧 Frontend: Refreshing media list after delete...");
        loadMediaList();
      } else {
        console.error("🔧 Frontend: Delete failed:", response.error);
        setUploadStatus("error");
        setUploadMessage(response.error || "Delete failed");
      }
    } catch (error) {
      console.error("🔧 Frontend: Delete error:", error);
      console.error("🔧 Frontend: Error type:", typeof error);
      console.error("🔧 Frontend: Error message:", error instanceof Error ? error.message : String(error));
      setUploadStatus("error");
      setUploadMessage(error instanceof Error ? error.message : "Delete failed");
    } finally {
      setDeletingMedia(null);
      console.log("🔧 Frontend: Delete process completed");
    }
  };

  const loadMediaList = async () => {
    try {
      console.log("🔧 Frontend: Starting to load media list...");
      const response = await mediaAPI.listMedia();
      console.log("🔧 Frontend: Received response:", response);
      
      if (response.success) {
        console.log("🔧 Frontend: Response successful, setting media data");
        console.log("🔧 Frontend: All media count:", response.media?.length || 0);
        console.log("🔧 Frontend: Images count:", response.images?.length || 0);
        console.log("🔧 Frontend: Videos count:", response.videos?.length || 0);
        
        setUploadedMedia(response.media || []);
        setUploadedImages(response.images || []);
        setUploadedVideos(response.videos || []);
        
        console.log("🔧 Frontend: Media data set successfully");
      } else {
        console.error("🔧 Frontend: Response not successful:", response.error);
      }
    } catch (error) {
      console.error("🔧 Frontend: Failed to load media list:", error);
      console.error("🔧 Frontend: Error type:", typeof error);
      console.error("🔧 Frontend: Error message:", error instanceof Error ? error.message : String(error));
    }
  };

  // Load media list on component mount
  useEffect(() => {
    loadMediaList();
  }, []);

  return (
    <div
      className="w-full h-full bg-cover bg-center flex flex-col overflow-y-auto overflow-x-hidden"
      style={{ backgroundImage: "url('/white_bg.png')" }}
    >
      {/* Header */}
      <div className="w-full mt-10 flex justify-start items-center p-3">
        <button
          className="h-10 w-10 bg-gray-500 rounded-md flex justify-center items-center text-white"
          onClick={() => setCurrentPage("home")}
        >
          <House />
        </button>
        <div className="text-md font-bold ml-3 flex justify-between items-center">
          <div>Upload Media</div>
          <Button className="text-xs p-1 ml-7" onClick={()=> setCurrentPage('add-product/ai-cameraman')}>AI Camera Man</Button>
        </div>
      </div>

      <div className="px-4 py-4 space-y-4">
        {/* Upload Form */}
        <Card className="p-4">
          <CardHeader>
            <CardTitle className="text-lg">Upload New Media</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Title Input */}
            <div>
              <Label htmlFor="title">Media Title *</Label>
              <Input
                id="title"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Enter a title for your media"
                className="mt-1"
              />
            </div>

            {/* Description Input */}
            <div>
              <Label htmlFor="description">Description (Optional)</Label>
              <Textarea
                id="description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Describe your media..."
                className="mt-1"
                rows={3}
              />
      </div>

            {/* File Upload */}
            <div>
              <Label htmlFor="file">Select File *</Label>
              <div className="mt-2">
                <input
                  ref={fileInputRef}
                  type="file"
                  id="file"
                  accept="image/*,video/*"
                  onChange={handleFileSelect}
                  className="hidden"
                />
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => fileInputRef.current?.click()}
                  className="w-full"
                >
                  <Upload className="w-4 h-4 mr-2" />
                  {selectedFile ? selectedFile.name : "Choose File"}
                </Button>
                {selectedFile && (
                  <div className="mt-2 text-sm text-gray-600">
                    Selected: {selectedFile.name} ({(selectedFile.size / 1024 / 1024).toFixed(2)} MB)
                  </div>
                )}
              </div>
      </div>

            {/* Media Type Selection */}
            <div>
              <Label>Media Type</Label>
              <div className="flex gap-2 mt-2">
                <Button
                  type="button"
                  variant={mediaType === "image" ? "default" : "outline"}
                  onClick={() => setMediaType("image")}
                  className="flex-1"
                >
                  <LucideImagePlus className="w-4 h-4 mr-2" />
                  Image
        </Button>
                <Button
                  type="button"
                  variant={mediaType === "video" ? "default" : "outline"}
                  onClick={() => setMediaType("video")}
                  className="flex-1"
                >
                  <LucideVideo className="w-4 h-4 mr-2" />
                  Video
        </Button>
        </div>
            </div>

            {/* Upload Button */}
            <Button
              onClick={handleUpload}
              disabled={uploading || !selectedFile || !title.trim()}
              className="w-full"
            >
              {uploading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Uploading...
                </>
              ) : (
                <>
                  <Upload className="w-4 h-4 mr-2" />
                  Upload Media
                </>
              )}
            </Button>

            {/* Status Message */}
            {uploadMessage && (
              <div className={`p-3 rounded-md flex items-center ${
                uploadStatus === "success" 
                  ? "bg-green-50 text-green-800 border border-green-200" 
                  : uploadStatus === "error"
                  ? "bg-red-50 text-red-800 border border-red-200"
                  : "bg-blue-50 text-blue-800 border border-blue-200"
              }`}>
                {uploadStatus === "success" ? (
                  <CheckCircle className="w-4 h-4 mr-2" />
                ) : uploadStatus === "error" ? (
                  <XCircle className="w-4 h-4 mr-2" />
                ) : null}
                {uploadMessage}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Uploaded Media List */}
        {uploadedMedia.length > 0 && (
          <Card className="p-4">
            <CardHeader>
              <CardTitle className="text-lg">Your Uploaded Media</CardTitle>
              <div className="flex gap-2 mt-2">
                <Button
                  variant={activeTab === 'all' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setActiveTab('all')}
                >
                  All ({uploadedMedia.length})
                </Button>
                <Button
                  variant={activeTab === 'images' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setActiveTab('images')}
                >
                  <LucideImagePlus className="w-4 h-4 mr-1" />
                  Images ({uploadedImages.length})
                </Button>
                <Button
                  variant={activeTab === 'videos' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setActiveTab('videos')}
                >
                  <LucideVideo className="w-4 h-4 mr-1" />
                  Videos ({uploadedVideos.length})
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {activeTab === 'all' && (
                <div className="space-y-4">
                  {/* Images Section */}
                  {uploadedImages.length > 0 && (
                    <div>
                      <h3 className="text-md font-semibold mb-3 flex items-center">
                        <LucideImagePlus className="w-4 h-4 mr-2" />
                        Images ({uploadedImages.length})
                      </h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {uploadedImages.map((media) => (
                          <div key={media.id} className="border rounded-lg p-3">
                            <div className="flex items-start justify-between mb-2">
                              <div className="flex-1">
                                <h4 className="font-medium">{media.title || media.original_filename}</h4>
                                <p className="text-sm text-gray-500">Image</p>
                              </div>
                              <div className="flex items-center gap-2">
                                <span className="text-xs text-gray-400">
                                  {new Date(media.uploaded_at).toLocaleDateString()}
                                </span>
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => handleDeleteMedia(media.id, media.title || media.original_filename)}
                                  disabled={deletingMedia === media.id}
                                  className="text-red-600 hover:text-red-700 hover:bg-red-50 border-red-200"
                                >
                                  {deletingMedia === media.id ? (
                                    <Loader2 className="w-3 h-3 animate-spin" />
                                  ) : (
                                    <Trash2 className="w-3 h-3" />
                                  )}
                                </Button>
                              </div>
                            </div>
                            
                            <img
                              src={media.public_url}
                              alt={media.title || media.original_filename}
                              className="w-full h-32 object-cover rounded"
                            />
                            
                            {media.description && (
                              <p className="text-sm text-gray-600 mt-2">{media.description}</p>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Videos Section */}
                  {uploadedVideos.length > 0 && (
                    <div>
                      <h3 className="text-md font-semibold mb-3 flex items-center">
                        <LucideVideo className="w-4 h-4 mr-2" />
                        Videos ({uploadedVideos.length})
                      </h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {uploadedVideos.map((media) => (
                          <div key={media.id} className="border rounded-lg p-3">
                            <div className="flex items-start justify-between mb-2">
                              <div className="flex-1">
                                <h4 className="font-medium">{media.title || media.original_filename}</h4>
                                <p className="text-sm text-gray-500">Video</p>
                              </div>
                              <div className="flex items-center gap-2">
                                <span className="text-xs text-gray-400">
                                  {new Date(media.uploaded_at).toLocaleDateString()}
                                </span>
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => handleDeleteMedia(media.id, media.title || media.original_filename)}
                                  disabled={deletingMedia === media.id}
                                  className="text-red-600 hover:text-red-700 hover:bg-red-50 border-red-200"
                                >
                                  {deletingMedia === media.id ? (
                                    <Loader2 className="w-3 h-3 animate-spin" />
                                  ) : (
                                    <Trash2 className="w-3 h-3" />
                                  )}
                                </Button>
                              </div>
                            </div>
                            
                            <video
                              src={media.public_url}
                              className="w-full h-32 object-cover rounded"
                              controls
                            />
                            
                            {media.description && (
                              <p className="text-sm text-gray-600 mt-2">{media.description}</p>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {activeTab === 'images' && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {uploadedImages.map((media) => (
                    <div key={media.id} className="border rounded-lg p-3">
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex-1">
                          <h4 className="font-medium">{media.title || media.original_filename}</h4>
                          <p className="text-sm text-gray-500">Image</p>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-xs text-gray-400">
                            {new Date(media.uploaded_at).toLocaleDateString()}
                          </span>
              <Button
                            size="sm"
                variant="outline"
                            onClick={() => handleDeleteMedia(media.id, media.title || media.original_filename)}
                            disabled={deletingMedia === media.id}
                            className="text-red-600 hover:text-red-700 hover:bg-red-50 border-red-200"
                          >
                            {deletingMedia === media.id ? (
                              <Loader2 className="w-3 h-3 animate-spin" />
                            ) : (
                              <Trash2 className="w-3 h-3" />
                            )}
              </Button>
                        </div>
                      </div>
                      
                      <img
                        src={media.public_url}
                        alt={media.title || media.original_filename}
                        className="w-full h-32 object-cover rounded"
                      />
                      
                      {media.description && (
                        <p className="text-sm text-gray-600 mt-2">{media.description}</p>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {activeTab === 'videos' && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {uploadedVideos.map((media) => (
                    <div key={media.id} className="border rounded-lg p-3">
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex-1">
                          <h4 className="font-medium">{media.title || media.original_filename}</h4>
                          <p className="text-sm text-gray-500">Video</p>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-xs text-gray-400">
                            {new Date(media.uploaded_at).toLocaleDateString()}
                          </span>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleDeleteMedia(media.id, media.title || media.original_filename)}
                            disabled={deletingMedia === media.id}
                            className="text-red-600 hover:text-red-700 hover:bg-red-50 border-red-200"
                          >
                            {deletingMedia === media.id ? (
                              <Loader2 className="w-3 h-3 animate-spin" />
                            ) : (
                              <Trash2 className="w-3 h-3" />
                            )}
                          </Button>
                        </div>
                      </div>
                      
                      <video
                        src={media.public_url}
                        className="w-full h-32 object-cover rounded"
                        controls
                      />
                      
                      {media.description && (
                        <p className="text-sm text-gray-600 mt-2">{media.description}</p>
                      )}
                    </div>
                ))}
              </div>
              )}

              {uploadedMedia.length === 0 && (
                <div className="text-center py-8 text-gray-500">
                  <Upload className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p>No media uploaded yet</p>
                </div>
              )}
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};

export default UploadMedia;
