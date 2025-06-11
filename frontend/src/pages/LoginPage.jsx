// frontend/src/pages/LoginPage.js

import React, { useState } from 'react';
import { loginUser } from '../services/api';
import { Link } from 'react-router-dom'; // Import Link for navigation

function LoginPage({ onLoginSuccess, setLoading, setError, loading, error }) {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');

    const handleLogin = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        try {
            await loginUser(username, password);
            onLoginSuccess(username); // Notify App.js, which will then navigate
            alert('Login successful!');
        } catch (err) {
            setError(err.message || 'Login failed.');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex items-center justify-center min-h-screen bg-gray-100 p-5">
            <div className="bg-white p-8 rounded-lg shadow-xl w-full max-w-md text-center">
                <h2 className="text-3xl font-bold text-gray-800 mb-6">Login</h2>
                {error && <p className="text-red-500 bg-red-100 p-2 rounded-md mb-4">{error}</p>}
                {loading && <p className="text-blue-500 mb-4">Loading...</p>}

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

                <p className="mt-6 text-gray-600">
                    Don't have an account? <Link to="/register" className="text-blue-600 hover:underline">Register here</Link>
                </p>
            </div>
        </div>
    );
}

export default LoginPage;