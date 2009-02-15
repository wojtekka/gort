all:	gort.ui

gort.ui:	gort.glade
	gtk-builder-convert $< $@

.PHONY:	all
