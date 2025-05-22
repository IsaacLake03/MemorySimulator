#!/usr/bin/env python3
"""
Comprehensive test suite for memSim page replacement algorithms
This script creates various test scenarios to verify algorithm effectiveness
"""

import subprocess
import os
import random
import json
from typing import List, Dict, Tuple

class TestGenerator:
    """Generate various test patterns for algorithm comparison"""
    
    @staticmethod
    def create_backing_store(filename="BACKING_STORE.bin"):
        """Create a backing store with predictable patterns"""
        with open(filename, 'wb') as f:
            for page in range(256):
                page_data = bytearray(256)
                for i in range(256):
                    # Each byte contains the page number for easy verification
                    page_data[i] = page
                f.write(page_data)
    
    @staticmethod
    def sequential_access(start_page=0, num_pages=20, accesses_per_page=3):
        """Generate sequential page access pattern"""
        addresses = []
        for page in range(start_page, start_page + num_pages):
            for _ in range(accesses_per_page):
                # Random offset within the page
                offset = random.randint(0, 255)
                addresses.append((page << 8) | offset)
        return addresses
    
    @staticmethod
    def temporal_locality_pattern(hot_pages: List[int], cold_pages: List[int], 
                                hot_ratio=0.8, total_accesses=1000):
        """Generate pattern with temporal locality (80/20 rule)"""
        addresses = []
        for _ in range(total_accesses):
            if random.random() < hot_ratio:
                page = random.choice(hot_pages)
            else:
                page = random.choice(cold_pages)
            offset = random.randint(0, 255)
            addresses.append((page << 8) | offset)
        return addresses
    
    @staticmethod
    def cyclic_pattern(pages: List[int], cycles=5):
        """Generate cyclic access pattern (good for testing FIFO vs LRU)"""
        addresses = []
        for _ in range(cycles):
            for page in pages:
                for _ in range(3):  # Multiple accesses per page
                    offset = random.randint(0, 255)
                    addresses.append((page << 8) | offset)
        return addresses
    
    @staticmethod
    def optimal_showcase_pattern():
        """Pattern designed to show OPT's superiority"""
        # This pattern accesses pages that will be needed again soon
        # OPT will keep these, while FIFO/LRU might evict them
        addresses = []
        
        # Phase 1: Fill up memory with pages 0-7 (assuming 8 frames)
        for page in range(8):
            addresses.append((page << 8) | 0)
        
        # Phase 2: Access page 8 (causes eviction)
        addresses.append((8 << 8) | 0)
        
        # Phase 3: Re-access pages 1,2,3 (LRU/FIFO might have evicted these)
        for page in [1, 2, 3]:
            addresses.append((page << 8) | 0)
        
        # Phase 4: Access pages 9,10 (more evictions)
        for page in [9, 10]:
            addresses.append((page << 8) | 0)
        
        # Phase 5: Re-access early pages that OPT would have kept
        for page in [0, 1, 2]:
            addresses.append((page << 8) | 0)
        
        return addresses
    
    @staticmethod
    def lru_worst_case():
        """Pattern that makes LRU perform poorly"""
        # Sequential scan that's larger than memory
        # LRU will perform like FIFO in this case
        addresses = []
        num_pages = 20  # Larger than typical frame count
        for cycle in range(3):
            for page in range(num_pages):
                addresses.append((page << 8) | 0)
        return addresses
    
    @staticmethod
    def fifo_anomaly_pattern():
        """Belady's anomaly pattern - more frames can increase page faults with FIFO"""
        # Classic pattern: 1,2,3,4,1,2,5,1,2,3,4,5
        pages = [1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5]
        addresses = []
        for page in pages:
            addresses.append((page << 8) | 0)
        return addresses
    
    @staticmethod
    def working_set_pattern():
        """Simulate a working set that changes over time"""
        addresses = []
        
        # Working set 1: pages 0-4
        for _ in range(100):
            page = random.choice([0, 1, 2, 3, 4])
            addresses.append((page << 8) | random.randint(0, 255))
        
        # Transition period
        for _ in range(20):
            page = random.choice([4, 5, 6, 7, 8])
            addresses.append((page << 8) | random.randint(0, 255))
        
        # Working set 2: pages 5-9
        for _ in range(100):
            page = random.choice([5, 6, 7, 8, 9])
            addresses.append((page << 8) | random.randint(0, 255))
        
        return addresses

class TestRunner:
    """Run tests and collect results"""
    
    def __init__(self, memsim_path="./memSim"):
        self.memsim_path = memsim_path
        
    def run_test(self, addresses: List[int], frames: int, algorithm: str) -> Dict:
        """Run a single test and parse results"""
        # Write addresses to temp file
        test_file = f"temp_test_{algorithm}_{frames}.txt"
        with open(test_file, 'w') as f:
            for addr in addresses:
                f.write(f"{addr}\n")
        
        try:
            # Run memSim
            result = subprocess.run([self.memsim_path, test_file, str(frames), algorithm], 
                                  capture_output=True, text=True)
            
            if result.returncode != 0:
                return {"error": f"memSim failed: {result.stderr}"}
            
            # Parse output
            lines = result.stdout.strip().split('\n')
            
            # Find statistics lines
            page_faults = 0
            page_fault_rate = 0.0
            tlb_hits = 0
            tlb_misses = 0
            tlb_hit_rate = 0.0
            
            for line in lines:
                if line.startswith("Page Faults ="):
                    page_faults = int(line.split('=')[1].strip())
                elif line.startswith("Page Fault Rate ="):
                    page_fault_rate = float(line.split('=')[1].strip().rstrip('%'))
                elif line.startswith("TLB Hits ="):
                    tlb_hits = int(line.split('=')[1].strip())
                elif line.startswith("TLB Misses ="):
                    tlb_misses = int(line.split('=')[1].strip())
                elif line.startswith("TLB Hit Rate ="):
                    tlb_hit_rate = float(line.split('=')[1].strip().rstrip('%'))
            
            return {
                "page_faults": page_faults,
                "page_fault_rate": page_fault_rate,
                "tlb_hits": tlb_hits,
                "tlb_misses": tlb_misses,
                "tlb_hit_rate": tlb_hit_rate,
                "total_accesses": len(addresses)
            }
            
        finally:
            # Clean up temp file
            if os.path.exists(test_file):
                os.remove(test_file)

def run_all_tests():
    """Run comprehensive test suite"""
    print("=== Virtual Memory Algorithm Effectiveness Test Suite ===\n")
    
    # Create backing store
    TestGenerator.create_backing_store()
    runner = TestRunner()
    
    # Test configurations
    test_cases = [
        {
            "name": "Small Sequential Access",
            "addresses": TestGenerator.sequential_access(0, 10, 2),
            "frames": [4, 8],
            "description": "Sequential access to 10 pages, 2 accesses each"
        },
        {
            "name": "Temporal Locality (80/20)",
            "addresses": TestGenerator.temporal_locality_pattern([1, 2, 3, 4], [10, 11, 12, 13, 14, 15]),
            "frames": [4, 8],
            "description": "80% access to hot pages [1-4], 20% to cold pages [10-15]"
        },
        {
            "name": "Cyclic Pattern",
            "addresses": TestGenerator.cyclic_pattern([1, 2, 3, 4, 5, 6], 5),
            "frames": [4, 8],
            "description": "Cycling through 6 pages, 5 complete cycles"
        },
        {
            "name": "OPT Showcase",
            "addresses": TestGenerator.optimal_showcase_pattern(),
            "frames": [4, 6],
            "description": "Pattern designed to highlight OPT's lookahead advantage"
        },
        {
            "name": "LRU Worst Case",
            "addresses": TestGenerator.lru_worst_case(),
            "frames": [4, 8],
            "description": "Sequential scan larger than memory"
        },
        {
            "name": "FIFO Anomaly Pattern",
            "addresses": TestGenerator.fifo_anomaly_pattern(),
            "frames": [3, 4],
            "description": "Belady's anomaly: more frames might increase FIFO faults"
        },
        {
            "name": "Working Set Changes",
            "addresses": TestGenerator.working_set_pattern(),
            "frames": [6, 10],
            "description": "Working set changes from pages [0-4] to [5-9]"
        },
        {
            "name": "Large Random Test",
            "addresses": [random.randint(0, 65535) for _ in range(2000)],
            "frames": [16, 32],
            "description": "2000 random memory accesses"
        }
    ]
    
    algorithms = ["FIFO", "LRU", "OPT"]
    
    for test_case in test_cases:
        print(f"🧪 {test_case['name']}")
        print(f"   {test_case['description']}")
        print(f"   Total accesses: {len(test_case['addresses'])}")
        print()
        
        for frames in test_case['frames']:
            print(f"   📊 Results with {frames} frames:")
            results = {}
            
            for algorithm in algorithms:
                result = runner.run_test(test_case['addresses'], frames, algorithm)
                if 'error' in result:
                    print(f"      ❌ {algorithm}: {result['error']}")
                else:
                    results[algorithm] = result
                    print(f"      {algorithm:4}: {result['page_faults']:3d} page faults ({result['page_fault_rate']:5.1f}%)")
            
            # Analysis
            if len(results) == 3:
                best_algo = min(results.keys(), key=lambda x: results[x]['page_faults'])
                worst_algo = max(results.keys(), key=lambda x: results[x]['page_faults'])
                
                print(f"      🏆 Best: {best_algo} | 💥 Worst: {worst_algo}")
                
                # Check if OPT is optimal
                if best_algo == "OPT":
                    print("      ✅ OPT performed optimally as expected")
                else:
                    print("      ⚠️  OPT was not the best (unusual but possible with ties)")
                
                # Check for anomalies
                if test_case['name'] == "FIFO Anomaly Pattern" and len(test_case['frames']) > 1:
                    fifo_3 = None
                    fifo_4 = None
                    # This would need to be tracked across frame sizes
            
            print()
        
        print("-" * 60)
        print()

def create_belady_anomaly_test():
    """Special test to demonstrate Belady's anomaly with FIFO"""
    print("🔍 Testing Belady's Anomaly (FIFO should perform worse with more frames)")
    
    TestGenerator.create_backing_store()
    runner = TestRunner()
    
    # Classic anomaly pattern
    addresses = TestGenerator.fifo_anomaly_pattern()
    
    print(f"Pattern: {[addr >> 8 for addr in addresses]}")
    print("Testing with 3 and 4 frames:")
    
    for frames in [3, 4]:
        result = runner.run_test(addresses, frames, "FIFO")
        print(f"  FIFO with {frames} frames: {result['page_faults']} page faults")
    
    print("\nIf Belady's anomaly occurs, 4 frames should have MORE page faults than 3 frames!")

def main():
    if not os.path.exists("memSim") and not os.path.exists("memSim.py"):
        print("❌ memSim not found. Please build it first with 'make'")
        return
    
    # Run main test suite
    run_all_tests()
    
    # Special anomaly test
    create_belady_anomaly_test()
    
    print("\n=== Summary ===")
    print("✅ OPT should consistently perform best or tie for best")
    print("✅ LRU should perform well with temporal locality")
    print("✅ FIFO should be simplest but may suffer from anomalies")
    print("✅ All algorithms should have reasonable TLB hit rates")

if __name__ == "__main__":
    main()