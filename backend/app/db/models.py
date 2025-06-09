# backend/app/db/models.py

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

# User Model
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=True) # Email can be optional
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False) # Example for future roles

    # Define relationships to other user-specific data
    # `uselist=False` for one-to-one or one-to-zero relationship
    user_profile = relationship("UserProfile", back_populates="owner", uselist=False, cascade="all, delete-orphan")
    learned_preferences = relationship("LearnedPreference", back_populates="owner", cascade="all, delete-orphan")
    resume_versions = relationship("ResumeVersion", back_populates="owner", cascade="all, delete-orphan")


# UserProfile Model (for core_data)
class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False) # One-to-one with User
    # We'll store the core_data as a JSON string for flexibility initially
    # In a more complex app, you might break this into separate tables (e.g., Education, Experience)
    core_data_json = Column(Text, nullable=True)

    owner = relationship("User", back_populates="user_profile")


# LearnedPreference Model
class LearnedPreference(Base):
    __tablename__ = "learned_preferences"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    # Store preference data as JSON string for now
    preference_data_json = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("User", back_populates="learned_preferences")


# ResumeVersion Model
class ResumeVersion(Base):
    __tablename__ = "resume_versions"

    id = Column(Integer, primary_key=True, index=True) # This will be our DB ID
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    # The 'id' that was generated as UUID for the file system can be stored as a string here
    resume_uuid = Column(String, unique=True, index=True, nullable=False) # This links to your original UUID
    version_name = Column(String, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    content = Column(Text, nullable=False) # The full resume content
    # Store related data as JSON strings, similar to your file system approach
    core_data_used_json = Column(Text, nullable=True)
    learned_preferences_used_json = Column(Text, nullable=True)
    target_job_description_used = Column(Text, nullable=True)
    critique_data_json = Column(Text, nullable=True) # The critique data

    owner = relationship("User", back_populates="resume_versions")