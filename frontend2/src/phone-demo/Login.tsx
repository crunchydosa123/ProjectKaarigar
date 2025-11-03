import { usePage } from '@/contexts/PageContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useState } from 'react';
import { UserCircle2, Users } from 'lucide-react';

const Login = () => {
  const { setCurrentPage, login } = usePage();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showGuestAccounts, setShowGuestAccounts] = useState(false);

  const guestAccounts = [
    { email: 'raju.deo@gmail.com', password: '123456', name: 'Guest Account 1' },
    { email: 'surajchavan99886@gmail.com', password: '123456', name: 'Guest Account 2' }
  ];

  const handleLogin = async (loginEmail?: string, loginPassword?: string) => {
    const emailToUse = loginEmail || email;
    const passwordToUse = loginPassword || password;

    if (!emailToUse || !passwordToUse) {
      setError('Please enter both email and password');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const success = await login(emailToUse, passwordToUse);
      
      if (!success) {
        setError('Authentication failed. Please check your credentials and try again.');
      }
    } catch (error) {
      console.error('Login error:', error);
      setError('Authentication failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleGuestLogin = async (guestEmail: string, guestPassword: string) => {
    setShowGuestAccounts(false);
    await handleLogin(guestEmail, guestPassword);
  };

  const handleSignupClick = () => {
    setCurrentPage('signup');
  };

  return (
    <div
      className="w-full h-full bg-cover bg-center flex flex-col overflow-y-auto overflow-x-hidden"
      style={{ backgroundImage: "url('/white_bg.png')" }}
    >
      {/* Header */}
      <div className="w-full mt-10 flex justify-center items-center p-3">
        <div className="text-lg font-bold">Welcome Back</div>
      </div>

      {/* Logo */}
      <div className="w-full flex justify-center items-center mt-8 mb-6">
        <div className="w-16 h-16 bg-cover bg-center rounded-full" style={{ backgroundImage: "url('/logo.png')" }}></div>
      </div>

      {/* Login Form */}
      <div className="w-full px-6 mt-4">
        <Card className="bg-white/90 backdrop-blur-sm">
          <CardHeader className="text-center pb-4">
            <CardTitle className="text-xl">Login to Your Account</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email" className="text-sm font-medium">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="Enter your email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full"
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="password" className="text-sm font-medium">Password</Label>
              <Input
                id="password"
                type="password"
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full"
              />
            </div>

            {error && (
              <div className="text-red-600 text-sm text-center mt-2">
                {error}
              </div>
            )}

            <Button 
              onClick={() => handleLogin()}
              disabled={loading}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 mt-6 disabled:opacity-50"
            >
              {loading ? 'Logging in...' : 'Login'}
            </Button>

            {/* Guest Account Section */}
            <div className="mt-6">
              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-gray-300"></div>
                </div>
                <div className="relative flex justify-center text-sm">
                  <span className="px-2 bg-white text-gray-500">or</span>
                </div>
              </div>

              <Button
                onClick={() => setShowGuestAccounts(!showGuestAccounts)}
                disabled={loading}
                className="w-full mt-4 bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium py-2 flex items-center justify-center gap-2"
                type="button"
              >
                <Users size={20} />
                Continue as Guest
              </Button>

              {showGuestAccounts && (
                <div className="mt-4 space-y-3 p-4 bg-gray-50 rounded-xl border border-gray-200">
                  <p className="text-sm text-gray-600 mb-3">Select a guest account:</p>
                  
                  {guestAccounts.map((account, index) => (
                    <Button
                      key={index}
                      onClick={() => handleGuestLogin(account.email, account.password)}
                      disabled={loading}
                      className="w-full bg-white hover:bg-blue-50 hover:text-blue-600 text-gray-700 font-medium border border-gray-200 flex items-center justify-center gap-2"
                      type="button"
                      variant="outline"
                    >
                      <UserCircle2 size={18} />
                      {account.name}
                    </Button>
                  ))}
                </div>
              )}
            </div>

            <div className="text-center mt-4">
              <span className="text-sm text-gray-600">Don't have an account? </span>
              <button 
                onClick={handleSignupClick}
                className="text-sm text-blue-600 hover:text-blue-700 font-medium"
              >
                Sign up
              </button>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Footer */}
      <div className="w-full px-6 mt-8 text-center">
        <p className="text-xs text-gray-500">
          By continuing, you agree to our Terms of Service and Privacy Policy
        </p>
      </div>
    </div>
  );
};

export default Login;
