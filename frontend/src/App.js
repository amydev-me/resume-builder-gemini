// frontend/src/App.js

import React, { useState, useEffect, useRef } from 'react';
import {
  getUserProfile,
  setupUserProfile,
  generateResume,
  submitFeedback,
  getSuggestions,
  logoutUser,
  uploadResumeFile
} from './services/api';

// NEW Imports for Router
import { BrowserRouter as Router, Routes, Route, useNavigate } from 'react-router-dom';

// Page Components
import LoginPage from './pages/LoginPage';     // NEW
import RegisterPage from './pages/RegisterPage'; // NEW
import DashboardPage from './pages/DashboardPage';

// Global Styles
import './index.css';
import JobHistorySection from './sections/JobHistorySection'; // Import the new component
import EducationSection from './sections/EducationSection'; // NEW
import SkillsSection from './sections/SkillsSection';       // NEW
import CertificationsSection from './sections/CertificationSection';
// Main App Component (wrapped by Router later)
function AppContent() {
  const [userProfile, setUserProfile] = useState(null);
  const [generatedResume, setGeneratedResume] = useState(null);
  const [feedbackText, setFeedbackText] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [targetJobDescription, setTargetJobDescription] = useState('');

  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);

  const [initialCoreData, setInitialCoreData] = useState({
    full_name: '',
    email: '',
    phone: '',
    linkedin: '',
    years_of_experience: 0,
    job_history: [], // CHANGE THIS from '[]' to []
    education: [],       // <<< CHANGED
    skills: [],          // <<< CHANGED
    certifications: [],  // <<< CHANGED
  });

  // ... inside useEffect for fetchUserProfile ...
  

  const fileInputRef = useRef(null);
  const [selectedFile, setSelectedFile] = useState(null);

  const navigate = useNavigate();

  // Initial check for token on app load
  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token) {
      setIsLoggedIn(true);
      fetchUserProfile();
    } else {
      navigate('/login'); // Redirect to login if no token
    }
  }, []);

  // Fetch profile when login status changes
  useEffect(() => {
    if (isLoggedIn) {
      fetchUserProfile();
      // Ensure we are on the dashboard or a dashboard sub-route
      if (window.location.pathname === '/' || window.location.pathname === '/login' || window.location.pathname === '/register') {
         navigate('/dashboard');
      }
    } else {
      setUserProfile(null);
      setGeneratedResume(null);
      setInitialCoreData({
        full_name: '', email: '', phone: '', linkedin: '', years_of_experience: 0,
        job_history: '[]', education: '[]', skills: '[]', certifications: '[]',
      });
      setCurrentUser(null);
      navigate('/login'); // Navigate to login page on logout
    }
  }, [isLoggedIn, navigate]);

  const fetchUserProfile = async () => {
    setLoading(true);
    setError(null);
    try {
      const profile = await getUserProfile();
      setUserProfile(profile);

      // Attempt to get username
      if (profile && profile.owner) { // Simplified check for owner
          setCurrentUser(prev => ({ ...prev, username: profile.core_data?.full_name || profile.owner.username || 'User' }));
      } else {
          setCurrentUser(prev => ({ ...prev, username: 'User' }));
      }

      // Initialize a temporary object to build the new state data
      let currentCoreData = {
          full_name: '',
          email: '',
          phone: '',
          linkedin: '',
          years_of_experience: 0,
          job_history: [],
          education: [],
          skills: [],
          certifications: [],
      };

      if (profile && profile.core_data) {
          currentCoreData.full_name = profile.core_data.full_name || '';
          currentCoreData.email = profile.core_data.email || '';
          currentCoreData.phone = profile.core_data.phone || '';
          currentCoreData.linkedin = profile.core_data.linkedin || '';
          currentCoreData.years_of_experience = Number(profile.core_data.years_of_experience) || 0;

          // --- Robust Parsing for Array Fields (job_history, education, skills, certifications) ---
          const arrayFields = ['job_history', 'education', 'skills', 'certifications'];

          arrayFields.forEach(key => {
              let parsedArray = [];
              const rawData = profile.core_data[key];

              try {
                  if (typeof rawData === 'string' && rawData.trim() !== '') {
                      // Attempt to parse if it's a non-empty string
                      parsedArray = JSON.parse(rawData);
                  } else if (Array.isArray(rawData)) {
                      // If it's already an array, use it directly
                      parsedArray = rawData;
                  }
                  // Ensure the result is an array
                  if (!Array.isArray(parsedArray)) {
                      console.warn(`${key} from backend was not a valid array/JSON string, defaulting to empty array.`);
                      parsedArray = [];
                  }
              } catch (parseError) {
                  console.error(`Error parsing ${key} from backend:`, parseError);
                  parsedArray = []; // Fallback to empty array on parse error
              }

              // --- Specific handling for job_history 'responsibilities' vs 'description' ---
              if (key === 'job_history') {
                  parsedArray = parsedArray.map(job => {
                      // If job has 'responsibilities' array, use it.
                      // Else if it has 'description' string, convert it to a single-item responsibilities array.
                      // Otherwise, default to empty array.
                      const responsibilities = Array.isArray(job.responsibilities)
                          ? job.responsibilities
                          : (typeof job.description === 'string' && job.description.trim() !== '' ? [job.description] : []);

                      // Return the job object with the 'responsibilities' field correctly set,
                      // and remove 'description' if it exists to clean up.
                      const newJob = { ...job, responsibilities };
                      delete newJob.description; // Remove old description field if it was there
                      return newJob;
                  });
              }
              // --- End specific handling for job_history ---

              currentCoreData[key] = parsedArray;
          });
          // --- End Robust Parsing ---
      }

      setInitialCoreData(currentCoreData); // Set the state once with the fully parsed object

    } catch (err) {
      setError(err.message || 'Failed to fetch user profile.');
      console.error(err);
      setIsLoggedIn(false);
      logoutUser(); // Ensure logout on fetch error
    } finally {
      setLoading(false);
    }
  };

  const handleInitialDataChange = (e) => {
    const { name, value } = e.target;
    setInitialCoreData(prev => ({ ...prev, [name]: value }));
  };

  const handleJobHistoryChange = (newJobHistory) => {
    setInitialCoreData(prev => ({ ...prev, job_history: newJobHistory }));
  };
  const handleEducationChange = (newEducation) => {
    setInitialCoreData(prev => ({ ...prev, education: newEducation }));
  };

  const handleSkillsChange = (newSkills) => {
    setInitialCoreData(prev => ({ ...prev, skills: newSkills }));
  };

  const handleCertificationsChange = (newCertifications) => {
    setInitialCoreData(prev => ({ ...prev, certifications: newCertifications }));
  };

  const handleSetupProfile = async () => {
    setLoading(true);
    setError(null);
    try {
      const parsedCoreData = {
        ...initialCoreData,
        job_history: JSON.stringify(initialCoreData.job_history),
        education: JSON.stringify(initialCoreData.education), // <<< CHANGED
        skills: JSON.stringify(initialCoreData.skills),       // <<< CHANGED
        certifications: JSON.stringify(initialCoreData.certifications), // <<< CHANGED
        years_of_experience: Number(initialCoreData.years_of_experience) || 0,
      };
      await setupUserProfile({ core_data: parsedCoreData });
      await fetchUserProfile();
      alert('User profile updated successfully!');
    } catch (err) {
      setError('Failed to set up user profile. Ensure JSON fields are valid and years of experience is a number.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateResume = async () => {
    setLoading(true);
    setError(null);
    setGeneratedResume(null);
    try {
      const response = await generateResume(targetJobDescription);
      setGeneratedResume(response);
    } catch (err) {
      setError(err.message || 'Failed to generate resume.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitFeedback = async () => {
    setLoading(true);
    setError(null);
    try {
      if (!generatedResume) {
        throw new Error("No resume generated to provide feedback on.");
      }
      if (!feedbackText.trim()) {
        throw new Error("Feedback comment cannot be empty.");
      }

      const feedbackData = {
        resume_version_id: generatedResume.id,
        feedback_items: [
          {
            section: "overall",
            text: generatedResume.content,
            comment: feedbackText.trim(),
            is_positive: true
          }
        ],
        target_job_description: targetJobDescription
      };
      await submitFeedback(feedbackData);
      alert('Feedback submitted! Generate a new resume to see changes.');
      setFeedbackText('');
    } catch (err) {
      setError(`Failed to submit feedback: ${err.message}`);
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleGetSuggestions = async () => {
    setLoading(true);
    setError(null);
    try {
        const suggestionsResponse = await getSuggestions(targetJobDescription);
        alert("Proactive Suggestions:\n\n" + suggestionsResponse.suggestions.map(s => `${s.category}: ${s.suggestion}`).join('\n\n'));
    } catch (err) {
        setError(err.message || 'Failed to get suggestions.');
        console.error(err);
    } finally {
        setLoading(false);
    }
  };

  const handleLoginSuccess = (loggedInUsername) => {
    setIsLoggedIn(true);
    setCurrentUser({ username: loggedInUsername });
    // Navigation handled by useEffect
  };

  const handleRegisterSuccess = () => {
    navigate('/login'); // After successful registration, go to login page
  };

  const handleLogout = () => {
    logoutUser();
    setIsLoggedIn(false);
    // Navigation handled by useEffect
  };

  const handleFileChange = (e) => {
    setSelectedFile(e.target.files[0]);
  };

  const handleUploadResume = async () => {
    if (!selectedFile) {
      alert("Please select a file to upload.");
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const response = await uploadResumeFile(selectedFile);
      alert(response.message);
      await fetchUserProfile();
      setSelectedFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    } catch (err) {
      setError(err.message || 'Failed to upload resume.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // The actual dashboard content, extracted to a render function for clarity
  const renderDashboardContent = () => (
    <>
      <div className="section">
        <h2 className="text-2xl font-bold text-gray-800 mb-4">1. User Profile Setup</h2>
        <p className="text-gray-600 mb-6">Edit your core data. Use valid JSON for lists.</p>

        <div className="resume-upload-section bg-gray-50 p-4 rounded-lg mb-6 border border-gray-200">
            <h3 className="text-lg font-semibold text-gray-800 mb-3">Upload Your Resume (PDF/DOCX)</h3>
            <input
                type="file"
                accept=".pdf,.docx"
                onChange={handleFileChange}
                ref={fileInputRef}
                className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
            />
            <button onClick={handleUploadResume} disabled={loading || !selectedFile} className="mt-4 bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-4 rounded transition duration-300 ease-in-out">
                Upload & Auto-Fill Profile
            </button>
            {selectedFile && <p className="mt-2 text-sm text-gray-600">Selected: {selectedFile.name}</p>}
            <p className="text-sm text-gray-500 mt-2">
                Upload a PDF or DOCX resume to automatically populate your profile fields below.
            </p>
        </div>

        <div className="space-y-4">
          <label className="block text-gray-700 font-medium">Full Name: <input type="text" name="full_name" value={initialCoreData.full_name} onChange={handleInitialDataChange} className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50" /></label>
          <label className="block text-gray-700 font-medium">Email: <input type="text" name="email" value={initialCoreData.email} onChange={handleInitialDataChange} className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50" /></label>
          <label className="block text-gray-700 font-medium">Phone: <input type="text" name="phone" value={initialCoreData.phone} onChange={handleInitialDataChange} className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50" /></label>
          <label className="block text-gray-700 font-medium">LinkedIn: <input type="text" name="linkedin" value={initialCoreData.linkedin} onChange={handleInitialDataChange} className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50" /></label>
          <label className="block text-gray-700 font-medium">Years of Experience: <input type="number" name="years_of_experience" value={initialCoreData.years_of_experience} onChange={handleInitialDataChange} className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50" /></label>
          <JobHistorySection
            jobHistory={initialCoreData.job_history}
            onJobHistoryChange={handleJobHistoryChange}
          />
        {/* NEW SECTIONS */}
        <EducationSection
            education={initialCoreData.education}
            onEducationChange={handleEducationChange}
          />
          <SkillsSection
            skills={initialCoreData.skills}
            onSkillsChange={handleSkillsChange}
          />
          <CertificationsSection
            certifications={initialCoreData.certifications}
            onCertificationsChange={handleCertificationsChange}
          />

          <button onClick={handleSetupProfile} disabled={loading} className="bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-4 rounded transition duration-300 ease-in-out">Update User Profile</button>
        </div>
        <h3 className="mt-6 text-xl font-semibold text-gray-800">Current Learned Preferences:</h3>
        <pre className="bg-gray-100 p-4 rounded-md overflow-auto max-h-96 text-sm text-gray-700">{userProfile ? JSON.stringify(userProfile.learned_preferences, null, 2) : 'Loading...'}</pre>
      </div>

      <div className="section">
        <h2 className="text-2xl font-bold text-gray-800 mb-4">2. Generate Resume</h2>
        <div className="mb-4">
          <label className="block mb-2 text-gray-700 font-medium">Target Job Description (Optional, for contextual generation):</label>
          <textarea
            value={targetJobDescription}
            onChange={(e) => setTargetJobDescription(e.target.value)}
            placeholder="Paste a job description here to tailor the resume to it. Example: 'Senior Software Engineer with expertise in AI and cloud platforms.'"
            rows="5"
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50"
          ></textarea>
        </div>
        <button onClick={handleGenerateResume} disabled={loading} className="bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-4 rounded transition duration-300 ease-in-out">Generate New Resume</button>
        <button onClick={handleGetSuggestions} disabled={loading} className="ml-4 bg-purple-500 hover:bg-purple-600 text-white font-bold py-2 px-4 rounded transition duration-300 ease-in-out">Get Proactive Suggestions</button>
        {generatedResume && (
          <div className="mt-6">
            <h3 className="text-xl font-semibold text-gray-800 mb-2">Generated Resume: {generatedResume.version_name}</h3>
            <pre className="bg-gray-100 p-4 rounded-md overflow-auto max-h-96 text-sm text-gray-700">{generatedResume.content}</pre>
          </div>
        )}
        {generatedResume && generatedResume.critique && (
            <div className="critique-results bg-yellow-100 border border-yellow-200 p-4 rounded-md mt-6">
                <h3 className="text-lg font-semibold text-yellow-800">AI's Self-Critique: {generatedResume.critique.overall_assessment}</h3>
                {generatedResume.critique.has_issues ? (
                    <div className="mt-2">
                        <p className="font-bold text-orange-700">Issues Identified:</p>
                        <ul className="list-disc list-inside mt-2 space-y-1">
                            {generatedResume.critique.issues.map((issue, index) => (
                                <li key={index}>
                                    <strong className="text-yellow-900">{issue.category} ({issue.severity}):</strong> {issue.description}
                                    {issue.suggested_action && ` (Action: ${issue.suggested_action})`}
                                    {issue.relevant_rule_id && ` (Rule ID: ${issue.relevant_rule_id})`}
                                </li>
                            ))}
                        </ul>
                    </div>
                ) : (
                    <p className="text-green-700 font-bold mt-2">No major issues identified in this draft.</p>
                )}
            </div>
        )}
      </div>

      {generatedResume && (
        <div className="section">
          <h2 className="text-2xl font-bold text-gray-800 mb-4">3. Provide Feedback</h2>
          <textarea
            value={feedbackText}
            onChange={(e) => setFeedbackText(e.target.value)}
            placeholder="e.g., 'Make the summary more concise', 'Use stronger action verbs for experience section'. If related to JD, mention it here."
            rows="4"
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50"
          ></textarea>
          <button onClick={handleSubmitFeedback} disabled={loading} className="mt-4 bg-indigo-500 hover:bg-indigo-600 text-white font-bold py-2 px-4 rounded transition duration-300 ease-in-out">Submit Feedback</button>
        </div>
      )}

      <p className="text-gray-600 text-sm mt-6 mb-4">
        **Note:** To see the effect of feedback, submit feedback, then click "Generate New Resume" again.
        The system should apply your new preferences.
      </p>
    </>
  );

  return (
    <div className="App">
      {/* Global error and loading indicators, outside routing */}
      {error && <p className="text-red-500 bg-red-100 p-2 rounded-md mb-4">{error}</p>}
      {loading && <p className="text-blue-500">Loading...</p>}

      <Routes>
        <Route
          path="/login"
          element={<LoginPage onLoginSuccess={handleLoginSuccess} setLoading={setLoading} setError={setError} loading={loading} error={error} />}
        />
        <Route
          path="/register"
          element={<RegisterPage onRegisterSuccess={handleRegisterSuccess} setLoading={setLoading} setError={setError} loading={loading} error={error} />}
        />
        {/* Protected Dashboard Route */}
        <Route
          path="/dashboard"
          element={isLoggedIn ? (
            <DashboardPage currentUser={currentUser} onLogout={handleLogout}>
              {renderDashboardContent()} {/* Render the dashboard content */}
            </DashboardPage>
          ) : (
            // Redirect to login if trying to access dashboard directly without login
            <p className="text-center text-xl text-gray-700 mt-20">Please log in to access the dashboard.</p>
          )}
        />
        {/* Redirect root path to login for fresh visits or unauthenticated users */}
        <Route path="/" element={<p className="text-center text-xl text-gray-700 mt-20">Redirecting to login...</p>} />
      </Routes>
    </div>
  );
}

// Wrapper for BrowserRouter
function AppWrapper() {
  return (
    <Router>
      <AppContent />
    </Router>
  );
}

export default AppWrapper; // Export AppWrapper