import os
import queue
import threading
import logging
from PyPDF2 import PdfFileReader, PdfFileWriter
from numpy import double

from reportlab.lib.colors import lightskyblue
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.units import mm

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Define paths
MARKS_PATH = 'mark.pdf'
INPUT_PATH = 'input.pdf'
OUTPUT_PATH = 'temp_output.pdf'
COORDINATES_PATH = "numbers"

# Define constants for conversion
ALPHA = 0.307  # For converting original coordination system to mm
SCALE = 0.50  # For scaling marks


def logger_thread_func(log_queue):
    """Helper function for logger thread"""
    while True:
        msg = log_queue.get()
        if msg == 'stop':
            break
        logging.info(msg)


def stop_and_exit(log_queue: queue.Queue, logger_thread: threading.Thread, exit_code: int):
    """Gracefully stop logger thread and exit with given code"""
    log_queue.put('stop')
    logger_thread.join()
    exit(exit_code)


def files_are_accessible(paths: list[str]) -> bool:
    """Check if all files exist, are not empty and are accessible"""
    for path in paths:
        if not os.path.exists(path) \
                or not os.path.isfile(path) \
                or not os.access(path, os.R_OK) \
                or os.path.getsize(path) == 0:
            return False
    return True


def paths_are_valid(pdfs: list[str], txts: list[str]) -> bool:
    """Check if all files have correct extensions and are accessible"""
    for pdf in pdfs:
        if not pdf.endswith('.pdf'):
            print("Input and output files must be pdf")
            return False
    for txt in txts:
        if not txt.endswith('.txt'):
            print("Coordinates file must be txt")
            return False
    if not files_are_accessible(pdfs + txts):
        print("Input file or coordinates file does not exist")
        return False
    return True


def get_number_of_pages(path: str) -> int:
    """Return number of pages in PDF file"""
    with open(path, 'rb') as f:
        pdf = PdfFileReader(f)
        return pdf.getNumPages()


def read_coordinates(txt_path: str) -> list[str]:
    """Return list of coordinates for every mark to draw"""
    with open(txt_path) as f:
        content = f.readlines()
        return content


def create_marks_pdf(output_path: str, marks: list[str], size: tuple[int, int]):
    print("Got size: ", size)
    """Generate empty PDF file with marks on it"""
    canvas = Canvas(output_path, pagesize=A4)
    height, width = float(size[0])*SCALE, float(size[1])*SCALE
    bubble_number = 0
    page_number = 1
    for mark in marks:
        mark = mark.replace(',', '.')
        parameters = mark.split(' ')
        zoom = double(parameters[3])
        x = double(parameters[1]) * ALPHA / zoom
        y = height - (double(parameters[2]) * ALPHA) / zoom

        if page_number < int(parameters[0]):
            page_number = int(parameters[0])
            canvas.showPage()  # Close page and move to the next one.

        canvas.setFillColor(lightskyblue)
        canvas.setFont("Helvetica-Bold", 8)
        canvas.drawString(x * mm, y * mm, str(bubble_number + 1))
        bubble_number += 1
    canvas.save()


def draw_marks(original_path: str, result_path: str, marks_path: str):
    """Use marks PDF file to draw them on original PDF file page by page"""
    mark_reader = PdfFileReader(marks_path)
    original_reader = PdfFileReader(original_path)
    writer = PdfFileWriter()
    for page_number in range(mark_reader.getNumPages()):
        page = original_reader.getPage(page_number)
        page.mergePage(mark_reader.getPage(page_number))
        writer.addPage(page)
    with open(result_path, 'wb') as output:
        writer.write(output)


def cleanup(paths: list[str]):
    """Remove files that were created during PDF generation"""
    for path in paths:
        if os.path.exists(path):
            os.remove(path)


def start_logger() -> tuple[queue.Queue, threading.Thread]:
    """Logging is done in separate thread to avoid blocking main thread"""
    log_queue = queue.Queue()
    logger_thread = threading.Thread(target=logger_thread_func, args=(log_queue,))
    logger_thread.start()
    return log_queue, logger_thread


def validate_input(log_queue: queue.Queue) -> tuple[bool, int, list[str]]:
    """
    Input files should not be empty and should be accessible.
    PDF files should have .pdf extension and coordinates file should have .txt extension.
    """
    if not paths_are_valid([INPUT_PATH, OUTPUT_PATH], [COORDINATES_PATH]):
        return False, 0, []
    msg = f"""
    Working with: 
    Input file: {INPUT_PATH}
    Coordinates file: {COORDINATES_PATH}
    Output file: {OUTPUT_PATH}
    """
    log_queue.put(msg)

    input_page_count = get_number_of_pages(INPUT_PATH)
    if input_page_count == 0:
        print("Input file is empty")
        return False, 0, []
    msg = f"""
    Information about {INPUT_PATH}:
    Number of pages: {input_page_count}
    """
    log_queue.put(msg)

    coordinates = read_coordinates(COORDINATES_PATH)
    if len(coordinates) == 0:
        print("Coordinates file is empty")
        return False, 0, []

    return True, input_page_count, coordinates


def get_page_size(pdf_path: str) -> tuple[int, int]:
    """Return size of input PDF file in mm"""
    with open(pdf_path, 'rb') as f:
        pdf = PdfFileReader(f)
        page = pdf.getPage(0)
        return page.mediaBox[2], page.mediaBox[3]


def execute(coordinates: list[str]):
    """Generate marks PDF file and draw marks on original PDF file"""
    try:
        size = get_page_size(INPUT_PATH)
        create_marks_pdf(MARKS_PATH, coordinates, size)
        draw_marks(INPUT_PATH, OUTPUT_PATH, MARKS_PATH)

    except Exception as e:
        raise RuntimeError("There was an error during PDF generation: ", e)

    try:
        cleanup([MARKS_PATH])

    except Exception as e:
        raise RuntimeError("There was an error during cleanup: ", e)


def validate_output(input_page_count: int, log_queue: queue.Queue):
    """Output file should not be empty and should have the same number of pages as input file"""
    output_page_count = get_number_of_pages(OUTPUT_PATH)
    if output_page_count == 0:
        print("Something went wrong: output file is empty")
        exit(1)
    if input_page_count != output_page_count:
        print("Some pages were not processed correctly: "
              "input and output page count does not match.\n")
    msg = f"""
    Information about {OUTPUT_PATH}:
    Number of pages: {output_page_count}
    """
    log_queue.put(msg)


def main():
    log_queue, logger_thread = start_logger()
    valid, input_page_count, coordinates = validate_input(log_queue)
    if not valid:
        stop_and_exit(log_queue, logger_thread, 1)

    try:
        execute(coordinates)
    except RuntimeError as e:
        print(e)
        stop_and_exit(log_queue, logger_thread, 1)
    except Exception as e:
        print("Something went wrong: ", e)
        stop_and_exit(log_queue, logger_thread, 1)

    validate_output(input_page_count, log_queue)
    stop_and_exit(log_queue, logger_thread, 0)


if __name__ == '__main__':
    main()
