CC = gcc
PKG_CONFIG := $(shell command -v pkg-config 2>/dev/null)
PYTHON ?= $(shell if [ -x /opt/homebrew/bin/python3 ]; then echo /opt/homebrew/bin/python3; else command -v python3; fi)
RGB_SOURCE ?= ../public/rgb/latte.jpg
LUMINANCE_SOURCE ?= ../public/rgb/RGB.png
LUMINANCE_PREFIX ?= $(basename $(notdir $(LUMINANCE_SOURCE)))
RGB_DATA ?= latte_rgb.dat
RGB_OUTPUT ?= latte_falsecolor.png
SUM_MAP ?= $(LUMINANCE_PREFIX)_luminance_sum_fair.dat
WEIGHTED_MAP ?= $(LUMINANCE_PREFIX)_luminance_weighted_fair.dat
DIFF_MAP ?= $(LUMINANCE_PREFIX)_luminance_diff_signed.dat
WEIGHTED_MINMAX_MAP ?= $(LUMINANCE_PREFIX)_luminance_weighted_minmax.dat
WEIGHTED_PERCENTILE_MAP ?= $(LUMINANCE_PREFIX)_luminance_weighted_percentile.dat
WEIGHTED_GAMMA_MAP ?= $(LUMINANCE_PREFIX)_luminance_weighted_gamma.dat
LUMINANCE_STATS ?= $(LUMINANCE_PREFIX)_luminance_stats.json
LUMINANCE_OUTPUT ?= $(LUMINANCE_PREFIX)_luminance_compare.png

ifeq ($(PKG_CONFIG),)
CFLAGS =
LIBS =
GTK_AVAILABLE = 0
else
CFLAGS = $(shell $(PKG_CONFIG) --cflags gtk+-3.0 gdk-pixbuf-2.0 2>/dev/null)
LIBS = $(shell $(PKG_CONFIG) --libs gtk+-3.0 gdk-pixbuf-2.0 2>/dev/null)
GTK_AVAILABLE = 1
endif

.PHONY: all build rebuild clean extract_latte export_luminance_maps plot_latte plot_latte_all plot_luminance_compare

all:
	@echo "使い方:"
	@echo "  make build FILE=rgb"
	@echo "  make extract_latte"
	@echo "  make plot_latte"
	@echo "  make plot_latte_all"
	@echo "  make plot_luminance_compare"

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
	rm -f rgb grey latte_rgb.dat latte_falsecolor.png latte_condition*.png \
		*_luminance_sum_fair.dat *_luminance_weighted_fair.dat *_luminance_diff_signed.dat \
		*_luminance_weighted_minmax.dat *_luminance_weighted_percentile.dat *_luminance_weighted_gamma.dat \
		*_luminance_compare.png *_luminance_stats.json

extract_latte:
	$(PYTHON) extract_rgb.py "$(RGB_SOURCE)" > "$(RGB_DATA)"

export_luminance_maps:
	$(PYTHON) export_luminance_maps.py \
		"$(LUMINANCE_SOURCE)" \
		"$(SUM_MAP)" \
		"$(WEIGHTED_MAP)" \
		"$(DIFF_MAP)" \
		"$(WEIGHTED_MINMAX_MAP)" \
		"$(WEIGHTED_PERCENTILE_MAP)" \
		"$(WEIGHTED_GAMMA_MAP)" \
		"$(LUMINANCE_STATS)"

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

plot_luminance_compare: export_luminance_maps
	gnuplot \
		-e "SUM_FILE='$(SUM_MAP)'" \
		-e "WEIGHTED_FILE='$(WEIGHTED_MAP)'" \
		-e "DIFF_FILE='$(DIFF_MAP)'" \
		-e "WEIGHTED_MINMAX_FILE='$(WEIGHTED_MINMAX_MAP)'" \
		-e "WEIGHTED_PERCENTILE_FILE='$(WEIGHTED_PERCENTILE_MAP)'" \
		-e "WEIGHTED_GAMMA_FILE='$(WEIGHTED_GAMMA_MAP)'" \
		-e "OUTPUT='$(LUMINANCE_OUTPUT)'" \
		sh/latte_luminance_compare.plt
	@echo "saved: $(LUMINANCE_OUTPUT)"
