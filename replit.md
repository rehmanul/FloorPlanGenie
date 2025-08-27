# Overview

FloorPlanGenie is an AI-powered web application that provides intelligent space optimization for floor plans. The system allows users to upload floor plan files (PDF, DWG, DXF, JPG, PNG), processes them to extract walls and dimensions, and then optimizes space placement using advanced algorithms. The application features both an interactive floor plan editor and an automated optimization engine that can place boxes/rooms and generate corridors while maximizing space efficiency.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Frontend Architecture
- **Technology Stack**: HTML, CSS, JavaScript with Canvas API for interactive drawing
- **Design Pattern**: Component-based architecture with a main FloorPlanGenie class managing tool interactions
- **Interactive Features**: 
  - Drag-and-drop file upload interface
  - Real-time drawing tools (walls, rooms, doors, windows, furniture)
  - Zoom and pan controls for canvas manipulation
  - Visual feedback with progress bars and tool selection states

## Backend Architecture
- **Framework**: Flask web framework with Python
- **Architecture Pattern**: Service-oriented with specialized processor classes
- **Core Components**:
  - `PlanProcessor`: Handles file parsing and feature extraction from various formats
  - `SpaceOptimizer`: Implements genetic algorithms for optimal space placement
  - `VisualGenerator`: Creates matplotlib-based visualizations and exports
- **File Handling**: Secure file uploads with 50MB size limit and sanitized filenames

## Data Processing Pipeline
- **Multi-format Support**: Dedicated processors for CAD files (DXF/DWG), PDFs, and images
- **Feature Extraction**: Automated detection of walls, dimensions, and spatial zones
- **Optimization Engine**: Uses scipy differential evolution and genetic algorithms for space optimization
- **Collision Detection**: Advanced algorithms to prevent overlapping placements and ensure corridor accessibility

## Visualization System
- **Rendering Engine**: Matplotlib-based generation of 2D floor plan visualizations
- **Interactive Canvas**: HTML5 Canvas with real-time drawing and editing capabilities
- **Export Capabilities**: Multiple output formats for optimized layouts
- **Real-time Updates**: Dynamic visual feedback during optimization process

# Recent Changes

## Replit Environment Migration (August 27, 2025)
- ✅ Migrated from Replit Agent to full Replit environment
- ✅ Restructured Flask app with proper security practices (SESSION_SECRET, ProxyFix)
- ✅ Added Flask-SQLAlchemy database integration with proper models
- ✅ Fixed all type safety issues and error handling
- ✅ Created proper main.py entry point following Replit guidelines
- ✅ Application now runs cleanly on port 5000 with debug mode
- ✅ Database models for FloorPlan and OptimizationResult created
- ✅ Secure session management and file upload handling implemented

## Previous Migration Completed (August 27, 2025)
- ✅ Successfully migrated from placeholder/demo data to real architectural file processing
- ✅ Enhanced CAD file processing to handle complex DXF/DWG files with proper scaling
- ✅ Removed all fallback/fake data generation - system now requires authentic architectural files
- ✅ Implemented professional visualization styling matching architectural standards
- ✅ Added proper error handling for invalid files (no fake data fallbacks)
- ✅ Verified system processes real files: 120m×97m apartment plans with 23,885+ walls
- ✅ Space optimization algorithm handles authentic architectural complexity

# External Dependencies

## Python Libraries
- **Flask**: Web framework for API endpoints and request handling
- **PIL (Pillow)**: Image processing and manipulation
- **OpenCV**: Advanced image analysis and feature detection
- **ezdxf**: CAD file parsing for DWG/DXF formats
- **PyPDF2**: PDF file processing and text extraction
- **matplotlib**: Scientific plotting and visualization generation
- **scipy**: Optimization algorithms and mathematical computations
- **numpy**: Numerical computing and array operations

## Frontend Libraries
- **HTML5 Canvas API**: Interactive drawing and real-time editing
- **Native JavaScript**: No external frameworks, pure vanilla JS implementation

## File Format Support
- **CAD Files**: DWG, DXF format processing
- **Document Files**: PDF parsing and analysis
- **Image Files**: JPG, JPEG, PNG support for scanned floor plans

## Optimization Algorithms
- **Genetic Algorithms**: Custom implementation for space placement optimization
- **Differential Evolution**: Scipy-based optimization for complex constraint solving
- **Collision Detection**: Custom algorithms for spatial conflict resolution