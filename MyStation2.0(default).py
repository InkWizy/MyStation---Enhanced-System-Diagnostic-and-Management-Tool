import shutil
import time
import sys
import os
import datetime
import threading

try:
    import psutil
except ImportError:
    psutil = None

try:
    import matplotlib.pyplot as plt

    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

try:
    import winshell
except ImportError:
    winshell = None


# Colors for styling
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    LIGHTBLUE = '\033[94m'
    LIGHTGREEN = '\033[92m'
    LIGHTYELLOW = '\033[93m'
    LIGHTRED = '\033[91m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'


def print_separator(title):
    print(Colors.HEADER + "\n" + "=" * len(title))
    print(Colors.BOLD + title + Colors.ENDC)
    print(Colors.HEADER + "=" * len(title) + Colors.ENDC)


# --- Core functions ---
def get_disks():
    if os.name == 'nt':
        import string
        return [f"{d}:\\ " for d in string.ascii_uppercase if os.path.exists(f"{d}:\\")]
    else:
        return ['/']


def format_size(bytes_value):
    if bytes_value >= 1024 ** 3:
        size = bytes_value / (1024 ** 3)
        unit = 'GB'
    elif bytes_value >= 1024 ** 2:
        size = bytes_value / (1024 ** 2)
        unit = 'MB'
    elif bytes_value >= 1024:
        size = bytes_value / 1024
        unit = 'KB'
    else:
        size = bytes_value
        unit = 'Bytes'
    return f"{size:.2f} {unit}"


def check_disk(drive):
    total, used, free = shutil.disk_usage(drive)
    print_separator(f"Disk: {drive}")
    print(f"{Colors.OKGREEN}  Total size: {format_size(total)}{Colors.ENDC}")
    print(f"{Colors.OKBLUE}  Used: {format_size(used)}{Colors.ENDC}")
    print(f"{Colors.WARNING}  Free: {format_size(free)}{Colors.ENDC}")
    return total, used, free


def save_history(data, filename='disk_usage_history.txt'):
    with open(filename, 'a') as file:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        file.write(f"\n{Colors.MAGENTA}{'-' * 40}\n")
        file.write(f"Timestamp: {timestamp}\n")
        for drive, usage in data.items():
            total, used, free = usage
            file.write(
                f"{drive} | Total: {format_size(total)} | Used: {format_size(used)} | Free: {format_size(free)}\n")
    print(Colors.OKCYAN + f"\nData saved to '{filename}'" + Colors.ENDC)


def plot_usage():
    if not HAS_MATPLOTLIB:
        print(Colors.FAIL + "Error: matplotlib is not installed. Install with 'pip install matplotlib'." + Colors.ENDC)
        return
    filename = 'disk_usage_history.txt'
    if not os.path.exists(filename):
        print(Colors.WARNING + "No data to display." + Colors.ENDC)
        return

    disks = []
    used_sizes = []
    free_sizes = []

    with open(filename, 'r') as f:
        for line in f:
            if 'Total' in line:
                parts = line.strip().split('|')  # split by vertical bar
                if len(parts) >= 3:
                    drive_name = parts[0].split(':')[0].strip()
                    try:
                        used_value = float(parts[1].split(':')[1].strip().replace(' GB', ''))
                        free_value = float(parts[2].split(':')[1].strip().replace(' GB', ''))
                        disks.append(drive_name)
                        used_sizes.append(used_value)
                        free_sizes.append(free_value)
                    except:
                        continue

    if disks:
        plt.figure(figsize=(10, 6))
        plt.bar(disks, used_sizes, label='Used', color='skyblue')
        plt.bar(disks, free_sizes, bottom=used_sizes, label='Free', color='lightgreen')
        plt.xlabel('Disks')
        plt.ylabel('Size (GB)')
        plt.title('Disk Usage Overview')
        plt.legend()
        plt.tight_layout()
        plt.show()


# --- Memory and CPU Monitoring ---
def get_memory_info():
    if psutil:
        mem = psutil.virtual_memory()
        total_gb = mem.total / (1024 ** 3)
        used_gb = mem.used / (1024 ** 3)
        percent_used = mem.percent
        return total_gb, used_gb, percent_used
    else:
        return None, None, None


def get_cpu_load():
    if psutil:
        return psutil.cpu_percent(interval=1)
    else:
        return None


def monitor_memory(interval=1):
    if not psutil:
        print(Colors.FAIL + "psutil is not installed. Memory monitoring is unavailable." + Colors.ENDC)
        return
    try:
        while True:
            total, used, percent = get_memory_info()
            print(f"\r{Colors.OKCYAN}Memory: {used:.2f} GB out of {total:.2f} GB ({percent}%) {Colors.ENDC}", end='')
            sys.stdout.flush()
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n" + Colors.WARNING + "Memory monitoring stopped." + Colors.ENDC)


def monitor_cpu(interval=1):
    if not psutil:
        print(Colors.FAIL + "psutil is not installed, CPU is unavailable." + Colors.ENDC)
        return
    try:
        while True:
            cpu_percent = get_cpu_load()
            print(f"\r{Colors.OKCYAN}CPU Load: {cpu_percent:.2f}% {Colors.ENDC}", end='')
            sys.stdout.flush()
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n" + Colors.WARNING + "CPU monitoring stopped." + Colors.ENDC)


# --- Extended Monitoring ---
def live_monitoring():
    if not psutil or not HAS_MATPLOTLIB:
        print(Colors.FAIL + "psutil and matplotlib are required." + Colors.ENDC)
        return
    duration = 10  # seconds
    cpu_usage = []
    memory_usage = []

    print(Colors.HEADER + "Starting 10-second monitoring..." + Colors.ENDC)
    for _ in range(duration):
        cpu_usage.append(psutil.cpu_percent(interval=1))
        mem = psutil.virtual_memory()
        memory_usage.append(mem.percent)
    timestamps = list(range(duration))
    plt.figure(figsize=(12, 6))
    plt.subplot(2, 1, 1)
    plt.plot(timestamps, cpu_usage, label='CPU %', color='blue')
    plt.ylabel('CPU Load (%)')
    plt.legend()

    plt.subplot(2, 1, 2)
    plt.plot(timestamps, memory_usage, label='Memory %', color='orange')
    plt.xlabel('Time (s)')
    plt.ylabel('Memory Usage (%)')
    plt.legend()

    plt.tight_layout()
    plt.show()


# --- Processes viewing ---
def list_processes():
    if not psutil:
        print(Colors.FAIL + "psutil is not installed. Unable to get processes." + Colors.ENDC)
        return
    print_separator("System Processes")
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
        try:
            pinfo = proc.info
            print(
                f"PID: {pinfo['pid']} | {pinfo['name']} | CPU: {pinfo['cpu_percent']}% | RAM: {pinfo['memory_percent']:.2f}%")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue


# --- System management ---
def system_commands():
    print_separator("System Management")
    print("1. Reboot\n2. Shutdown\n3. Clear temp files")
    choice = input("Choose an action: ")
    if choice == '1':
        if os.name == 'nt':
            os.system('shutdown /r /t 5')
        else:
            os.system('sudo reboot')
    elif choice == '2':
        if os.name == 'nt':
            os.system('shutdown /s /t 5')
        else:
            os.system('sudo shutdown now')
    elif choice == '3':
        temp_dir = os.getenv('TMP', '/tmp') if os.name != 'nt' else os.getenv('TEMP')
        try:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                os.makedirs(temp_dir)
                print(Colors.OKGREEN + "Temporary files cleaned." + Colors.ENDC)
        except Exception as e:
            print(Colors.FAIL + f"Error cleaning: {e}" + Colors.ENDC)
    else:
        print("Invalid choice.")


# --- File browsing ---
def browse_files():
    print_separator("Local Filesystem")
    path = input("Enter path to browse (default /): ").strip()
    if not path:
        path = '/'
    if os.path.exists(path):
        print(f"Files and folders in {path}:")
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            size = os.path.getsize(item_path)
            print(f"{item} - {format_size(size)}")
    else:
        print(Colors.FAIL + "Path not found." + Colors.ENDC)


# --- Windows System Optimization ---
def windows_optimization():
    """Perform Windows system optimization tasks"""
    if os.name != 'nt':
        print(Colors.FAIL + "This feature is only available on Windows systems." + Colors.ENDC)
        return

    print_separator("Windows System Optimization")

    while True:
        print(f"{Colors.OKGREEN}1.{Colors.ENDC} Clean Temporary Files")
        print(f"{Colors.OKGREEN}2.{Colors.ENDC} Clear Windows Update Cache")
        print(f"{Colors.OKGREEN}3.{Colors.ENDC} Clear DNS Cache")
        print(f"{Colors.OKGREEN}4.{Colors.ENDC} Clear Windows Prefetch")
        print(f"{Colors.OKGREEN}5.{Colors.ENDC} Optimize Disk Drives (Defrag)")
        print(f"{Colors.OKGREEN}6.{Colors.ENDC} Clean Recycle Bin")
        print(f"{Colors.OKGREEN}7.{Colors.ENDC} Clear Windows Event Logs")
        print(f"{Colors.OKGREEN}8.{Colors.ENDC} Disable Unnecessary Startup Programs")
        print(f"{Colors.OKGREEN}9.{Colors.ENDC} Run All Optimizations")
        print(f"{Colors.WARNING}0.{Colors.ENDC} Return to Main Menu")

        choice = input("Select optimization task: ")

        if choice == '0':
            break
        elif choice == '1':
            clean_temp_files()
        elif choice == '2':
            clear_update_cache()
        elif choice == '3':
            clear_dns_cache()
        elif choice == '4':
            clear_prefetch()
        elif choice == '5':
            optimize_disks()
        elif choice == '6':
            clean_recycle_bin()
        elif choice == '7':
            clear_event_logs()
        elif choice == '8':
            manage_startup_programs()
        elif choice == '9':
            run_all_optimizations()
        else:
            print(Colors.FAIL + "Invalid choice. Please try again." + Colors.ENDC)


def clean_temp_files():
    """Clean Windows temporary files"""
    print(Colors.OKCYAN + "Cleaning temporary files..." + Colors.ENDC)
    temp_dirs = [
        os.getenv('TEMP'),
        os.getenv('WINDIR') + '\\Temp' if os.getenv('WINDIR') else None,
        os.getenv('LOCALAPPDATA') + '\\Temp' if os.getenv('LOCALAPPDATA') else None
    ]

    cleaned_size = 0
    for temp_dir in temp_dirs:
        if temp_dir and os.path.exists(temp_dir):
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    try:
                        file_path = os.path.join(root, file)
                        file_size = os.path.getsize(file_path)
                        os.remove(file_path)
                        cleaned_size += file_size
                    except:
                        continue

    print(Colors.OKGREEN + f"Cleaned {format_size(cleaned_size)} of temporary files." + Colors.ENDC)


def clear_update_cache():
    """Clear Windows Update cache"""
    print(Colors.OKCYAN + "Clearing Windows Update cache..." + Colors.ENDC)
    update_cache = os.getenv('WINDIR') + '\\SoftwareDistribution\\Download' if os.getenv('WINDIR') else None

    if update_cache and os.path.exists(update_cache):
        try:
            shutil.rmtree(update_cache)
            os.makedirs(update_cache)
            print(Colors.OKGREEN + "Windows Update cache cleared successfully." + Colors.ENDC)
        except Exception as e:
            print(Colors.FAIL + f"Error clearing update cache: {e}" + Colors.ENDC)
    else:
        print(Colors.WARNING + "Update cache directory not found." + Colors.ENDC)


def clear_dns_cache():
    """Clear DNS cache"""
    print(Colors.OKCYAN + "Clearing DNS cache..." + Colors.ENDC)
    try:
        os.system('ipconfig /flushdns')
        print(Colors.OKGREEN + "DNS cache cleared successfully." + Colors.ENDC)
    except Exception as e:
        print(Colors.FAIL + f"Error clearing DNS cache: {e}" + Colors.ENDC)


def clear_prefetch():
    """Clear Windows Prefetch files"""
    print(Colors.OKCYAN + "Clearing Prefetch files..." + Colors.ENDC)
    prefetch_dir = os.getenv('WINDIR') + '\\Prefetch' if os.getenv('WINDIR') else None

    if prefetch_dir and os.path.exists(prefetch_dir):
        try:
            for file in os.listdir(prefetch_dir):
                file_path = os.path.join(prefetch_dir, file)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            print(Colors.OKGREEN + "Prefetch files cleared successfully." + Colors.ENDC)
        except Exception as e:
            print(Colors.FAIL + f"Error clearing prefetch: {e}" + Colors.ENDC)
    else:
        print(Colors.WARNING + "Prefetch directory not found." + Colors.ENDC)


def optimize_disks():
    """Optimize/defragment disk drives"""
    print(Colors.OKCYAN + "Optimizing disk drives..." + Colors.ENDC)
    try:
        # Get all drives
        import string
        drives = [f"{d}:" for d in string.ascii_uppercase if os.path.exists(f"{d}:\\")]

        for drive in drives:
            print(f"Optimizing drive {drive}...")
            os.system(f'defrag {drive}: /U /V' if os.name == 'nt' else f'sudo defrag {drive}:')

        print(Colors.OKGREEN + "Disk optimization completed." + Colors.ENDC)
    except Exception as e:
        print(Colors.FAIL + f"Error optimizing disks: {e}" + Colors.ENDC)


def clean_recycle_bin():
    """Clean Recycle Bin for all users"""
    print(Colors.OKCYAN + "Cleaning Recycle Bin..." + Colors.ENDC)
    try:
        # Using Windows shell command to empty recycle bin
        if winshell:
            winshell.recycle_bin().empty(confirm=False, show_progress=False, sound=False)
            print(Colors.OKGREEN + "Recycle Bin cleared successfully." + Colors.ENDC)
        else:
            print(Colors.WARNING + "winshell module not installed. Install with 'pip install winshell'." + Colors.ENDC)
    except Exception as e:
        print(Colors.FAIL + f"Error cleaning Recycle Bin: {e}" + Colors.ENDC)


def clear_event_logs():
    """Clear Windows Event Logs"""
    print(Colors.OKCYAN + "Clearing Windows Event Logs..." + Colors.ENDC)
    try:
        logs = ['Application', 'System', 'Security', 'Setup']
        for log in logs:
            os.system(f'wevtutil cl {log}')
        print(Colors.OKGREEN + "Event logs cleared successfully." + Colors.ENDC)
    except Exception as e:
        print(Colors.FAIL + f"Error clearing event logs: {e}" + Colors.ENDC)


def manage_startup_programs():
    """Manage startup programs"""
    print(Colors.OKCYAN + "Managing startup programs..." + Colors.ENDC)
    try:
        # Open startup folder
        startup_path = os.getenv('APPDATA') + '\\Microsoft\\Windows\\Start Menu\\Programs\\Startup'
        if os.path.exists(startup_path):
            print(f"Startup programs location: {startup_path}")
            print("List of startup programs:")
            for item in os.listdir(startup_path):
                print(f"  - {item}")

            remove = input("Enter filename to remove from startup (or press Enter to skip): ").strip()
            if remove:
                file_path = os.path.join(startup_path, remove)
                if os.path.exists(file_path):
                    os.remove(file_path)
                    print(Colors.OKGREEN + f"Removed {remove} from startup." + Colors.ENDC)
        else:
            print(Colors.WARNING + "Startup folder not found." + Colors.ENDC)
    except Exception as e:
        print(Colors.FAIL + f"Error managing startup programs: {e}" + Colors.ENDC)


def run_all_optimizations():
    """Run all optimization tasks"""
    print(Colors.HEADER + "Running all Windows optimizations..." + Colors.ENDC)

    optimizations = [
        ("Cleaning temporary files", clean_temp_files),
        ("Clearing update cache", clear_update_cache),
        ("Clearing DNS cache", clear_dns_cache),
        ("Clearing prefetch", clear_prefetch),
        ("Optimizing disks", optimize_disks),
        ("Cleaning Recycle Bin", clean_recycle_bin),
        ("Clearing event logs", clear_event_logs),
    ]

    for task_name, task_func in optimizations:
        print(f"\n{Colors.OKCYAN}>>> {task_name}..." + Colors.ENDC)
        try:
            task_func()
        except Exception as e:
            print(Colors.FAIL + f"Error during {task_name}: {e}" + Colors.ENDC)
        time.sleep(1)

    print(Colors.OKGREEN + "\nAll optimizations completed!" + Colors.ENDC)


# --- Main menu ---
def main():
    while True:
        print_separator(
            "MyStation: Memory and data view. Simple.\nv2.0\nBy - InkWizy")
        print(f"{Colors.OKGREEN}1.{Colors.ENDC} Check Disks")
        print(
            f"{Colors.OKGREEN}2.{Colors.ENDC} Memory Monitoring{Colors.WARNING} (Warning: This feature overrides all others.)")
        print(
            f"{Colors.OKGREEN}3.{Colors.ENDC} CPU Monitoring{Colors.WARNING} (Warning: This feature overrides all others.)")
        print(f"{Colors.OKGREEN}4.{Colors.ENDC} Usage Graphs")
        print(f"{Colors.OKGREEN}5.{Colors.ENDC} View Processes")
        print(f"{Colors.OKGREEN}6.{Colors.ENDC} System Management")
        print(f"{Colors.OKGREEN}7.{Colors.ENDC} File Browser")
        print(f"{Colors.OKGREEN}8.{Colors.ENDC} Windows System Optimization")
        print(f"{Colors.WARNING}9.{Colors.ENDC} Extended Features (Coming soon!)")
        print(f"{Colors.FAIL}10.{Colors.ENDC} Exit")
        choice = input("Select a menu item: ")

        if choice == '1':
            disks = get_disks()
            usage_data = {}
            for d in disks:
                total, used, free = check_disk(d)
                usage_data[d] = (total, used, free)
            save_history(usage_data)
        elif choice == '2':
            monitor_memory()
        elif choice == '3':
            monitor_cpu()
        elif choice == '4':
            plot_usage()
        elif choice == '5':
            list_processes()
        elif choice == '6':
            system_commands()
        elif choice == '7':
            browse_files()
        elif choice == '8':
            windows_optimization()
        elif choice == '9':
            live_monitoring()
        elif choice == '10':
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()