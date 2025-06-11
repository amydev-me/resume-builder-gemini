// frontend/src/sections/EducationSection.js

import React, { useState, useEffect } from 'react';

function EducationSection({ education, onEducationChange }) {
    const safeEducation = Array.isArray(education) ? education : [];

    const [editingIndex, setEditingIndex] = useState(null);
    const [currentEducation, setCurrentEducation] = useState({
        degree: '',
        institution: '',
        field_of_study: '',
        start_date: '',
        end_date: '',
        description: '', // Optional: achievements/notes
    });

    useEffect(() => {
        if (editingIndex === null) {
            setCurrentEducation({ degree: '', institution: '', field_of_study: '', start_date: '', end_date: '', description: '' });
        }
    }, [editingIndex]);

    const handleChange = (e) => {
        const { name, value } = e.target;
        setCurrentEducation(prev => ({ ...prev, [name]: value }));
    };

    const handleAddOrUpdate = () => {
        if (!currentEducation.degree || !currentEducation.institution) {
            alert('Degree and Institution are required for education experience.');
            return;
        }

        let updatedEducation;
        if (editingIndex !== null) {
            updatedEducation = safeEducation.map((edu, index) =>
                index === editingIndex ? currentEducation : edu
            );
        } else {
            updatedEducation = [...safeEducation, currentEducation];
        }
        onEducationChange(updatedEducation);
        setEditingIndex(null);
        setCurrentEducation({ degree: '', institution: '', field_of_study: '', start_date: '', end_date: '', description: '' });
    };

    const handleEdit = (index) => {
        setEditingIndex(index);
        const eduToEdit = safeEducation[index];
        setCurrentEducation({
            degree: eduToEdit.degree || '',
            institution: eduToEdit.institution || '',
            field_of_study: eduToEdit.field_of_study || '',
            start_date: eduToEdit.start_date || '',
            end_date: eduToEdit.end_date || '',
            description: eduToEdit.description || '',
        });
    };

    const handleDelete = (index) => {
        if (window.confirm('Are you sure you want to delete this education entry?')) {
            const updatedEducation = safeEducation.filter((_, i) => i !== index);
            onEducationChange(updatedEducation);
            if (editingIndex === index) {
                setEditingIndex(null);
                setCurrentEducation({ degree: '', institution: '', field_of_study: '', start_date: '', end_date: '', description: '' });
            }
        }
    };

    const renderList = safeEducation.length > 0;

    return (
        <div className="bg-white p-6 rounded-lg shadow-md mb-6">
            <h3 className="text-xl font-semibold text-gray-800 mb-4">Education</h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6 p-4 border border-gray-200 rounded-md bg-gray-50">
                <div>
                    <label htmlFor="edu-degree" className="block text-sm font-medium text-gray-700">Degree/Qualification:</label>
                    <input type="text" id="edu-degree" name="degree" value={currentEducation.degree} onChange={handleChange} placeholder="e.g., Master of Science" className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring focus:ring-blue-200 focus:ring-opacity-50" required />
                </div>
                <div>
                    <label htmlFor="edu-institution" className="block text-sm font-medium text-gray-700">Institution:</label>
                    <input type="text" id="edu-institution" name="institution" value={currentEducation.institution} onChange={handleChange} placeholder="e.g., National University of Singapore" className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring focus:ring-blue-200 focus:ring-opacity-50" required />
                </div>
                <div className="col-span-full">
                    <label htmlFor="edu-field" className="block text-sm font-medium text-gray-700">Field of Study:</label>
                    <input type="text" id="edu-field" name="field_of_study" value={currentEducation.field_of_study} onChange={handleChange} placeholder="e.g., Computer Science" className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring focus:ring-blue-200 focus:ring-opacity-50" />
                </div>
                <div>
                    <label htmlFor="edu-start-date" className="block text-sm font-medium text-gray-700">Start Date (YYYY-MM-DD/YYYY):</label>
                    <input type="text" id="edu-start-date" name="start_date" value={currentEducation.start_date} onChange={handleChange} placeholder="e.g., 2014-08 or 2014" className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring focus:ring-blue-200 focus:ring-opacity-50" />
                </div>
                <div>
                    <label htmlFor="edu-end-date" className="block text-sm font-medium text-gray-700">End Date (YYYY-MM-DD/YYYY) / Present:</label>
                    <input type="text" id="edu-end-date" name="end_date" value={currentEducation.end_date} onChange={handleChange} placeholder="e.g., 2018-05 or Present" className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring focus:ring-blue-200 focus:ring-opacity-50" />
                </div>
                <div className="col-span-full">
                    <label htmlFor="edu-description" className="block text-sm font-medium text-gray-700">Description (Notes/Achievements):</label>
                    <textarea id="edu-description" name="description" value={currentEducation.description} onChange={handleChange} rows="3" placeholder="e.g., Graduated with First Class Honours, GPA 4.8/5.0" className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring focus:ring-blue-200 focus:ring-opacity-50"></textarea>
                </div>
                <div className="col-span-full flex justify-end">
                    <button onClick={handleAddOrUpdate} className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-md transition duration-300 ease-in-out">
                        {editingIndex !== null ? 'Update Education' : 'Add Education'}
                    </button>
                    {editingIndex !== null && (
                        <button onClick={() => { setEditingIndex(null); setCurrentEducation({ degree: '', institution: '', field_of_study: '', start_date: '', end_date: '', description: '' }); }} className="ml-2 bg-gray-400 hover:bg-gray-500 text-white font-bold py-2 px-4 rounded-md transition duration-300 ease-in-out">
                            Cancel Edit
                        </button>
                    )}
                </div>
            </div>

            {renderList && (
                <div className="mt-8">
                    <h4 className="text-lg font-semibold text-gray-700 mb-3">Your Current Education:</h4>
                    <ul className="space-y-4">
                        {safeEducation.map((edu, index) => (
                            <li key={index} className="bg-gray-100 p-4 rounded-md border border-gray-200 flex justify-between items-center">
                                <div>
                                    <p className="font-bold text-gray-900">{edu.degree} from {edu.institution}</p>
                                    {edu.field_of_study && <p className="text-sm text-gray-600">{edu.field_of_study}</p>}
                                    {(edu.start_date || edu.end_date) && <p className="text-sm text-gray-600">{edu.start_date} - {edu.end_date || 'Present'}</p>}
                                    {edu.description && <p className="text-sm text-gray-700 mt-1 line-clamp-2">{edu.description}</p>}
                                </div>
                                <div className="flex space-x-2">
                                    <button onClick={() => handleEdit(index)} className="bg-yellow-500 hover:bg-yellow-600 text-white text-sm py-1 px-3 rounded">
                                        Edit
                                    </button>
                                    <button onClick={() => handleDelete(index)} className="bg-red-500 hover:bg-red-600 text-white text-sm py-1 px-3 rounded">
                                        Delete
                                    </button>
                                </div>
                            </li>
                        ))}
                    </ul>
                </div>
            )}
            {!renderList && (
                <p className="text-center text-gray-500 italic mt-6">No education entries added yet. Use the form above to add one.</p>
            )}
        </div>
    );
}

export default EducationSection;