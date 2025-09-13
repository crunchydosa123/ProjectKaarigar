import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";

export default function Profile() {
    const { slug } = useParams();
    const [profile, setProfile] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        // if (!slug) {
        //     setError("No profile specified.");
        //     setLoading(false);
        //     return;
        // }
        const fetchProfile = async () => {
            setLoading(true);
            setError(null);
            try {
                const res = await fetch(`http://localhost:5000/api/converse/profile_json/Siddhartha`);
                if (!res.ok) {
                    const body = await res.json().catch(() => ({}));
                    throw new Error(body?.error || `Server returned ${res.status}`);
                }
                const data = await res.json();
                setProfile(data);
            } catch (e) {
                console.error(e);
                setError(e.message || "Failed to load profile");
            } finally {
                setLoading(false);
            }
        };
        fetchProfile();
    }, [slug]);

    return (
        <div className="min-h-screen bg-gradient-to-br from-purple-100 via-blue-50 to-pink-100 overflow-hidden relative p-6">
            {/* Floating accents */}
            <div className="absolute top-8 left-8 w-56 h-56 bg-gradient-to-br from-purple-300 to-pink-300 rounded-full mix-blend-multiply filter blur-xl opacity-40 animate-pulse" />
            <div className="absolute top-20 right-8 w-48 h-48 bg-gradient-to-br from-blue-300 to-purple-300 rounded-full mix-blend-multiply filter blur-xl opacity-40 animate-pulse delay-1000" />

            <div className="relative z-10 max-w-4xl mx-auto">
                <div className="flex items-center justify-between mb-6">
                    <div>
                        <h2 className="text-2xl font-bold text-gray-800">Artisan Profile</h2>
                        <p className="text-sm text-gray-600 mt-1">A concise profile generated from the interview</p>
                    </div>
                    <div>
                        <Link
                            to="/"
                            className="inline-block bg-white/80 backdrop-blur-sm px-4 py-2 rounded-2xl shadow hover:shadow-lg border border-white/30 text-gray-700"
                        >
                            Back
                        </Link>
                    </div>
                </div>

                {loading && (
                    <div className="p-8 bg-white/60 rounded-2xl shadow-md border border-white/30">
                        <div className="animate-pulse space-y-4">
                            <div className="h-8 bg-gray-200 rounded w-3/5" />
                            <div className="h-6 bg-gray-200 rounded w-2/5" />
                            <div className="h-4 bg-gray-200 rounded w-full" />
                            <div className="h-4 bg-gray-200 rounded w-full" />
                        </div>
                    </div>
                )}

                {!loading && error && (
                    <div className="p-6 bg-white rounded-2xl shadow-md border border-red-100 text-red-700">
                        <strong>Error:</strong> {error}
                    </div>
                )}

                {!loading && profile && (
                    <div className="bg-white rounded-2xl shadow-lg p-8 mt-4">
                        <div className="flex items-center space-x-6">
                            <div className="w-28 h-28 rounded-xl bg-gradient-to-br from-purple-200 to-pink-200 flex items-center justify-center text-3xl font-bold text-white">
                                {profile["Full Name"] ? profile["Full Name"].split(" ").map(n => n[0]).slice(0, 2).join("") : "A"}
                            </div>
                            <div className="flex-1">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <h1 className="text-2xl font-extrabold text-gray-900">
                                            {profile["Full Name"] || "Unknown Artisan"}
                                        </h1>
                                        <p className="text-sm text-gray-600 mt-1">{profile["Tagline"] || profile["Bio"]?.slice(0, 80)}</p>
                                    </div>
                                    <div className="text-right">
                                        <div className="text-sm text-gray-500">Location</div>
                                        <div className="text-base font-semibold text-gray-800">{profile["Location"] || "—"}</div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-8">
                            <div>
                                <h3 className="text-sm font-semibold text-gray-700 mb-2">Bio</h3>
                                <div className="text-gray-600 leading-relaxed">
                                    {profile["Bio"] || "No bio available."}
                                </div>
                            </div>

                            <div>
                                <h3 className="text-sm font-semibold text-gray-700 mb-2">Materials Used</h3>
                                <div className="text-gray-600 leading-relaxed">
                                    {profile["Materials Used"] || "Not specified."}
                                </div>

                                <h3 className="text-sm font-semibold text-gray-700 mt-6 mb-2">Aspiration</h3>
                                <div className="text-gray-600 leading-relaxed">
                                    {profile["Aspiration"] || "Not specified."}
                                </div>
                            </div>
                        </div>

                        <div className="mt-8 flex items-center justify-between">
                            <div className="text-sm text-gray-500">
                                Generated on <strong>{new Date().toLocaleDateString()}</strong>
                            </div>
                            <div>
                                <a
                                    href={`http://localhost:5000/api/converse/profile_json/${slug}`}
                                    target="_blank"
                                    rel="noreferrer"
                                    className="inline-block bg-gradient-to-br from-blue-500 to-purple-500 text-white px-4 py-2 rounded-2xl shadow hover:shadow-lg"
                                >
                                    View JSON
                                </a>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
