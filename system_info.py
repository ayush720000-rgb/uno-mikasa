"""System status shown by /ping: uptime, RAM, CPU, disk and API latency.

Only the standard library is used. Inside a container (e.g. Render) the
numbers come from cgroup v2, so they describe the bot's own limits; on a
plain Linux host they come from /proc. A value that cannot be read is
returned as None and shown as "n/a" instead of raising.
"""

import os
import shutil
import time

BOT_STARTED = time.time()

CGROUP_DIR = '/sys/fs/cgroup'
PROC_DIR = '/proc'

# Mathematical sans-serif bold / italic letters, used for the /about text
_BOLD_BASE = (0x1D5D4, 0x1D5EE)    # capital A, small a
_ITALIC_BASE = (0x1D608, 0x1D622)  # capital A, small a


def styled(text, italic=False):
    """Write ASCII letters in the bold (or italic) sans-serif alphabet"""
    upper, lower = _ITALIC_BASE if italic else _BOLD_BASE
    out = []
    for ch in text:
        if 'A' <= ch <= 'Z':
            out.append(chr(upper + ord(ch) - ord('A')))
        elif 'a' <= ch <= 'z':
            out.append(chr(lower + ord(ch) - ord('a')))
        else:
            out.append(ch)
    return ''.join(out)


def _read(path):
    with open(path, encoding='utf-8') as handle:
        return handle.read()


def uptime_seconds(now=None):
    return (time.time() if now is None else now) - BOT_STARTED


def format_uptime(seconds):
    seconds = int(seconds)
    days, rest = divmod(seconds, 86400)
    hours, rest = divmod(rest, 3600)
    minutes, secs = divmod(rest, 60)
    if days:
        return "{}ᴅ:{:02d}ʜ:{:02d}ᴍ:{:02d}s".format(days, hours, minutes, secs)
    return "{}ʜ:{:02d}ᴍ:{:02d}s".format(hours, minutes, secs)


def format_percent(value):
    return "n/a" if value is None else "{:.1f}%".format(value)


def ram_percent(cgroup_dir=CGROUP_DIR, proc_dir=PROC_DIR):
    """Share of memory in use, counting page cache as free (like `docker stats`)"""
    try:
        limit = _read(os.path.join(cgroup_dir, 'memory.max')).strip()
        if limit != 'max':
            current = int(_read(os.path.join(cgroup_dir, 'memory.current')))
            inactive = 0
            try:
                for line in _read(os.path.join(cgroup_dir, 'memory.stat')).splitlines():
                    key, _sep, value = line.partition(' ')
                    if key == 'inactive_file':
                        inactive = int(value)
            except (OSError, ValueError):
                pass
            return 100.0 * max(current - inactive, 0) / int(limit)
    except (OSError, ValueError):
        pass

    try:
        info = {}
        for line in _read(os.path.join(proc_dir, 'meminfo')).splitlines():
            key, _sep, value = line.partition(':')
            info[key] = int(value.split()[0])
        total = info['MemTotal']
        return 100.0 * (total - info['MemAvailable']) / total
    except (OSError, ValueError, KeyError, ZeroDivisionError):
        return None


def _cgroup_cpu_usage_usec(cgroup_dir):
    for line in _read(os.path.join(cgroup_dir, 'cpu.stat')).splitlines():
        key, _sep, value = line.partition(' ')
        if key == 'usage_usec':
            return int(value)
    raise ValueError('usage_usec missing')


def _proc_cpu_times(proc_dir):
    fields = [int(x) for x in _read(os.path.join(proc_dir, 'stat')).splitlines()[0].split()[1:]]
    return fields[3] + fields[4], sum(fields)  # idle + iowait, total


def cpu_percent(interval=0.25, cgroup_dir=CGROUP_DIR, proc_dir=PROC_DIR):
    """CPU use over a short sample window"""
    try:
        cpus = os.cpu_count() or 1
        before = _cgroup_cpu_usage_usec(cgroup_dir)
        started = time.monotonic()
        time.sleep(interval)
        used = _cgroup_cpu_usage_usec(cgroup_dir) - before
        elapsed = time.monotonic() - started
        return 100.0 * (used / 1e6) / (elapsed * cpus)
    except (OSError, ValueError, ZeroDivisionError):
        pass

    try:
        idle_before, total_before = _proc_cpu_times(proc_dir)
        time.sleep(interval)
        idle_after, total_after = _proc_cpu_times(proc_dir)
        delta = total_after - total_before
        if delta <= 0:
            return 0.0
        return 100.0 * (1 - (idle_after - idle_before) / delta)
    except (OSError, ValueError, IndexError):
        return None


def disk_percent(path=None):
    """Share of the disk in use, measured where the bot runs"""
    path = path or os.path.abspath(os.sep)
    try:
        usage = shutil.disk_usage(path)
    except OSError:
        return None
    total = usage.used + usage.free
    return 100.0 * usage.used / total if total else None


def render_status(username, uptime, ram, cpu, disk, api_ms):
    """The /ping message. Labels use the same styled alphabet as the design."""
    api = "n/a" if api_ms is None else "{:.3f}ᴍs".format(api_ms)
    return "\n".join([
        "@{}♪ 𝖲𝗒𝗌𝗍𝖾𝗆 𝖲𝗍𝖺𝗍𝗌 :".format(username),
        "",
        "↬ 𝖴𝗉𝖳𝗂𝗆𝖾 : {}".format(format_uptime(uptime)),
        "↬ 𝖱𝖠𝖬 : {}".format(format_percent(ram)),
        "↬ 𝖢𝖯𝖴 : {}".format(format_percent(cpu)),
        "↬ 𝖣𝗂𝗌𝗄 : {}".format(format_percent(disk)),
        "↬ 𝖯𝗒-𝖳𝗀𝖼𝖺𝗅𝗅𝗌 : not avl.",
        "↬ 𝖳𝖾𝗅𝖾𝗀𝗋𝖺𝗆 𝖠𝖯𝖨 𝖯𝗂𝗇𝗀 : {}".format(api),
    ])
