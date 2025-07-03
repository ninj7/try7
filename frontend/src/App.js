import React, { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [url, setUrl] = useState("");
  const [videoInfo, setVideoInfo] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [selectedFormat, setSelectedFormat] = useState("");
  const [downloading, setDownloading] = useState(false);

  const handleUrlSubmit = async (e) => {
    e.preventDefault();
    if (!url.trim()) {
      setError("Please enter a YouTube URL");
      return;
    }

    setLoading(true);
    setError("");
    setVideoInfo(null);

    try {
      const response = await axios.post(`${API}/video-info`, { url });
      setVideoInfo(response.data);
      if (response.data.formats && response.data.formats.length > 0) {
        setSelectedFormat(response.data.formats[0].format_id);
      }
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to fetch video information");
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async () => {
    if (!selectedFormat) {
      setError("Please select a format");
      return;
    }

    setDownloading(true);
    setError("");

    try {
      const response = await axios.post(
        `${API}/download`,
        { url, format_id: selectedFormat },
        { responseType: 'blob' }
      );

      // Create download link
      const downloadUrl = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = downloadUrl;
      
      // Get filename from response headers
      const contentDisposition = response.headers['content-disposition'];
      let filename = 'video.mp4';
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="(.+)"/);
        if (filenameMatch) {
          filename = filenameMatch[1];
        }
      }
      
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(downloadUrl);
    } catch (err) {
      setError(err.response?.data?.detail || "Download failed");
    } finally {
      setDownloading(false);
    }
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return "Unknown size";
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
  };

  const formatDuration = (seconds) => {
    if (!seconds) return "Unknown";
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-900 via-blue-800 to-indigo-900">
      {/* Hero Section */}
      <div className="relative overflow-hidden">
        {/* Background Image */}
        <div 
          className="absolute inset-0 bg-cover bg-center opacity-20"
          style={{
            backgroundImage: `url('https://images.unsplash.com/photo-1548328928-34db1c5fcc1f?auto=format&fit=crop&w=1920&q=80')`
          }}
        />
        
        {/* Overlay */}
        <div className="absolute inset-0 bg-black bg-opacity-50" />
        
        {/* Content */}
        <div className="relative z-10 container mx-auto px-4 py-16">
          <div className="text-center mb-12">
            <h1 className="text-5xl md:text-6xl font-bold text-white mb-6 leading-tight">
              YouTube Video <span className="text-blue-400">Downloader</span>
            </h1>
            <p className="text-xl text-blue-100 mb-8 max-w-2xl mx-auto">
              Download your favorite YouTube videos in high quality. Fast, free, and easy to use.
            </p>
          </div>

          {/* URL Input Form */}
          <div className="max-w-4xl mx-auto">
            <form onSubmit={handleUrlSubmit} className="mb-8">
              <div className="flex flex-col md:flex-row gap-4">
                <input
                  type="text"
                  placeholder="Paste YouTube URL here..."
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  className="flex-1 px-6 py-4 rounded-lg text-lg border-2 border-blue-300 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50"
                  disabled={loading}
                />
                <button
                  type="submit"
                  disabled={loading}
                  className="bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white px-8 py-4 rounded-lg font-semibold text-lg transition-colors duration-200 flex items-center justify-center min-w-[120px]"
                >
                  {loading ? (
                    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-white" />
                  ) : (
                    "Get Video"
                  )}
                </button>
              </div>
            </form>

            {/* Error Message */}
            {error && (
              <div className="bg-red-500 bg-opacity-90 text-white p-4 rounded-lg mb-6 backdrop-blur-sm">
                {error}
              </div>
            )}

            {/* Video Info Card */}
            {videoInfo && (
              <div className="bg-white bg-opacity-95 backdrop-blur-sm rounded-xl shadow-2xl p-8 mb-8">
                <div className="flex flex-col md:flex-row gap-6">
                  {/* Video Thumbnail */}
                  {videoInfo.thumbnail && (
                    <div className="flex-shrink-0">
                      <img
                        src={videoInfo.thumbnail}
                        alt="Video thumbnail"
                        className="w-full md:w-80 h-48 object-cover rounded-lg shadow-lg"
                      />
                    </div>
                  )}

                  {/* Video Details */}
                  <div className="flex-1">
                    <h2 className="text-2xl font-bold text-gray-800 mb-4 leading-tight">
                      {videoInfo.title}
                    </h2>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                      {videoInfo.uploader && (
                        <div className="flex items-center">
                          <span className="text-gray-600 font-medium mr-2">Channel:</span>
                          <span className="text-gray-800">{videoInfo.uploader}</span>
                        </div>
                      )}
                      
                      {videoInfo.duration && (
                        <div className="flex items-center">
                          <span className="text-gray-600 font-medium mr-2">Duration:</span>
                          <span className="text-gray-800">{formatDuration(videoInfo.duration)}</span>
                        </div>
                      )}
                      
                      {videoInfo.view_count && (
                        <div className="flex items-center">
                          <span className="text-gray-600 font-medium mr-2">Views:</span>
                          <span className="text-gray-800">{videoInfo.view_count.toLocaleString()}</span>
                        </div>
                      )}
                    </div>

                    {/* Format Selection */}
                    <div className="mb-6">
                      <label className="block text-gray-700 font-medium mb-3">
                        Select Quality:
                      </label>
                      <select
                        value={selectedFormat}
                        onChange={(e) => setSelectedFormat(e.target.value)}
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      >
                        {videoInfo.formats.map((format) => (
                          <option key={format.format_id} value={format.format_id}>
                            {format.quality} - {format.ext.toUpperCase()} 
                            {format.filesize && ` (${formatFileSize(format.filesize)})`}
                          </option>
                        ))}
                      </select>
                    </div>

                    {/* Download Button */}
                    <button
                      onClick={handleDownload}
                      disabled={downloading || !selectedFormat}
                      className="w-full bg-green-600 hover:bg-green-700 disabled:bg-green-400 text-white py-4 px-6 rounded-lg font-semibold text-lg transition-colors duration-200 flex items-center justify-center"
                    >
                      {downloading ? (
                        <>
                          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-white mr-3" />
                          Downloading...
                        </>
                      ) : (
                        <>
                          <svg className="w-6 h-6 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                          </svg>
                          Download Video
                        </>
                      )}
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-black bg-opacity-50 text-white py-8">
        <div className="container mx-auto px-4 text-center">
          <p className="text-blue-100">
            © 2025 YouTube Video Downloader - Fast, Free, and Easy to Use
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;