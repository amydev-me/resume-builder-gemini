import React, { useState } from 'react';

function LearnedPreferencesSection({ learnedPreferences, onUpdatePreference, onDeletePreference, onAddPreference }) {
    const [newPreference, setNewPreference] = useState('');

    const handleAdd = () => {
        if (newPreference.trim()) {
            // Assuming a simple structure for now, where rule is just a string
            // In a real scenario, you might add 'type', 'active' etc.
            onAddPreference({ rule: newPreference.trim(), active: true, type: 'stylistic' });
            setNewPreference('');
        }
    };

    return (
        <div className="bg-purple-50 border-l-4 border-purple-400 text-purple-800 p-4 rounded-lg shadow-sm">
            <h4 className="font-bold text-lg mb-2">AI's Learned Preferences / Rules</h4>
            <p className="text-sm text-purple-700 mb-3">These are rules the AI has learned or you've added for future resume generations.</p>

            {learnedPreferences && learnedPreferences.length > 0 ? (
                <ul className="list-disc list-inside space-y-2 text-sm">
                    {learnedPreferences.map((pref, index) => (
                        <li key={index} className="flex items-center justify-between">
                            <span className="flex-1">{pref.rule}</span>
                            <div className="flex items-center space-x-2 ml-4">
                                {/* Toggle active state (optional) */}
                                {/*
                                <label className="relative inline-flex items-center cursor-pointer">
                                    <input type="checkbox" checked={pref.active} onChange={() => onUpdatePreference(index, { ...pref, active: !pref.active })} className="sr-only peer" />
                                    <div className="w-9 h-5 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
                                </label>
                                */}
                                <button
                                    onClick={() => onDeletePreference(index)}
                                    className="text-red-600 hover:text-red-800 text-xs font-semibold"
                                >
                                    Remove
                                </button>
                            </div>
                        </li>
                    ))}
                </ul>
            ) : (
                <p className="text-sm italic text-purple-700">No learned preferences yet. Add one below!</p>
            )}

            <div className="mt-4 flex items-center space-x-2">
                <input
                    type="text"
                    value={newPreference}
                    onChange={(e) => setNewPreference(e.target.value)}
                    placeholder="Add a new preference (e.g., 'Be concise')"
                    className="flex-1 mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50"
                />
                <button
                    onClick={handleAdd}
                    className="bg-purple-600 hover:bg-purple-700 text-white font-bold py-2 px-4 rounded-md transition duration-300 ease-in-out"
                >
                    Add Preference
                </button>
            </div>
        </div>
    );
}

export default LearnedPreferencesSection;