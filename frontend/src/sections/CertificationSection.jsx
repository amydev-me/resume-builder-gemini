// frontend/src/sections/CertificationsSection.js

import React, { useState, useEffect } from 'react';

function CertificationsSection({ certifications, onCertificationsChange }) {
    const safeCertifications = Array.isArray(certifications) ? certifications : [];

    // currentCert will now be a string, not an object
    const [currentCert, setCurrentCert] = useState('');
    const [editingIndex, setEditingIndex] = useState(null);


    // When editingIndex changes or is cleared, reset the input field
    useEffect(() => {
        if (editingIndex === null) {
            setCurrentCert('');
        } else {
            // Load the certification string into the input for editing
            setCurrentCert(safeCertifications[editingIndex] || '');
        }
    }, [editingIndex, safeCertifications]); // Added safeCertifications to dependencies

    const handleChange = (e) => {
        setCurrentCert(e.target.value);
    };

    const handleEdit = (index) => {
        setEditingIndex(index);
        const certToEdit = safeCertifications[index];
        setCurrentCert({
            name: certToEdit.name || '',
            issuer: certToEdit.issuer || '',
            date: certToEdit.date || '',
        });
    };

    const handleAddOrUpdate = () => {
        const trimmedCert = currentCert.trim();
        if (trimmedCert === '') {
            alert('Certification entry cannot be empty.');
            return;
        }

        let updatedCerts;
        if (editingIndex !== null) {
            // Update existing certification string
            updatedCerts = safeCertifications.map((cert, index) =>
                index === editingIndex ? trimmedCert : cert
            );
        } else {
            // Add new certification string, prevent duplicates
            if (safeCertifications.includes(trimmedCert)) {
                alert('This certification already exists.');
                setCurrentCert('');
                return;
            }
            updatedCerts = [...safeCertifications, trimmedCert];
        }
        onCertificationsChange(updatedCerts);
        setEditingIndex(null); // Clear editing state
        setCurrentCert('');    // Clear input field
    };

    const handleDelete = (index) => {
        if (window.confirm('Are you sure you want to delete this certification?')) {
            const updatedCerts = safeCertifications.filter((_, i) => i !== index);
            onCertificationsChange(updatedCerts);
            if (editingIndex === index) { // If deleting the currently edited item
                setEditingIndex(null);
                setCurrentCert('');
            }
        }
    };

    const renderList = safeCertifications.length > 0;

    return (
        <div className="bg-white p-6 rounded-lg shadow-md mb-6">
            <h3 className="text-xl font-semibold text-gray-800 mb-4">Certifications</h3>

            <div className="grid grid-cols-1 gap-4 mb-6 p-4 border border-gray-200 rounded-md bg-gray-50">
                <div className="col-span-full">
                    <label htmlFor="cert-entry" className="block text-sm font-medium text-gray-700">Certification Entry:</label>
                    <input
                        type="text"
                        id="cert-entry"
                        name="certEntry" // Use a generic name as it's a single string
                        value={currentCert}
                        onChange={handleChange}
                        placeholder="e.g., AWS CERTIFIED DEVELOPER ASSOCIATE | UDEMY"
                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring focus:ring-blue-200 focus:ring-opacity-50"
                        required
                    />
                </div>
                <div className="col-span-full flex justify-end">
                    <button onClick={handleAddOrUpdate} className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-md transition duration-300 ease-in-out">
                        {editingIndex !== null ? 'Update Certification' : 'Add Certification'}
                    </button>
                    {editingIndex !== null && (
                        <button onClick={() => { setEditingIndex(null); setCurrentCert(''); }} className="ml-2 bg-gray-400 hover:bg-gray-500 text-white font-bold py-2 px-4 rounded-md transition duration-300 ease-in-out">
                            Cancel Edit
                        </button>
                    )}
                </div>
            </div>

            {renderList && (
                <div className="mt-8">
                    <h4 className="text-lg font-semibold text-gray-700 mb-3">Your Current Certifications:</h4>
                    <ul className="space-y-4">
                        {safeCertifications.map((certString, index) => ( // Iterate directly over strings
                            <li key={index} className="bg-gray-100 p-4 rounded-md border border-gray-200 flex justify-between items-center">
                                <div>
                                    <p className="font-bold text-gray-900">{certString}</p> {/* Display the string directly */}
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
                <p className="text-center text-gray-500 italic mt-6">No certifications added yet. Use the form above to add one.</p>
            )}
        </div>
    );
}

export default CertificationsSection;