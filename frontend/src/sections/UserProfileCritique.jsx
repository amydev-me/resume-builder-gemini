import React from 'react';

function UserProfileCritique({ critique, onAcceptCritique }) {
    if (!critique) {
        return null; // Don't render if no critique is available
    }

    return (
        <div className="bg-blue-50 border-l-4 border-blue-400 text-blue-800 p-4 rounded-lg shadow-sm">
            <h4 className="font-bold text-lg mb-2">AI's Self-Critique / Suggestions</h4>
            <div className="prose prose-blue max-w-none text-sm leading-relaxed">
                {critique.split('\n').map((line, index) => (
                    <p key={index} className="mb-1 last:mb-0">{line}</p>
                ))}
            </div>
            {/* You can add an "Accept" button if the critique has actionable items */}
            {/*
            <div className="mt-4 text-right">
                <button
                    onClick={onAcceptCritique} // This function would handle applying the critique
                    className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded transition duration-300 ease-in-out"
                >
                    Accept Suggestions
                </button>
            </div>
            */}
        </div>
    );
}

export default UserProfileCritique;