import threading
import time

import m2_loader

dispatch_mod = m2_loader.module("dispatch")
Dispatcher = dispatch_mod.Dispatcher


def wait_for(predicate, timeout=3.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.01)
    return predicate()


def test_dispatcher_delivers_and_collapses_repeat_submits():
    executed = []
    gate = threading.Event()

    def handle(item):
        gate.wait(2)
        executed.append(item)

    dispatcher = Dispatcher(handle, workers=1)
    dispatcher.submit("INC-1")
    dispatcher.submit("INC-2")
    dispatcher.submit("INC-2")  # still queued: collapsed
    gate.set()
    assert wait_for(lambda: sorted(executed) == ["INC-1", "INC-2"])
    assert dispatcher.stats()["deduplicated"] == 1
    dispatcher.close(1)


def test_saturated_queue_defers_instead_of_dropping_and_the_sweep_delivers_later():
    gate = threading.Event()
    delivered = []
    dispatcher = Dispatcher(lambda i: (gate.wait(3), delivered.append(i)), maxsize=2, workers=1,
                            sweep=lambda: [], sweep_interval_s=60)
    accepted = [dispatcher.submit(f"I{n}") for n in range(6)]
    # One in flight + two queued; the rest are deferred, counted, and not lost.
    assert wait_for(lambda: dispatcher.stats()["in_flight"] == 1 or len(delivered) > 0)
    assert accepted.count(False) >= 2
    stats = dispatcher.stats()
    assert stats["deferred"] >= 2 and stats["deferred_now"] >= 2
    gate.set()
    while dispatcher.stats()["deferred_now"]:
        assert wait_for(lambda: dispatcher.stats()["queued"] == 0 and dispatcher.stats()["in_flight"] == 0)
        dispatcher.sweep_once()
    assert wait_for(lambda: sorted(set(delivered)) == [f"I{n}" for n in range(6)])
    dispatcher.close(1)


def test_submit_during_delivery_runs_once_more_after_it():
    started, release = threading.Event(), threading.Event()
    calls = []

    def handle(item):
        calls.append(item)
        if len(calls) == 1:
            started.set()
            release.wait(2)

    dispatcher = Dispatcher(handle, workers=2)
    dispatcher.submit("INC-X")
    assert started.wait(2)
    dispatcher.submit("INC-X")  # new alert while the first delivery is running
    assert dispatcher.stats()["in_flight"] == 1
    release.set()
    assert wait_for(lambda: calls == ["INC-X", "INC-X"])
    dispatcher.close(1)


def test_one_incident_is_never_delivered_concurrently_but_incidents_run_in_parallel():
    active, peak, same = {}, [0], []
    lock = threading.Lock()
    both_running = threading.Event()

    def handle(item):
        with lock:
            if active.get(item):
                same.append(item)
            active[item] = True
            peak[0] = max(peak[0], sum(active.values()))
            if sum(active.values()) == 2:
                both_running.set()
        both_running.wait(1)
        with lock:
            active[item] = False

    dispatcher = Dispatcher(handle, workers=2)
    for _ in range(3):
        dispatcher.submit("A")
        dispatcher.submit("B")
    assert both_running.wait(2)
    dispatcher.close(3)
    assert peak[0] == 2 and same == []


def test_unavailable_downstream_is_counted_and_retried_by_the_sweep():
    attempts = []
    pending = {"INC-DOWN"}

    def handle(item):
        attempts.append(item)
        if len(attempts) < 3:
            raise ConnectionError("shared API unavailable")
        pending.discard(item)

    dispatcher = Dispatcher(handle, workers=1, sweep=lambda: sorted(pending), sweep_interval_s=0.05)
    dispatcher.submit("INC-DOWN")
    assert wait_for(lambda: not pending, timeout=5)
    stats = dispatcher.stats()
    assert stats["failed_calls"] == 2 and stats["completed_calls"] == 1 and len(attempts) == 3
    dispatcher.close(1)


def test_close_drains_queued_work_and_reports_what_could_not_finish():
    gate = threading.Event()
    delivered = []
    dispatcher = Dispatcher(lambda i: (gate.wait(5), delivered.append(i)), workers=1)
    for n in range(3):
        dispatcher.submit(f"Q{n}")
    gate.set()
    assert dispatcher.close(timeout=3) == {"undelivered": []}
    assert delivered == ["Q0", "Q1", "Q2"]
    assert dispatcher.submit("LATE") is False  # intake stops on close

    stuck = Dispatcher(lambda i: time.sleep(2), workers=1)
    stuck.submit("SLOW")
    stuck.submit("WAITING")
    assert set(stuck.close(timeout=0.2)["undelivered"]) >= {"WAITING"}
