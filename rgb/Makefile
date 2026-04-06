CC = gcc
CFLAGS = $(shell pkg-config --cflags gtk+-3.0)
LIBS = $(shell pkg-config --libs gtk+-3.0)

all: rgb

rgb: rgb.o
	$(CC) -o rgb rgb.o $(LIBS)

rgb.o: rgb.c
	$(CC) $(CFLAGS) -c rgb.c

clean:
	rm -f rgb rgb.o