CC = gcc
PKG_CONFIG := $(shell command -v pkg-config 2>/dev/null)
PYTHON ?= $(shell if [ -x /opt/homebrew/bin/python3 ]; then echo /opt/homebrew/bin/python3; else command -v python3; fi)
RGB_SOURCE ?= ../public/rgb/latte.jpg
RGB_DATA ?= latte_rgb.dat
RGB_OUTPUT ?= latte_falsecolor.png

ifeq ($(PKG_CONFIG),)
CFLAGS =
LIBS =
GTK_AVAILABLE = 0
else
CFLAGS = $(shell $(PKG_CONFIG) --cflags gtk+-3.0 gdk-pixbuf-2.0 2>/dev/null)
LIBS = $(shell $(PKG_CONFIG) --libs gtk+-3.0 gdk-pixbuf-2.0 2>/dev/null)
GTK_AVAILABLE = 1
endif

.PHONY: all build rebuild clean extract_latte plot_latte plot_latte_all

all:
	@echo "使い方:"
	@echo "  make build FILE=rgb"
	@echo "  make extract_latte"
	@echo "  make plot_latte"
	@echo "  make plot_latte_all"

build:
	@if [ -z "$(FILE)" ]; then \
		echo "使い方: make build FILE=rgb"; \
		exit 1; \
	fi
	@if [ "$(GTK_AVAILABLE)" = "0" ]; then \
		echo "pkg-config/GTK が見つからないため C 版はビルドできません。"; \
		echo "$(PYTHON) extract_rgb.py <image> > output.dat で互換抽出できます。"; \
		exit 1; \
	fi
	$(CC) $(FILE).c -o $(FILE) $(CFLAGS) $(LIBS)

rebuild:
	@if [ -z "$(FILE)" ]; then \
		echo "使い方: make rebuild FILE=rgb"; \
		exit 1; \
	fi
	$(MAKE) clean FILE=$(FILE)
	$(MAKE) build FILE=$(FILE)

clean:
	rm -f rgb grey latte_rgb.dat latte_falsecolor.png latte_condition*.png

extract_latte:
	$(PYTHON) extract_rgb.py "$(RGB_SOURCE)" > "$(RGB_DATA)"

plot_latte: extract_latte
	gnuplot -e "INPUT='$(RGB_DATA)'" -e "OUTPUT='$(RGB_OUTPUT)'" sh/latte_falsecolor.plt
	@echo "saved: $(RGB_OUTPUT)"

plot_latte_all: extract_latte
	gnuplot -e "INPUT='$(RGB_DATA)'" -e "OUTPUT='latte_condition1.png'" -e "MODE=1" sh/latte_falsecolor.plt
	gnuplot -e "INPUT='$(RGB_DATA)'" -e "OUTPUT='latte_condition2.png'" -e "MODE=2" sh/latte_falsecolor.plt
	gnuplot -e "INPUT='$(RGB_DATA)'" -e "OUTPUT='latte_condition3.png'" -e "MODE=3" sh/latte_falsecolor.plt
	gnuplot -e "INPUT='$(RGB_DATA)'" -e "OUTPUT='latte_condition4.png'" -e "MODE=4" sh/latte_falsecolor.plt
	@echo "saved: latte_condition1.png"
	@echo "saved: latte_condition2.png"
	@echo "saved: latte_condition3.png"
	@echo "saved: latte_condition4.png"
