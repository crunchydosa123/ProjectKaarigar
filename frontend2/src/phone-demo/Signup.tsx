import { usePage } from '@/contexts/PageContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useState } from 'react';

const Signup = () => {
  const { setCurrentPage } = usePage();
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: ''
  });

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleSignup = () => {
    // No validation needed - just navigate to home
    setCurrentPage('home');
  };

  const handleLoginClick = () => {
    setCurrentPage('login');
  };

  return (
    <div
      className="w-full h-full bg-cover bg-center flex flex-col overflow-y-auto overflow-x-hidden"
      style={{ backgroundImage: "url('/white_bg.png')" }}
    >
      {/* Header */}
      <div className="w-full mt-8 flex justify-center items-center p-3">
        <div className="text-lg font-bold">Create Account</div>
      </div>

      {/* Logo */}
      <div className="w-full flex justify-center items-center mt-6 mb-4">
        <div className="w-16 h-16 bg-cover bg-center rounded-full" style={{ backgroundImage: "url('/logo.png')" }}></div>
      </div>

      {/* Signup Form */}
      <div className="w-full px-6 mt-2">
        <Card className="bg-white/90 backdrop-blur-sm">
          <CardHeader className="text-center pb-4">
            <CardTitle className="text-xl">Join Project Kaarigar</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="space-y-2">
              <Label htmlFor="name" className="text-sm font-medium">Full Name</Label>
              <Input
                id="name"
                type="text"
                placeholder="Enter your full name"
                value={formData.name}
                onChange={(e) => handleInputChange('name', e.target.value)}
                className="w-full"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="email" className="text-sm font-medium">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="Enter your email"
                value={formData.email}
                onChange={(e) => handleInputChange('email', e.target.value)}
                className="w-full"
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="password" className="text-sm font-medium">Password</Label>
              <Input
                id="password"
                type="password"
                placeholder="Create a password"
                value={formData.password}
                onChange={(e) => handleInputChange('password', e.target.value)}
                className="w-full"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="confirmPassword" className="text-sm font-medium">Confirm Password</Label>
              <Input
                id="confirmPassword"
                type="password"
                placeholder="Confirm your password"
                value={formData.confirmPassword}
                onChange={(e) => handleInputChange('confirmPassword', e.target.value)}
                className="w-full"
              />
            </div>

            <Button 
              onClick={handleSignup}
              className="w-full bg-green-600 hover:bg-green-700 text-white font-medium py-2 mt-4"
            >
              Create Account
            </Button>

            <div className="text-center mt-4">
              <span className="text-sm text-gray-600">Already have an account? </span>
              <button 
                onClick={handleLoginClick}
                className="text-sm text-blue-600 hover:text-blue-700 font-medium"
              >
                Login
              </button>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Footer */}
      <div className="w-full px-6 mt-6 text-center">
        <p className="text-xs text-gray-500">
          By creating an account, you agree to our Terms of Service and Privacy Policy
        </p>
      </div>
    </div>
  );
};

export default Signup;
