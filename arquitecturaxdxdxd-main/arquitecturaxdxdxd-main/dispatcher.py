from collections import deque


class Dispatcher:
    def __init__(self, num_cores=1):
        self.num_cores = max(1, int(num_cores))
        self.cores = [None for _ in range(self.num_cores)]
        self.gantt = []  # (time, core_id, pid)

    def set_cores(self, n):
        self.num_cores = max(1, int(n))
        self.cores = [None for _ in range(self.num_cores)]

    def tick(self, time, runnable_processes):
        """Assign up to num_cores processes to cores and record Gantt.

        runnable_processes: list[Proceso] selected by the scheduler for this tick.
        The first N elements are mapped to cores 0..N-1.
        """
        for core_id in range(self.num_cores):
            proc = runnable_processes[core_id] if core_id < len(runnable_processes) else None
            self.cores[core_id] = proc
            if proc is not None:
                self.gantt.append((time, core_id, proc.pid))

    def current_running(self):
        return [p for p in self.cores if p is not None]