"""
PDF Preview module for timesheet service and charge summary.
Displays a PDF preview dialog before saving.
"""
import os
import tempfile
from pathlib import Path

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, 
    QPushButton, QFileDialog, QMessageBox,
    QLabel, QSizePolicy
)
from PySide6.QtCore import Qt

# Try to import PDF-specific modules, but provide fallback implementation if not available
try:
    from PySide6.QtPdf import QPdfDocument
    from PySide6.QtPdfWidgets import QPdfView
    HAS_PDF_SUPPORT = True
    
    # Define zoom mode values based on what's actually available
    if hasattr(QPdfView, 'ZoomMode'):
        ZoomMode = QPdfView.ZoomMode
    else:
        # Fall back to fixed values that are commonly used
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
        self.setWindowTitle("Timesheet PDF Preview")
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
            
            # Reset zoom button
            self.reset_button = QPushButton("Reset Zoom")
            self.reset_button.setToolTip("Reset to 100% zoom")
            self.reset_button.clicked.connect(self.reset_zoom)
            zoom_layout.addWidget(self.reset_button)
            
            # Fit page button
            self.fit_button = QPushButton("Fit Page")
            self.fit_button.setToolTip("Fit entire page to view")
            self.fit_button.clicked.connect(self.fit_to_page)
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
            
            # Create document object
            self.pdf_document = QPdfDocument()
            self.pdf_view.setDocument(self.pdf_document)
            
            # Add page navigation buttons
            page_nav_layout = QHBoxLayout()
            
            # Previous page button
            self.prev_page_btn = QPushButton("← Previous Page")
            self.prev_page_btn.clicked.connect(self.go_to_prev_page)
            page_nav_layout.addWidget(self.prev_page_btn)
            
            # Page indicator
            self.page_indicator = QLabel("Page 1")
            self.page_indicator.setAlignment(Qt.AlignCenter)
            self.page_indicator.setMinimumWidth(100)
            page_nav_layout.addWidget(self.page_indicator)
            
            # Next page button
            self.next_page_btn = QPushButton("Next Page →")
            self.next_page_btn.clicked.connect(self.go_to_next_page)
            page_nav_layout.addWidget(self.next_page_btn)
            
            # Add navigation layout to the main layout
            layout.addLayout(page_nav_layout)
            
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
        
        # Print button
        self.print_button = QPushButton("Print")
        self.print_button.clicked.connect(self.print_pdf)
        button_layout.addWidget(self.print_button)
        
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
            self.pdf_view.setZoomFactor(self.current_zoom)
            
            # Make sure all pages are visible by setting the zoom mode to fit width
            if ZoomMode is not None:
                self.pdf_view.setZoomMode(ZoomMode.FitToWidth)
            
            # Get total page count
            total_pages = self.pdf_document.pageCount()
            
            # Let's use the actual page count detected in the PDF document
            # This ensures we show the correct number of pages based on content
            
            # Store the total page count for reference in other methods
            self._total_pages = total_pages
            
            # Initialize page indicator
            self.page_indicator.setText(f"Page 1 of {total_pages}")
            
            # Set initial button states
            self.prev_page_btn.setEnabled(False)  # Disable prev button on first page
            self.next_page_btn.setEnabled(total_pages > 1)  # Enable next if multiple pages
            
            if total_pages > 1:
                # Let the user know there are multiple pages
                page_info = QLabel(f"Document has {total_pages} pages. Use navigation buttons or scroll to view all pages.")
                page_info.setStyleSheet("color: blue; font-weight: bold;")
                page_info.setAlignment(Qt.AlignCenter)
                
                # Insert above the PDF view
                layout = self.layout()
                layout.insertWidget(1, page_info)
                
                # Connect to page change signals if available
                try:
                    navigator = self.pdf_view.pageNavigator()
                    navigator.currentPageChanged.connect(self.update_page_indicator)
                except Exception as e:
                    print(f"Could not connect to page change signal: {e}")
        
    def zoom_in(self):
        """Increase zoom level by 10%"""
        if not HAS_PDF_SUPPORT:
            return
            
        try:
            # First ensure we're in custom zoom mode, not fit mode
            if ZoomMode is not None:
                self.pdf_view.setZoomMode(ZoomMode.Custom)
            
            # Get current zoom factor
            current = self.pdf_view.zoomFactor()
            
            # Calculate new zoom factor (increase by 10%)
            new_zoom = current * 1.1
            
            # Set new zoom factor
            self.pdf_view.setZoomFactor(new_zoom)
            
            # Update zoom label
            self.zoom_label.setText(f"{int(new_zoom * 100)}%")
            
            # Update current zoom
            self.current_zoom = new_zoom
        except Exception as e:
            print(f"Error zooming in: {e}")
    
    def zoom_out(self):
        """Decrease zoom level by 10%"""
        if not HAS_PDF_SUPPORT:
            return
            
        try:
            # First ensure we're in custom zoom mode, not fit mode
            if ZoomMode is not None:
                self.pdf_view.setZoomMode(ZoomMode.Custom)
            
            # Get current zoom factor
            current = self.pdf_view.zoomFactor()
            
            # Calculate new zoom factor (decrease by 10%)
            new_zoom = max(0.1, current * 0.9)
            
            # Set new zoom factor
            self.pdf_view.setZoomFactor(new_zoom)
            
            # Update zoom label
            self.zoom_label.setText(f"{int(new_zoom * 100)}%")
            
            # Update current zoom
            self.current_zoom = new_zoom
        except Exception as e:
            print(f"Error zooming out: {e}")
    
    def fit_to_page(self):
        """Fit the entire page to the view"""
        if not HAS_PDF_SUPPORT:
            return
            
        try:
            # Set zoom mode to fit page
            if ZoomMode is not None:
                self.pdf_view.setZoomMode(ZoomMode.FitInView)
                
                # Update the zoom label to show "Fit Page"
                self.zoom_label.setText("Fit Page")
                
                # Store current zoom factor so we can restore it when user zooms in/out again
                self.current_zoom = self.pdf_view.zoomFactor()
        except Exception as e:
            print(f"Error fitting page to view: {e}")
    
    def reset_zoom(self):
        """Reset zoom to 100%"""
        if not HAS_PDF_SUPPORT:
            return
            
        try:
            # Ensure we're in custom zoom mode
            if ZoomMode is not None:
                self.pdf_view.setZoomMode(ZoomMode.Custom)
            
            # Reset zoom factor to 1.0 (100%)
            self.pdf_view.setZoomFactor(1.0)
            
            # Update zoom label
            self.zoom_label.setText("100%")
            
            # Update current zoom
            self.current_zoom = 1.0
        except Exception as e:
            print(f"Error resetting zoom: {e}")
    
    def go_to_prev_page(self):
        """Navigate to the previous page"""
        if not HAS_PDF_SUPPORT:
            return
            
        try:
            # Get current page
            current_page = self.pdf_view.pageNavigator().currentPage()
            
            # Go to previous page if not already at first page
            if current_page > 0:
                # Create a point at the top center of the page
                from PySide6.QtCore import QPointF
                location = QPointF(0.5, 0)
                
                # Jump to previous page
                self.pdf_view.pageNavigator().jump(current_page - 1, location)
                self.update_page_indicator(current_page - 1)
        except Exception as e:
            print(f"Error navigating to previous page: {e}")
    
    def go_to_next_page(self):
        """Navigate to the next page"""
        if not HAS_PDF_SUPPORT:
            return
            
        try:
            # Get current page and total page count
            current_page = self.pdf_view.pageNavigator().currentPage()
            total_pages = self.pdf_document.pageCount()
            
            # Go to next page if not already at last page
            if current_page < total_pages - 1:
                # Create a point at the top center of the page
                from PySide6.QtCore import QPointF
                location = QPointF(0.5, 0)
                
                # Jump to next page
                self.pdf_view.pageNavigator().jump(current_page + 1, location)
                self.update_page_indicator(current_page + 1)
        except Exception as e:
            print(f"Error navigating to next page: {e}")
    
    def update_page_indicator(self, page_number):
        """Update the page indicator label"""
        if not HAS_PDF_SUPPORT:
            return
        
        # Use the stored total pages value for consistency
        total_pages = getattr(self, '_total_pages', self.pdf_document.pageCount())
        
        self.page_indicator.setText(f"Page {page_number + 1} of {total_pages}")
        
        # Update button states
        self.prev_page_btn.setEnabled(page_number > 0)
        self.next_page_btn.setEnabled(page_number < total_pages - 1)
    
    def save_pdf(self):
        """Save the PDF to a user-selected location"""
        if not self.temp_pdf_path or not os.path.exists(self.temp_pdf_path):
            QMessageBox.warning(self, "Error", "PDF file not found or could not be created.")
            return
            
        # Set default directory and filename
        default_dir = os.path.expanduser("~/Documents")
        
        # Use suggested filename if provided, otherwise use a generic name
        default_name = self.suggested_filename or "timesheet.pdf"
        default_path = os.path.join(default_dir, default_name)
        
        # Open file dialog to get save location
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Timesheet PDF",
            default_path,
            "PDF Files (*.pdf)"
        )
        
        if not file_path:
            # User canceled
            return
        
        try:
            # Ensure the path has .pdf extension
            if not file_path.lower().endswith('.pdf'):
                file_path += '.pdf'
                
            # Copy temporary PDF to selected location
            import shutil
            shutil.copy2(self.temp_pdf_path, file_path)
            
            # Store saved path
            self.saved_path = file_path
            
            # Show success message
            QMessageBox.information(
                self,
                "PDF Saved",
                f"The timesheet PDF has been saved to:\n{file_path}"
            )
            
            # Close dialog with accept status
            self.accept()
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error Saving PDF",
                f"Failed to save PDF: {str(e)}"
            )

    def print_pdf(self):
        """Print the PDF"""
        if not self.temp_pdf_path or not os.path.exists(self.temp_pdf_path):
            QMessageBox.warning(self, "Error", "PDF file not found or could not be created.")
            return
            
        try:
            from PySide6.QtPrintSupport import QPrinter, QPrintDialog
            
            printer = QPrinter(QPrinter.HighResolution)
            dialog = QPrintDialog(printer, self)
            
            if dialog.exec() == QPrintDialog.Accepted:
                # For now, show a message that printing is not fully implemented
                QMessageBox.information(
                    self,
                    "Print Request",
                    "Print feature is not fully implemented.\n\n"
                    "Please use the Save PDF option and print from your PDF viewer."
                )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error Printing",
                f"Failed to print PDF: {str(e)}"
            )

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
    try:
        # Create a temporary directory
        temp_dir = tempfile.mkdtemp()
        
        # Create a temporary file path
        temp_pdf_path = os.path.join(temp_dir, "temp_timesheet.pdf")
        
        # Create the PDF
        create_pdf_func(data, temp_pdf_path)
        
        # Check if the PDF was created
        if not os.path.exists(temp_pdf_path):
            if parent_widget:
                QMessageBox.critical(
                    parent_widget,
                    "PDF Creation Error",
                    "Failed to create the PDF file."
                )
            return None
        
        # Show the preview dialog
        dialog = PDFPreviewDialog(
            parent=parent_widget,
            temp_pdf_path=temp_pdf_path,
            suggested_filename=suggested_filename
        )
        
        # Show dialog and get result
        result = dialog.exec()
        
        # Get saved path from dialog
        saved_path = dialog.saved_path
        
        # Clean up temporary files if the dialog was accepted (PDF was saved elsewhere)
        # or if we're returning None because the dialog was cancelled
        # Schedule the cleanup for later since the file might still be in use
        import shutil
        import atexit
        
        def delayed_cleanup(directory):
            """Function to clean up temp files on application exit"""
            try:
                if os.path.exists(directory):
                    shutil.rmtree(directory)
            except Exception as e:
                # Suppress the error message, as it's just cleanup of temp files
                pass
        
        # Register the cleanup function to run at program exit
        atexit.register(delayed_cleanup, temp_dir)
        
        # Return the path where the PDF was saved, or None if cancelled
        return saved_path if result == QDialog.Accepted and saved_path else None
    
    except Exception as e:
        if parent_widget:
            QMessageBox.critical(
                parent_widget,
                "PDF Preview Error",
                f"Error creating or previewing PDF: {str(e)}"
            )
        return None
