import React from 'react';

// This component now expects the full critique object as received from the backend
function UserProfileCritique({ critique, onAcceptCritique }) {
    if (!critique || typeof critique !== 'object') {
        return null; // Don't render if critique is null, undefined, or not an object
    }

    return (
        <div className="critique-results bg-yellow-100 border border-yellow-200 p-4 rounded-md shadow-sm">
            <h4 className="font-bold text-lg mb-2 text-yellow-800">AI's Self-Critique: {critique.overall_assessment}</h4>

            {critique.has_issues ? (
                <div className="mt-2">
                    <p className="font-bold text-orange-700">Issues Identified:</p>
                    <ul className="list-disc list-inside mt-2 space-y-1">
                        {Array.isArray(critique.issues) && critique.issues.map((issue, index) => (
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

            {/* If you add an "Accept" button for the critique itself */}
            {/*
            <div className="mt-4 text-right">
                <button
                    onClick={onAcceptCritique}
                    className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded transition duration-300 ease-in-out"
                >
                    Acknowledge Critique
                </button>
            </div>
            */}
        </div>
    );
}

export default UserProfileCritique;