// frontend/src/pages/DashboardPage.js

import React from 'react';
// import { Outlet } from 'react-router-dom'; // Will be used when we add nested routes
import './DashboardPage.css'; // Keep its dedicated CSS for the header/footer layout

function DashboardPage({ currentUser, onLogout, children }) {
    return (
        <div className="dashboard-container">
            <header className="dashboard-header bg-gray-800 text-white p-4 shadow-md flex justify-between items-center"> {/* Added Tailwind classes */}
                <div className="header-left">
                    <h1 className="text-2xl font-bold">Agentic Resume Builder</h1>
                </div>
                <div className="header-right flex items-center space-x-4"> {/* Added Tailwind classes */}
                    <span className="text-lg">Welcome, {currentUser?.username || 'User'}!</span>
                    <button onClick={onLogout} className="bg-red-500 hover:bg-red-600 text-white font-bold py-2 px-4 rounded transition duration-300 ease-in-out"> {/* Added Tailwind classes */}
                        Logout
                    </button>
                </div>
            </header>
            <main className="dashboard-content p-6 max-w-6xl mx-auto flex-grow"> {/* Added Tailwind classes */}
                {children} {/* This will render the content passed from App.js */}
                {/* When we add nested routes, we might use <Outlet /> here */}
            </main>
        </div>
    );
}

export default DashboardPage;