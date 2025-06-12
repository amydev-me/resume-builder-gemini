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
import ReactMarkdown from 'react-markdown'; // NEW
import remarkGfm from 'remark-gfm';       // NEW
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
  const totalSteps = 5; // We defined 5 steps: Personal, Work, Education, Skills/Cert, Generation
  const [uploadSuccess, setUploadSuccess] = useState(false); // NEW
  const [uploadError, setUploadError] = useState(null);    // NEW
  const [initialRequest, setInitialRequest] = useState(''); // NEW
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
  
  const [currentStep, setCurrentStep] = useState(1); // Start at Step 1

  const fileInputRef = useRef(null);
  const [selectedFile, setSelectedFile] = useState(null);

  const navigate = useNavigate();
  const nextStep = () => {
    setCurrentStep(prev => Math.min(prev + 1, totalSteps));
  };

  const prevStep = () => {
      setCurrentStep(prev => Math.max(prev - 1, 1));
  };
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
    // Main container for the entire two-column layout
    // flex-grow makes it take available space, min-h-screen ensures it pushes footer down
    <div className="flex flex-col md:flex-row flex-grow min-h-[calc(100vh-64px)] bg-gray-50"> {/* min-h-screen to ensure it spans full height, minus header if fixed */}

        {/* Left Column: Input Forms with Stepper */}
        <div className="w-full md:w-1/2 lg:w-1/2 p-6 overflow-y-auto border-r border-gray-200"> {/* Added overflow-y-auto for scrollability */}
            <h2 className="text-3xl font-bold text-gray-900 mb-6 text-center">Resume Builder Dashboard</h2>

            {/* Stepper Navigation/Indicators */}
            <div className="mb-8 p-4 bg-white rounded-lg shadow-md"> {/* Added background and shadow for stepper */}
                <div className="flex justify-between items-center text-sm font-medium text-gray-600">
                    {/* Step 1: Personal Information & Upload */}
                    <div className={`flex flex-col items-center p-2 rounded-lg ${currentStep === 1 ? 'text-blue-600 font-bold' : ''}`}>
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center border-2 ${currentStep === 1 ? 'border-blue-600 bg-blue-100' : 'border-gray-300 bg-gray-100'}`}>
                            <span className={currentStep === 1 ? 'text-blue-600' : 'text-gray-500'}>1</span>
                        </div>
                        <span className="mt-1 text-center text-xs sm:text-sm">Personal Info & Upload</span>
                    </div>
                    <div className="flex-1 border-t-2 border-gray-200 -mt-8"></div> {/* Divider */}

                    {/* Step 2: Work Experience */}
                    <div className={`flex flex-col items-center p-2 rounded-lg ${currentStep === 2 ? 'text-blue-600 font-bold' : ''}`}>
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center border-2 ${currentStep === 2 ? 'border-blue-600 bg-blue-100' : 'border-gray-300 bg-gray-100'}`}>
                            <span className={currentStep === 2 ? 'text-blue-600' : 'text-gray-500'}>2</span>
                        </div>
                        <span className="mt-1 text-center text-xs sm:text-sm">Work Experience</span>
                    </div>
                    <div className="flex-1 border-t-2 border-gray-200 -mt-8"></div> {/* Divider */}

                    {/* Step 3: Education */}
                    <div className={`flex flex-col items-center p-2 rounded-lg ${currentStep === 3 ? 'text-blue-600 font-bold' : ''}`}>
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center border-2 ${currentStep === 3 ? 'border-blue-600 bg-blue-100' : 'border-gray-300 bg-gray-100'}`}>
                            <span className={currentStep === 3 ? 'text-blue-600' : 'text-gray-500'}>3</span>
                        </div>
                        <span className="mt-1 text-center text-xs sm:text-sm">Education</span>
                    </div>
                    <div className="flex-1 border-t-2 border-gray-200 -mt-8"></div> {/* Divider */}

                    {/* Step 4: Skills & Certifications */}
                    <div className={`flex flex-col items-center p-2 rounded-lg ${currentStep === 4 ? 'text-blue-600 font-bold' : ''}`}>
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center border-2 ${currentStep === 4 ? 'border-blue-600 bg-blue-100' : 'border-gray-300 bg-gray-100'}`}>
                            <span className={currentStep === 4 ? 'text-blue-600' : 'text-gray-500'}>4</span>
                        </div>
                        <span className="mt-1 text-center text-xs sm:text-sm">Skills & Certs</span>
                    </div>
                    <div className="flex-1 border-t-2 border-gray-200 -mt-8"></div> {/* Divider */}

                    {/* Step 5: Generate & Review */}
                    <div className={`flex flex-col items-center p-2 rounded-lg ${currentStep === 5 ? 'text-blue-600 font-bold' : ''}`}>
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center border-2 ${currentStep === 5 ? 'border-blue-600 bg-blue-100' : 'border-gray-300 bg-gray-100'}`}>
                            <span className={currentStep === 5 ? 'text-blue-600' : 'text-gray-500'}>5</span>
                        </div>
                        <span className="mt-1 text-center text-xs sm:text-sm">Generate & Review</span>
                    </div>
                </div>
            </div>

            {/* Content Area for each step */}
            <div className="py-6 space-y-8"> {/* Added space-y-8 for consistent vertical spacing between sections */}
                {/* Step 1: Personal Information & Upload */}
                {currentStep === 1 && (
                    <div className="bg-white p-6 rounded-lg shadow-md"> {/* Add card styling back for individual step sections */}
                        <h3 className="text-2xl font-semibold text-gray-800 mb-4">1. Personal Information & Upload</h3>

                        {/* Resume Upload section */}
                        <div className="mb-6 bg-gray-50 p-4 rounded-md border border-gray-200">
                            <h4 className="text-lg font-semibold text-gray-700 mb-2">Upload Existing Resume (Optional)</h4>
                            <p className="text-sm text-gray-600 mb-3">Upload a PDF or DOCX resume to automatically populate your profile fields below.</p>
                            <input type="file" onChange={handleFileChange} className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"/>
                            <button onClick={handleUploadResume} disabled={!selectedFile || loading} className="mt-3 bg-green-500 hover:bg-green-600 text-white font-bold py-2 px-4 rounded-md transition duration-300 ease-in-out disabled:opacity-50">
                                {loading ? 'Uploading...' : 'Upload Resume'}
                            </button>
                            {uploadSuccess && <p className="text-green-600 text-sm mt-2">Resume uploaded successfully!</p>}
                            {uploadError && <p className="text-red-600 text-sm mt-2">{uploadError}</p>}
                        </div>

                        {/* Personal Information Fields */}
                        <div className="space-y-4">
                            <label className="block text-gray-700 font-medium">Full Name: <input type="text" name="full_name" value={initialCoreData.full_name} onChange={handleInitialDataChange} className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50" /></label>
                            <label className="block text-gray-700 font-medium">Email: <input type="text" name="email" value={initialCoreData.email} onChange={handleInitialDataChange} className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50" /></label>
                            <label className="block text-gray-700 font-medium">Phone: <input type="text" name="phone" value={initialCoreData.phone} onChange={handleInitialDataChange} className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-300 focus:ring focus:ring-ring-indigo-200 focus:ring-opacity-50" /></label>
                            <label className="block text-gray-700 font-medium">LinkedIn: <input type="text" name="linkedin" value={initialCoreData.linkedin} onChange={handleInitialDataChange} className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50" /></label>
                            <label className="block text-gray-700 font-medium">Years of Experience: <input type="number" name="years_of_experience" value={initialCoreData.years_of_experience} onChange={handleInitialDataChange} className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50" /></label>
                        </div>
                    </div>
                )}

                {/* Step 2: Work Experience */}
                {currentStep === 2 && (
                    <div className="bg-white p-6 rounded-lg shadow-md"> {/* Add card styling */}
                        <h3 className="text-2xl font-semibold text-gray-800 mb-4">2. Work Experience</h3>
                        <JobHistorySection
                            jobHistory={initialCoreData.job_history}
                            onJobHistoryChange={handleJobHistoryChange}
                        />
                    </div>
                )}

                {/* Step 3: Education */}
                {currentStep === 3 && (
                    <div className="bg-white p-6 rounded-lg shadow-md"> {/* Add card styling */}
                        <h3 className="text-2xl font-semibold text-gray-800 mb-4">3. Education</h3>
                        <EducationSection
                            education={initialCoreData.education}
                            onEducationChange={handleEducationChange}
                        />
                    </div>
                )}

                {/* Step 4: Skills & Certifications */}
                {currentStep === 4 && (
                    <div className="bg-white p-6 rounded-lg shadow-md"> {/* Add card styling */}
                        <h3 className="text-2xl font-semibold text-gray-800 mb-4">4. Skills & Certifications</h3>
                        <SkillsSection
                            skills={initialCoreData.skills}
                            onSkillsChange={handleSkillsChange}
                        />
                        <div className="mt-8"> {/* Keep mt-8 for separation between Skills and Certs */}
                            <CertificationsSection
                                certifications={initialCoreData.certifications}
                                onCertificationsChange={handleCertificationsChange}
                            />
                        </div>
                    </div>
                )}

                {/* Step 5: Generate Resume & Review */}
                {currentStep === 5 && (
                    <div className="bg-white p-6 rounded-lg shadow-md"> {/* Add card styling */}
                        <h3 className="text-2xl font-semibold text-gray-800 mb-4">5. Generate & Review Resume</h3>

                        {/* Target Job Description & Initial Request */}
                        <div className="mb-6 bg-gray-50 p-4 rounded-md border border-gray-200">
                            <h4 className="text-lg font-semibold text-gray-700 mb-2">Resume Customization</h4>
                            <label className="block text-gray-700 font-medium mb-4">
                                Target Job Description (Optional):
                                <textarea
                                    value={targetJobDescription}
                                    onChange={(e) => setTargetJobDescription(e.target.value)}
                                    rows="4"
                                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50"
                                    placeholder="Paste the job description here to tailor your resume."
                                ></textarea>
                            </label>
                            <label className="block text-gray-700 font-medium">
                                Specific Instructions / Initial Request (Optional):
                                <textarea
                                    value={initialRequest}
                                    onChange={(e) => setInitialRequest(e.target.value)}
                                    rows="2"
                                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50"
                                    placeholder="e.g., 'Make it concise', 'Focus on leadership skills'."
                                ></textarea>
                            </label>
                        </div>

                         

                        {/* Generate Resume Button */}
                        <div className="text-center mb-6">
                            <button onClick={handleGenerateResume} disabled={loading} className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-8 rounded-md text-lg transition duration-300 ease-in-out disabled:opacity-50">
                                {loading ? 'Generating...' : 'Generate Resume'}
                            </button>
                        </div>
                    </div>
                )}
            </div>

            {/* Navigation Buttons - Placed at the bottom of the left column */}
            <div className="flex justify-between mt-8 p-4 bg-gray-100 rounded-lg shadow-inner sticky bottom-0"> {/* Sticky at bottom of scrollable area */}
                {currentStep > 1 && (
                    <button onClick={prevStep} className="bg-gray-300 hover:bg-gray-400 text-gray-800 font-bold py-2 px-4 rounded-md transition duration-300 ease-in-out">
                        &larr; Previous
                    </button>
                )}
                {currentStep < totalSteps && (
                    <button onClick={nextStep} className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-md transition duration-300 ease-in-out">
                        Next &rarr;
                    </button>
                )}
                {currentStep === totalSteps && (
                    <button onClick={handleSetupProfile} disabled={loading} className="bg-purple-600 hover:bg-purple-700 text-white font-bold py-2 px-4 rounded-md transition duration-300 ease-in-out">
                        Save All Profile Data
                    </button>
                )}
            </div>
        </div>

        {/* Right Column: Resume Preview */}
        <div className="w-full md:w-1/2 lg:w-1/2 p-6 bg-white shadow-lg rounded-lg m-6 md:m-0 md:ml-6 overflow-y-auto min-h-[calc(100vh-64px)]"> {/* Added styling and overflow-y-auto */}
            <h3 className="text-2xl font-semibold text-gray-800 mb-4 text-center">Resume Preview</h3>
            <div className="markdown-resume-display border border-gray-300 rounded-md bg-gray-50 p-4"> {/* Removed max-h, added p-4 for inner spacing */}
                {generatedResume ? (
                    <div className="prose prose-blue max-w-none">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {generatedResume.content}
                    </ReactMarkdown>
                  </div>
                ) : (
                    <p className="text-gray-500 italic text-center">Generate your resume to see it here.</p>
                )}
            </div>
            {/* Optional: Add a "Download PDF" or "Customize" button here for the preview */}
            {generatedResume && (
                <div className="text-center mt-4">
                    <button className="bg-green-500 hover:bg-green-600 text-white font-bold py-2 px-4 rounded-md transition duration-300 ease-in-out">
                        Download PDF
                    </button>
                </div>
            )}
        </div>
    </div>
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