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

// Force reload - Logo Generation API ready
