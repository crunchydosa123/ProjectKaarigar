# Frontend-Backend Integration Guide

## 🚀 Quick Start

### 1. Start Backend
```bash
cd ProjectKaarigar/backend
pip install -r requirements.txt
python app.py
```
Backend will run on `http://localhost:5000`

### 2. Start Frontend
```bash
cd ProjectKaarigar/frontend2
npm install
npm run dev
```
Frontend will run on `http://localhost:5173`

### 3. Test Authentication Flow

1. **Open** `http://localhost:5173` in your browser
2. **Signup** with a new account:
   - Email: `test@example.com`
   - Password: `password123`
   - Name: `Test User`
3. **Login** with the same credentials
4. **Navigate** through the app
5. **Logout** using the logout button

## 🔧 What's Integrated

### ✅ Authentication System
- **Signup** - Create new user accounts
- **Login** - Authenticate existing users
- **Session Management** - Automatic session handling
- **Logout** - Clear session and return to login
- **Loading States** - Smooth user experience

### ✅ Backend Integration
- **API Communication** - RESTful API calls
- **Session Cookies** - Automatic session management
- **Error Handling** - User-friendly error messages
- **CORS Support** - Cross-origin requests enabled

### ✅ Frontend Features
- **Context Management** - Global state for user data
- **Loading States** - Loading screens during API calls
- **Error Display** - Clear error messages
- **User Profile** - Display user information
- **Responsive Design** - Works in phone layout

## 📱 User Flow

1. **App Start** → Loading screen while checking session
2. **Not Authenticated** → Login page
3. **Signup/Login** → API call to backend
4. **Success** → Navigate to home page
5. **Home Page** → Shows user name and logout button
6. **Logout** → Clear session and return to login

## 🔍 API Endpoints Used

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/auth/signup` | POST | User registration |
| `/api/auth/login` | POST | User authentication |
| `/api/auth/logout` | POST | User logout |
| `/api/auth/session` | GET | Check session status |
| `/api/auth/profile` | GET | Get user profile |

## 🐛 Troubleshooting

### Backend Issues
- **Port 5000 in use**: Change port in `app.py`
- **Firestore errors**: Check Google Cloud credentials
- **CORS errors**: Verify frontend URL in CORS config

### Frontend Issues
- **API calls failing**: Check backend is running
- **Session not persisting**: Check browser cookies
- **Loading forever**: Check network tab for errors

### Common Solutions
1. **Clear browser cache** and cookies
2. **Restart both** backend and frontend
3. **Check console** for error messages
4. **Verify URLs** match in API calls

## 📊 Testing

### Manual Testing
1. Test signup with new email
2. Test login with existing credentials
3. Test logout functionality
4. Test session persistence (refresh page)
5. Test error handling (wrong credentials)

### Browser Dev Tools
- **Network Tab**: Monitor API calls
- **Application Tab**: Check session cookies
- **Console**: View error messages
- **Storage**: Check local storage

## 🎯 Next Steps

1. **Add more features** to the app
2. **Integrate content creation** APIs
3. **Add user profile** editing
4. **Implement data persistence**
5. **Add real-time features**

## 📞 Support

If you encounter issues:
1. Check the browser console for errors
2. Verify both backend and frontend are running
3. Check the network tab for failed requests
4. Ensure all dependencies are installed
