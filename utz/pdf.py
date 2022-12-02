#!/usr/bin/env python

from pathlib import Path
from PyPDF2 import PdfFileWriter, PdfFileReader
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from subprocess import check_output


def maybe_open_pdf(path, open_pdf):
    if open_pdf:
        check_output(['open', path])


def write(path, out, *args, page=0, font_size=None, open_pdf=False):
    path = str(path)
    out = str(out)
    page_idx = page

    if isinstance(args[0], int) and isinstance(args[1], int) and isinstance(args[2], str):
        args = [args]
    
    packet = BytesIO()
    # create a new PDF with Reportlab
    can = canvas.Canvas(packet, pagesize=letter)
    if font_size:
        can.setFontSize(font_size)
    
    for x, y, s in args:
        can.drawString(x, y, s)
    
    can.save()

    # move to the beginning of the StringIO buffer
    packet.seek(0)
    new_pdf = PdfFileReader(packet)
    # read your existing PDF
    existing_pdf = PdfFileReader(open(path, "rb"))
    output = PdfFileWriter()
    
    # add the "watermark" (which is the new pdf) on the existing page
    page = existing_pdf.getPage(page_idx)
    page.mergePage(new_pdf.getPage(page_idx))
    output.addPage(page)

    # finally, write "output" to a real file
    with open(out, "wb") as f:
        output.write(f)

    maybe_open_pdf(out, open_pdf)


def cat(inputs, output, open_pdf=False):
    """https://stackoverflow.com/a/3444735"""
    input_streams = []
    try:
        # First open all the files, then produce the output file, and
        # finally close the input files. This is necessary because
        # the data isn't read from the input files until the write
        # operation. Thanks to
        # https://stackoverflow.com/questions/6773631/problem-with-closing-python-pypdf-writing-getting-a-valueerror-i-o-operation/6773733#6773733
        for input in inputs:
            input = Path(input)
            input_streams.append(input.open('rb'))
        writer = PdfFileWriter()
        for reader in map(PdfFileReader, input_streams):
            for n in range(reader.getNumPages()):
                writer.addPage(reader.getPage(n))

        if isinstance(output, Path):
            with output.open('wb') as f:
                writer.write(f)
        elif isinstance(output, str):
            with open(output, 'wb') as f:
                writer.write(f)
        else:
            writer.write(output)
    finally:
        for f in input_streams:
            f.close()
    
    maybe_open_pdf(output, open_pdf)
