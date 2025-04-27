
import random
import matplotlib.pyplot as plt
import numpy as np

TOTAL_PAGES = 2048
NODE_SPLIT = 1024
PAGE_SIZE = 4 * 1024
CYCLE_ACCESSES = 10240

class Page:
    def __init__(self, pfn):
        self.pfn = pfn
        self.accessed = False
        self.access_count = 0
        self.node = 0 if pfn < NODE_SPLIT else 1
        self.latency_ns = 10 if self.node == 0 else 25
        self.is_hot = False

class MemorySimulator:
    def __init__(self):
        self.pages = [Page(pfn) for pfn in range(TOTAL_PAGES)]

    def access_page(self, pfn):
        page = self.pages[pfn]
        page.accessed = True
        page.access_count += 1

    def simulate_access_cycle(self, num_accesses=CYCLE_ACCESSES):
        mu = TOTAL_PAGES / 2
        sigma = TOTAL_PAGES / 6
        for _ in range(num_accesses):
            pfn = int(random.gauss(mu, sigma)) % TOTAL_PAGES
            self.access_page(pfn)

    def classify_hot_cold_by_histogram(self, threshold_accesses=5120):
        access_counts = sorted([page.access_count for page in self.pages])
        cumulative = 0
        freq_threshold = 0
        for count in sorted(set(access_counts)):
            pages_with_this_count = access_counts.count(count)
            cumulative += pages_with_this_count * count
            if cumulative >= threshold_accesses:
                freq_threshold = count
                break
        for page in self.pages:
            page.is_hot = page.access_count >= freq_threshold
        return freq_threshold

    def migrate_pages_with_pfn_update(self, max_hot_ratio_node0=0.9):
        node0_pages = [p for p in self.pages if p.node == 0]
        node1_pages = [p for p in self.pages if p.node == 1]
        node0_hot = [p for p in node0_pages if p.is_hot]
        node0_cold = [p for p in node0_pages if not p.is_hot]
        node1_hot = [p for p in node1_pages if p.is_hot]
        max_hot_allowed = int(len(node0_pages) * max_hot_ratio_node0)
        num_migratable = min(len(node0_cold), len(node1_hot), max_hot_allowed - len(node0_hot))
        pages_to_swap = list(zip(node0_cold[:num_migratable], node1_hot[:num_migratable]))
        for cold_page, hot_page in pages_to_swap:
            cold_pfn, hot_pfn = cold_page.pfn, hot_page.pfn
            self.pages[cold_pfn], self.pages[hot_pfn] = hot_page, cold_page
            cold_page.pfn, hot_page.pfn = hot_pfn, cold_pfn
            cold_page.node = 1
            cold_page.latency_ns = 25
            hot_page.node = 0
            hot_page.latency_ns = 10

    def calculate_total_latency(self):
        return sum(page.access_count * page.latency_ns for page in self.pages)

    def plot_colored_pfn_access_distribution(self):
        access_counts = [page.access_count for page in self.pages]
        colors = ['red' if page.is_hot else 'blue' for page in self.pages]
        plt.figure(figsize=(14, 4))
        plt.bar(range(TOTAL_PAGES), access_counts, color=colors)
        plt.title("PFN Access Count (Red: Hot, Blue: Cold)")
        plt.xlabel("Page Frame Number (PFN)")
        plt.ylabel("Access Count")
        plt.tight_layout()
        plt.show()

    def plot_colored_access_frequency_histogram(self):
        access_counts = [page.access_count for page in self.pages]
        max_count = max(access_counts)
        hist = [0] * (max_count + 1)
        for page in self.pages:
            hist[page.access_count] += 1
        colors = ['red' if count >= min(p.access_count for p in self.pages if p.is_hot) else 'blue'
                  for count in range(len(hist))]
        plt.figure(figsize=(10, 4))
        plt.bar(range(len(hist)), hist, color=colors, align='center', width=0.8)
        plt.title("Access Frequency Histogram (Red: Hot, Blue: Cold)")
        plt.xlabel("Access Frequency")
        plt.ylabel("Number of Pages")
        plt.tight_layout()
        plt.show()

if __name__ == "__main__":
    sim = MemorySimulator()
    sim.simulate_access_cycle()

    # 未染色访问图（PFN和频次）
    access_counts = [page.access_count for page in sim.pages]
    plt.figure(figsize=(14, 4))
    plt.bar(range(TOTAL_PAGES), access_counts)
    plt.title("PFN Access Count (Uncolored)")
    plt.xlabel("Page Frame Number (PFN)")
    plt.ylabel("Access Count")
    plt.tight_layout()
    plt.show()

    plt.figure(figsize=(10, 4))
    plt.hist(access_counts, bins=range(max(access_counts) + 2), align='left', rwidth=0.8)
    plt.title("Access Frequency Histogram (Uncolored)")
    plt.xlabel("Access Frequency")
    plt.ylabel("Number of Pages")
    plt.tight_layout()
    plt.show()

    threshold = sim.classify_hot_cold_by_histogram()
    sim.plot_colored_pfn_access_distribution()
    sim.plot_colored_access_frequency_histogram()
    latency_before = sim.calculate_total_latency()
    sim.migrate_pages_with_pfn_update()
    latency_after = sim.calculate_total_latency()
    sim.plot_colored_pfn_access_distribution()
    # sim.plot_colored_access_frequency_histogram()
    print(f"Latency before migration: {latency_before} ns")
    print(f"Latency after migration: {latency_after} ns")
