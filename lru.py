# Implementation of LRU Cache

def lru(pages, capacity):
    """
    Function to simulate LRU Cache
    :param ages: List of page numbers
    :param capacity: Capacity of the cache
    :return: Number of page faults
    """
    cache = []
    page_faults = 0

    for page in pages:
        if page not in cache:
            if len(cache) < capacity:
                cache.append(page)
            else:
                cache.pop(0)  # Remove the least recently used page
                cache.append(page)
            page_faults += 1
        else:
            # Move the accessed page to the end to mark it as recently used
            cache.remove(page)
            cache.append(page)

    return page_faults