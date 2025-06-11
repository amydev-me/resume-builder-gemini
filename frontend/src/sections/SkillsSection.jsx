// frontend/src/sections/SkillsSection.js

import React, { useState } from 'react';

function SkillsSection({ skills, onSkillsChange }) {
    const safeSkills = Array.isArray(skills) ? skills : [];
    const [currentSkill, setCurrentSkill] = useState('');

    const handleAddSkill = () => {
        if (currentSkill.trim() === '') {
            alert('Skill cannot be empty.');
            return;
        }
        if (safeSkills.includes(currentSkill.trim())) {
            alert('This skill already exists.');
            setCurrentSkill('');
            return;
        }
        onSkillsChange([...safeSkills, currentSkill.trim()]);
        setCurrentSkill('');
    };

    const handleDeleteSkill = (index) => {
        if (window.confirm('Are you sure you want to delete this skill?')) {
            const updatedSkills = safeSkills.filter((_, i) => i !== index);
            onSkillsChange(updatedSkills);
        }
    };

    const renderList = safeSkills.length > 0;

    return (
        <div className="bg-white p-6 rounded-lg shadow-md mb-6">
            <h3 className="text-xl font-semibold text-gray-800 mb-4">Skills</h3>

            <div className="flex flex-col md:flex-row gap-4 mb-6 p-4 border border-gray-200 rounded-md bg-gray-50">
                <div className="flex-grow">
                    <label htmlFor="skill-input" className="block text-sm font-medium text-gray-700">Add a new skill:</label>
                    <input
                        type="text"
                        id="skill-input"
                        value={currentSkill}
                        onChange={(e) => setCurrentSkill(e.target.value)}
                        onKeyPress={(e) => { // Allow adding with Enter key
                            if (e.key === 'Enter') {
                                e.preventDefault(); // Prevent form submission if in a form
                                handleAddSkill();
                            }
                        }}
                        placeholder="e.g., React, Python, AWS"
                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring focus:ring-blue-200 focus:ring-opacity-50"
                    />
                </div>
                <div className="flex items-end"> {/* Align button to bottom */}
                    <button onClick={handleAddSkill} className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-md transition duration-300 ease-in-out md:w-auto w-full">
                        Add Skill
                    </button>
                </div>
            </div>

            {renderList && (
                <div className="mt-8">
                    <h4 className="text-lg font-semibold text-gray-700 mb-3">Your Current Skills:</h4>
                    <ul className="flex flex-wrap gap-2">
                        {safeSkills.map((skill, index) => (
                            <li key={index} className="flex items-center bg-blue-100 text-blue-800 text-sm font-medium px-3 py-1 rounded-full">
                            {skill}
                            <button
      onClick={() => handleDeleteSkill(index)}
      className="ml-2 bg-white hover:bg-gray-100 text-gray-700 focus:outline-none text-xs w-4 h-4 flex items-center justify-center rounded-full"
  >
      &times;
  </button>
                        </li>
                        ))}
                    </ul>
                </div>
            )}
            {!renderList && (
                <p className="text-center text-gray-500 italic mt-6">No skills added yet. Use the input above to add some.</p>
            )}
        </div>
    );
}

export default SkillsSection;