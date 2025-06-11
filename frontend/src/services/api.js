import axios from 'axios';

const api = axios.create({
  baseURL: 'http://127.0.0.1:8000/', // Axios will automatically prepend the proxy base URL
});
api.interceptors.request.use(
    config => {
        const token = getAuthToken();
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    error => {
        return Promise.reject(error);
    }
);
// const API_BASE_URL = 'http://127.0.0.1:8000/';
// export const getUserProfile = async () => {
//   const response = await api.get('http://127.0.0.1:8000/user-profile/');
//   return response.data;
// };

// export const setupUserProfile = async (profileData) => {
//   const response = await api.post('http://127.0.0.1:8000/setup-user-profile/', profileData);
//   return response.data;
// };

const getAuthToken = () => {
    return localStorage.getItem('access_token');
};

// Function to store the token
const setAuthToken = (token) => {
    localStorage.setItem('access_token', token);
};

// Function to remove the token (on logout)
const removeAuthToken = () => {
    localStorage.removeItem('access_token');
};

// export const generateResume = async (initialPrompt = null, targetJobDescription = null) => {
//     console.log('Generating resume with initialPrompt:', initialPrompt, 'and targetJobDescription:', targetJobDescription);

//     const response = await api.post(`${API_BASE_URL}/generate-resume/`, { initial_prompt: initialPrompt, target_job_description: targetJobDescription });
//     return response.data;
// };
// export const generateResume = async (initialPrompt = null, targetJobDescription = '') => {
//     const response = await fetch(`${API_BASE_URL}/generate-resume/`, {
//         method: 'POST',
//         headers: getAuthenticatedHeaders(), // Now requires authentication
//         body: JSON.stringify({ initial_prompt: "generate a professional resume", target_job_description: targetJobDescription }),
//     });
//     if (!response.ok) {
//         const errorData = await response.json();
//         throw new Error(errorData.detail || 'Failed to generate resume');
//     }
//     return response.json();
// };

// export const submitFeedback = async (feedbackData) => {
//   const response = await api.post(`${API_BASE_URL}/submit-feedback/`, feedbackData);
//   return response.data;
// };

// export const getSuggestions = async (targetJobDescription = null) => { // <--- NEW API CALL
//     console.log('Getting suggestions with targetJobDescription:', targetJobDescription);
//     const response = await api.post(`${API_BASE_URL}/get-suggestions/`, { target_job_description: targetJobDescription });
//     return response.data;
// };

// Register a new user
export const registerUser = async (username, email, password) => {
    try {
        const response = await api.post('/register', { username, email, password });
        return response.data;
    } catch (error) {
        throw new Error(error.response?.data?.detail || 'Registration failed');
    }
};

// Login user and get an access token
export const loginUser = async (username, password) => {
    // Axios sends application/json by default. For application/x-www-form-urlencoded
    // which FastAPI's OAuth2PasswordRequestForm expects, we need URLSearchParams.
    const details = new URLSearchParams();
    details.append('username', username);
    details.append('password', password);

    try {
        const response = await api.post('/token', details, {
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
        });
        setAuthToken(response.data.access_token); // Store the token
        return response.data;
    } catch (error) {
        throw new Error(error.response?.data?.detail || 'Login failed');
    }
};

// Logout user
export const logoutUser = () => {
    removeAuthToken(); // Remove the token from storage
};

// --- Helper function to create authenticated headers ---
// const getAuthenticatedHeaders = () => {
//     const token = getAuthToken();
//     if (token) {
//         return {
//             'Content-Type': 'application/json',
//             'Authorization': `Bearer ${token}`,
//         };
//     }
//     return {
//         'Content-Type': 'application/json',
//     };
// };

// --- Modify existing functions to include authentication headers ---

export const getUserProfile = async () => {
    try {
        const response = await api.get('/user-profile/');
        return response.data;
    } catch (error) {
        throw new Error(error.response?.data?.detail || 'Failed to fetch user profile');
    }
};

export const setupUserProfile = async (profileData) => {
    try {
        const response = await api.post('/setup-user-profile/', profileData);
        return response.data;
    } catch (error) {
        throw new Error(error.response?.data?.detail || 'Failed to set up user profile');
    }
};

export const generateResume = async (initialPrompt = null, targetJobDescription = '') => {
    try {
        const response = await api.post('/generate-resume/', { initial_prompt: "generate a professional resume", target_job_description: targetJobDescription });
        return response.data;
    } catch (error) {
        throw new Error(error.response?.data?.detail || 'Failed to generate resume');
    }
};

export const submitFeedback = async (feedbackData) => {
    try {
        const response = await api.post('/submit-feedback/', feedbackData);
        return response.data;
    } catch (error) {
        throw new Error(error.response?.data?.detail || 'Failed to submit feedback');
    }
};

export const getSuggestions = async (targetJobDescription = '') => {
    try {
        const response = await api.post('/get-suggestions/', { target_job_description: targetJobDescription });
        return response.data;
    } catch (error) {
        throw new Error(error.response?.data?.detail || 'Failed to get suggestions');
    }
};

// New function to fetch all resume versions for the authenticated user
export const getAllResumeVersions = async () => {
    try {
        const response = await api.get('/resume-versions/');
        return response.data;
    } catch (error) {
        throw new Error(error.response?.data?.detail || 'Failed to fetch resume versions');
    }
};

export const uploadResumeFile = async (file) => {
    const formData = new FormData();
    formData.append('file', file); // 'file' must match the parameter name in your FastAPI endpoint

    try {
        // Axios handles 'Content-Type': 'multipart/form-data' automatically for FormData
        const response = await api.post('/upload-resume/', formData);
        return response.data;
    } catch (error) {
        throw new Error(error.response?.data?.detail || 'Failed to upload resume file.');
    }
};