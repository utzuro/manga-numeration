from PyPDF2 import PdfFileReader, PdfFileWriter

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

    for page_number in range(original_reader.getNumPages()):
        page = original_reader.getPage(page_number)
        page.mergePage(mark_reader.getPage(0))  # page_number
        writer.addPage(page)

    with open(output, 'wb') as output:
        writer.write(output)


def create_marks_pdf(marks, output):
    canvas = Canvas(output, pagesize=A4)
    canvas.setFillColor(lightskyblue)
    canvas.setFont("Helvetica-Bold", 25)
    # for mark in marks:
    #     parameters = mark.split(' ')
    #     canvas.drawString(float(parameters[1]), float(parameters[2]), "4")
    for i in range(0,1000,5):
        canvas.drawString(i * mm, 10 * mm, i)

    j = 1
    for i in range(0,700, 5):
        canvas.drawString(j * 5 * mm, i * mm, i)
        if j%10 == 0:
            j++



    canvas.drawString(300/3.78 * mm, 300/3.78 * mm, "Blue Text!")
    canvas.save()

if __name__ == '__main__':
    pdf_path = 'test.pdf'
    mark_path = 'mark.pdf'
    output_path = 'test_output.pdf'
    coordinates_path = "numbers"
    numeric_pdf_path = ""
    get_number_of_pages(pdf_path)
    coordinates = read_coordinates(coordinates_path)  # we got the list
    create_marks_pdf(coordinates, mark_path)
    merge_pdfs(pdf_path, output_path, mark_path)
