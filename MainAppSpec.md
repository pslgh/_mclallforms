# Engineering Services Company Main Application Specification

## Overview
This document provides specifications for a comprehensive management application for an engineering services company. The application will serve as a central platform with multiple sub-applications accessed through a hideable sidebar menu.

## Technology Stack
- **Frontend**: Python with PySide6 for UI
- **Data Storage**: JSON files (with MongoDB planned for future implementation)

## Core Application Features

### 1. Main Application Shell
- **Hideable Sidebar Menu**: Toggle visibility with a button
- **Authentication System**: Login screen for employees
- **Consistent UI**: Common styling across all sub-applications
- **Responsive Layout**: Adjust to different screen sizes

### 2. Navigation System
- **Sidebar Menu Structure**:
  - Dashboard (Home)
  - Expense Reimbursement
  - Service Timesheet
  - Quotation Generation & Tracking
  - Customer PO Record & Tracking
  - Settings
  - Help/Documentation

### 3. Dashboard
- Summary widgets showing key metrics from each sub-application
- Recent activities across all modules
- Quick action buttons to common tasks

### 4. Common Services Layer
- **Data Management**: Common utilities for reading/writing JSON files
- **User Management**: Employee profiles and access levels
- **Notification System**: Alert users about approvals, rejections, etc.
- **Reporting Engine**: Generate PDF reports with standardized formatting
- **Document Management**: Store, retrieve, and attach supporting documents
- **Audit Logging**: Track all system activities

## Technical Specifications

### 1. Application Architecture
- Main shell application (with login and sidebar)
- Modular sub-applications loaded dynamically
- Common utilities package for shared functionality

### 2. UI Design Guidelines
- **Color Scheme**: Professional blue-based palette
- **Typography**: Sans-serif fonts for readability
- **Layout**: Three-column design (sidebar, main content, optional details)
- **Components**: Reusable widgets across all sub-applications

### 3. Data Structure
- Central configuration file for application settings
- Each sub-application should have its own JSON data store
- Consistent data schema for user information across all modules

### 4. File Organization
```
engineering_app/
├── main.py                  # Application entry point
├── config.json              # App configuration
├── assets/                  # Images, icons, etc.
├── common/                  # Shared utilities
│   ├── data_manager.py      # JSON data handling
│   ├── auth.py              # Authentication
│   ├── ui_components.py     # Reusable UI components
│   └── pdf_generator.py     # Report generation
├── models/                  # Data models
├── views/                   # UI views
│   ├── main_window.py       # Main application window
│   ├── sidebar.py           # Sidebar implementation
│   └── login.py             # Login screen
├── modules/                 # Sub-applications
│   ├── expense/             # Expense reimbursement module
│   ├── timesheet/           # Service timesheet module
│   ├── quotation/           # Quotation generation module
│   └── po_tracking/         # PO tracking module
└── data/                    # JSON data storage
    ├── users.json           # User information
    ├── expenses/            # Expense records
    ├── timesheets/          # Timesheet records
    ├── quotations/          # Quotation records
    └── purchase_orders/     # PO records
```

## Implementation Guidelines

### 1. Main Window Class
```python
class MainWindow(QMainWindow):
    """Main application window with sidebar navigation."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Engineering Services Management")
        self.setupUi()
        self.loadModule("dashboard")
        
    def setupUi(self):
        # Setup sidebar, main content area, etc.
        
    def toggleSidebar(self):
        # Show/hide sidebar
        
    def loadModule(self, module_name):
        # Dynamic loading of different modules
```

### 2. Authentication Flow
- Login screen should appear first
- After successful login, show main application with sidebar
- Store session information for auto-login
- Include timeout/auto-logout for security

### 3. Module Loading System
- Each sub-application should be loadable independently
- Modules should share a common interface for integration
- State should be preserved when switching between modules

### 4. Data Management
- Create a common API for all JSON file operations
- Implement concurrency control for data access
- Include validation for all data operations
- Plan for future migration to MongoDB

## Additional Considerations

### 1. Performance
- Optimize for fast module switching
- Implement lazy loading for modules
- Minimize memory usage through efficient data structures

### 2. Security
- Encrypt sensitive data in JSON files
- Implement role-based access control
- Validate all user inputs

### 3. Future Expansion
- Design with scalability in mind
- Document API for adding new modules
- Plan for future web/mobile versions

### 4. Offline Operation
- All features should work without internet connection
- Implement data synchronization when connection is available
