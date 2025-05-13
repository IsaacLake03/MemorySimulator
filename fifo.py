# This file is the implementation for the FIFO page replacement algorithm.

def fifo(pages, capacity):
    """
    Simulates the FIFO page replacement algorithm.

    Args:
        pages (list): A list of page numbers to be accessed.
        capacity (int): The maximum number of pages that can be held in memory.

    Returns:
        int: The number of page faults that occurred during the simulation.
    """
    memory = []
    page_faults = 0

    for page in pages:
        if page not in memory:
            if len(memory) < capacity:
                memory.append(page)
            else:
                memory.pop(0)  # Remove the oldest page
                memory.append(page)
            page_faults += 1

    return page_faults