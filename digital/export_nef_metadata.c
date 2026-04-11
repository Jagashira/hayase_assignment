#include <dirent.h>
#include <errno.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/wait.h>

#define FIELD_COUNT 18

static const char *k_headers[FIELD_COUNT] = {
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

struct metadata_row {
    char *values[FIELD_COUNT];
};

static void free_metadata_row(struct metadata_row *row) {
    int i;
    for (i = 0; i < FIELD_COUNT; i++) {
        free(row->values[i]);
        row->values[i] = NULL;
    }
}

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

static int field_index(const char *key) {
    int i;
    for (i = 0; i < FIELD_COUNT; i++) {
        if (strcmp(key, k_headers[i]) == 0) {
            return i;
        }
    }
    return -1;
}

static char *trim_whitespace(char *text) {
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
    if (fputc('"', fp) == EOF) {
        return -1;
    }
    return 0;
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

static int collect_nef_files(const char *input_dir, char ***out_files, size_t *out_count) {
    DIR *dir;
    struct dirent *entry;
    char **files = NULL;
    size_t count = 0;
    size_t capacity = 0;

    dir = opendir(input_dir);
    if (!dir) {
        fprintf(stderr, "failed to open input directory %s: %s\n", input_dir, strerror(errno));
        return -1;
    }

    while ((entry = readdir(dir)) != NULL) {
        char *name_copy;

        if (entry->d_name[0] == '.') {
            continue;
        }
        if (!has_nef_extension(entry->d_name)) {
            continue;
        }
        if (count == capacity) {
            size_t new_capacity = capacity ? capacity * 2 : 32;
            char **new_files = (char **)realloc(files, new_capacity * sizeof(*new_files));
            if (!new_files) {
                closedir(dir);
                fprintf(stderr, "out of memory while listing NEF files\n");
                return -1;
            }
            files = new_files;
            capacity = new_capacity;
        }
        name_copy = xstrdup(entry->d_name);
        if (!name_copy) {
            closedir(dir);
            fprintf(stderr, "out of memory while copying NEF file name\n");
            return -1;
        }
        files[count++] = name_copy;
    }

    closedir(dir);

    qsort(files, count, sizeof(*files), compare_names);
    *out_files = files;
    *out_count = count;
    return 0;
}

static void free_file_list(char **files, size_t count) {
    size_t i;
    for (i = 0; i < count; i++) {
        free(files[i]);
    }
    free(files);
}

static int collect_metadata(const char *dcraw_path,
                            const char *input_dir,
                            const char *filename,
                            struct metadata_row *row) {
    char command[PATH_MAX * 3];
    char filepath[PATH_MAX];
    char line[4096];
    FILE *pipe;
    int status;
    size_t i;

    for (i = 0; i < FIELD_COUNT; i++) {
        row->values[i] = xstrdup("");
        if (!row->values[i]) {
            fprintf(stderr, "out of memory while initializing metadata row\n");
            return -1;
        }
    }

    if (snprintf(filepath, sizeof(filepath), "%s/%s", input_dir, filename) >= (int)sizeof(filepath)) {
        fprintf(stderr, "input path is too long for %s\n", filename);
        return -1;
    }
    free(row->values[0]);
    row->values[0] = xstrdup(filename);
    if (!row->values[0]) {
        fprintf(stderr, "out of memory while storing filename\n");
        return -1;
    }

    if (snprintf(command, sizeof(command), "\"%s\" -i -v \"%s\"", dcraw_path, filepath) >= (int)sizeof(command)) {
        fprintf(stderr, "command is too long for %s\n", filename);
        return -1;
    }

    pipe = popen(command, "r");
    if (!pipe) {
        fprintf(stderr, "failed to run dcraw for %s: %s\n", filename, strerror(errno));
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
        key = trim_whitespace(line);
        value = trim_whitespace(colon + 1);
        index = field_index(key);
        if (index < 0) {
            continue;
        }
        if (index == 0) {
            continue;
        }
        free(row->values[index]);
        row->values[index] = xstrdup(value);
        if (!row->values[index]) {
            pclose(pipe);
            fprintf(stderr, "out of memory while storing field %s for %s\n", key, filename);
            return -1;
        }
    }

    status = pclose(pipe);
    if (status == -1) {
        fprintf(stderr, "failed to close dcraw pipe for %s: %s\n", filename, strerror(errno));
        return -1;
    }
    if (WIFEXITED(status) && WEXITSTATUS(status) != 0) {
        fprintf(stderr, "dcraw exited with status %d for %s\n", WEXITSTATUS(status), filename);
        return -1;
    }
    if (WIFSIGNALED(status)) {
        fprintf(stderr, "dcraw was terminated by signal %d for %s\n", WTERMSIG(status), filename);
        return -1;
    }

    return 0;
}

int main(int argc, char **argv) {
    const char *dcraw_path = "./dcraw";
    const char *input_dir = "./public/nef";
    const char *output_csv = "./digital/nef_metadata_summary.csv";
    char **files = NULL;
    size_t file_count = 0;
    FILE *out;
    size_t i;

    if (argc > 1) {
        dcraw_path = argv[1];
    }
    if (argc > 2) {
        input_dir = argv[2];
    }
    if (argc > 3) {
        output_csv = argv[3];
    }
    if (argc > 4) {
        fprintf(stderr, "usage: %s [dcraw_path] [input_dir] [output_csv]\n", argv[0]);
        return 1;
    }

    if (collect_nef_files(input_dir, &files, &file_count) != 0) {
        return 1;
    }
    if (file_count == 0) {
        fprintf(stderr, "no .NEF files found in %s\n", input_dir);
        free_file_list(files, file_count);
        return 1;
    }

    out = fopen(output_csv, "w");
    if (!out) {
        fprintf(stderr, "failed to open output CSV %s: %s\n", output_csv, strerror(errno));
        free_file_list(files, file_count);
        return 1;
    }

    for (i = 0; i < FIELD_COUNT; i++) {
        if (write_csv_value(out, k_headers[i]) != 0) {
            fprintf(stderr, "failed to write CSV header\n");
            fclose(out);
            free_file_list(files, file_count);
            return 1;
        }
        if (fputc(i + 1 == FIELD_COUNT ? '\n' : ',', out) == EOF) {
            fprintf(stderr, "failed to write CSV header delimiter\n");
            fclose(out);
            free_file_list(files, file_count);
            return 1;
        }
    }

    for (i = 0; i < file_count; i++) {
        struct metadata_row row;
        int field;

        memset(&row, 0, sizeof(row));
        if (collect_metadata(dcraw_path, input_dir, files[i], &row) != 0) {
            free_metadata_row(&row);
            fclose(out);
            free_file_list(files, file_count);
            return 1;
        }

        for (field = 0; field < FIELD_COUNT; field++) {
            if (write_csv_value(out, row.values[field]) != 0) {
                fprintf(stderr, "failed to write CSV value for %s\n", files[i]);
                free_metadata_row(&row);
                fclose(out);
                free_file_list(files, file_count);
                return 1;
            }
            if (fputc(field + 1 == FIELD_COUNT ? '\n' : ',', out) == EOF) {
                fprintf(stderr, "failed to write CSV delimiter for %s\n", files[i]);
                free_metadata_row(&row);
                fclose(out);
                free_file_list(files, file_count);
                return 1;
            }
        }
        free_metadata_row(&row);
    }

    fclose(out);
    free_file_list(files, file_count);

    printf("Wrote %zu rows to %s\n", file_count, output_csv);
    return 0;
}
