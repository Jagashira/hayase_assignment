#include <dirent.h>
#include <errno.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

struct sample_row {
    char *filename;
    char *filename_iso;
    char *filename_shutter;
    char *metadata_iso;
    char *metadata_shutter;
    double shutter_seconds;
    int row_1based;
    int col_1based;
    unsigned raw_r;
    unsigned raw_g;
    unsigned raw_b;
    double raw_luminance;
    unsigned r;
    unsigned g;
    unsigned b;
    double luminance;
};

static char *xstrdup(const char *src) {
    size_t len;
    char *dst;
    if (!src) src = "";
    len = strlen(src);
    dst = (char *)malloc(len + 1);
    if (!dst) return NULL;
    memcpy(dst, src, len + 1);
    return dst;
}

static int has_nef_extension(const char *name) {
    size_t len = strlen(name);
    return len >= 4 && strcmp(name + len - 4, ".NEF") == 0;
}

static int is_target_file(const char *name) {
    return has_nef_extension(name) && strncmp(name, "DSC_", 4) != 0;
}

static int compare_names(const void *lhs, const void *rhs) {
    const char *const *a = (const char *const *)lhs;
    const char *const *b = (const char *const *)rhs;
    return strcmp(*a, *b);
}

static char *trim(char *text) {
    char *end;
    while (*text == ' ' || *text == '\t' || *text == '\r' || *text == '\n') text++;
    end = text + strlen(text);
    while (end > text &&
           (end[-1] == ' ' || end[-1] == '\t' || end[-1] == '\r' || end[-1] == '\n')) {
        end--;
    }
    *end = '\0';
    return text;
}

static int write_csv_value(FILE *fp, const char *value) {
    const unsigned char *p = (const unsigned char *)value;
    if (fputc('"', fp) == EOF) return -1;
    while (*p) {
        if (*p == '"') {
            if (fputc('"', fp) == EOF || fputc('"', fp) == EOF) return -1;
        } else if (fputc(*p, fp) == EOF) {
            return -1;
        }
        p++;
    }
    if (fputc('"', fp) == EOF) return -1;
    return 0;
}

static int collect_files(const char *input_dir, char ***out_files, size_t *out_count) {
    DIR *dir;
    struct dirent *entry;
    char **files = NULL;
    size_t count = 0;
    size_t capacity = 0;

    dir = opendir(input_dir);
    if (!dir) {
        fprintf(stderr, "failed to open %s: %s\n", input_dir, strerror(errno));
        return -1;
    }

    while ((entry = readdir(dir)) != NULL) {
        char *copy;
        if (entry->d_name[0] == '.') continue;
        if (!is_target_file(entry->d_name)) continue;
        if (count == capacity) {
            size_t new_capacity = capacity ? capacity * 2 : 16;
            char **tmp = (char **)realloc(files, new_capacity * sizeof(*files));
            if (!tmp) {
                closedir(dir);
                fprintf(stderr, "out of memory while collecting file list\n");
                return -1;
            }
            files = tmp;
            capacity = new_capacity;
        }
        copy = xstrdup(entry->d_name);
        if (!copy) {
            closedir(dir);
            fprintf(stderr, "out of memory while copying filename\n");
            return -1;
        }
        files[count++] = copy;
    }
    closedir(dir);
    qsort(files, count, sizeof(*files), compare_names);
    *out_files = files;
    *out_count = count;
    return 0;
}

static void free_files(char **files, size_t count) {
    size_t i;
    for (i = 0; i < count; i++) free(files[i]);
    free(files);
}

static void parse_filename_tokens(const char *filename, char **out_iso, char **out_shutter) {
    char base[PATH_MAX];
    char *dot;
    char *dash1;
    char *dash2;

    strncpy(base, filename, sizeof(base) - 1);
    base[sizeof(base) - 1] = '\0';
    dot = strrchr(base, '.');
    if (dot) *dot = '\0';

    dash1 = strchr(base, '-');
    if (!dash1) {
        *out_iso = xstrdup("");
        *out_shutter = xstrdup("");
        return;
    }
    *dash1 = '\0';
    dash2 = strchr(dash1 + 1, '-');

    *out_iso = xstrdup(base);
    if (dash2) {
        *dash2 = '\0';
        *out_shutter = xstrdup(dash1 + 1);
    } else {
        *out_shutter = xstrdup(dash1 + 1);
    }
}

static int parse_shutter_seconds(const char *text, double *seconds_out) {
    double numerator, denominator, seconds;

    if (sscanf(text, "%lf/%lf sec", &numerator, &denominator) == 2 && denominator != 0.0) {
        *seconds_out = numerator / denominator;
        return 0;
    }
    if (sscanf(text, "%lf sec", &seconds) == 1) {
        *seconds_out = seconds;
        return 0;
    }
    return -1;
}

static int collect_metadata(const char *dcraw_path,
                            const char *input_dir,
                            const char *filename,
                            char **iso_out,
                            char **shutter_out,
                            double *seconds_out) {
    char filepath[PATH_MAX];
    char command[PATH_MAX * 3];
    char line[4096];
    FILE *pipe;

    *iso_out = xstrdup("");
    *shutter_out = xstrdup("");
    *seconds_out = 0.0;

    snprintf(filepath, sizeof(filepath), "%s/%s", input_dir, filename);
    snprintf(command, sizeof(command), "\"%s\" -i -v \"%s\"", dcraw_path, filepath);

    pipe = popen(command, "r");
    if (!pipe) {
        fprintf(stderr, "failed to run dcraw metadata for %s: %s\n", filename, strerror(errno));
        return -1;
    }

    while (fgets(line, sizeof(line), pipe)) {
        char *colon = strchr(line, ':');
        char *key;
        char *value;
        if (!colon) continue;
        *colon = '\0';
        key = trim(line);
        value = trim(colon + 1);
        if (strcmp(key, "ISO speed") == 0) {
            free(*iso_out);
            *iso_out = xstrdup(value);
        } else if (strcmp(key, "Shutter") == 0) {
            free(*shutter_out);
            *shutter_out = xstrdup(value);
            parse_shutter_seconds(value, seconds_out);
        }
    }

    if (pclose(pipe) == -1) {
        fprintf(stderr, "failed to close metadata pipe for %s\n", filename);
        return -1;
    }
    return 0;
}

static int collect_trace_result(const char *dcraw_path,
                                const char *input_dir,
                                const char *filename,
                                int row_1based,
                                int col_1based,
                                unsigned *raw_r_out,
                                unsigned *raw_g_out,
                                unsigned *raw_b_out,
                                double *raw_l_out,
                                unsigned *r_out,
                                unsigned *g_out,
                                unsigned *b_out,
                                double *l_out) {
    char filepath[PATH_MAX];
    char command[PATH_MAX * 4];
    char line[4096];
    FILE *pipe;
    int found_final = 0;
    int found_raw = 0;

    snprintf(filepath, sizeof(filepath), "%s/%s", input_dir, filename);
    snprintf(command, sizeof(command),
             "\"%s\" -c -T -Z %d %d \"%s\" 2>&1 1>/dev/null",
             dcraw_path, row_1based, col_1based, filepath);

    pipe = popen(command, "r");
    if (!pipe) {
        fprintf(stderr, "failed to run dcraw trace for %s: %s\n", filename, strerror(errno));
        return -1;
    }

    while (fgets(line, sizeof(line), pipe)) {
        int row_tmp, col_tmp;
        unsigned r_tmp, g_tmp, b_tmp;
        double l_tmp;

        if (sscanf(line,
                   "TRACE_RAW_RESULT,row=%d,col=%d,R=%u,G=%u,B=%u,L=%lf",
                   &row_tmp, &col_tmp, &r_tmp, &g_tmp, &b_tmp, &l_tmp) == 6) {
            *raw_r_out = r_tmp;
            *raw_g_out = g_tmp;
            *raw_b_out = b_tmp;
            *raw_l_out = l_tmp;
            found_raw = 1;
        }
        if (sscanf(line,
                   "TRACE_RESULT,row=%d,col=%d,R=%u,G=%u,B=%u,L=%lf",
                   &row_tmp, &col_tmp, &r_tmp, &g_tmp, &b_tmp, &l_tmp) == 6) {
            *r_out = r_tmp;
            *g_out = g_tmp;
            *b_out = b_tmp;
            *l_out = l_tmp;
            found_final = 1;
        }
    }

    if (pclose(pipe) == -1) {
        fprintf(stderr, "failed to close trace pipe for %s\n", filename);
        return -1;
    }
    if (!found_raw || !found_final) {
        fprintf(stderr, "TRACE_RESULT/TRACE_RAW_RESULT not found for %s\n", filename);
        return -1;
    }
    return 0;
}

static void free_row(struct sample_row *row) {
    free(row->filename);
    free(row->filename_iso);
    free(row->filename_shutter);
    free(row->metadata_iso);
    free(row->metadata_shutter);
}

int main(int argc, char **argv) {
    const char *dcraw_path = "./dcraw";
    const char *input_dir = "./public/nef";
    const char *output_csv = "./digital/non_dsc_shutter_rgb.csv";
    int row_1based = 26;
    int col_1based = 6;
    char **files = NULL;
    size_t count = 0;
    size_t i;
    FILE *out;

    if (argc > 1) row_1based = atoi(argv[1]);
    if (argc > 2) col_1based = atoi(argv[2]);
    if (argc > 3) output_csv = argv[3];
    if (argc > 4) dcraw_path = argv[4];
    if (argc > 5) input_dir = argv[5];

    if (collect_files(input_dir, &files, &count) != 0) return 1;
    if (count == 0) {
        fprintf(stderr, "no non-DSC .NEF files found in %s\n", input_dir);
        return 1;
    }

    out = fopen(output_csv, "w");
    if (!out) {
        fprintf(stderr, "failed to open %s: %s\n", output_csv, strerror(errno));
        free_files(files, count);
        return 1;
    }

    fprintf(out,
            "\"Filename\",\"Filename ISO\",\"Filename Shutter\",\"Metadata ISO\",\"Metadata Shutter\",\"Shutter Seconds\",\"Row\",\"Col\",\"Raw R\",\"Raw G\",\"Raw B\",\"Raw Luminance\",\"R\",\"G\",\"B\",\"Luminance\"\n");

    for (i = 0; i < count; i++) {
        struct sample_row row;
        memset(&row, 0, sizeof(row));
        row.filename = xstrdup(files[i]);
        parse_filename_tokens(files[i], &row.filename_iso, &row.filename_shutter);
        if (collect_metadata(dcraw_path, input_dir, files[i],
                             &row.metadata_iso, &row.metadata_shutter,
                             &row.shutter_seconds) != 0) {
            free_row(&row);
            fclose(out);
            free_files(files, count);
            return 1;
        }
        if (collect_trace_result(dcraw_path, input_dir, files[i], row_1based, col_1based,
                                 &row.raw_r, &row.raw_g, &row.raw_b, &row.raw_luminance,
                                 &row.r, &row.g, &row.b, &row.luminance) != 0) {
            free_row(&row);
            fclose(out);
            free_files(files, count);
            return 1;
        }
        row.row_1based = row_1based;
        row.col_1based = col_1based;

        write_csv_value(out, row.filename);
        fputc(',', out);
        write_csv_value(out, row.filename_iso);
        fputc(',', out);
        write_csv_value(out, row.filename_shutter);
        fputc(',', out);
        write_csv_value(out, row.metadata_iso);
        fputc(',', out);
        write_csv_value(out, row.metadata_shutter);
        fprintf(out, ",\"%.6f\",\"%d\",\"%d\",\"%u\",\"%u\",\"%u\",\"%.3f\",\"%u\",\"%u\",\"%u\",\"%.3f\"\n",
                row.shutter_seconds, row.row_1based, row.col_1based,
                row.raw_r, row.raw_g, row.raw_b, row.raw_luminance,
                row.r, row.g, row.b, row.luminance);

        free_row(&row);
    }

    fclose(out);
    free_files(files, count);
    printf("Wrote %zu rows to %s\n", count, output_csv);
    return 0;
}
