// frontend/src/sections/JobHistorySection.js

import React, { useState, useEffect } from 'react';

function JobHistorySection({ jobHistory, onJobHistoryChange }) {
    // Debugging line (keep it for now if you want, remove it when done debugging)
    console.log("JobHistorySection received jobHistory:", jobHistory, "Type:", typeof jobHistory, "Is Array:", Array.isArray(jobHistory));

    const safeJobHistory = Array.isArray(jobHistory) ? jobHistory : [];

    const [editingIndex, setEditingIndex] = useState(null);
    const [currentJob, setCurrentJob] = useState({
        title: '',
        company: '',
        start_date: '',
        end_date: '',
        responsibilities: [], // <<< CHANGED: from 'description' to 'responsibilities', and default to empty array
    });

    useEffect(() => {
        if (editingIndex === null) {
            setCurrentJob({ title: '', company: '', start_date: '', end_date: '', responsibilities: [] }); // Reset responsibilities to empty array
        }
    }, [editingIndex]);

    const handleJobChange = (e) => {
        const { name, value } = e.target;
        // This handler is now for title, company, dates. Responsibilities will have its own handler.
        setCurrentJob(prev => ({ ...prev, [name]: value }));
    };

    // NEW: Specific handler for the responsibilities textarea
    const handleResponsibilitiesChange = (e) => {
        // Split the textarea value by new line to create an array of responsibilities
        // Filter out empty strings that might result from extra new lines
        const newResponsibilities = e.target.value.split('\n').filter(line => line.trim() !== '');
        setCurrentJob(prev => ({ ...prev, responsibilities: newResponsibilities }));
    };


    const handleAddOrUpdateJob = () => {
        if (!currentJob.title || !currentJob.company || !currentJob.start_date) {
            alert('Title, Company, and Start Date are required for job experience.');
            return;
        }

        let updatedHistory;
        if (editingIndex !== null) {
            updatedHistory = safeJobHistory.map((job, index) =>
                index === editingIndex ? currentJob : job
            );
        } else {
            updatedHistory = [...safeJobHistory, currentJob];
        }
        onJobHistoryChange(updatedHistory);
        setEditingIndex(null);
        setCurrentJob({ title: '', company: '', start_date: '', end_date: '', responsibilities: [] }); // Reset responsibilities
    };

    const handleEditJob = (index) => {
        setEditingIndex(index);
        const jobToEdit = safeJobHistory[index];

        // FIX: Ensure all fields have a string/array value, defaulting to empty
        setCurrentJob({
            title: jobToEdit.title || '',
            company: jobToEdit.company || '',
            start_date: jobToEdit.start_date || '',
            end_date: jobToEdit.end_date || '',
            // Handle responsibilities: if it's an array, use it; otherwise, default to empty array
            responsibilities: Array.isArray(jobToEdit.responsibilities) ? jobToEdit.responsibilities : [],
        });
    };

    const handleDeleteJob = (index) => {
        if (window.confirm('Are you sure you want to delete this job experience?')) {
            const updatedHistory = safeJobHistory.filter((_, i) => i !== index);
            onJobHistoryChange(updatedHistory);
            if (editingIndex === index) {
                setEditingIndex(null);
                setCurrentJob({ title: '', company: '', start_date: '', end_date: '', responsibilities: [] });
            }
        }
    };

    const renderJobList = safeJobHistory.length > 0;

    return (
        <div className="bg-white p-6 rounded-lg shadow-md mb-6">
            <h3 className="text-xl font-semibold text-gray-800 mb-4">Job History</h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6 p-4 border border-gray-200 rounded-md bg-gray-50">
                <div className="col-span-full">
                    <label htmlFor="job-title" className="block text-sm font-medium text-gray-700">Job Title:</label>
                    <input type="text" id="job-title" name="title" value={currentJob.title} onChange={handleJobChange} placeholder="e.g., Senior Software Engineer" className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring focus:ring-blue-200 focus:ring-opacity-50" required />
                </div>
                <div>
                    <label htmlFor="job-company" className="block text-sm font-medium text-gray-700">Company:</label>
                    <input type="text" id="job-company" name="company" value={currentJob.company} onChange={handleJobChange} placeholder="e.g., Google" className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring focus:ring-blue-200 focus:ring-opacity-50" required />
                </div>
                <div>
                    <label htmlFor="job-start-date" className="block text-sm font-medium text-gray-700">Start Date (YYYY-MM-DD):</label>
                    <input type="text" id="job-start-date" name="start_date" value={currentJob.start_date} onChange={handleJobChange} placeholder="e.g., 2018-06-01 or June 2018" className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring focus:ring-blue-200 focus:ring-opacity-50" required />
                </div>
                <div>
                    <label htmlFor="job-end-date" className="block text-sm font-medium text-gray-700">End Date (YYYY-MM-DD) / Present:</label>
                    <input type="text" id="job-end-date" name="end_date" value={currentJob.end_date} onChange={handleJobChange} placeholder="e.g., 2023-12-31 or Present" className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring focus:ring-blue-200 focus:ring-opacity-50" />
                </div>
                <div className="col-span-full">
                    <label htmlFor="job-responsibilities" className="block text-sm font-medium text-gray-700">Responsibilities (One per line):</label> {/* <<< CHANGED LABEL */}
                    <textarea
                        id="job-responsibilities" // <<< CHANGED ID
                        name="responsibilities" // <<< CHANGED NAME
                        value={currentJob.responsibilities.join('\n')} // <<< CHANGED: Join array to string for display
                        onChange={handleResponsibilitiesChange} // <<< NEW: Use specific handler
                        rows="4"
                        placeholder="Enter key responsibilities or achievements, one per line (e.g., 'Developed feature X', 'Managed team Y', 'Optimized performance by Z%')" // <<< CHANGED PLACEHOLDER
                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring focus:ring-blue-200 focus:ring-opacity-50"
                    ></textarea>
                </div>
                <div className="col-span-full flex justify-end">
                    <button onClick={handleAddOrUpdateJob} className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-md transition duration-300 ease-in-out">
                        {editingIndex !== null ? 'Update Job' : 'Add Job'}
                    </button>
                    {editingIndex !== null && (
                        <button onClick={() => { setEditingIndex(null); setCurrentJob({ title: '', company: '', start_date: '', end_date: '', responsibilities: [] }); }} className="ml-2 bg-gray-400 hover:bg-gray-500 text-white font-bold py-2 px-4 rounded-md transition duration-300 ease-in-out">
                            Cancel Edit
                        </button>
                    )}
                </div>
            </div>

            {renderJobList && (
                <div className="mt-8">
                    <h4 className="text-lg font-semibold text-gray-700 mb-3">Your Current Job Experiences:</h4>
                    <ul className="space-y-4">
                        {safeJobHistory.map((job, index) => (
                            <li key={index} className="bg-gray-100 p-4 rounded-md border border-gray-200 flex justify-between items-center">
                                <div>
                                    <p className="font-bold text-gray-900">{job.title} at {job.company}</p>
                                    <p className="text-sm text-gray-600">{job.start_date} - {job.end_date || 'Present'}</p>
                                    {/* <<< NEW: Render responsibilities as a list */}
                                    {Array.isArray(job.responsibilities) && job.responsibilities.length > 0 && (
                                        <ul className="list-disc list-inside text-sm text-gray-700 mt-1 pl-4"> {/* Added pl-4 for indentation */}
                                            {job.responsibilities.map((resp, i) => (
                                                <li key={i}>{resp}</li>
                                            ))}
                                        </ul>
                                    )}
                                    {/* END NEW */}
                                </div>
                                <div className="flex space-x-2">
                                    <button onClick={() => handleEditJob(index)} className="bg-yellow-500 hover:bg-yellow-600 text-white text-sm py-1 px-3 rounded">
                                        Edit
                                    </button>
                                    <button onClick={() => handleDeleteJob(index)} className="bg-red-500 hover:bg-red-600 text-white text-sm py-1 px-3 rounded">
                                        Delete
                                    </button>
                                </div>
                            </li>
                        ))}
                    </ul>
                </div>
            )}
            {!renderJobList && (
                <p className="text-center text-gray-500 italic mt-6">No job experiences added yet. Use the form above to add one.</p>
            )}
        </div>
    );
}

export default JobHistorySection;