import psutil
from prometheus_client import Gauge

MEMORY_USAGE_VMS = Gauge(
    "odoo_worker_memory_user_vms_mb", "Memory usage in MB", ["process", "pid"]
)

MEMORY_USAGE_RSS = Gauge(
    "odoo_worker_memory_user_rss_mb", "Memory usage in MB", ["process", "pid"]
)


def get_process_info():
    for process in psutil.process_iter(
        ["pid", "name", "memory_full_info", "cmdline", "nice"]
    ):
        try:
            if process.info["memory_full_info"]:
                if process.info["nice"] == 10:
                    ProcessLabel = "workercron"
                elif process.info["pid"] == 1:
                    ProcessLabel = "dispatcher"
                elif any("gevent" in x for x in process.info["cmdline"]):
                    ProcessLabel = "gevent"
                elif any("odoo" in x for x in process.info["cmdline"]):
                    ProcessLabel = "workerhttp"
                elif any("shell" in x for x in process.cmdline()):
                    ProcessLabel = "OdooShell"
                else:
                    ProcessLabel = "other"
                MEMORY_USAGE_VMS.labels(ProcessLabel, process.info["pid"]).set(
                    process.info["memory_full_info"].rss // 1000000
                )
                MEMORY_USAGE_RSS.labels(ProcessLabel, process.info["pid"]).set(
                    process.info["memory_full_info"].vms // 1000000
                )

        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
