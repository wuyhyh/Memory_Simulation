
import random
import matplotlib.pyplot as plt
import numpy as np
import os

TOTAL_PAGES = 2048
NODE_SPLIT = 1024
CYCLE_ACCESSES = 10240

class Page:
    def __init__(self, pfn):
        self.pfn = pfn
        self.access_count = 0
        self.node = 0 if pfn < NODE_SPLIT else 1
        self.latency_ns = 10 if self.node == 0 else 25
        self.is_hot = False

class MemorySimulator:
    def __init__(self):
        self.pages = [Page(pfn) for pfn in range(TOTAL_PAGES)]

    def access_page(self, pfn):
        self.pages[pfn].access_count += 1

    def simulate_access_cycle(self):
        mu = TOTAL_PAGES / 2
        sigma = TOTAL_PAGES / 6
        for _ in range(CYCLE_ACCESSES):
            pfn = int(random.gauss(mu, sigma)) % TOTAL_PAGES
            self.access_page(pfn)

    def classify_hot_cold(self, threshold_accesses=5120):
        access_counts = sorted([page.access_count for page in self.pages])
        cumulative = 0
        freq_threshold = 0
        for count in sorted(set(access_counts)):
            count_total = access_counts.count(count) * count
            cumulative += count_total
            if cumulative >= threshold_accesses:
                freq_threshold = count
                break
        for page in self.pages:
            page.is_hot = page.access_count >= freq_threshold
        return freq_threshold

    def migrate_pages_with_pfn_update(self, max_hot_ratio_node0=0.9):
        node0 = [p for p in self.pages if p.node == 0]
        node1 = [p for p in self.pages if p.node == 1]
        node0_cold = [p for p in node0 if not p.is_hot]
        node1_hot = [p for p in node1 if p.is_hot]
        node0_hot = [p for p in node0 if p.is_hot]
        limit = int(len(node0) * max_hot_ratio_node0)
        num = min(len(node0_cold), len(node1_hot), limit - len(node0_hot))
        pairs = zip(node0_cold[:num], node1_hot[:num])
        for cold, hot in pairs:
            cold_pfn, hot_pfn = cold.pfn, hot.pfn
            self.pages[cold_pfn], self.pages[hot_pfn] = hot, cold
            cold.pfn, hot.pfn = hot_pfn, cold_pfn
            cold.node, hot.node = 1, 0
            cold.latency_ns, hot.latency_ns = 25, 10

    def total_latency(self):
        return sum(p.access_count * p.latency_ns for p in self.pages)

    def plot_pfn_access(self, color=False):
        access = [p.access_count for p in self.pages]
        colors = ['red' if p.is_hot else 'blue' for p in self.pages] if color else 'blue'
        plt.figure(figsize=(14, 4))
        plt.bar(range(TOTAL_PAGES), access, color=colors)
        plt.title("PFN Access Count" + (" (Red: Hot, Blue: Cold)" if color else " (Uncolored)"))
        plt.xlabel("Page Frame Number (PFN)")
        plt.ylabel("Access Count")
        plt.tight_layout()
        plt.savefig(f"output/{plt.gca().get_title().replace(' ', '_').replace(':', '').lower()}.png")
        plt.close()

    def plot_access_histogram(self, color=False):
        access_counts = [p.access_count for p in self.pages]
        hist = np.bincount(access_counts)
        if color:
            threshold = min(p.access_count for p in self.pages if p.is_hot)
            colors = ['red' if i >= threshold else 'blue' for i in range(len(hist))]
        else:
            colors = 'lightblue'
        plt.figure(figsize=(10, 4))
        plt.bar(range(len(hist)), hist, color=colors)
        plt.title("Access Frequency Histogram" + (" (Red: Hot, Blue: Cold)" if color else " (Uncolored)"))
        plt.xlabel("Access Frequency")
        plt.ylabel("Number of Pages")
        plt.tight_layout()
        plt.savefig(f"output/{plt.gca().get_title().replace(' ', '_').replace(':', '').lower()}.png")
        plt.close()

if __name__ == "__main__":
    os.makedirs("output", exist_ok=True)
    sim = MemorySimulator()
    sim.simulate_access_cycle()

    # 迁移前图
    sim.plot_pfn_access(color=False)
    sim.plot_access_histogram(color=False)

    sim.classify_hot_cold()
    latency_before = sim.total_latency()

    sim.migrate_pages_with_pfn_update()
    latency_after = sim.total_latency()

    # 迁移后图
    sim.plot_pfn_access(color=True)
    sim.plot_access_histogram(color=True)

    print(f"Latency before migration: {latency_before} ns")
    print(f"Latency after migration: {latency_after} ns")
