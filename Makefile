CC := gcc
CFLAGS := -DNODEPS
LDFLAGS := -lm
PYTHON := python3

BIN_DIR := bin
OUTPUT_DIR := output
CSV_DIR := $(OUTPUT_DIR)/csv
IMAGE_DIR := $(OUTPUT_DIR)/images

DCRAW_SRC := digital/dcraw.c
DCRAW_BIN := $(BIN_DIR)/dcraw

EXPORT_METADATA_SRC := digital/export_nef_metadata.c
EXPORT_METADATA_BIN := $(BIN_DIR)/export_nef_metadata

EXTRACT_SHUTTER_SRC := digital/extract_shutter_rgb.c
EXTRACT_SHUTTER_BIN := $(BIN_DIR)/extract_shutter_rgb

METADATA_CSV := $(CSV_DIR)/nef_metadata_summary.csv
SHUTTER_CSV := $(CSV_DIR)/non_dsc_shutter_rgb.csv
ISO100_EXPOSURE_CSV := $(CSV_DIR)/iso100_exposure_values.csv
ISO100_ADJUSTED_CSV := $(CSV_DIR)/iso100_adjusted_to_f1_8.csv
ISO100_RAW_PLOT := $(IMAGE_DIR)/iso100_shutter_vs_raw_luminance.png
ISO100_THEORY_PLOT := $(IMAGE_DIR)/iso100_theoretical_raw_luminance.png
ISO100_ADJUSTED_PLOT := $(IMAGE_DIR)/iso100_adjusted_to_f1_8.png

TRACE_ROW ?= 3991
TRACE_COL ?= 5520
NEF_FILE ?= ./public/nef/100-1000-1.8.NEF

.PHONY: help all dirs tools clean metadata-csv shutter-csv iso100-csv iso100-adjusted-f18 iso100-plot iso100-theory-plot pixel-view

help:
	@printf '%s\n' \
	  'make dcraw               Build dcraw into bin/' \
	  'make tools               Build helper C programs into bin/' \
	  'make metadata-csv        Export ./public/nef metadata to CSV' \
	  'make shutter-csv         Extract RGB/raw-luminance CSV for non-DSC NEF files' \
	  'make iso100-csv          Export ISO=100 shutter/exposure values sorted by shutter speed' \
	  'make iso100-adjusted-f18 Create CSV and graph adjusted as if all shots were f/1.8' \
	  'make iso100-plot         Plot ISO=100 raw luminance graph' \
	  'make iso100-theory-plot  Plot theoretical ISO=100 exposure curve using t/F^2' \
	  'make pixel-view          Open the Python NEF hover viewer' \
	  'make clean               Remove generated binaries'

all: dirs $(DCRAW_BIN) tools

dirs:
	mkdir -p $(BIN_DIR) $(CSV_DIR) $(IMAGE_DIR)

$(DCRAW_BIN): $(DCRAW_SRC) | dirs
	$(CC) $(CFLAGS) $< -o $@ $(LDFLAGS)

tools: $(EXPORT_METADATA_BIN) $(EXTRACT_SHUTTER_BIN)

$(EXPORT_METADATA_BIN): $(EXPORT_METADATA_SRC) | dirs
	$(CC) $< -o $@

$(EXTRACT_SHUTTER_BIN): $(EXTRACT_SHUTTER_SRC) | dirs
	$(CC) $< -o $@

metadata-csv: $(DCRAW_BIN) $(EXPORT_METADATA_BIN)
	$(EXPORT_METADATA_BIN) $(DCRAW_BIN) ./public/nef $(METADATA_CSV)

shutter-csv: $(DCRAW_BIN) $(EXTRACT_SHUTTER_BIN)
	$(EXTRACT_SHUTTER_BIN) $(TRACE_ROW) $(TRACE_COL) $(SHUTTER_CSV) $(DCRAW_BIN) ./public/nef

iso100-csv: $(ISO100_EXPOSURE_CSV)

$(ISO100_EXPOSURE_CSV): digital/export_iso100_exposure_table.py | dirs
	$(PYTHON) digital/export_iso100_exposure_table.py --input-dir ./public/nef --measured-csv $(SHUTTER_CSV) --output $(ISO100_EXPOSURE_CSV)

iso100-adjusted-f18: $(ISO100_ADJUSTED_CSV) $(ISO100_ADJUSTED_PLOT)

$(ISO100_ADJUSTED_CSV) $(ISO100_ADJUSTED_PLOT): $(ISO100_EXPOSURE_CSV) digital/plot_iso100_adjusted_f18.py | dirs
	$(PYTHON) digital/plot_iso100_adjusted_f18.py --input $(ISO100_EXPOSURE_CSV) --output-csv $(ISO100_ADJUSTED_CSV) --output-image $(ISO100_ADJUSTED_PLOT)

iso100-plot: $(ISO100_RAW_PLOT)

$(ISO100_RAW_PLOT): $(SHUTTER_CSV) digital/plot_iso100_shutter_luminance.py | dirs
	$(PYTHON) digital/plot_iso100_shutter_luminance.py --input $(SHUTTER_CSV) --output $(ISO100_RAW_PLOT)

iso100-theory-plot: $(ISO100_THEORY_PLOT)

$(ISO100_THEORY_PLOT): digital/plot_iso100_exposure_theory.py | dirs
	$(PYTHON) digital/plot_iso100_exposure_theory.py --input-dir ./public/nef --output $(ISO100_THEORY_PLOT)

pixel-view: $(DCRAW_BIN) digital/view_nef_pixel_hover.py
	$(PYTHON) digital/view_nef_pixel_hover.py --dcraw $(DCRAW_BIN) $(NEF_FILE)

clean:
	rm -f $(DCRAW_BIN) $(EXPORT_METADATA_BIN) $(EXTRACT_SHUTTER_BIN)
