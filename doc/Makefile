MAIN=report
LATEX=/usr/bin/xelatex
PDFVIEWER=/usr/bin/evince

all:
	$(LATEX) -shell-escape $(MAIN).tex
	$(PDFVIEWER) $(MAIN).pdf

clean:
	rm -f *.{dot,pdf,lo?,out,toc,aux,idx,aux,bbl}
