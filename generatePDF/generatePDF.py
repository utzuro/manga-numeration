from PyPDF2 import PdfFileReader, PdfFileWriter
from numpy import double

from reportlab.lib.colors import lightskyblue
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.units import mm


def get_number_of_pages(path):
    with open(path, 'rb') as f:
        pdf = PdfFileReader(f)
        num_of_pages = pdf.getNumPages()

        log = f"""
        Information about {path}:
        Number of pages: {num_of_pages}
        """

        print(log)
        return num_of_pages


def read_coordinates(txt_path):
    with open(txt_path) as f:
        content = f.readlines()
        return content


def con_pdfs(paths, output):
    pdf_writer = PdfFileWriter()
    for path in paths:
        pdf_reader = PdfFileReader(path)
        for page in range(pdf_reader.getNumPages()):
            pdf_writer.addPage(pdf_reader.getPage(page))
    with open(output, 'wb') as output:
        pdf_writer.write(output)


def merge_pdfs(original, output, mark):
    mark_reader = PdfFileReader(mark)
    original_reader = PdfFileReader(original)
    writer = PdfFileWriter()

    if mark_reader.getNumPages() != original_reader.getNumPages():
        print("Number of pages is not the same")
        # return

    for page_number in range(mark_reader.getNumPages()):
        page = original_reader.getPage(page_number)
        page.mergePage(mark_reader.getPage(page_number))
        writer.addPage(page)

    with open(output, 'wb') as output:
        writer.write(output)


def create_marks_pdf(output, marks):
    canvas = Canvas(output, pagesize=A4)
    # h: 1300, w: 1000
    alpha = 0.15  # For converting original coordination system to mm
    max_height = 195  # shojo: 180 # zero: 195
    bubble_number = 0
    page_number = 1
    for mark in marks:
        mark = mark.replace(',', '.')
        parameters = mark.split(' ')
        zoom = double(parameters[3])
        x = double(parameters[1]) * alpha / zoom + 4
        y = max_height - (double(parameters[2]) * alpha) / zoom + 13

        if page_number < int(parameters[0]):
            page_number = int(parameters[0])
            canvas.showPage()  # Close page and move to the next one.

        canvas.setFillColor(lightskyblue)
        canvas.setFont("Helvetica-Bold", 8)
        canvas.drawString(x * mm, y * mm, str(bubble_number + 1))
        bubble_number += 1
    canvas.save()


if __name__ == '__main__':
    pdf_path = 'temp.pdf'
    mark_path = 'mark.pdf'
    output_path = 'temp_output.pdf'
    coordinates_path = "numbers"
    numeric_pdf_path = ""
    get_number_of_pages(pdf_path)
    coordinates = read_coordinates(coordinates_path)  # we got the list
    create_marks_pdf(mark_path, coordinates)
    merge_pdfs(pdf_path, output_path, mark_path)
    get_number_of_pages(output_path)
