import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { usePage } from '@/contexts/PageContext'
import { Facebook, House, Instagram, Twitter, Loader2, Save } from 'lucide-react';
import { useState, useEffect } from 'react';
import { logoAPI, profileAPI } from '@/lib/api';

// Define the interfaces locally to avoid import issues
/*interface LogoInfo {
  logo_url?: string;
  brand_name?: string;
  logo_prompt?: string;
  logo_generated_at?: string;
  has_logo: boolean;
}*/

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

const ProfilePage = () => {
  const { setCurrentPage } = usePage();
  const [logoInfo, setLogoInfo] = useState({
    logo_url: "/ai_gen_logo.jpeg",
    brand_name: "Your Brand",
    has_logo: false,
    logo_prompt: "",
    logo_generated_at: ""
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
    const fetchData = async () => {
      try {
        console.log("🔄 Starting to fetch profile data...");

        // Always try to get fresh profile data first (this will extract from Cloud Storage and save to profiles collection)
        try {
          console.log("🔄 Getting fresh profile data from Cloud Storage...");
          const profileResponse = await profileAPI.getProfileData();
          console.log("📄 Fresh profile response:", profileResponse);

          if (profileResponse.success && profileResponse.profile_data) {
            setProfileData(profileResponse.profile_data);
            console.log("✅ Loaded fresh profile data:", profileResponse.profile_data);

            // Update brand name if available in the response
            if (profileResponse.brand_info && profileResponse.brand_info.brand_name) {
              setLogoInfo(prev => ({
                ...prev,
                brand_name: profileResponse.brand_info?.brand_name ?? prev.brand_name,
              }));
              console.log("🏷️ Updated brand name from profile:", profileResponse.brand_info.brand_name);
            }
          } else {
            console.log("⚠️ Failed to get fresh profile data, trying saved profile...");
            // Fallback to saved profile
            const savedResponse = await profileAPI.getSavedProfile();
            console.log("📄 Saved profile response:", savedResponse);

            if (savedResponse.success && savedResponse.profile_data) {
              setProfileData(savedResponse.profile_data);
              console.log("✅ Loaded saved profile:", savedResponse.profile_data);
            } else {
              console.log("❌ No profile data available");
            }
          }
        } catch (profileError) {
          console.error("❌ Failed to fetch profile data:", profileError);
          // Keep default empty values
        }

        // Fetch logo info after profile data is loaded (so it can find the saved profile)
        console.log("🔄 Fetching logo info...");
        const logoResponse = await logoAPI.getLogo();
        if (logoResponse.success && logoResponse.logo_info) {
          setLogoInfo({
            logo_url: logoResponse.logo_info.logo_url ?? "",
            has_logo: logoResponse.logo_info.has_logo,
            logo_generated_at: logoResponse.logo_info.logo_generated_at ?? "",
            logo_prompt: logoResponse.logo_info.logo_prompt ?? "",
            brand_name: logoResponse.logo_info.brand_name ?? "",
          });
          console.log("✅ Logo info loaded:", logoResponse.logo_info);
        } else {
          console.log("⚠️ No logo info found, using defaults");
          // Set default logo info
          setLogoInfo({
            logo_url: "/ai_gen_logo.jpeg",
            brand_name: "Your Brand",
            has_logo: false,
            logo_prompt: "",
            logo_generated_at: ""
          });
        }
      } catch (error) {
        console.error("❌ Failed to fetch data:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  // Debug function for profile data
  const debugProfileData = () => {
    console.log("🔍 Profile Debug Info:", {
      profileData: profileData,
      logoInfo: logoInfo,
      saving: saving,
      error: error,
      success: success
    });
  };

  // Make debug function available globally for console access
  (window as any).debugProfileData = debugProfileData;

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
            🔄 Loading your profile data from Cloud Storage...
          </div>
        </div>
      )}

      {!loading && profileData.name && (
        <div className="mx-4 mb-4 p-3 bg-green-50 border border-green-200 rounded-md">
          <div className="text-sm text-green-800">
            ✅ Profile data loaded successfully!
            <br />
            <span className="text-xs">
              Auto-filled: Name, Occupation ({profileData.occupation}), Bio, Materials, Aspirations, Craft Details
              {profileData.challenges && ', Challenges'}
            </span>
          </div>
        </div>
      )}

      {!loading && !profileData.name && (
        <div className="mx-4 mb-4 p-3 bg-orange-50 border border-orange-200 rounded-md">
          <div className="text-sm text-orange-800">
            ⚠️ No profile data found. Please fill in your information manually.
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
              setLogoInfo({ ...logoInfo, brand_name: newBrandName });

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
            onChange={(e) => setProfileData({ ...profileData, name: e.target.value })}
            className='text-sm'
            placeholder={loading ? "Loading..." : "Enter your name"}
            disabled={loading}
          />
          {!loading && !profileData.name && (
            <div className="text-xs text-orange-600 mt-1">
              ⚠️ No name found in profile data. Please enter manually.
            </div>
          )}
        </div>

        <div className='my-4'>
          <Label className='mb-1'>Your Email</Label>
          <Input
            type='email'
            value={profileData.email}
            onChange={(e) => setProfileData({ ...profileData, email: e.target.value })}
            className='text-sm'
            placeholder="Enter your email"
            disabled={loading}
          />
        </div>

        <div className='my-4'>
          <Label className='mb-1'>Occupation</Label>
          <Input
            type='text'
            value={profileData.occupation}
            onChange={(e) => setProfileData({ ...profileData, occupation: e.target.value })}
            className='text-sm'
            placeholder="Enter your occupation"
            disabled={loading}
          />
        </div>

        <div className='my-4'>
          <Label className='mb-1'>Bio</Label>
          <Textarea
            value={profileData.bio}
            onChange={(e) => setProfileData({ ...profileData, bio: e.target.value })}
            className='text-sm min-h-[60px]'
            placeholder={loading ? "Loading..." : "Tell us about yourself, your craft, and your story..."}
            rows={3}
            disabled={loading}
          />
          {!loading && !profileData.bio && (
            <div className="text-xs text-orange-600 mt-1">
              ⚠️ No bio found in profile data. Please enter manually.
            </div>
          )}
        </div>

        {/* Only show location if it has data */}
        {profileData.location && (
          <div className='my-4'>
            <Label className='mb-1'>Location</Label>
            <Input
              type='text'
              value={profileData.location}
              onChange={(e) => setProfileData({ ...profileData, location: e.target.value })}
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
            onChange={(e) => setProfileData({ ...profileData, craft_details: e.target.value })}
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
            onChange={(e) => setProfileData({ ...profileData, materials_used: e.target.value })}
            className='text-sm'
            placeholder="e.g., Clay, Wood, Metal, Traditional techniques..."
            disabled={loading}
          />
        </div>

        {/* Only show experience years if it has data */}
        {profileData.experience_years && (
          <div className='my-4'>
            <Label className='mb-1'>Years of Experience</Label>
            <Input
              type='text'
              value={profileData.experience_years}
              onChange={(e) => setProfileData({ ...profileData, experience_years: e.target.value })}
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
            onChange={(e) => setProfileData({ ...profileData, aspirations: e.target.value })}
            className='text-sm min-h-[50px]'
            placeholder="What are your goals and aspirations for your craft?"
            rows={2}
            disabled={loading}
          />
        </div>

        {/* Only show challenges if it has data */}
        {profileData.challenges && (
          <div className='my-4'>
            <Label className='mb-1'>Challenges</Label>
            <Textarea
              value={profileData.challenges}
              onChange={(e) => setProfileData({ ...profileData, challenges: e.target.value })}
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
                onChange={(e) => setProfileData({ ...profileData, instagram: e.target.value })}
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
                onChange={(e) => setProfileData({ ...profileData, facebook: e.target.value })}
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
                onChange={(e) => setProfileData({ ...profileData, twitter: e.target.value })}
                className='text-sm'
                placeholder="@your_twitter"
                disabled={loading}
              />
            </div>
          </div>
        </div>

        {/* Debug Info - Remove this in production */}
        {import.meta.env.DEV && (
          <div className="text-xs text-gray-500 mt-2 p-2 bg-gray-50 rounded">
            <div className="font-bold">Debug Info (Working Fields):</div>
            <div>Name: {profileData.name || 'Empty'}</div>
            <div>Email: {profileData.email || 'Empty'}</div>
            <div>Occupation: {profileData.occupation || 'Empty'} {profileData.occupation && profileData.occupation !== 'Artisan' ? '✅' : ''}</div>
            <div>Bio: {profileData.bio || 'Empty'}</div>
            <div>Materials: {profileData.materials_used || 'Empty'}</div>
            <div>Aspirations: {profileData.aspirations || 'Empty'}</div>
            <div>Craft Details: {profileData.craft_details ? '✅ Has data' : 'Empty'}</div>
            <div>Challenges: {profileData.challenges ? '✅ Has data' : 'Empty'}</div>
            <div className="text-orange-600 mt-1">Hidden fields: Location, Experience Years (empty)</div>
            <div className="mt-2 flex gap-2 flex-wrap">
              <Button
                size="sm"
                variant="outline"
                onClick={async () => {
                  console.log("🔄 Manual profile fetch...");
                  setLoading(true);
                  try {
                    const response = await profileAPI.getProfileData();
                    console.log("📄 Manual fetch response:", response);
                    if (response.success && response.profile_data) {
                      setProfileData(response.profile_data);
                      console.log("✅ Manual fetch successful");
                      setSuccess("Profile data refreshed from Cloud Storage!");
                    } else {
                      setError("Failed to fetch profile data");
                    }
                  } catch (error) {
                    console.error("❌ Manual fetch failed:", error);
                    setError("Failed to fetch profile data");
                  } finally {
                    setLoading(false);
                  }
                }}
              >
                🔄 Refresh Profile
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={async () => {
                  console.log("🔄 Testing profile API health...");
                  try {
                    const response = await profileAPI.healthCheck();
                    console.log("📄 Health check response:", response);
                  } catch (error) {
                    console.error("❌ Health check failed:", error);
                  }
                }}
              >
                Test API Health
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={async () => {
                  console.log("🔄 Refreshing logo info...");
                  try {
                    const response = await logoAPI.getLogo();
                    console.log("📄 Logo refresh response:", response);
                    if (response.success && response.logo_info) {
                      setLogoInfo({
                        logo_url: response.logo_info.logo_url ?? "",
                        has_logo: response.logo_info.has_logo,
                        logo_generated_at: response.logo_info.logo_generated_at ?? "",
                        logo_prompt: response.logo_info.logo_prompt ?? "",
                        brand_name: response.logo_info.brand_name ?? "",
                      });
                      console.log("✅ Logo info refreshed:", response.logo_info);
                    }
                  } catch (error) {
                    console.error("❌ Logo refresh failed:", error);
                  }
                }}
              >
                🔄 Refresh Logo
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={async () => {
                  console.log("🔄 Updating logo from Cloud Storage...");
                  try {
                    const response = await profileAPI.updateLogoFromStorage();
                    console.log("📄 Logo update response:", response);
                    if (response.success) {
                      setSuccess("✅ Logo updated from Cloud Storage!");
                      // Refresh logo info after update
                      const logoResponse = await logoAPI.getLogo();
                      if (logoResponse.success && logoResponse.logo_info) {
                        console.log("logo info: ", logoResponse)
                        setLogoInfo({
                          logo_url: logoResponse.logo_info.logo_url ?? "",
                          has_logo: logoResponse.logo_info.has_logo,
                          logo_generated_at: logoResponse.logo_info.logo_generated_at ?? "",
                          logo_prompt: logoResponse.logo_info.logo_prompt ?? "",
                          brand_name: logoResponse.logo_info.brand_name ?? "",
                        });
                      }
                    } else {
                      setError(`❌ Failed to update logo: ${response.error}`);
                    }
                  } catch (error) {
                    console.error("❌ Logo update failed:", error);
                    setError("❌ Failed to update logo from Cloud Storage");
                  }
                }}
              >
                🔄 Update from Storage
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={async () => {
                  console.log("🧪 Testing profile save...");
                  try {
                    const response = await profileAPI.saveProfile(profileData);
                    console.log("📄 Test save response:", response);
                    if (response.success) {
                      setSuccess("✅ Test save successful!");
                    } else {
                      setError(`❌ Test save failed: ${response.error}`);
                    }
                  } catch (error) {
                    console.error("❌ Test save failed:", error);
                    setError("❌ Test save failed");
                  }
                }}
              >
                🧪 Test Save
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={async () => {
                  console.log("🔄 Debugging user data...");
                  try {
                    const response = await profileAPI.debugUserData();
                    console.log("📄 Debug user data response:", response);
                    if (response.success) {
                      console.log("👤 User ID:", response.user_id);
                      console.log("🔗 Kaarigar ID:", response.kaarigar_id);
                      console.log("📄 User Data Keys:", response.user_data_keys);
                      console.log("📄 Kaarigar Data Keys:", response.kaarigar_data_keys);
                      console.log("🔗 Profile URLs:", response.profile_urls);
                      console.log("📄 Cloud Storage Profile:", response.cloud_storage_profile);
                      console.log("📄 User Data Sample:", response.user_data_sample);

                      // Show in alert for easy viewing
                      alert(`Debug Info:
User ID: ${response.user_id}
Kaarigar ID: ${response.kaarigar_id}
User Data Keys: ${response.user_data_keys.join(', ')}
Profile URLs: ${JSON.stringify(response.profile_urls, null, 2)}
Cloud Storage Profile: ${JSON.stringify(response.cloud_storage_profile, null, 2)}`);
                    }
                  } catch (error) {
                    console.error("❌ Debug failed:", error);
                    alert(`Debug failed: ${(error as any).message}`);
                  }
                }}
              >
                Debug User Data
              </Button>
            </div>
          </div>
        )}

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

export default ProfilePage