#!/usr/bin/env python3

import sys
import struct
from collections import deque, OrderedDict

class TLB:
    """Translation Lookaside Buffer with 16 entries using FIFO replacement"""
    def __init__(self):
        self.entries = OrderedDict()  # page_num -> frame_num
        self.max_size = 16
    
    def lookup(self, page_num):
        """Returns frame number if found, None otherwise"""
        return self.entries.get(page_num)
    
    def insert(self, page_num, frame_num):
        """Insert or update TLB entry"""
        if page_num in self.entries:
            # Remove and re-add to maintain FIFO order
            del self.entries[page_num]
        elif len(self.entries) >= self.max_size:
            # Remove oldest entry (FIFO)
            self.entries.popitem(last=False)
        
        self.entries[page_num] = frame_num

class PageTableEntry:
    """Entry in the page table"""
    def __init__(self):
        self.present = False
        self.frame_num = None

class PageTable:
    """Page table with 256 entries"""
    def __init__(self):
        self.entries = [PageTableEntry() for _ in range(256)]
    
    def lookup(self, page_num):
        """Returns PageTableEntry for the given page number"""
        return self.entries[page_num]
    
    def set_entry(self, page_num, frame_num):
        """Set page table entry as present and assign frame"""
        entry = self.entries[page_num]
        entry.present = True
        entry.frame_num = frame_num

class PhysicalMemory:
    """Physical memory management"""
    def __init__(self, num_frames):
        self.num_frames = num_frames
        self.frames = [bytearray(256) for _ in range(num_frames)]
        self.frame_to_page = {}  # frame_num -> page_num mapping
        self.free_frames = deque(range(num_frames))
        
    def allocate_frame(self):
        """Allocate a free frame, returns frame number or None if full"""
        if self.free_frames:
            return self.free_frames.popleft()
        return None
    
    def load_page(self, frame_num, page_data, page_num):
        """Load page data into specified frame"""
        self.frames[frame_num] = bytearray(page_data)
        self.frame_to_page[frame_num] = page_num
    
    def get_frame_content(self, frame_num):
        """Get the content of a frame as hex string"""
        return self.frames[frame_num].hex()
    
    def get_byte(self, frame_num, offset):
        """Get a specific byte from a frame"""
        return struct.unpack('b', self.frames[frame_num][offset:offset+1])[0]
    
    def deallocate_frame(self, frame_num):
        """Mark frame as free"""
        if frame_num in self.frame_to_page:
            del self.frame_to_page[frame_num]
        self.free_frames.append(frame_num)

class PageReplacementAlgorithm:
    """Base class for page replacement algorithms"""
    def __init__(self, physical_memory, page_table):
        self.physical_memory = physical_memory
        self.page_table = page_table
    
    def select_victim(self, reference_sequence=None, current_index=None):
        """Select a frame to evict. To be implemented by subclasses"""
        raise NotImplementedError

class FIFOAlgorithm(PageReplacementAlgorithm):
    """First-In-First-Out page replacement"""
    def __init__(self, physical_memory, page_table):
        super().__init__(physical_memory, page_table)
        self.insertion_order = deque()
    
    def add_page(self, frame_num):
        """Record that a page was loaded into this frame"""
        self.insertion_order.append(frame_num)
    
    def select_victim(self, reference_sequence=None, current_index=None):
        """Select the oldest frame"""
        return self.insertion_order.popleft()

class LRUAlgorithm(PageReplacementAlgorithm):
    """Least Recently Used page replacement"""
    def __init__(self, physical_memory, page_table):
        super().__init__(physical_memory, page_table)
        self.usage_order = []  # Most recent at the end
    
    def access_page(self, frame_num):
        """Record that a page in this frame was accessed"""
        if frame_num in self.usage_order:
            self.usage_order.remove(frame_num)
        self.usage_order.append(frame_num)
    
    def add_page(self, frame_num):
        """Record that a page was loaded into this frame"""
        self.access_page(frame_num)
    
    def select_victim(self, reference_sequence=None, current_index=None):
        """Select the least recently used frame"""
        return self.usage_order.pop(0)

class OPTAlgorithm(PageReplacementAlgorithm):
    """Optimal page replacement (Belady's algorithm)"""
    def __init__(self, physical_memory, page_table):
        super().__init__(physical_memory, page_table)
    
    def add_page(self, frame_num):
        """No special tracking needed for OPT"""
        pass
    
    def access_page(self, frame_num):
        """No special tracking needed for OPT"""
        pass
    
    def select_victim(self, reference_sequence, current_index):
        """Select the frame that will be used farthest in the future"""
        frame_to_page = self.physical_memory.frame_to_page
        farthest_frame = None
        farthest_distance = -1
        
        for frame_num in frame_to_page:
            page_num = frame_to_page[frame_num]
            
            # Find next use of this page
            next_use = float('inf')
            for i in range(current_index + 1, len(reference_sequence)):
                addr = reference_sequence[i]
                future_page = (addr >> 8) & 0xFF
                if future_page == page_num:
                    next_use = i
                    break
            
            if next_use > farthest_distance:
                farthest_distance = next_use
                farthest_frame = frame_num
        
        return farthest_frame

class VirtualMemorySimulator:
    """Main virtual memory simulator"""
    def __init__(self, num_frames, replacement_algorithm, backing_store_file):
        self.num_frames = num_frames
        self.tlb = TLB()
        self.page_table = PageTable()
        self.physical_memory = PhysicalMemory(num_frames)
        self.backing_store_file = backing_store_file
        
        # Initialize page replacement algorithm
        if replacement_algorithm == "FIFO":
            self.replacement_algo = FIFOAlgorithm(self.physical_memory, self.page_table)
        elif replacement_algorithm == "LRU":
            self.replacement_algo = LRUAlgorithm(self.physical_memory, self.page_table)
        elif replacement_algorithm == "OPT":
            self.replacement_algo = OPTAlgorithm(self.physical_memory, self.page_table)
        else:
            raise ValueError(f"Unknown replacement algorithm: {replacement_algorithm}")
        
        # Statistics
        self.page_faults = 0
        self.tlb_hits = 0
        self.tlb_misses = 0
        self.total_accesses = 0
    
    def load_page_from_backing_store(self, page_num):
        """Load a page from backing store"""
        try:
            with open(self.backing_store_file, 'rb') as f:
                f.seek(page_num * 256)
                return f.read(256)
        except IOError:
            # If backing store doesn't exist or is too small, return zeros
            return bytes(256)
    
    def handle_page_fault(self, page_num, reference_sequence=None, current_index=None):
        """Handle a page fault by loading page from backing store"""
        self.page_faults += 1
        
        # Get page data from backing store
        page_data = self.load_page_from_backing_store(page_num)
        
        # Try to allocate a free frame
        frame_num = self.physical_memory.allocate_frame()
        
        if frame_num is None:
            # No free frames, need to evict a page
            victim_frame = self.replacement_algo.select_victim(reference_sequence, current_index)
            
            # Invalidate the victim page in page table
            victim_page = self.physical_memory.frame_to_page[victim_frame]
            self.page_table.entries[victim_page].present = False
            
            # Remove from TLB if present
            if victim_page in self.tlb.entries:
                del self.tlb.entries[victim_page]
            
            frame_num = victim_frame
        
        # Load the new page
        self.physical_memory.load_page(frame_num, page_data, page_num)
        self.page_table.set_entry(page_num, frame_num)
        
        # Update replacement algorithm
        self.replacement_algo.add_page(frame_num)
        
        return frame_num
    
    def translate_address(self, virtual_address, reference_sequence=None, current_index=None):
        """Translate virtual address to physical address"""
        # Extract page number and offset
        page_num = (virtual_address >> 8) & 0xFF
        offset = virtual_address & 0xFF
        
        self.total_accesses += 1
        
        # Check TLB first
        frame_num = self.tlb.lookup(page_num)
        if frame_num is not None:
            self.tlb_hits += 1
            # Update LRU if needed
            if isinstance(self.replacement_algo, LRUAlgorithm):
                self.replacement_algo.access_page(frame_num)
        else:
            self.tlb_misses += 1
            
            # Check page table
            page_entry = self.page_table.lookup(page_num)
            if page_entry.present:
                frame_num = page_entry.frame_num
                # Update LRU if needed
                if isinstance(self.replacement_algo, LRUAlgorithm):
                    self.replacement_algo.access_page(frame_num)
            else:
                # Page fault
                frame_num = self.handle_page_fault(page_num, reference_sequence, current_index)
            
            # Update TLB
            self.tlb.insert(page_num, frame_num)
        
        # Get the byte value and frame content
        byte_value = self.physical_memory.get_byte(frame_num, offset)
        frame_content = self.physical_memory.get_frame_content(frame_num)
        
        return frame_num, byte_value, frame_content
    
    def print_statistics(self):
        """Print simulation statistics"""
        page_fault_rate = (self.page_faults / self.total_accesses) * 100 if self.total_accesses > 0 else 0
        tlb_hit_rate = (self.tlb_hits / self.total_accesses) * 100 if self.total_accesses > 0 else 0
        
        print(f"Page Faults = {self.page_faults}")
        print(f"Page Fault Rate = {page_fault_rate:.2f}%")
        print(f"TLB Hits = {self.tlb_hits}")
        print(f"TLB Misses = {self.tlb_misses}")
        print(f"TLB Hit Rate = {tlb_hit_rate:.2f}%")

def main():
    if len(sys.argv) < 2:
        print("Usage: memSim <reference-sequence-file.txt> [FRAMES] [PRA]")
        print("Defaults: FRAMES=256, PRA=FIFO")
        sys.exit(1)
    
    reference_file = sys.argv[1]
    frames = int(sys.argv[2]) if len(sys.argv) > 2 else 256
    algorithm = sys.argv[3] if len(sys.argv) > 3 else "FIFO"
    
    # Validate inputs
    if frames <= 0 or frames > 256:
        print("Error: FRAMES must be between 1 and 256")
        sys.exit(1)
    
    if algorithm not in ["FIFO", "LRU", "OPT"]:
        print("Error: PRA must be FIFO, LRU, or OPT")
        sys.exit(1)
    
    # Read reference sequence
    try:
        with open(reference_file, 'r') as f:
            addresses = [int(line.strip()) & 0xFFFF for line in f if line.strip()]
    except IOError:
        print(f"Error: Cannot read reference file {reference_file}")
        sys.exit(1)
    
    # Initialize simulator
    backing_store = "BACKING_STORE.bin"
    simulator = VirtualMemorySimulator(frames, algorithm, backing_store)
    
    # Process each address
    for i, address in enumerate(addresses):
        frame_num, byte_value, frame_content = simulator.translate_address(
            address, addresses, i
        )
        print(f"{address},{byte_value},{frame_num},{frame_content}")
    
    # Print statistics
    simulator.print_statistics()

if __name__ == "__main__":
    main()