"""Main driver for the PDF loader service.

This module serves as the entry point for the loader service that processes
PDFs from a configurable directory path.
"""

import os
import sys
from pathlib import Path

from loader import Loader


def get_pdf_path() -> str:
    """Get the PDF path from environment variables.

    Returns:
        The path to the directory containing PDFs to process.

    Raises:
        ValueError: If PDF_PATH environment variable is not set.
    """
    pdf_path = os.getenv("PDF_PATH", "/data/book")
    if not pdf_path:
        raise ValueError("PDF_PATH environment variable must be set")
    return pdf_path


def main() -> None:
    """Main function to run the PDF loader service.

    This function initializes the PDF processor and processes all PDFs
    in the configured directory.
    """
    try:
        pdf_path = get_pdf_path()
        print("Starting PDF loader service...")
        print(f"Processing PDFs from: {pdf_path}")

        # Initialize the PDF processor
        processor = Loader()

        # Process PDFs from the configured path
        pdf_directory = Path(pdf_path)
        if not pdf_directory.exists():
            print(f"Warning: PDF directory {pdf_path} does not exist")
            return

        pdf_files = list(pdf_directory.glob("*.pdf"))
        if not pdf_files:
            print(f"No PDF files found in {pdf_path}")
            return

        print(f"Found {len(pdf_files)} PDF files to process")

        for pdf_file in pdf_files:
            print(f"Processing: {pdf_file.name}")
            try:
                # Process the PDF file
                processor.process_pdf_file(pdf_file)
                print(f"Successfully processed: {pdf_file.name}")
            except Exception as e:
                print(f"Error processing {pdf_file.name}: {e}")

        print("PDF loading service completed")

    except Exception as e:
        print(f"Error in PDF loader service: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
