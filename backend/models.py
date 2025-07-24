# -*- coding: utf-8 -*-
"""
Modelos ORM para la base de datos.
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship

from backend.database import Base

class InstagramProfile(Base):
    __tablename__ = "instagram_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    full_name = Column(String)
    last_scraped = Column(DateTime)
    
    posts = relationship("Post", back_populates="profile")

class Post(Base):
    __tablename__ = "posts"
    
    id = Column(Integer, primary_key=True, index=True)
    shortcode = Column(String, unique=True, index=True)
    profile_id = Column(Integer, ForeignKey("instagram_profiles.id"))
    caption = Column(Text)
    timestamp = Column(DateTime, index=True)
    image_path = Column(String)
    ocr_text = Column(Text)
    is_job_post = Column(Boolean, default=False)
    
    profile = relationship("InstagramProfile", back_populates="posts")
    job = relationship("JobPost", back_populates="post", uselist=False)

class JobPost(Base):
    __tablename__ = "job_posts"
    
    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"), unique=True)
    company = Column(String, index=True)
    title = Column(String, index=True)
    area = Column(String, index=True)
    skills = Column(JSON)
    benefits = Column(JSON)
    deadline = Column(String)
    is_open = Column(Boolean, default=True)
    
    post = relationship("Post", back_populates="job")
