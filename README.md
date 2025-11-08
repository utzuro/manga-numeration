# Mark PDF with numbers

Tool that reads the coordinates emitted by [zathura-numerator](https://github.com/utzuro/zathura-numerator) and burns the numbers directly into the original PDF pages. No manual tweaking of scale/alpha is required anymore – the script derives everything from the PDF metadata and the values stored in `numbers.txt`.

I've created this tool to use during manga translation work, as I needed a way to mark the text on original PDFs with numbers.

## Coordinates file example:

#numbers.txt

```txt
1 4.000000 5.000000 3.041967
1 379.000000 7.000000 3.041967
1 6.000000 565.000000 3.041967
1 382.000000 561.000000 3.041967
2 78.000000 277.000000 3.041967
2 107.000000 273.000000 3.041967
2 128.000000 280.000000 3.041967
2 149.000000 276.000000 3.041967
2 177.000000 281.000000 3.041967
2 204.000000 278.000000 3.041967
2 221.000000 280.000000 3.041967
2 243.000000 277.000000 3.041967
2 267.000000 282.000000 3.041967
2 294.000000 276.000000 3.041967
```

Where:

- 1st column: number of the PDF page to draw;
- 2nd column: x coordinate;
- 3rd column: y coordinate;
- 4th column: scale.

## Usage

1. Configure zathura to export the coordinates by setting `numbers-file` (e.g. `:set numbers-file /path/to/numbers.txt`). Each double-click will append a row with the page number, raw X/Y position, and current zoom.
2. Collect the coordinates by double-clicking every balloon/bubble you want to enumerate.
3. Run the helper script:

```bash
cd generatePDF
python markPDF.py --input manga.pdf --numbers /path/to/numbers.txt --output marked.pdf
```

The defaults still use `input.pdf`, `numbers.txt` and `marked.pdf` in the current directory, so running `python markPDF.py` is enough when you copy the files next to the script.

### Options

- `--font-size` – tweak the number size (points).
- `--bubble-radius` – tweak the size of the colored circle (points). If omitted the radius scales with the font size.
- `--bubble-color`/`--text-color` – override colours using hex values (`#RRGGBB`).

## How it works

The script inspects every page in the source PDF, converts the recorded widget coordinates back into PDF units (points) using the zoom factor stored in the log, flips the Y axis, and merges a temporary overlay PDF on top of the original. Because we read the real page size from the file, the result is reliable for any PDF size without fiddling with mysterious constants.
