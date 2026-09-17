CC      = gcc
CFLAGS  = -std=c11 -Wall -Wextra -Wpedantic -g -I.. -fno-omit-frame-pointer
LDFLAGS = -lm

SRCS = ../can_id.c \
       ../spn_decode.c \
       ../spn_spec.c \
       ../signal_state.c \
       ../grid_sample.c

.PHONY: all compare test clean

all: compare

compare: compare.c $(SRCS)
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

test: compare
	./run_compare.sh

clean:
	rm -f compare *.o c_output.txt py_output.txt
