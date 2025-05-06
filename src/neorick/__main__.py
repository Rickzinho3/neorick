import psutil
import platform
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from rich.progress import Progress

def create_pdf():
    with Progress() as progress:
        task = progress.add_task("Coletando dados do sistema", total=10)
        cpu_percent = [psutil.cpu_percent(interval=1) for _ in range(10)]
        progress.update(task, advance=1)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        sys_info = {
            "Sistema Operacional": platform.system(),
            "Versão": platform.version(),
            "Arquitetura": platform.machine(),
            "Processador": platform.processor(),
            "RAM Total (GB)": round(mem.total / (1024**3), 2),
            "Disco Total (GB)": round(disk.total / (1024**3), 2),
        }
        progress.update(task, advance=9)

    # Criar PDF
    with Progress() as progress:
        task = progress.add_task("Criando PDF", total=10)
        with PdfPages("relatorio_sistema.pdf") as pdf:
        # Página com informações do sistema
            plt.figure(figsize=(8.27, 11.69))
            plt.axis("off")
            text = "Informações do Sistema:\n\n" + "\n".join(f"{k}: {v}" for k, v in sys_info.items())
            plt.text(0.05, 0.95, text, va='top', ha='left', fontsize=12, wrap=True)
            pdf.savefig()
            plt.close()

            progress.update(task, advance=2)

            # Gráfico de uso da CPU
            plt.figure(figsize=(8.27, 11.69))
            plt.plot(cpu_percent, marker='o', color='blue')
            plt.title("Uso da CPU (%) nos últimos 10 segundos")
            plt.xlabel("Tempo (s)")
            plt.ylabel("Uso (%)")
            plt.grid(True)
            pdf.savefig()
            plt.close()

            progress.update(task, advance=3)

            # Gráfico de uso da RAM
            labels = ['Usada', 'Disponível']
            sizes = [mem.used, mem.available]
            plt.figure(figsize=(8.27, 11.69))
            plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140)
            plt.title("Uso da Memória RAM")
            pdf.savefig()
            plt.close()

            progress.update(task, advance=4)

            # Gráfico de uso do Disco
            labels = ['Usado', 'Livre']
            sizes = [disk.used, disk.free]
            plt.figure(figsize=(8.27, 11.69))
            plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140)
            plt.title("Uso do Disco")
            pdf.savefig()
            plt.close()

            progress.update(task, advance=1)

    print("Relatório criado com sucesso.")

if __name__ == "__main__":
    create_pdf()
