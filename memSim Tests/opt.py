# Implementation of a theoretical optimal page replacement algorithm

def opt(pages, capacity):
    """
    Simulates the Optimal page replacement algorithm.

    Args:
        pages (list): A list of page numbers to be accessed.
        capacity (int): The maximum number of pages that can be held in memory.

    Returns:
        int: The number of page faults that occurred during the simulation.
    """
    memory = []
    page_faults = 0

    for i, page in enumerate(pages):
        if page not in memory:
            if len(memory) < capacity:
                memory.append(page)
            else:
                # Find the page to replace
                farthest = -1
                page_to_replace = -1
                for mem_page in memory:
                    try:
                        next_use = pages[i + 1:].index(mem_page)
                    except ValueError:
                        next_use = float('inf')  # Page not found again
                    if next_use > farthest:
                        farthest = next_use
                        page_to_replace = mem_page

                memory.remove(page_to_replace)
                memory.append(page)
            page_faults += 1

    return page_faults