# Makefile — build preprocess_c as a shared library for Python ctypes bindings
#
# Targets:
#   make          - build shared library (libpreprocess.so / libpreprocess.dylib)
#   make test     - run differential tests via pytest
#   make clean    - remove compiled artifacts

CC      = gcc
CFLAGS  = -std=c11 -Wall -Wextra -Wpedantic -O3 -fPIC -I.
LDFLAGS = -lm

UNAME_S := $(shell uname -s)
ifeq ($(UNAME_S),Darwin)
    SHLIB_EXT = dylib
    SHLIB_FLAGS = -dynamiclib
else
    SHLIB_EXT = so
    SHLIB_FLAGS = -shared
endif

TARGET = libpreprocess.$(SHLIB_EXT)

SRCS = can_id.c \
       spn_decode.c \
       spn_spec.c \
       signal_state.c \
       grid_sample.c

OBJS = $(SRCS:.c=.o)

.PHONY: all clean test

all: $(TARGET)

$(TARGET): $(OBJS)
	$(CC) $(SHLIB_FLAGS) -o $@ $^ $(LDFLAGS)

%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@

test: $(TARGET)
	@echo "=== Running Native C Unit Tests ==="
	$(MAKE) -C test test
	@echo "\n=== Running Python vs C Differential Tests ==="
	python3 -m pytest ../tests/test_c_differential.py -v

clean:
	rm -f $(OBJS) libpreprocess.so libpreprocess.dylib
	$(MAKE) -C test clean
	$(MAKE) -C compare clean
