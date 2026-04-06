CC = gcc
CFLAGS = $(shell pkg-config --cflags gtk+-3.0 gdk-pixbuf-2.0)
LIBS = $(shell pkg-config --libs gtk+-3.0 gdk-pixbuf-2.0)

.PHONY: all build rebuild clean

all:
	@echo "既存の all です"
	@echo "使い方:"
	@echo "  make build FILE=grey"
	@echo "  make rebuild FILE=grey"
	@echo "  make clean FILE=grey"

build:
	@if [ -z "$(FILE)" ]; then \
		echo "使い方: make build FILE=grey"; \
		exit 1; \
	fi
	$(CC) $(FILE).c -o $(FILE) $(CFLAGS) $(LIBS)

rebuild:
	@if [ -z "$(FILE)" ]; then \
		echo "使い方: make rebuild FILE=grey"; \
		exit 1; \
	fi
	$(MAKE) clean FILE=$(FILE)
	$(MAKE) build FILE=$(FILE)

clean:
	@if [ -z "$(FILE)" ]; then \
		echo "使い方: make clean FILE=grey"; \
		exit 1; \
	fi
	rm -f $(FILE)


open:
	@if [ -z "$(FILE)" ]; then \
		echo "使い方: make open FILE=hayase_grey.jpg"; \
		exit 1; \
	fi
	explorer.exe "$$(wslpath -w $(FILE))"


plot:
	@if [ -z "$(FILE)" ]; then \
		echo "使い方: make plot FILE=gray.dat"; \
		exit 1; \
	fi	
	gnuplot -persist -e "FILE='$(FILE)'" -e "set terminal wxt; unset key; set size ratio -1; set view map; set yrange [*:*] reverse; plot FILE using 1:2:3 with image"

plot3d:
	@if [ -z "$(FILE)" ]; then \
		echo "使い方: make plot3d FILE=gray.dat"; \
		exit 1; \
	fi
	gnuplot -persist -e "FILE='$(FILE)'" -e "set terminal wxt; unset key; set view 65,35; set hidden3d; set palette gray; splot FILE using 1:2:3 with lines"