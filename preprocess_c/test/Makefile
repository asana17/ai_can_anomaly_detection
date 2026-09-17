# Makefile — native host build for preprocess_c unit tests
#
# Run from preprocess_c/test/:
#   make          # build all test binaries
#   make test     # build and run all tests
#   make clean
#
# The source files live one level up (../). All tests link the same set of
# translation units.

CC      = gcc
CFLAGS  = -std=c11 -Wall -Wextra -Wpedantic -g \
           -I.. \
           -fno-omit-frame-pointer
LDFLAGS = -lm

# Source files shared by every test binary
SRCS = ../can_id.c \
       ../spn_decode.c \
       ../spn_spec.c \
       ../signal_state.c \
       ../grid_sample.c

TESTS = test_can_id \
        test_spn_decode \
        test_signal_state \
        test_grid_sample

.PHONY: all test clean

all: $(TESTS)

test: all
	@echo "=== test_can_id ===";       ./test_can_id
	@echo "=== test_spn_decode ===";   ./test_spn_decode
	@echo "=== test_signal_state ==="; ./test_signal_state
	@echo "=== test_grid_sample ===";  ./test_grid_sample
	@echo ""
	@echo "All tests passed."

test_can_id: test_can_id.c $(SRCS)
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

test_spn_decode: test_spn_decode.c $(SRCS)
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

test_signal_state: test_signal_state.c $(SRCS)
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

test_grid_sample: test_grid_sample.c $(SRCS)
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

clean:
	rm -f $(TESTS)
