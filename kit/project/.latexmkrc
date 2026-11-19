# The svg package calls Inkscape during the build, which needs -shell-escape.
$pdf_mode = 1;
$pdflatex = 'pdflatex -shell-escape -interaction=nonstopmode -file-line-error -synctex=1 %O %S';
