#include <dirent.h>
#include <errno.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/wait.h>

#define METADATA_FIELD_COUNT 18

static const char *k_metadata_headers[METADATA_FIELD_COUNT] = {
    "Filename",
    "Timestamp",
    "Camera",
    "Owner",
    "ISO speed",
    "Shutter",
    "Aperture",
    "Focal length",
    "Embedded ICC profile",
    "Number of raw images",
    "Thumb size",
    "Full size",
    "Image size",
    "Output size",
    "Raw colors",
    "Filter pattern",
    "Daylight multipliers",
    "Camera multipliers",
};

struct summary_row {
    char *metadata[METADATA_FIELD_COUNT];
    int row_1based;
    int col_1based;
    unsigned raw_r;
    unsigned raw_g;
    unsigned raw_b;
    double raw_luminance;
    unsigned final_r;
    unsigned final_g;
    unsigned final_b;
    double final_luminance;
};

static char *xstrdup(const char *src) {
    size_t len;
    char *dst;

    if (!src) {
        src = "";
    }
    len = strlen(src);
    dst = (char *)malloc(len + 1);
    if (!dst) {
        return NULL;
    }
    memcpy(dst, src, len + 1);
    return dst;
}

static char *trim(char *text) {
    char *end;

    while (*text == ' ' || *text == '\t' || *text == '\r' || *text == '\n') {
        text++;
    }
    end = text + strlen(text);
    while (end > text &&
           (end[-1] == ' ' || end[-1] == '\t' || end[-1] == '\r' || end[-1] == '\n')) {
        end--;
    }
    *end = '\0';
    return text;
}

static int field_index(const char *key) {
    int i;
    for (i = 0; i < METADATA_FIELD_COUNT; i++) {
        if (strcmp(key, k_metadata_headers[i]) == 0) {
            return i;
        }
    }
    return -1;
}

static void free_summary_row(struct summary_row *row) {
    int i;
    for (i = 0; i < METADATA_FIELD_COUNT; i++) {
        free(row->metadata[i]);
        row->metadata[i] = NULL;
    }
}

static int write_csv_value(FILE *fp, const char *value) {
    const unsigned char *p;

    if (fputc('"', fp) == EOF) {
        return -1;
    }
    for (p = (const unsigned char *)value; *p; p++) {
        if (*p == '"') {
            if (fputc('"', fp) == EOF || fputc('"', fp) == EOF) {
                return -1;
            }
        } else if (fputc(*p, fp) == EOF) {
            return -1;
        }
    }
    return fputc('"', fp) == EOF ? -1 : 0;
}

static int has_nef_extension(const char *name) {
    size_t len = strlen(name);
    return len >= 4 && strcmp(name + len - 4, ".NEF") == 0;
}

static int compare_names(const void *lhs, const void *rhs) {
    const char *const *a = (const char *const *)lhs;
    const char *const *b = (const char *const *)rhs;
    return strcmp(*a, *b);
}

static void free_file_list(char **files, size_t count) {
    size_t i;
    for (i = 0; i < count; i++) {
        free(files[i]);
    }
    free(files);
}

static int collect_nef_files(const char *input_dir, char ***out_files, size_t *out_count) {
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

        if (entry->d_name[0] == '.') {
            continue;
        }
        if (!has_nef_extension(entry->d_name)) {
            continue;
        }
        if (count == capacity) {
            size_t new_capacity = capacity ? capacity * 2 : 32;
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

static int collect_metadata(const char *dcraw_path,
                            const char *input_dir,
                            const char *filename,
                            struct summary_row *row) {
    char filepath[PATH_MAX];
    char command[PATH_MAX * 3];
    char line[4096];
    FILE *pipe;
    int status;
    int i;

    for (i = 0; i < METADATA_FIELD_COUNT; i++) {
        row->metadata[i] = xstrdup("");
        if (!row->metadata[i]) {
            fprintf(stderr, "out of memory while initializing metadata\n");
            return -1;
        }
    }

    free(row->metadata[0]);
    row->metadata[0] = xstrdup(filename);
    if (!row->metadata[0]) {
        fprintf(stderr, "out of memory while storing filename\n");
        return -1;
    }

    if (snprintf(filepath, sizeof(filepath), "%s/%s", input_dir, filename) >= (int)sizeof(filepath)) {
        fprintf(stderr, "input path too long: %s/%s\n", input_dir, filename);
        return -1;
    }
    if (snprintf(command, sizeof(command), "\"%s\" -i -v \"%s\"", dcraw_path, filepath) >=
        (int)sizeof(command)) {
        fprintf(stderr, "metadata command too long for %s\n", filename);
        return -1;
    }

    pipe = popen(command, "r");
    if (!pipe) {
        fprintf(stderr, "failed to run metadata command for %s: %s\n", filename, strerror(errno));
        return -1;
    }

    while (fgets(line, sizeof(line), pipe)) {
        char *colon;
        char *key;
        char *value;
        int index;

        colon = strchr(line, ':');
        if (!colon) {
            continue;
        }
        *colon = '\0';
        key = trim(line);
        value = trim(colon + 1);
        index = field_index(key);
        if (index < 0 || index == 0) {
            continue;
        }
        free(row->metadata[index]);
        row->metadata[index] = xstrdup(value);
        if (!row->metadata[index]) {
            pclose(pipe);
            fprintf(stderr, "out of memory while storing %s for %s\n", key, filename);
            return -1;
        }
    }

    status = pclose(pipe);
    if (status == -1) {
        fprintf(stderr, "failed to close metadata pipe for %s: %s\n", filename, strerror(errno));
        return -1;
    }
    if (WIFEXITED(status) && WEXITSTATUS(status) != 0) {
        fprintf(stderr, "metadata command exited with status %d for %s\n", WEXITSTATUS(status), filename);
        return -1;
    }
    if (WIFSIGNALED(status)) {
        fprintf(stderr, "metadata command killed by signal %d for %s\n", WTERMSIG(status), filename);
        return -1;
    }
    return 0;
}

static int collect_trace(const char *dcraw_path,
                         const char *input_dir,
                         const char *filename,
                         int row_1based,
                         int col_1based,
                         struct summary_row *row) {
    char filepath[PATH_MAX];
    char command[PATH_MAX * 4];
    char line[4096];
    FILE *pipe;
    int found_raw = 0;
    int found_final = 0;

    if (snprintf(filepath, sizeof(filepath), "%s/%s", input_dir, filename) >= (int)sizeof(filepath)) {
        fprintf(stderr, "input path too long: %s/%s\n", input_dir, filename);
        return -1;
    }
    if (snprintf(command, sizeof(command),
                 "\"%s\" -c -T -Z %d %d \"%s\" 2>&1 1>/dev/null",
                 dcraw_path, row_1based, col_1based, filepath) >= (int)sizeof(command)) {
        fprintf(stderr, "trace command too long for %s\n", filename);
        return -1;
    }

    pipe = popen(command, "r");
    if (!pipe) {
        fprintf(stderr, "failed to run trace command for %s: %s\n", filename, strerror(errno));
        return -1;
    }

    while (fgets(line, sizeof(line), pipe)) {
        int row_tmp;
        int col_tmp;
        unsigned r_tmp;
        unsigned g_tmp;
        unsigned b_tmp;
        double l_tmp;

        if (sscanf(line,
                   "TRACE_RAW_RESULT,row=%d,col=%d,R=%u,G=%u,B=%u,L=%lf",
                   &row_tmp, &col_tmp, &r_tmp, &g_tmp, &b_tmp, &l_tmp) == 6) {
            row->raw_r = r_tmp;
            row->raw_g = g_tmp;
            row->raw_b = b_tmp;
            row->raw_luminance = l_tmp;
            found_raw = 1;
        }
        if (sscanf(line,
                   "TRACE_RESULT,row=%d,col=%d,R=%u,G=%u,B=%u,L=%lf",
                   &row_tmp, &col_tmp, &r_tmp, &g_tmp, &b_tmp, &l_tmp) == 6) {
            row->final_r = r_tmp;
            row->final_g = g_tmp;
            row->final_b = b_tmp;
            row->final_luminance = l_tmp;
            found_final = 1;
        }
    }

    if (pclose(pipe) == -1) {
        fprintf(stderr, "failed to close trace pipe for %s\n", filename);
        return -1;
    }
    if (!found_raw || !found_final) {
        fprintf(stderr, "TRACE_RAW_RESULT/TRACE_RESULT not found for %s\n", filename);
        return -1;
    }
    return 0;
}

static int write_header(FILE *out) {
    int i;
    for (i = 0; i < METADATA_FIELD_COUNT; i++) {
        if (write_csv_value(out, k_metadata_headers[i]) != 0 || fputc(',', out) == EOF) {
            return -1;
        }
    }
    return fprintf(out,
                   "\"Trace Row\",\"Trace Col\",\"Raw R\",\"Raw G\",\"Raw B\",\"Raw Luminance\","
                   "\"Final R\",\"Final G\",\"Final B\",\"Final Luminance\"\n") < 0
               ? -1
               : 0;
}

static int write_row(FILE *out, const struct summary_row *row) {
    int i;
    for (i = 0; i < METADATA_FIELD_COUNT; i++) {
        if (write_csv_value(out, row->metadata[i]) != 0 || fputc(',', out) == EOF) {
            return -1;
        }
    }
    return fprintf(out,
                   "\"%d\",\"%d\",\"%u\",\"%u\",\"%u\",\"%.3f\","
                   "\"%u\",\"%u\",\"%u\",\"%.3f\"\n",
                   row->row_1based, row->col_1based,
                   row->raw_r, row->raw_g, row->raw_b, row->raw_luminance,
                   row->final_r, row->final_g, row->final_b, row->final_luminance) < 0
               ? -1
               : 0;
}

int main(int argc, char **argv) {
    const char *dcraw_path = "./a.out";
    const char *input_dir = "../public/tmp";
    const char *output_csv = "./tmp_nef_summary.csv";
    int row_1based = 20;
    int col_1based = 20;
    char **files = NULL;
    size_t count = 0;
    size_t i;
    FILE *out;

    if (argc > 1) {
        row_1based = atoi(argv[1]);
    }
    if (argc > 2) {
        col_1based = atoi(argv[2]);
    }
    if (argc > 3) {
        output_csv = argv[3];
    }
    if (argc > 4) {
        dcraw_path = argv[4];
    }
    if (argc > 5) {
        input_dir = argv[5];
    }
    if (argc > 6) {
        fprintf(stderr,
                "usage: %s [row_1based] [col_1based] [output_csv] [dcraw_path] [input_dir]\n",
                argv[0]);
        return 1;
    }

    if (collect_nef_files(input_dir, &files, &count) != 0) {
        return 1;
    }
    if (count == 0) {
        fprintf(stderr, "no .NEF files found in %s\n", input_dir);
        return 1;
    }

    out = fopen(output_csv, "w");
    if (!out) {
        fprintf(stderr, "failed to open %s: %s\n", output_csv, strerror(errno));
        free_file_list(files, count);
        return 1;
    }

    if (write_header(out) != 0) {
        fprintf(stderr, "failed to write CSV header to %s\n", output_csv);
        fclose(out);
        free_file_list(files, count);
        return 1;
    }

    for (i = 0; i < count; i++) {
        struct summary_row row;
        memset(&row, 0, sizeof(row));
        row.row_1based = row_1based;
        row.col_1based = col_1based;

        if (collect_metadata(dcraw_path, input_dir, files[i], &row) != 0 ||
            collect_trace(dcraw_path, input_dir, files[i], row_1based, col_1based, &row) != 0 ||
            write_row(out, &row) != 0) {
            fprintf(stderr, "failed while processing %s\n", files[i]);
            free_summary_row(&row);
            fclose(out);
            free_file_list(files, count);
            return 1;
        }

        free_summary_row(&row);
    }

    fclose(out);
    free_file_list(files, count);
    printf("Wrote %zu rows to %s\n", count, output_csv);
    return 0;
}
