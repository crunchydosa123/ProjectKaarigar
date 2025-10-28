import React, { createContext, useContext, useState, useEffect } from "react";
import type { ReactNode } from "react";
import { authAPI } from '@/lib/api';
import type { User, Profile } from '@/lib/api';

type PageContextType = {
  currentPage: string;
  setCurrentPage: (page: string) => void;
  user: User | null;
  profile: Profile | null;
  isAuthenticated: boolean;
  loading: boolean;
  selectedVideo: any;
  setSelectedVideo: (video: any) => void;
  selectedProductId: string | null;
  setSelectedProductId: (id: string | null) => void;
  login: (email: string, password: string) => Promise<boolean>;
  signup: (email: string, password: string, name: string) => Promise<boolean>;
  logout: () => Promise<void>;
  checkSession: () => Promise<void>;
};

const PageContext = createContext<PageContextType | undefined>(undefined);

type PageProviderProps = {
  children: ReactNode;
};

export const PageProvider: React.FC<PageProviderProps> = ({ children }) => {
  const [currentPage, setCurrentPage] = useState<string>("login");
  const [user, setUser] = useState<User | null>(null);
  const [profile, setProfile] = useState<Profile | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedVideo, setSelectedVideo] = useState<any>(null);
  const [selectedProductId, setSelectedProductId] = useState<string | null>(null);

  // Check session on app start
  useEffect(() => {
    checkSession();
  }, []);

  const checkSession = async () => {
    try {
      setLoading(true);
      const response = await authAPI.checkSession();
      
      if (response.authenticated && response.user) {
        setUser(response.user);
        setIsAuthenticated(true);
        
        // Try to get profile data
        try {
          const profileResponse = await authAPI.getProfile();
          if (profileResponse.success) {
            setProfile(profileResponse.profile);
          }
        } catch (error) {
          console.warn('Could not fetch profile:', error);
        }
        
        // Navigate to home if user is authenticated
        setCurrentPage('home');
      } else {
        setUser(null);
        setProfile(null);
        setIsAuthenticated(false);
        setCurrentPage('login');
      }
    } catch (error) {
      console.error('Session check error:', error);
      setUser(null);
      setProfile(null);
      setIsAuthenticated(false);
      setCurrentPage('login');
    } finally {
      setLoading(false);
    }
  };

  const login = async (email: string, password: string): Promise<boolean> => {
    try {
      const response = await authAPI.login(email, password);
      
      if (response.success && response.user) {
        setUser(response.user);
        setIsAuthenticated(true);
        
        if (response.profile) {
          setProfile(response.profile);
        }
        
        setCurrentPage('home');
        return true;
      }
      return false;
    } catch (error) {
      console.error('Login error:', error);
      return false;
    }
  };

  const signup = async (email: string, password: string, name: string): Promise<boolean> => {
    try {
      const response = await authAPI.signup(email, password, name);
      
      if (response.success && response.user) {
        setUser(response.user);
        setIsAuthenticated(true);
        
        if (response.profile) {
          setProfile(response.profile);
        }
        
        setCurrentPage('home');
        return true;
      }
      return false;
    } catch (error) {
      console.error('Signup error:', error);
      return false;
    }
  };

  const logout = async (): Promise<void> => {
    try {
      await authAPI.logout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      setUser(null);
      setProfile(null);
      setIsAuthenticated(false);
      setCurrentPage('login');
    }
  };

  return (
    <PageContext.Provider value={{ 
      currentPage, 
      setCurrentPage, 
      user, 
      profile, 
      isAuthenticated, 
      loading,
      selectedVideo,
      setSelectedVideo,
      selectedProductId,
      setSelectedProductId,
      login,
      signup,
      logout,
      checkSession
    }}>
      {children}
    </PageContext.Provider>
  );
};

// Custom hook for easier usage
export const usePage = (): PageContextType => {
  const context = useContext(PageContext);
  if (!context) {
    throw new Error("usePage must be used within a PageProvider");
  }
  return context;
};
