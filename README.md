# Mark PDF with numbers

Tool that reads the coordinates and marks them on the pdf file as continuing numbers. Meant to be used with [zathura-numerator](https://github.com/utzuro/zathura-numerator) to generate coordinates.

I've created this tool to use during manga translation work, as I needed a way to mark the text on original PDF with numbers.

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

## Notes

This script is meant to be used with [zathura-numerator](https://github.com/utzuro/zathura-numerator) to generate coordinates, so there is some specificy involved. For example, Zathura and PyPDF2 have reverse coordinate systems (Y in Zathura is upside down for Y in PyPDF2) so script is reversing it. Also, ALPHA and SCALE constants have to be adjusted manually, because they are different for every PDF and automatic way to determine those values is yet to be implemented.
