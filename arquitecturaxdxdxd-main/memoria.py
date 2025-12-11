from collections import OrderedDict


class MemoryManager:

    def __init__(self, total_ram_bytes=1024, page_size_bytes=64, cache_capacity_pages=32):
        self.page_size = page_size_bytes
        self.total_pages = max(1, total_ram_bytes // page_size_bytes)
        self.free_pages = self.total_pages
        
        self.page_table = {}
        self.swap_table = {}
        
        self.cache = OrderedDict()
        self.cache_capacity = cache_capacity_pages
        
        self.logs = []

    def log(self, message):
        self.logs.append(message)

    def allocate(self, pid, bytes_requested):
        pages_needed = max(0, (bytes_requested + self.page_size - 1) // self.page_size)
        if pages_needed == 0:
            return True

        self.page_table.setdefault(pid, 0)
        self.swap_table.setdefault(pid, 0)

        while self.free_pages < pages_needed:
            if not self.cache:
                victim_pid = max(self.page_table, key=lambda p: self.page_table[p], default=None)
                
                if victim_pid is None or self.page_table[victim_pid] == 0:
                    self.log(f"ALLOC FAIL: pid={pid}, need={pages_needed} pages, free={self.free_pages}")
                    return False
                
                self.page_table[victim_pid] -= 1
                self.swap_table[victim_pid] += 1
                self.free_pages += 1
                self.log(f"SWAP OUT: pid={victim_pid} -> swap pages={self.swap_table[victim_pid]}")
            else:
                victim_key, _ = self.cache.popitem(last=False)
                victim_pid, _victim_index = victim_key
                
                if self.page_table.get(victim_pid, 0) > 0:
                    self.page_table[victim_pid] -= 1
                    self.swap_table[victim_pid] = self.swap_table.get(victim_pid, 0) + 1
                    self.free_pages += 1
                    self.log(f"SWAP OUT (LRU): pid={victim_pid}")

        self.page_table[pid] += pages_needed
        self.free_pages -= pages_needed
        
        for i in range(pages_needed):
            self._touch_cache((pid, i))

        self.log(f"ALLOC: pid={pid}, pages={pages_needed}, free={self.free_pages}")
        return True

    def _touch_cache(self, key):
        if key in self.cache:
            self.cache.move_to_end(key, last=True)
        else:
            self.cache[key] = True
            if len(self.cache) > self.cache_capacity:
                self.cache.popitem(last=False)

    def access(self, pid, page_index):
        if self.page_table.get(pid, 0) == 0 and self.swap_table.get(pid, 0) > 0:
            
            if self.free_pages == 0:
                if self.cache:
                    victim_key, _ = self.cache.popitem(last=False)
                    victim_pid, _victim_index = victim_key
                    self.page_table[victim_pid] -= 1
                    self.swap_table[victim_pid] = self.swap_table.get(victim_pid, 0) + 1
                    self.free_pages += 1
                    self.log(f"SWAP OUT (on access): pid={victim_pid}")
            
            self.swap_table[pid] -= 1
            self.page_table[pid] = self.page_table.get(pid, 0) + 1
            self.free_pages -= 1
            self.log(f"SWAP IN: pid={pid}")

        self._touch_cache((pid, page_index))

    def free(self, pid):
        pages = self.page_table.pop(pid, 0)
        self.free_pages += pages
        
        self.swap_table.pop(pid, None)
        
        for key in list(self.cache.keys()):
            if key[0] == pid:
                del self.cache[key]
        
        self.log(f"FREE: pid={pid}, freed={pages}, free={self.free_pages}")

    def stats(self):
        used_ram = self.total_pages - self.free_pages
        swap_pages = sum(self.swap_table.values()) if self.swap_table else 0
        return {
            'total_pages': self.total_pages,
            'used_pages': used_ram,
            'free_pages': self.free_pages,
            'swap_pages': swap_pages,
            'cache_size': len(self.cache),
        }