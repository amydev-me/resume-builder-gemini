// frontend/src/pages/AuthPage.js

import React, { useState } from 'react';
import { registerUser, loginUser } from '../services/api';
// No AuthPage.css needed anymore, all styles are in Tailwind classes within JSX
// import './AuthPage.css'; // REMOVE THIS LINE

function AuthPage({ onLoginSuccess, setLoading, setError, loading, error }) {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [email, setEmail] = useState('');
    const [showRegisterForm, setShowRegisterForm] = useState(false); // NEW state to toggle forms

    const handleRegister = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        try {
            await registerUser(username, email, password);
            alert('Registration successful! Please login.');
            setUsername('');
            setEmail('');
            setPassword('');
            setShowRegisterForm(false); // Switch back to login form after successful registration
        } catch (err) {
            setError(err.message || 'Registration failed.');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const handleLogin = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        try {
            await loginUser(username, password);
            onLoginSuccess(username); // Notify App.js, which will then navigate
        } catch (err) {
            setError(err.message || 'Login failed.');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex flex-col items-center justify-center min-h-screen bg-gray-100 p-5">
            {error && <p className="text-red-500 bg-red-100 p-2 rounded-md mb-4 max-w-md w-full text-center">{error}</p>}
            {loading && <p className="text-blue-500 mb-4">Loading...</p>}

            <div className="bg-white p-8 rounded-lg shadow-xl w-full max-w-md text-center">
                {/* Toggle Buttons/Links */}
                <div className="flex justify-center mb-6 border-b border-gray-200">
                    <button
                        onClick={() => setShowRegisterForm(false)}
                        className={`px-6 py-3 text-lg font-semibold transition-colors duration-300 ${!showRegisterForm ? 'text-blue-700 border-b-2 border-blue-700' : 'text-gray-500 hover:text-gray-700'}`}
                        disabled={loading}
                    >
                        Login
                    </button>
                    <button
                        onClick={() => setShowRegisterForm(true)}
                        className={`px-6 py-3 text-lg font-semibold transition-colors duration-300 ${showRegisterForm ? 'text-blue-700 border-b-2 border-blue-700' : 'text-gray-500 hover:text-gray-700'}`}
                        disabled={loading}
                    >
                        Register
                    </button>
                </div>

                {/* Conditional Rendering of Forms */}
                {!showRegisterForm ? (
                    // Login Form
                    <div>
                        <h2 className="text-3xl font-bold text-gray-800 mb-6">Login</h2>
                        <form onSubmit={handleLogin} className="space-y-5">
                            <div>
                                <label htmlFor="login-username" className="block text-left text-gray-700 font-medium mb-2">Username:</label>
                                <input
                                    type="text"
                                    id="login-username"
                                    value={username}
                                    onChange={(e) => setUsername(e.target.value)}
                                    required
                                    className="w-full p-3 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                                />
                            </div>
                            <div>
                                <label htmlFor="login-password" className="block text-left text-gray-700 font-medium mb-2">Password:</label>
                                <input
                                    type="password"
                                    id="login-password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    required
                                    className="w-full p-3 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                                />
                            </div>
                            <button type="submit" disabled={loading} className="w-full bg-blue-600 text-white py-3 rounded-md font-semibold hover:bg-blue-700 transition duration-300 ease-in-out">
                                Login
                            </button>
                        </form>
                    </div>
                ) : (
                    // Register Form
                    <div>
                        <h2 className="text-3xl font-bold text-gray-800 mb-6">Register</h2>
                        <form onSubmit={handleRegister} className="space-y-5">
                            <div>
                                <label htmlFor="register-username" className="block text-left text-gray-700 font-medium mb-2">Username:</label>
                                <input
                                    type="text"
                                    id="register-username"
                                    value={username}
                                    onChange={(e) => setUsername(e.target.value)}
                                    required
                                    className="w-full p-3 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                                />
                            </div>
                            <div>
                                <label htmlFor="register-email" className="block text-left text-gray-700 font-medium mb-2">Email (Optional):</label>
                                <input
                                    type="email"
                                    id="register-email"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    className="w-full p-3 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                                />
                            </div>
                            <div>
                                <label htmlFor="register-password" className="block text-left text-gray-700 font-medium mb-2">Password:</label>
                                <input
                                    type="password"
                                    id="register-password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    required
                                    className="w-full p-3 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                                />
                            </div>
                            <button type="submit" disabled={loading} className="w-full bg-green-600 text-white py-3 rounded-md font-semibold hover:bg-green-700 transition duration-300 ease-in-out">
                                Register
                            </button>
                        </form>
                    </div>
                )}
            </div>
        </div>
    );
}

export default AuthPage;