/**
 * API Helper for Project Kaarigar Backend
 * Handles all communication with the backend authentication system
 */

const API_BASE_URL = 'http://localhost:5000/api/auth';

export interface User {
  userId: string;
  email: string;
  name: string;
}

export interface Profile {
  userId: string;
  name: string;
  email: string;
  occupation: string;
  languages: string[];
  bio: string;
  username: string;
  brandId: string;
  profileImage: string;
  brandLogo?: string;
  brandName?: string;
  logoPrompt?: string;
  logoGeneratedAt?: string;
  createdAt: string;
  lastLogin: string;
  isActive: boolean;
  preferences: {
    language: string;
    notifications: boolean;
    theme: string;
  };
  stats: {
    videosCreated: number;
    productsListed: number;
    totalViews: number;
  };
}

export interface AuthResponse {
  success: boolean;
  message: string;
  user?: User;
  profile?: Profile;
  error?: string;
}

export interface SessionResponse {
  success: boolean;
  authenticated: boolean;
  user?: User;
}

class AuthAPI {
  private baseURL: string;

  constructor() {
    this.baseURL = API_BASE_URL;
  }

  /**
   * Make HTTP request to backend
   */
  private async request<T>(
    endpoint: string,
    method: string = 'GET',
    data?: any
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    
    const options: RequestInit = {
      method,
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include', // Important for session cookies
    };

    if (data) {
      options.body = JSON.stringify(data);
    }

    try {
      const response = await fetch(url, options);
      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.error || `HTTP ${response.status}: ${response.statusText}`);
      }

      return result;
    } catch (error) {
      console.error('API Error:', error);
      throw error;
    }
  }

  /**
   * User signup
   */
  async signup(email: string, password: string, name: string): Promise<AuthResponse> {
    return this.request<AuthResponse>('/signup', 'POST', {
      email,
      password,
      name
    });
  }

  /**
   * User login
   */
  async login(email: string, password: string): Promise<AuthResponse> {
    return this.request<AuthResponse>('/login', 'POST', {
      email,
      password
    });
  }

  /**
   * User logout
   */
  async logout(): Promise<AuthResponse> {
    return this.request<AuthResponse>('/logout', 'POST');
  }

  /**
   * Check session status
   */
  async checkSession(): Promise<SessionResponse> {
    return this.request<SessionResponse>('/session');
  }

  /**
   * Get user profile
   */
  async getProfile(): Promise<{ success: boolean; profile: Profile }> {
    return this.request<{ success: boolean; profile: Profile }>('/profile');
  }

  /**
   * Health check
   */
  async healthCheck(): Promise<{ status: string; service: string; firestore_available: boolean }> {
    return this.request<{ status: string; service: string; firestore_available: boolean }>('/health');
  }
}

// Create and export API instance
export const authAPI = new AuthAPI();

// Logo Generation API
export interface LogoGenerationRequest {
  conversation_data: string;
  brand_name?: string;
  language?: string;
}

export interface LogoGenerationResponse {
  success: boolean;
  message: string;
  logo_url?: string;
  brand_name?: string;
  logo_prompt?: string;
  logo_spec?: {
    brand_name: string;
    final_prompt: string;
    descriptors: string[];
    style_adjectives: string[];
    color_palette: string[];
  };
  error?: string;
}

export interface LogoInfo {
  logo_url?: string;
  brand_name?: string;
  logo_prompt?: string;
  logo_generated_at?: string;
  has_logo: boolean;
}

export interface GetLogoResponse {
  success: boolean;
  logo_info: LogoInfo;
  error?: string;
}

class LogoAPI {
  private baseURL: string;

  constructor() {
    this.baseURL = 'http://localhost:5000/api/logo';
  }

  private async request<T>(
    endpoint: string,
    method: string = 'GET',
    data?: any
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;

    const options: RequestInit = {
      method,
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include', // Important for session cookies
    };

    if (data) {
      options.body = JSON.stringify(data);
    }

    try {
      const response = await fetch(url, options);
      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.error || `HTTP ${response.status}: ${response.statusText}`);
      }

      return result;
    } catch (error) {
      console.error('Logo API Error:', error);
      throw error;
    }
  }

  async generateLogo(data: LogoGenerationRequest): Promise<LogoGenerationResponse> {
    return this.request<LogoGenerationResponse>('/generate', 'POST', data);
  }

  async getLogo(): Promise<GetLogoResponse> {
    return this.request<GetLogoResponse>('/get-logo', 'GET');
  }

  async healthCheck(): Promise<{ status: string; service: string; firestore_available: boolean; storage_available: boolean; gemini_available: boolean }> {
    return this.request('/health', 'GET');
  }

  async saveLogoUrl(logoUrl: string, brandName: string): Promise<{ success: boolean; message: string; logo_url?: string; brand_name?: string; error?: string }> {
    return this.request('/save-logo-url', 'POST', {
      logo_url: logoUrl,
      brand_name: brandName
    });
  }
}

export const logoAPI = new LogoAPI();

// Media Upload API
export interface MediaUploadRequest {
  file: File;
  media_type: 'image' | 'video';
  title?: string;
  description?: string;
}

export interface MediaUploadResponse {
  success: boolean;
  message: string;
  media_id?: string;
  public_url?: string;
  blob_path?: string;
  error?: string;
}

export interface MediaItem {
  id: string;
  user_id: string;
  kaarigar_id: string;
  media_type: 'image' | 'video';
  filename: string;
  original_filename: string;
  blob_path: string;
  public_url: string;
  file_size: number;
  content_type: string;
  title?: string;
  description?: string;
  uploaded_at: string;
  is_active: boolean;
}

export interface MediaListResponse {
  success: boolean;
  media: MediaItem[];
  images: MediaItem[];
  videos: MediaItem[];
  count: number;
  images_count: number;
  videos_count: number;
  error?: string;
}

export interface MediaByTypeResponse {
  success: boolean;
  media_type: 'images' | 'videos';
  media: MediaItem[];
  count: number;
  error?: string;
}

class MediaAPI {
  private baseURL: string;

  constructor() {
    this.baseURL = 'http://localhost:5000/api/media';
  }

  private async request<T>(
    endpoint: string,
    method: string = 'GET',
    data?: any
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;

    const options: RequestInit = {
      method,
      headers: {},
      credentials: 'include', // Important for session cookies
    };

    if (data) {
      if (data instanceof FormData) {
        // Don't set Content-Type for FormData, let browser set it
        options.body = data;
      } else {
        options.headers = {
          'Content-Type': 'application/json',
        };
        options.body = JSON.stringify(data);
      }
    }

    try {
      const response = await fetch(url, options);
      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.error || `HTTP ${response.status}: ${response.statusText}`);
      }

      return result;
    } catch (error) {
      console.error('Media API Error:', error);
      throw error;
    }
  }

  async uploadMedia(request: MediaUploadRequest): Promise<MediaUploadResponse> {
    const formData = new FormData();
    formData.append('file', request.file);
    formData.append('media_type', request.media_type);
    if (request.title) formData.append('title', request.title);
    if (request.description) formData.append('description', request.description);

    return this.request<MediaUploadResponse>('/upload', 'POST', formData);
  }

  async listMedia(): Promise<MediaListResponse> {
    return this.request<MediaListResponse>('/list', 'GET');
  }

  async listMediaByType(mediaType: 'images' | 'videos'): Promise<MediaByTypeResponse> {
    return this.request<MediaByTypeResponse>(`/list/${mediaType}`, 'GET');
  }

  async deleteMedia(mediaId: string): Promise<{ success: boolean; message: string; deleted_path?: string; error?: string }> {
    return this.request(`/delete/${mediaId}`, 'DELETE');
  }

  async healthCheck(): Promise<{ status: string; service: string; firestore_available: boolean; storage_available: boolean }> {
    return this.request('/health', 'GET');
  }
}

export const mediaAPI = new MediaAPI();

// Profile Management API
export interface ProfileData {
  name: string;
  email: string;
  occupation: string;
  bio: string;
  location: string;
  languages: string[];
  craft_details: string;
  materials_used: string;
  experience_years: string;
  aspirations: string;
  challenges: string;
  instagram?: string;
  facebook?: string;
  twitter?: string;
}

export interface ProfileResponse {
  success: boolean;
  profile_data: ProfileData;
  user_id?: string;
  error?: string;
}

export interface SaveProfileResponse {
  success: boolean;
  message: string;
  profile_id?: string;
  error?: string;
}

class ProfileAPI {
  private baseURL: string;

  constructor() {
    this.baseURL = 'http://localhost:5000/api/profile';
  }

  private async request<T>(
    endpoint: string,
    method: string = 'GET',
    data?: any
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;

    const options: RequestInit = {
      method,
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include', // Important for session cookies
    };

    if (data) {
      options.body = JSON.stringify(data);
    }

    try {
      const response = await fetch(url, options);
      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.error || `HTTP ${response.status}: ${response.statusText}`);
      }

      return result;
    } catch (error) {
      console.error('Profile API Error:', error);
      throw error;
    }
  }

  async getProfileData(): Promise<ProfileResponse> {
    return this.request<ProfileResponse>('/get-profile-data', 'GET');
  }

  async saveProfile(data: ProfileData): Promise<SaveProfileResponse> {
    return this.request<SaveProfileResponse>('/save-profile', 'POST', data);
  }

  async getSavedProfile(): Promise<ProfileResponse> {
    return this.request<ProfileResponse>('/get-saved-profile', 'GET');
  }

  async healthCheck(): Promise<{ status: string; service: string; firestore_available: boolean; storage_available: boolean; gemini_available: boolean }> {
    return this.request('/health', 'GET');
  }

        async debugUserData(): Promise<any> {
            return this.request('/debug-user-data', 'GET');
        }

        async updateBrand(brandName: string, brandLogo?: string): Promise<{ success: boolean; message: string; brand_name?: string; brand_logo?: string; error?: string }> {
            return this.request('/update-brand', 'POST', {
                brand_name: brandName,
                brand_logo: brandLogo
            });
        }

        async updateLogoFromStorage(): Promise<{ success: boolean; message: string; logo_url?: string; profile_id?: string; error?: string }> {
            return this.request('/update-logo-from-storage', 'POST');
        }
    }

    export const profileAPI = new ProfileAPI();

// Reel Generation API
export interface ReelGenerationRequest {
  selected_image_ids: string[];
  prompt: string;
  title: string;
  description?: string;
  duration_seconds?: number;
}

export interface ReelGenerationResponse {
  success: boolean;
  message: string;
  reel_id?: string;
  public_url?: string;
  title?: string;
  file_size?: number;
  error?: string;
}

export interface GeneratedReel {
  id: string;
  user_id: string;
  kaarigar_id: string;
  video_type: string;
  title: string;
  description: string;
  prompt: string;
  optimized_prompt: string;
  selected_image_ids: string[];
  duration_seconds: number;
  filename: string;
  blob_path: string;
  public_url: string;
  file_size: number;
  generated_at: string;
  is_active: boolean;
}

export interface GeneratedReelsResponse {
  success: boolean;
  reels: GeneratedReel[];
  count: number;
  error?: string;
}

class ReelAPI {
  private baseURL: string;

  constructor() {
    this.baseURL = 'http://localhost:5000/api/reel';
  }

  private async request<T>(
    endpoint: string,
    method: string = 'GET',
    data?: any
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;

    const options: RequestInit = {
      method,
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include', // Important for session cookies
    };

    if (data) {
      options.body = JSON.stringify(data);
    }

    try {
      const response = await fetch(url, options);
      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.error || `HTTP ${response.status}: ${response.statusText}`);
      }

      return result;
    } catch (error) {
      console.error('Reel API Error:', error);
      throw error;
    }
  }

  async generateReel(request: ReelGenerationRequest): Promise<ReelGenerationResponse> {
    return this.request<ReelGenerationResponse>('/generate-reel', 'POST', request);
  }

  async getGeneratedReels(): Promise<GeneratedReelsResponse> {
    return this.request<GeneratedReelsResponse>('/get-generated-reels', 'GET');
  }

  async healthCheck(): Promise<{ status: string; service: string; firestore_available: boolean; storage_available: boolean }> {
    return this.request('/health', 'GET');
  }
}

export const reelAPI = new ReelAPI();

// Image Generation API
export interface ImageGenerationRequest {
  prompt: string;
  title: string;
  description?: string;
  aspect_ratio?: string;
  reference_image_id?: string;
}

export interface ImageGenerationResponse {
  success: boolean;
  message: string;
  image_id?: string;
  public_url?: string;
  title?: string;
  image_type?: string;
  file_size?: number;
  error?: string;
}

export interface GeneratedImage {
  id: string;
  user_id: string;
  kaarigar_id: string;
  image_type: string;
  title: string;
  description: string;
  prompt: string;
  reference_image_id: string;
  aspect_ratio: string;
  filename: string;
  blob_path: string;
  public_url: string;
  file_size: number;
  generated_at: string;
  is_active: boolean;
}

export interface GeneratedImagesResponse {
  success: boolean;
  images: GeneratedImage[];
  count: number;
  error?: string;
}

class ImageGenAPI {
  private baseURL: string;

  constructor() {
    this.baseURL = 'http://localhost:5000/api/image-gen';
  }

  private async request<T>(
    endpoint: string,
    method: string = 'GET',
    data?: any
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;

    const options: RequestInit = {
      method,
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include', // Important for session cookies
    };

    if (data) {
      options.body = JSON.stringify(data);
    }

    try {
      const response = await fetch(url, options);
      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.error || `HTTP ${response.status}: ${response.statusText}`);
      }

      return result;
    } catch (error) {
      console.error('Image Gen API Error:', error);
      throw error;
    }
  }

  async generateImage(request: ImageGenerationRequest): Promise<ImageGenerationResponse> {
    return this.request<ImageGenerationResponse>('/generate-image', 'POST', request);
  }

  async getGeneratedImages(): Promise<GeneratedImagesResponse> {
    return this.request<GeneratedImagesResponse>('/get-generated-images', 'GET');
  }

  async healthCheck(): Promise<{ status: string; service: string; firestore_available: boolean; storage_available: boolean }> {
    return this.request('/health', 'GET');
  }
}

export const imageGenAPI = new ImageGenAPI();

// Image Editing API
export interface ImageAnalysisRequest {
  image_url: string;
}

export interface ImageSuggestion {
  prompt: string;
  description: string;
  category: string;
}

export interface ImageAnalysisResponse {
  success: boolean;
  suggestions: ImageSuggestion[];
  raw_analysis?: string;
  error?: string;
}

export interface ImageEditRequest {
  image_url: string;
  prompt: string;
  title: string;
  original_image_id?: string;
}

export interface ImageEditResponse {
  success: boolean;
  message: string;
  image_id?: string;
  public_url?: string;
  title?: string;
  file_size?: number;
  error?: string;
}

class ImageEditAPI {
  private baseURL: string;

  constructor() {
    this.baseURL = 'http://localhost:5000/api/image-edit';
  }

  private async request<T>(
    endpoint: string,
    method: string = 'GET',
    data?: any
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;

    const options: RequestInit = {
      method,
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include', // Important for session cookies
    };

    if (data) {
      options.body = JSON.stringify(data);
    }

    try {
      const response = await fetch(url, options);
      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.error || `HTTP ${response.status}: ${response.statusText}`);
      }

      return result;
    } catch (error) {
      console.error('Image Edit API Error:', error);
      throw error;
    }
  }

  async analyzeImage(request: ImageAnalysisRequest): Promise<ImageAnalysisResponse> {
    return this.request<ImageAnalysisResponse>('/analyze-image', 'POST', request);
  }

  async editImage(request: ImageEditRequest): Promise<ImageEditResponse> {
    return this.request<ImageEditResponse>('/edit-image', 'POST', request);
  }

  async healthCheck(): Promise<{ status: string; service: string; firestore_available: boolean; storage_available: boolean }> {
    return this.request('/health', 'GET');
  }
}

export const imageEditAPI = new ImageEditAPI();

// Video Editing API - matches test script structure
export interface UserVideo {
  id: string;
  title: string;
  public_url: string;
  file_size: number;
  created_at: string;
  type: 'uploaded' | 'generated_reel';
  filename?: string;
  duration?: number;
  segments?: number;
  generation_type?: string;
}

export interface UserVideosResponse {
  success: boolean;
  videos: UserVideo[];
  count: number;
  error?: string;
}

export interface VideoEditRequest {
  video_url: string;
  edit_prompt: string;
  topic?: string;
  save_name?: string;
}

export interface TrendingAudioRequest {
  video_url: string;
  song_id: number;
  topic?: string;
  save_name?: string;
}

export interface TrendingSong {
  id: string;
  title: string;
  artist: string;
  duration: number;
  public_url: string;
}

export interface VideoEditResponse {
  success: boolean;
  edited_video_url?: string;
  video_info?: any;
  message: string;
  save_name?: string;
  error?: string;
}

class VideoEditAPI {
  private baseURL: string;

  constructor() {
    this.baseURL = 'http://localhost:5000/api/video-edit';
  }

  private async request<T>(
    endpoint: string,
    method: string = 'GET',
    data?: any
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;

    const options: RequestInit = {
      method,
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include', // Important for session cookies
    };

    if (data) {
      options.body = JSON.stringify(data);
    }

    try {
      const response = await fetch(url, options);
      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.error || `HTTP ${response.status}: ${response.statusText}`);
      }

      return result;
    } catch (error) {
      console.error('Video Edit API Error:', error);
      throw error;
    }
  }

  async getUserVideos(): Promise<UserVideosResponse> {
    return this.request<UserVideosResponse>('/get-user-videos', 'GET');
  }

  async editVideo(request: VideoEditRequest): Promise<VideoEditResponse> {
    return this.request<VideoEditResponse>('/edit-video', 'POST', request);
  }

  async addTrendingAudio(request: TrendingAudioRequest): Promise<VideoEditResponse> {
    return this.request<VideoEditResponse>('/add-trending-audio', 'POST', request);
  }

  async getTrendingSongs(): Promise<{success: boolean, songs: TrendingSong[]}> {
    return this.request('/get-trending-songs', 'GET');
  }

  async healthCheck(): Promise<{ status: string; service: string; message: string }> {
    return this.request('/health', 'GET');
  }
}

export const videoEditAPI = new VideoEditAPI();

// ==================== REEL GENERATOR API ====================

export interface ScriptSuggestionRequest {
  prompt: string;
  images?: File[];
  imageUrls?: string[];
}

export interface ScriptSuggestionResponse {
  success: boolean;
  suggestions: string[];
  count: number;
  has_images: boolean;
  images_count: number;
  error?: string;
}

export interface GeneratedReel {
  id: string;
  title: string;
  prompt: string;
  filename: string;
  cloud_path: string;
  public_url: string;
  images_count: number;
  created_at: string;
  file_size_mb: number;
  status: string;
}

export interface ReelGenerationResponse {
  success: boolean;
  message: string;
  reel_id: string;
  title: string;
  public_url: string;
  cloud_path: string;
  file_size_mb: number;
  images_used: number;
  error?: string;
}

export interface UserReelsResponse {
  success: boolean;
  reels: GeneratedReel[];
  total: number;
  error?: string;
}

export interface NewReelGenerationRequest {
  prompt: string;
  images?: File[];
  imageUrls?: string[];
}

class ReelGeneratorAPI {
  private baseURL = 'https://reels-editor-298842469563.asia-south1.run.app';

  private async request<T>(
    endpoint: string,
    method: string = 'GET',
    data?: any,
    files?: File[]
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    
    console.log(`\n📡 ===== REEL GENERATOR API REQUEST =====`);
    console.log(`🌐 URL: ${url}`);
    console.log(`📡 Method: ${method}`);
    console.log(`📦 Data Type:`, typeof data);
    console.log(`📦 Data:`, data);
    console.log(`📁 Files:`, files ? files.length : 'None');
    console.log(`⏰ Timestamp: ${new Date().toISOString()}`);

    const options: RequestInit = {
      method,
    };

    if (files && files.length > 0) {
      // Handle file upload with FormData
      console.log(`📁 Processing files with FormData`);
      const formData = new FormData();
      
      if (data) {
        Object.keys(data).forEach(key => {
          formData.append(key, data[key]);
          console.log(`📝 Added to FormData: ${key} = ${data[key]}`);
        });
      }
      
      files.forEach(file => {
        formData.append('images', file);
        console.log(`📁 Added file: ${file.name} (${file.size} bytes)`);
      });
      
      options.body = formData;
    } else if (data) {
      // Handle JSON data
      console.log(`📦 Processing JSON data`);
      options.headers = {
        'Content-Type': 'application/json',
      };
      options.body = JSON.stringify(data);
      console.log(`📦 JSON Body:`, JSON.stringify(data));
    }

    console.log(`🔄 Making request with options:`, {
      method: options.method,
      headers: options.headers,
      bodyType: options.body instanceof FormData ? 'FormData' : typeof options.body,
      credentials: options.credentials
    });

    try {
      const response = await fetch(url, options);
      
      console.log(`📡 Response received:`);
      console.log(`📡 Status: ${response.status} ${response.statusText}`);
      console.log(`📡 Headers:`, Object.fromEntries(response.headers.entries()));
      console.log(`📡 URL: ${response.url}`);
      console.log(`📡 Redirected: ${response.redirected}`);
      
      const result = await response.json();
      console.log(`📄 Response JSON:`, result);

      if (!response.ok) {
        console.error(`❌ HTTP Error: ${response.status} ${response.statusText}`);
        console.error(`❌ Error Response:`, result);
        throw new Error(result.error || `HTTP ${response.status}: ${response.statusText}`);
      }

      console.log(`✅ Request completed successfully`);
      return result;
    } catch (error) {
      console.error(`❌ Request failed:`, error);
      console.error(`❌ Error details:`, {
        name: error instanceof Error ? error.name : 'Unknown',
        message: error instanceof Error ? error.message : 'Unknown error',
        stack: error instanceof Error ? error.stack : undefined
      });
      throw error;
    }
  }

  async generateReel(request: NewReelGenerationRequest, userId: string): Promise<ReelGenerationResponse> {
    console.log(`\n🎬 ===== GENERATE REEL REQUEST =====`);
    console.log(`📝 Prompt: ${request.prompt}`);
    console.log(`👤 User ID: ${userId}`);
    console.log(`🖼️ Image URLs:`, request.imageUrls);
    console.log(`📁 Images:`, request.images ? request.images.length : 0);
    
    const formData = new FormData();
    formData.append('prompt', request.prompt);
    
    // Handle image URLs by converting them to files via proxy
    if (request.imageUrls && request.imageUrls.length > 0) {
      console.log(`🔄 Converting ${request.imageUrls.length} image URLs to files via proxy...`);
      
      try {
        for (let i = 0; i < request.imageUrls.length; i++) {
          const imageUrl = request.imageUrls[i];
          console.log(`📥 Downloading image ${i + 1} via proxy: ${imageUrl}`);
          
          // Use our backend proxy to avoid CORS issues
          const proxyUrl = `http://localhost:5000/api/reel-generator/proxy-image?url=${encodeURIComponent(imageUrl)}&t=${Date.now()}`;
          console.log(`🔄 Proxy URL: ${proxyUrl}`);
          const response = await fetch(proxyUrl);
          
          if (!response.ok) {
            console.error(`❌ Failed to fetch image ${i + 1} via proxy: ${response.status} ${response.statusText}`);
            continue;
          }
          
          const blob = await response.blob();
          const fileName = `image_${i + 1}.${blob.type.split('/')[1] || 'jpg'}`;
          const file = new File([blob], fileName, { type: blob.type });
          
          formData.append('images', file);
          console.log(`✅ Added image ${i + 1}: ${fileName} (${file.size} bytes)`);
        }
      } catch (error) {
        console.error(`❌ Error converting image URLs to files:`, error);
        throw new Error(`Failed to process image URLs: ${error instanceof Error ? error.message : 'Unknown error'}`);
      }
    }
    
    // Handle direct file uploads
    if (request.images && request.images.length > 0) {
      request.images.forEach((file, index) => {
        formData.append('images', file);
        console.log(`📁 Added image ${index + 1}: ${file.name} (${file.size} bytes)`);
      });
    }
    
    console.log(`🔄 Calling request method...`);
    return this.request<ReelGenerationResponse>('/api/generate-video/images', 'POST', formData);
  }

  async suggestScript(request: ScriptSuggestionRequest, userId: string): Promise<ScriptSuggestionResponse> {
    console.log(`\n🤖 ===== SCRIPT SUGGESTION REQUEST =====`);
    console.log(`📝 Prompt: ${request.prompt}`);
    console.log(`👤 User ID: ${userId}`);
    console.log(`🖼️ Image URLs:`, request.imageUrls);
    console.log(`📁 Images:`, request.images ? request.images.length : 0);
    
    const formData = new FormData();
    formData.append('initial_prompt', request.prompt);
    
    // Handle image URLs by converting them to files via proxy
    if (request.imageUrls && request.imageUrls.length > 0) {
      console.log(`🔄 Converting ${request.imageUrls.length} image URLs to files via proxy...`);
      
      try {
        for (let i = 0; i < request.imageUrls.length; i++) {
          const imageUrl = request.imageUrls[i];
          console.log(`📥 Downloading image ${i + 1} via proxy: ${imageUrl}`);
          
          // Use our backend proxy to avoid CORS issues
          const proxyUrl = `http://localhost:5000/api/reel-generator/proxy-image?url=${encodeURIComponent(imageUrl)}&t=${Date.now()}`;
          console.log(`🔄 Proxy URL: ${proxyUrl}`);
          const response = await fetch(proxyUrl);
          
          if (!response.ok) {
            console.error(`❌ Failed to fetch image ${i + 1} via proxy: ${response.status} ${response.statusText}`);
            continue;
          }
          
          const blob = await response.blob();
          const fileName = `image_${i + 1}.${blob.type.split('/')[1] || 'jpg'}`;
          const file = new File([blob], fileName, { type: blob.type });
          
          formData.append('image', file);
          console.log(`✅ Added image ${i + 1}: ${fileName} (${file.size} bytes)`);
        }
      } catch (error) {
        console.error(`❌ Error converting image URLs to files:`, error);
        throw new Error(`Failed to process image URLs: ${error instanceof Error ? error.message : 'Unknown error'}`);
      }
    }
    
    // Handle direct file uploads
    if (request.images && request.images.length > 0) {
      request.images.forEach((file, index) => {
        formData.append('image', file);
        console.log(`📁 Added image ${index + 1}: ${file.name} (${file.size} bytes)`);
      });
    }
    
    console.log(`🔄 Calling request method...`);
    return this.request<ScriptSuggestionResponse>('/api/reel-generation/ideas', 'POST', formData);
  }

  async getUserReels(userId: string): Promise<UserReelsResponse> {
    console.log(`\n📹 ===== GET USER REELS REQUEST =====`);
    console.log(`👤 User ID: ${userId}`);
    console.log(`🔄 Calling request method...`);
    return this.request<UserReelsResponse>('/api/videos', 'GET');
  }

  async generateTextToVideo(prompt: string): Promise<ReelGenerationResponse> {
    console.log(`\n📝 ===== GENERATE TEXT TO VIDEO REQUEST =====`);
    console.log(`📝 Prompt: ${prompt}`);
    
    const formData = new FormData();
    formData.append('prompt', prompt);
    
    console.log(`🔄 Calling request method...`);
    return this.request<ReelGenerationResponse>('/api/generate-video/text', 'POST', formData);
  }

  async healthCheck(): Promise<{ status: string; service: string; bucket: string; brand_id: string }> {
    return this.request('/api/health', 'GET');
  }
}

export const reelGeneratorAPI = new ReelGeneratorAPI();

// Force reload - Logo Generation API ready
