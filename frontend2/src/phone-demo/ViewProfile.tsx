import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { usePage } from '@/contexts/PageContext'
import { Facebook, House, Instagram, Twitter, Loader2, Save } from 'lucide-react';
import { useState, useEffect } from 'react';
import { logoAPI, profileAPI } from '@/lib/api';

// Define the interfaces locally to avoid import issues
interface LogoInfo {
  logo_url?: string;
  brand_name?: string;
  logo_prompt?: string;
  logo_generated_at?: string;
  has_logo: boolean;
}

interface ProfileData {
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

const ViewProfile = () => {
  const { setCurrentPage } = usePage();
  
  const [logoInfo, setLogoInfo] = useState({
    logo_url: "/ai_gen_logo.jpeg",
    brand_name: "Your Brand",
    has_logo: false
  });
  const [profileData, setProfileData] = useState<ProfileData>({
    name: "",
    email: "",
    occupation: "",
    bio: "",
    location: "",
    languages: ["en"],
    craft_details: "",
    materials_used: "",
    experience_years: "",
    aspirations: "",
    challenges: "",
    instagram: "",
    facebook: "",
    twitter: ""
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    const fetchSavedProfile = async () => {
      try {
        console.log("🔄 Loading saved profile data (no extraction)...");

        // Get saved profile data only (no extraction from Cloud Storage)
        const savedResponse = await profileAPI.getSavedProfile();
        console.log("📄 Saved profile response:", savedResponse);
        
        if (savedResponse.success && savedResponse.profile_data) {
          setProfileData(savedResponse.profile_data);
          console.log("✅ Loaded saved profile:", savedResponse.profile_data);
          
          // Update brand name if available in the response
          if (savedResponse.brand_info && savedResponse.brand_info.brand_name) {
            setLogoInfo(prev => ({
              ...prev,
              brand_name: savedResponse?.brand_info?.brand_name ?? prev.brand_name
            }));

            console.log("🏷️ Updated brand name from saved profile:", savedResponse.brand_info.brand_name);
          }
        } else {
          console.log("⚠️ No saved profile data found");
        }

        // Fetch logo info
        console.log("🔄 Fetching logo info...");
        const logoResponse = await logoAPI.getLogo();
        if (logoResponse.success && logoResponse.logo_info) {
          setLogoInfo({
            logo_url: logoResponse.logo_info?.logo_url ?? '',
            brand_name: logoResponse.logo_info?.brand_name ?? '',
            has_logo: logoResponse.logo_info?.has_logo ?? false,
          });

          console.log("✅ Logo info loaded:", logoResponse.logo_info);
        } else {
          console.log("⚠️ No logo info found, using defaults");
          setLogoInfo({
            logo_url: "/ai_gen_logo.jpeg",
            brand_name: "Your Brand",
            has_logo: false
          });
        }
      } catch (error) {
        console.error("❌ Failed to fetch saved profile:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchSavedProfile();
  }, []);

  const handleSaveProfile = async () => {
    setSaving(true);
    setError("");
    setSuccess("");

    try {
      console.log("💾 Starting profile save process...");
      console.log("📋 Profile data to save:", profileData);
      console.log("🏷️ Brand info to save:", logoInfo);

      // First update brand information if it has changed
      if (logoInfo.brand_name && logoInfo.brand_name !== "Your Brand") {
        console.log("🔄 Updating brand information...");
        try {
          const brandResponse = await profileAPI.updateBrand(logoInfo.brand_name, logoInfo.logo_url);
          console.log("✅ Brand information updated:", brandResponse);
        } catch (brandError) {
          console.warn("⚠️ Failed to update brand info:", brandError);
          // Continue with profile save even if brand update fails
        }
      }

      // Then save the profile data
      console.log("🔄 Saving profile data to profiles collection...");
      const response = await profileAPI.saveProfile(profileData);
      console.log("📄 Save profile response:", response);
      
      if (response.success) {
        setSuccess("Profile saved successfully!");
        console.log("✅ Profile saved successfully to profiles collection");
        setTimeout(() => {
          setCurrentPage('home');
        }, 1500);
      } else {
        console.error("❌ Profile save failed:", response);
        setError(`Failed to save profile: ${response.error || 'Unknown error'}`);
      }
    } catch (err) {
      console.error("❌ Save profile error:", err);
      setError(`Failed to save profile: ${(err as any).message || 'Please check your connection and try again.'}`);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div
      className="w-full h-full bg-cover bg-center flex flex-col overflow-y-auto overflow-x-hidden"
      style={{ backgroundImage: "url('/white_bg.png')" }}
    >
      {/* Header */}
      <div className="w-full mt-10 flex justify-start items-center p-3">
        <button className="h-10 w-10 bg-gray-500 rounded-md flex justify-center items-center text-white" onClick={() => setCurrentPage('home')}><House /></button>
        <div className="text-md font-bold ml-3">Your Profile</div>
      </div>


      {/* Status Message */}
      {loading && (
        <div className="mx-4 mb-4 p-3 bg-blue-50 border border-blue-200 rounded-md">
          <div className="text-sm text-blue-800">
            🔄 Loading your saved profile data...
          </div>
        </div>
      )}
      
      {!loading && profileData.name && (
        <div className="mx-4 mb-4 p-3 bg-green-50 border border-green-200 rounded-md">
          <div className="text-sm text-green-800">
            ✅ Profile loaded from saved data! 
            <br />
            <span className="text-xs">
              This is your saved profile information. Make changes and click Save to update.
            </span>
          </div>
        </div>
      )}
      
      {!loading && !profileData.name && (
        <div className="mx-4 mb-4 p-3 bg-orange-50 border border-orange-200 rounded-md">
          <div className="text-sm text-orange-800">
            ⚠️ No saved profile data found. Please complete the onboarding process first.
          </div>
        </div>
      )}

      <div className='px-4 mb-5'>
        {loading ? (
          <div className='flex flex-col justify-center items-center rounded-md py-8'>
            <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
            <Label className='mt-2'>Loading profile data...</Label>
          </div>
        ) : (
          <div className='flex flex-col justify-center items-center rounded-md'>
            <img 
              src={logoInfo.logo_url} 
              alt="Brand Logo" 
              className='h-30 w-30 rounded-lg object-contain' 
            />
            <Label className='mt-2'>Your Brand Logo</Label>
            {logoInfo.has_logo && (
              <div className="text-xs text-green-600 mt-1">✓ AI Generated</div>
            )}
          </div>
        )}

        <div className='my-4'>
          <Label className='mb-1'>Your Brand's Name</Label>
          <Input 
            type='text' 
            value={logoInfo.brand_name} 
            onChange={(e) => {
              const newBrandName = e.target.value;
              setLogoInfo({...logoInfo, brand_name: newBrandName});
              
              // Auto-save brand name changes
              if (newBrandName && newBrandName !== "Your Brand") {
                console.log("🔄 Auto-saving brand name:", newBrandName);
                profileAPI.updateBrand(newBrandName, logoInfo.logo_url).catch(err => {
                  console.warn("⚠️ Auto-save brand failed:", err);
                });
              }
            }}
            className='text-sm'
            placeholder="Enter your brand name"
            disabled={loading}
          />
          {logoInfo.brand_name && logoInfo.brand_name !== "Your Brand" && (
            <div className="text-xs text-green-600 mt-1">
              ✓ Brand name will be saved automatically
            </div>
          )}
        </div>

        <div className=''>
          <Label className='mb-1'>Your Name</Label>
          <Input 
            type='text' 
            value={profileData.name} 
            onChange={(e) => setProfileData({...profileData, name: e.target.value})}
            className='text-sm'
            placeholder={loading ? "Loading..." : "Enter your name"}
            disabled={loading}
          />
        </div>

        <div className='my-4'>
          <Label className='mb-1'>Your Email</Label>
          <Input 
            type='email' 
            value={profileData.email} 
            onChange={(e) => setProfileData({...profileData, email: e.target.value})}
            className='text-sm'
            placeholder={loading ? "Loading..." : "Enter your email"}
            disabled={loading}
          />
        </div>

        <div className='my-4'>
          <Label className='mb-1'>Occupation</Label>
          <Input 
            type='text' 
            value={profileData.occupation} 
            onChange={(e) => setProfileData({...profileData, occupation: e.target.value})}
            className='text-sm'
            placeholder={loading ? "Loading..." : "Enter your occupation"}
            disabled={loading}
          />
        </div>

        <div className='my-4'>
          <Label className='mb-1'>Bio</Label>
          <Textarea 
            value={profileData.bio} 
            onChange={(e) => setProfileData({...profileData, bio: e.target.value})}
            className='text-sm min-h-[60px]'
            placeholder={loading ? "Loading..." : "Tell us about yourself, your craft, and your story..."}
            rows={3}
            disabled={loading}
          />
        </div>

        {profileData.location && (
          <div className='my-4'>
            <Label className='mb-1'>Location</Label>
            <Input 
              type='text' 
              value={profileData.location} 
              onChange={(e) => setProfileData({...profileData, location: e.target.value})}
              className='text-sm'
              placeholder="City, State, Country"
              disabled={loading}
            />
          </div>
        )}

        <div className='my-4'>
          <Label className='mb-1'>Craft Details</Label>
          <Textarea 
            value={profileData.craft_details} 
            onChange={(e) => setProfileData({...profileData, craft_details: e.target.value})}
            className='text-sm min-h-[50px]'
            placeholder="Describe your craft, techniques, and specialties..."
            rows={2}
            disabled={loading}
          />
        </div>

        <div className='my-4'>
          <Label className='mb-1'>Materials Used</Label>
          <Input 
            type='text' 
            value={profileData.materials_used} 
            onChange={(e) => setProfileData({...profileData, materials_used: e.target.value})}
            className='text-sm'
            placeholder="e.g., Clay, Wood, Metal, Traditional techniques..."
            disabled={loading}
          />
        </div>

        {profileData.experience_years && (
          <div className='my-4'>
            <Label className='mb-1'>Years of Experience</Label>
            <Input 
              type='text' 
              value={profileData.experience_years} 
              onChange={(e) => setProfileData({...profileData, experience_years: e.target.value})}
              className='text-sm'
              placeholder="e.g., 5 years, 10+ years, Since childhood..."
              disabled={loading}
            />
          </div>
        )}

        <div className='my-4'>
          <Label className='mb-1'>Aspirations & Goals</Label>
          <Textarea 
            value={profileData.aspirations} 
            onChange={(e) => setProfileData({...profileData, aspirations: e.target.value})}
            className='text-sm min-h-[50px]'
            placeholder="What are your goals and aspirations for your craft?"
            rows={2}
            disabled={loading}
          />
        </div>

        {profileData.challenges && (
          <div className='my-4'>
            <Label className='mb-1'>Challenges</Label>
            <Textarea 
              value={profileData.challenges} 
              onChange={(e) => setProfileData({...profileData, challenges: e.target.value})}
              className='text-sm min-h-[50px]'
              placeholder="What challenges do you face in your craft or business?"
              rows={2}
              disabled={loading}
            />
          </div>
        )}

        <div className='my-4 '>
          <Label className='mb-1'>Social Media Links</Label>

          <div className='flex flex-col gap-2'>
            <div className='flex justify-start items-center gap-1'>
              <Instagram />
              <Input 
                type='text' 
                value={profileData.instagram || ''} 
                onChange={(e) => setProfileData({...profileData, instagram: e.target.value})}
                className='text-sm'
                placeholder="@your_instagram"
                disabled={loading}
              />
            </div>
            <div className='flex justify-start items-center gap-1'>
              <Facebook />
              <Input 
                type='text' 
                value={profileData.facebook || ''} 
                onChange={(e) => setProfileData({...profileData, facebook: e.target.value})}
                className='text-sm'
                placeholder="@your_facebook"
                disabled={loading}
              />
            </div>
            <div className='flex justify-start items-center gap-1'>
              <Twitter />
              <Input 
                type='text' 
                value={profileData.twitter || ''} 
                onChange={(e) => setProfileData({...profileData, twitter: e.target.value})}
                className='text-sm'
                placeholder="@your_twitter"
                disabled={loading}
              />
            </div>
          </div>
        </div>

        {/* Status Messages */}
        {error && (
          <div className="text-red-600 text-sm mt-2 p-2 bg-red-50 rounded">
            {error}
          </div>
        )}
        {success && (
          <div className="text-green-600 text-sm mt-2 p-2 bg-green-50 rounded">
            {success}
          </div>
        )}

        <Button 
          className='w-full mt-3' 
          onClick={handleSaveProfile}
          disabled={saving}
        >
          {saving ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              Saving...
            </>
          ) : (
            <>
              <Save className="w-4 h-4 mr-2" />
              Save Profile
            </>
          )}
        </Button>
      </div>
    </div>
  )
}

export default ViewProfile
