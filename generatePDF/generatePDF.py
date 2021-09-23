from PyPDF4 import PdfFileReader


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


if __name__ == '__main__':
    pdf_path = 'test.pdf'
    coordinates_path = "numbers"
    get_number_of_pages(pdf_path)
    coordinates = read_coordinates(coordinates_path)  # we got the list
    print(coordinates[0])
