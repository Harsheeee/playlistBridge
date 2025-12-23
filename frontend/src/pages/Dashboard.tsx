import { useEffect, useState } from "react";

type Playlist = {
  id: string;
  name: string;
  tracks: { total: number };
};
type YouTubePlaylist = {
  id: string;
  name: string;
  count: number;
};
type CurrentUser = {
  id: number;
  name: string;
  email: string;
  picture?: string | null;
};

export default function Dashboard() {
  const [playlists, setPlaylists] = useState<Playlist[]>([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [messageType, setMessageType] = useState<"success" | "info">("info");
  const [ytTargetTitle, setYtTargetTitle] = useState("Transferred from Spotify");
  const [spotifyTargetTitle, setSpotifyTargetTitle] = useState(
    "Transferred from YouTube"
  );
  const [authChecked, setAuthChecked] = useState(false);
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [profileOpen, setProfileOpen] = useState(false);

  const connectSpotify = () => {
    window.location.href = "http://127.0.0.1:8000/api/oauth/spotify/login";
  };

  const connectYouTube = () => {
    window.location.href = "http://127.0.0.1:8000/api/oauth/youtube/login";
  };

  const fetchPlaylists = async () => {
    setLoading(true);
    const res = await fetch(
      "http://127.0.0.1:8000/api/spotify/playlists",
      { credentials: "include" }
    );
    if (res.ok) {
      const data = await res.json();
      setPlaylists(data);
    }
    setLoading(false);
  };

  const transfer = async (playlistId: string) => {
    setMessage("Transferring playlist...");
    setMessageType("info");
    const res = await fetch(
      `http://127.0.0.1:8000/api/transfer/spotify-to-youtube/${playlistId}`,
      {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: ytTargetTitle }),
      }
    );
    const data = await res.json();
    setMessageType("success");
    setMessage(
      `Transfer complete: ${data.matched}/${data.total} tracks matched`
    );
  };

  const transferYouTubeToSpotify = async (playlistId: string) => {
    setMessage("Transferring YouTube playlist...");
    setMessageType("info");
    const res = await fetch(
      `http://127.0.0.1:8000/api/transfer/youtube-to-spotify/${playlistId}`,
      {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: spotifyTargetTitle }),
      }
    );
    const data = await res.json();
    setMessageType("success");
    setMessage(
      `Transfer complete: ${data.matched}/${data.total} tracks matched`
    );
  };

  const [ytPlaylists, setYtPlaylists] = useState<YouTubePlaylist[]>([]);
  const [ytLoading, setYtLoading] = useState(false);

  const fetchYouTubePlaylists = async () => {
    setYtLoading(true);
    const res = await fetch(
      "http://127.0.0.1:8000/api/youtube/playlists",
      { credentials: "include" }
    );
    if (res.ok) {
      const data = await res.json();
      setYtPlaylists(data);
    }
    setYtLoading(false);
  };

  const logout = async () => {
    await fetch("http://127.0.0.1:8000/api/users/logout", {
      method: "POST",
      credentials: "include",
    });
    window.location.href = "/login";
  };

  const ensureAuthenticated = async () => {
    const res = await fetch("http://127.0.0.1:8000/api/users/me", {
      credentials: "include",
    });
    if (!res.ok) {
      window.location.href = "/login";
      return;
    }
    const data: CurrentUser = await res.json();
    setUser(data);
    setAuthChecked(true);
    await fetchPlaylists();
    await fetchYouTubePlaylists();
  };

  useEffect(() => {
    ensureAuthenticated();
  }, []);

  if (!authChecked) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-gray-700 text-sm">Checking session...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-900">Playlist Bridge</h1>
          {user && (
            <div className="relative">
              <button
                onClick={() => setProfileOpen((p) => !p)}
                className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-gray-100 transition-colors"
              >
                {user.picture ? (
                  <img
                    src={user.picture}
                    alt={user.name}
                    className="w-9 h-9 rounded-full object-cover"
                    referrerPolicy="no-referrer"
                  />
                ) : (
                  <div className="w-9 h-9 rounded-full bg-gray-200 flex items-center justify-center text-sm font-semibold text-gray-700">
                    {user.name?.charAt(0)?.toUpperCase() || "U"}
                  </div>
                )}
                <div className="flex flex-col items-start">
                  <span className="text-sm font-medium text-gray-900">
                    {user.name}
                  </span>
                  <span className="text-xs text-gray-500">{user.email}</span>
                </div>
                <svg
                  className={`w-4 h-4 text-gray-500 transition-transform ${
                    profileOpen ? "rotate-180" : ""
                  }`}
                  viewBox="0 0 20 20"
                  fill="currentColor"
                >
                  <path
                    fillRule="evenodd"
                    d="M5.23 7.21a.75.75 0 011.06.02L10 10.94l3.71-3.71a.75.75 0 111.06 1.06l-4.24 4.25a.75.75 0 01-1.06 0L5.21 8.29a.75.75 0 01.02-1.08z"
                    clipRule="evenodd"
                  />
                </svg>
              </button>
              {profileOpen && (
                <div className="absolute right-0 mt-2 w-48 bg-white border border-gray-200 rounded-lg shadow-md py-2 z-20">
                  <button
                    onClick={logout}
                    className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                  >
                    Logout
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Account Connections */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Connect Accounts
          </h2>
          <div className="flex flex-wrap gap-3">
            <button
              onClick={connectSpotify}
              className="px-5 py-2.5 bg-[#1DB954] text-white rounded-lg font-medium hover:bg-[#1ed760] transition-colors duration-200 flex items-center gap-2"
            >
              <svg
                className="w-5 h-5"
                viewBox="0 0 24 24"
                fill="currentColor"
              >
                <path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-11.939-1.38-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141C9.6 9.9 15 10.561 18.72 12.84c.361.181.54.78.241 1.2zm.12-3.36C15.24 8.4 8.82 8.16 5.16 9.301c-.6.179-1.2-.181-1.38-.721-.18-.601.18-1.2.72-1.381 4.26-1.26 11.28-1.02 15.721 1.621.539.3.719 1.02.42 1.56-.299.421-1.02.599-1.559.3z" />
              </svg>
              Connect Spotify
            </button>

            <button
              onClick={connectYouTube}
              className="px-5 py-2.5 bg-[#FF0000] text-white rounded-lg font-medium hover:bg-[#ff1a1a] transition-colors duration-200 flex items-center gap-2"
            >
              <svg
                className="w-5 h-5"
                viewBox="0 0 24 24"
                fill="currentColor"
              >
                <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z" />
              </svg>
              Connect YouTube
            </button>
          </div>
        </div>

        {/* Status Message */}
        {message && (
          <div
            className={`mb-6 p-4 rounded-lg border ${
              messageType === "success"
                ? "bg-green-50 border-green-200 text-green-800"
                : "bg-blue-50 border-blue-200 text-blue-800"
            }`}
          >
            <div className="flex items-center gap-2">
              {messageType === "success" ? (
                <svg
                  className="w-5 h-5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M5 13l4 4L19 7"
                  />
                </svg>
              ) : (
                <svg
                  className="w-5 h-5 animate-spin"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  />
                </svg>
              )}
              <span className="font-medium">{message}</span>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Spotify Playlists */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center gap-2 mb-4">
              <div className="w-8 h-8 bg-[#1DB954] rounded-full flex items-center justify-center">
                <svg
                  className="w-5 h-5 text-white"
                  viewBox="0 0 24 24"
                  fill="currentColor"
                >
                  <path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-11.939-1.38-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141C9.6 9.9 15 10.561 18.72 12.84c.361.181.54.78.241 1.2zm.12-3.36C15.24 8.4 8.82 8.16 5.16 9.301c-.6.179-1.2-.181-1.38-.721-.18-.601.18-1.2.72-1.381 4.26-1.26 11.28-1.02 15.721 1.621.539.3.719 1.02.42 1.56-.299.421-1.02.599-1.559.3z" />
                </svg>
              </div>
              <h2 className="text-lg font-semibold text-gray-900">
                Spotify Playlists
              </h2>
            </div>

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                New YouTube playlist title
              </label>
              <input
                value={ytTargetTitle}
                onChange={(e) => setYtTargetTitle(e.target.value)}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#1DB954] focus:border-transparent text-sm"
                placeholder="Transferred from Spotify"
              />
            </div>

            {loading && (
              <div className="flex items-center justify-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#1DB954]"></div>
              </div>
            )}

            {!loading && playlists.length === 0 && (
              <p className="text-gray-500 text-center py-8">
                No Spotify playlists found. Connect your Spotify account to get
                started.
              </p>
            )}

            <ul className="space-y-2">
              {playlists.map((p) => (
                <li
                  key={p.id}
                  className="flex justify-between items-center p-3 rounded-lg border border-gray-200 hover:border-gray-300 hover:bg-gray-50 transition-colors"
                >
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-gray-900 truncate">
                      {p.name}
                    </p>
                    <p className="text-sm text-gray-500">
                      {p.tracks.total} {p.tracks.total === 1 ? "track" : "tracks"}
                    </p>
                  </div>

                  <button
                    onClick={() => transfer(p.id)}
                    className="ml-4 px-4 py-2 bg-[#FF0000] text-white text-sm font-medium rounded-lg hover:bg-[#ff1a1a] transition-colors duration-200 whitespace-nowrap"
                  >
                    Transfer
                  </button>
                </li>
              ))}
            </ul>
          </div>

          {/* YouTube Playlists */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center gap-2 mb-4">
              <div className="w-8 h-8 bg-[#FF0000] rounded-full flex items-center justify-center">
                <svg
                  className="w-5 h-5 text-white"
                  viewBox="0 0 24 24"
                  fill="currentColor"
                >
                  <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z" />
                </svg>
              </div>
              <h2 className="text-lg font-semibold text-gray-900">
                YouTube Playlists
              </h2>
            </div>

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                New Spotify playlist title
              </label>
              <input
                value={spotifyTargetTitle}
                onChange={(e) => setSpotifyTargetTitle(e.target.value)}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#FF0000] focus:border-transparent text-sm"
                placeholder="Transferred from YouTube"
              />
            </div>

            {ytLoading && (
              <div className="flex items-center justify-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#FF0000]"></div>
              </div>
            )}

            {!ytLoading && ytPlaylists.length === 0 && (
              <p className="text-gray-500 text-center py-8">
                No YouTube playlists found. Connect your YouTube account to get
                started.
              </p>
            )}

            <ul className="space-y-2">
              {ytPlaylists.map((p) => (
                <li
                  key={p.id}
                  className="flex justify-between items-center p-3 rounded-lg border border-gray-200 hover:border-gray-300 hover:bg-gray-50 transition-colors"
                >
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-gray-900 truncate">
                      {p.name}
                    </p>
                    <p className="text-sm text-gray-500">
                      {p.count} {p.count === 1 ? "video" : "videos"}
                    </p>
                  </div>

                  <button
                    onClick={() => transferYouTubeToSpotify(p.id)}
                    className="ml-4 px-4 py-2 bg-[#1DB954] text-white text-sm font-medium rounded-lg hover:bg-[#1ed760] transition-colors duration-200 whitespace-nowrap"
                  >
                    Transfer
                  </button>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </main>
    </div>
  );
}
