# Makefile for memSim Virtual Memory Simulator

# Default target
all: memSim

# Create the executable by making the Python script executable
memSim: memSim.py
	chmod +x memSim.py
	ln -sf memSim.py memSim

# Clean up generated files
clean:
	rm -f memSim

# Test with example (requires reference file and backing store)
test: memSim
	@echo "Testing memSim with default settings..."
	@if [ -f addresses.txt ]; then \
		./memSim addresses.txt; \
	else \
		echo "No addresses.txt file found for testing"; \
	fi

# Install (copy to a system directory)
install: memSim
	cp memSim /usr/local/bin/

.PHONY: all clean test install