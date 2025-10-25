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
