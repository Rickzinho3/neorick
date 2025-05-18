"""
    @Author: Henrique, J. F. S
    @Version: 1.0.0
    @Release: 21.04.2025
"""

import wmi
from math import ceil
import psutil
from time import sleep
from rich.console import Console
from rich.progress import Progress
import os
import socket

console = Console()
time = 0.05

def main():
    with Progress() as progress:
        task = progress.add_task("Loading information...", total=100)
        progress.update(task, advance=10)

        pc = wmi.WMI()
        os_info = pc.Win32_OperatingSystem()[0]
        gpu = pc.Win32_VideoController()[0].name
        cpu = pc.Win32_Processor()[0].name
        progress.update(task, advance=40)
        user = pc.Win32_Processor()[0].SystemName
        system = os_info.Caption
        ram = ceil(int(os_info.TotalVisibleMemorySize) / (1024 ** 2))
        fram = ceil(int(os_info.FreePhysicalMemory) / (1024 ** 2))
        arch = os_info.OSArchitecture
        email = os_info.RegisteredUser

        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)

        net = psutil.net_io_counters()
        sent = net.bytes_sent / (1024 ** 2)
        recv = net.bytes_recv / (1024 ** 2)

        storage = ''
        free_storage = ''
        for partition in pc.Win32_LogicalDisk():
            if partition.DriveType == 3:
                storage = f'{int(partition.Size) // (1024 ** 3)} GB'
                free_storage = f'{int(partition.FreeSpace) // (1024 ** 3)} GB' if partition.FreeSpace else '0 GB'
        
        progress.update(task, advance=50)

    logo_lines = """
...=****+:....=*****+...:************+=......
..=%*****%#..*%******@..@*************#%%*...
..+%******%#.-%******@..@****************%#..
..#%*******%#-##*****@..@*******##*******#%..
..%#********#%@#*****@..@******%#+%#*****%:..
..@******************%.-%******#%%#***%%*....
..@******************%-+%***********#%%*:....
..@******%@%#********%=*%******%@%******%#...
..@******%*-%#*******%=%%******%#*%******#%..
..@******##.:%%******%=%#******%*=%*******%+.
..@******#%-..+%#****@.%#******%#-##******#%.
..-**###**-.....=*##*...***##**+:.:**###***:.
""".splitlines()

    os.system("cls" if os.name == 'nt' else "clear")

    infos = [
        f"[purple]USER[/]           {user}",
        f"[purple]HOSTNAME[/]       {hostname or 'Unknown'}",
        f"[purple]E-MAIL[/]         {email}",
        f"[purple]SYSTEM[/]         {system}",
        f"[purple]CPU[/]            {cpu}",
        f"[purple]GPU[/]            {gpu}",
        f"[purple]RAM[/]            {ram:.2f} GB",
        f"[purple]FREE RAM[/]       {fram:.2f} GB",
        f"[purple]STORAGE[/]        {storage}",
        f"[purple]FREE STORAGE[/]   {free_storage}",
        f"[purple]ARCHITECTURE[/]   {arch}",
        f"[purple]UPLOAD[/]         {sent:.2f} MB",
        f"[purple]DOWNLOAD[/]       {recv:.2f} MB",
        f"[purple]LOCAL IP[/]       {ip_address}"
    ]

    max_lines = max(len(logo_lines), len(infos))
    logo_lines += [""] * (max_lines - len(logo_lines))
    infos += [""] * (max_lines - len(infos))

    for l, i in zip(logo_lines, infos):
        console.print(f"[white]{l:<50}[/] {i}")
        sleep(time)

    cpu_usage = psutil.cpu_percent()
    cpu_percent = cpu_usage / 100
    mem_usage = psutil.virtual_memory().percent
    mem_percent = mem_usage / 100
    bars = 30

    cpu_bar = '[purple]/[/]' * int(cpu_percent * bars) + '[white]/[/]' * (bars - int(cpu_percent * bars))
    mem_bar = '[purple]/[/]' * int(mem_percent * bars) + '[white]/[/]' * (bars - int(mem_percent * bars))

    console.print(f'\n[purple]CPU[/]    -=[ {cpu_bar} ]=-  [purple]{cpu_usage:.2f}[/]%    |    ', end='')
    console.print(f"[purple]MEMORY[/] -=[ {mem_bar} ]=- [purple]{mem_usage:.2f}[/]%\n")

if __name__ == "__main__":
    main()
