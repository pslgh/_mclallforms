"""
PDF Preview module for expense reimbursement.
Displays a PDF preview dialog before saving.
"""
import os
import tempfile
from pathlib import Path

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, 
    QPushButton, QFileDialog, QMessageBox,
    QLabel, QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt, QUrl, QSize, QPoint
from PySide6.QtGui import QPixmap, QImage

# Try to import PDF-specific modules, but provide fallback implementation if not available
try:
    from PySide6.QtPdf import QPdfDocument
    from PySide6.QtPdfWidgets import QPdfView
    HAS_PDF_SUPPORT = True
    
    # Define zoom mode values based on what's actually available
    # In some PySide6 versions, these values may be different
    # Let's discover what's available
    if hasattr(QPdfView, 'ZoomMode'):
        ZoomMode = QPdfView.ZoomMode
        # Print all available zoom modes for debugging
        # print("Available ZoomMode values:", dir(ZoomMode))
    else:
        # Fall back to fixed values that are commonly used
        # print("ZoomMode not available, using fallback values")
        ZoomMode = None
except ImportError:
    HAS_PDF_SUPPORT = False
    ZoomMode = None

class PDFPreviewDialog(QDialog):
    """Dialog for previewing a PDF before saving"""
    
    def __init__(self, parent=None, temp_pdf_path=None, suggested_filename=None):
        """
        Initialize the PDF Preview Dialog
        
        Args:
            parent: Parent widget
            temp_pdf_path: Path to the temporary PDF file to preview
            suggested_filename: Suggested filename when saving
        """
        super().__init__(parent)
        self.parent = parent
        self.temp_pdf_path = temp_pdf_path
        self.suggested_filename = suggested_filename
        self.saved_path = None
        
        # Get the screen size to make dialog a reasonable size
        if parent:
            screen_size = parent.screen().size()
        else:
            from PySide6.QtWidgets import QApplication
            screen_size = QApplication.primaryScreen().size()
            
        # Set dialog to 80% of screen size
        dialog_width = int(screen_size.width() * 0.8)
        dialog_height = int(screen_size.height() * 0.8)
        self.resize(dialog_width, dialog_height)
        
        # Set up the UI
        self.setWindowTitle("PDF Preview")
        self.setup_ui()
        
        # Load the PDF
        self.load_pdf()
        
    def setup_ui(self):
        """Set up the dialog UI"""
        layout = QVBoxLayout(self)
        
        if HAS_PDF_SUPPORT:
            # Add zoom controls at the top
            zoom_layout = QHBoxLayout()
            
            # Zoom out button
            self.zoom_out_button = QPushButton("-")
            self.zoom_out_button.setToolTip("Zoom Out")
            self.zoom_out_button.clicked.connect(self.zoom_out)
            zoom_layout.addWidget(self.zoom_out_button)
            
            # Current zoom level label
            self.zoom_label = QLabel("100%")
            self.zoom_label.setAlignment(Qt.AlignCenter)
            self.zoom_label.setMinimumWidth(70)
            zoom_layout.addWidget(self.zoom_label)
            
            # Zoom in button
            self.zoom_in_button = QPushButton("+")
            self.zoom_in_button.setToolTip("Zoom In")
            self.zoom_in_button.clicked.connect(self.zoom_in)
            zoom_layout.addWidget(self.zoom_in_button)
            
            # Reset zoom button (renamed from Fit)
            self.fit_button = QPushButton("Reset Zoom")
            self.fit_button.setToolTip("Reset to 100% zoom")
            self.fit_button.clicked.connect(self.reset_zoom)
            zoom_layout.addWidget(self.fit_button)
            
            # Add spacer to push controls to the left
            zoom_layout.addStretch(1)
            
            # Add zoom controls to main layout
            layout.addLayout(zoom_layout)
            
            # Create PDF view using Qt's built-in PDF viewer
            self.pdf_view = QPdfView()
            self.pdf_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            
            # Initialize with a default zoom factor of 1.0 (100%)
            self.current_zoom = 1.0
            
            # We'll set the zoom factor directly after loading the document
            # This tends to work better than setting the zoom mode
            # print("PDF view created with initial zoom factor of 1.0")
            
            # Create document object
            self.pdf_document = QPdfDocument()
            self.pdf_view.setDocument(self.pdf_document)
            
            # Add PDF view to layout
            layout.addWidget(self.pdf_view)
        else:
            # Fallback implementation when QtPdf is not available
            self.info_label = QLabel("PDF Preview not available. QtPdf module is required.")
            self.info_label.setAlignment(Qt.AlignCenter)
            self.info_label.setStyleSheet("font-size: 14px; color: #555;")
            layout.addWidget(self.info_label)
            
            # Additional instructions
            file_path_label = QLabel(f"The PDF has been created at: {self.temp_pdf_path}")
            file_path_label.setAlignment(Qt.AlignCenter)
            file_path_label.setWordWrap(True)
            layout.addWidget(file_path_label)
        
        # Create button layout
        button_layout = QHBoxLayout()
        
        # Save button
        self.save_button = QPushButton("Save PDF")
        self.save_button.clicked.connect(self.save_pdf)
        button_layout.addWidget(self.save_button)
        
        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        # Add button layout to main layout
        layout.addLayout(button_layout)
        
    def load_pdf(self):
        """Load the PDF into the preview"""
        if not self.temp_pdf_path or not os.path.exists(self.temp_pdf_path):
            QMessageBox.warning(self, "Error", "PDF file not found or could not be created.")
            self.reject()
            return
            
        if HAS_PDF_SUPPORT:
            # Load the PDF document using QtPdf
            self.pdf_document.load(self.temp_pdf_path)
            
            # Check for loading errors
            if self.pdf_document.status() != QPdfDocument.Status.Ready:
                QMessageBox.warning(self, "Error", "Failed to load PDF for preview.")
                self.reject()
                return
                
            # Now that document is loaded, apply initial zoom factor
            print("Document loaded successfully, setting initial zoom factor")
            self.pdf_view.setZoomFactor(self.current_zoom)
            
            # Verify zoom factor was set
            actual_zoom = self.pdf_view.zoomFactor()
            print(f"Initial zoom factor set to: {actual_zoom}")
            
    def _set_custom_zoom(self):
        """Helper to set up for custom zoom level"""
        # Don't try to set zoom mode, just apply zoom factor directly
        pass
        
    def _set_fit_view(self):
        """Helper to make document fit in view"""
        # Simply reset the zoom factor to 1.0
        # This is a safer approach than trying to use page navigation
        pass
    
    def zoom_in(self):
        """Increase zoom level by 10%"""
        if not HAS_PDF_SUPPORT:
            return
            
        try:
            # Print current zoom factor before change
            current = self.pdf_view.zoomFactor()
            # print(f"Current zoom factor before zoom in: {current}")
            
            # Increase zoom by 10%
            self.current_zoom += 0.1
            if self.current_zoom > 5.0:  # Limit to 500%
                self.current_zoom = 5.0
            
            # print(f"Setting zoom factor to: {self.current_zoom}")
                
            # Apply zoom factor directly - force the view to use our zoom
            self.pdf_view.setZoomFactor(self.current_zoom)
            
            # Double-check if zoom was applied
            new_zoom = self.pdf_view.zoomFactor()
            # print(f"Zoom factor after setting: {new_zoom}")
            
            # Update label
            self.zoom_label.setText(f"{int(self.current_zoom * 100)}%")
            
            # Force update
            self.pdf_view.update()
        except Exception as e:
            # print(f"Error during zoom in: {e}")
            pass
        
    def zoom_out(self):
        """Decrease zoom level by 10%"""
        if not HAS_PDF_SUPPORT:
            return
            
        try:
            # Print current zoom factor before change
            current = self.pdf_view.zoomFactor()
            # print(f"Current zoom factor before zoom out: {current}")
            
            # Decrease zoom by 10%
            self.current_zoom -= 0.1
            if self.current_zoom < 0.2:  # Limit to 20%
                self.current_zoom = 0.2
            
            # print(f"Setting zoom factor to: {self.current_zoom}")
                
            # Apply zoom factor directly - force the view to use our zoom
            self.pdf_view.setZoomFactor(self.current_zoom)
            
            # Double-check if zoom was applied
            new_zoom = self.pdf_view.zoomFactor()
            # print(f"Zoom factor after setting: {new_zoom}")
            
            # Update label
            self.zoom_label.setText(f"{int(self.current_zoom * 100)}%")
            
            # Force update
            self.pdf_view.update()
        except Exception as e:
            print(f"Error during zoom out: {e}")
            pass
        
    def reset_zoom(self):
        """Reset zoom to 100%"""
        if not HAS_PDF_SUPPORT:
            return
            
        try:
            # Reset zoom factor directly to 1.0 (100%)
            self.current_zoom = 1.0
            
            # Force the zoom factor directly
            self.pdf_view.setZoomFactor(1.0)
            
            # Update the label
            self.zoom_label.setText("100%")
            
            # Force the view to update
            self.pdf_view.update()
            
            print("Zoom reset to 100%")
        except Exception as e:
            # print(f"Error resetting zoom: {e}")
            pass
    
    def save_pdf(self):
        """Save the PDF to a user-selected location"""
        # Determine default directory and filename
        if self.suggested_filename:
            default_name = self.suggested_filename
        else:
            default_name = os.path.basename(self.temp_pdf_path)
            
        # Get default directory - user's documents folder
        documents_dir = os.path.join(os.path.expanduser('~'), 'Documents')
        expense_reports_dir = os.path.join(documents_dir, 'ExpenseReports')
        
        # Create directory if it doesn't exist
        try:
            os.makedirs(expense_reports_dir, exist_ok=True)
        except Exception:
            # Fall back to Documents folder
            expense_reports_dir = documents_dir
            
        # Show save dialog
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save PDF",
            os.path.join(expense_reports_dir, default_name),
            "PDF Files (*.pdf)"
        )
        
        if not file_path:
            # User cancelled
            return
            
        try:
            # Make sure target directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Copy the file
            import shutil
            shutil.copy2(self.temp_pdf_path, file_path)
            
            # Store the saved path
            self.saved_path = file_path
            
            # Close dialog with accept result
            self.accept()
        except Exception as e:
            QMessageBox.warning(self, "Save Error", f"Error saving PDF: {str(e)}")
            
def create_and_preview_pdf(create_pdf_func, data, parent_widget=None, suggested_filename=None):
    """
    Create a PDF using the provided function and show it in a preview dialog
    
    Args:
        create_pdf_func: Function that creates a PDF (accepts data and path parameters)
        data: Data to pass to the create_pdf_func
        parent_widget: Parent widget for the dialog
        suggested_filename: Suggested filename for saving
        
    Returns:
        str: Path where the PDF was saved, or None if cancelled
    """
    # Create a temporary file for the PDF
    temp_fd, temp_path = tempfile.mkstemp(suffix='.pdf')
    os.close(temp_fd)  # Close the file descriptor
    
    try:
        # Create the PDF in the temporary file
        create_pdf_func(data, temp_path)
        
        # Create and show the preview dialog
        preview_dialog = PDFPreviewDialog(
            parent=parent_widget,
            temp_pdf_path=temp_path,
            suggested_filename=suggested_filename
        )
        
        # Show the dialog modally
        result = preview_dialog.exec()
        
        # Return the saved path if accepted
        if result == QDialog.Accepted and preview_dialog.saved_path:
            return preview_dialog.saved_path
        else:
            return None
            
    except Exception as e:
        if parent_widget:
            QMessageBox.warning(
                parent_widget,
                "Preview Error",
                f"Error creating PDF preview: {str(e)}"
            )
        return None
    finally:
        # Clean up temporary file
        try:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
        except Exception:
            pass  # Ignore deletion errors
