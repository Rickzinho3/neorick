import psutil
import platform
import datetime
import os
import time
import socket
import matplotlib.pyplot as plt
import numpy as np
import io
from fpdf import FPDF
import matplotlib
from pathlib import Path
matplotlib.use('Agg')  # Necessário para ambientes sem interface gráfica

# Função para obter o diretório de Downloads do usuário
def obter_pasta_downloads():
    """Retorna o caminho para a pasta de Downloads do usuário atual."""
    # Primeiro, tenta o método mais comum
    home = Path.home()
    downloads = home / "Downloads"
    
    if downloads.exists() and downloads.is_dir():
        return downloads
    
    # Se não encontrou, tenta métodos específicos por sistema operacional
    sistema = platform.system()
    
    if sistema == "Windows":
        # No Windows, podemos usar a API do shell para obter a pasta de Downloads
        import winreg
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                               r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders") as key:
                downloads = Path(winreg.QueryValueEx(key, "{374DE290-123F-4565-9164-39C4925E467B}")[0])
                if downloads.exists():
                    return downloads
        except Exception:
            pass
        
        # Tenta outro método para Windows
        try:
            import ctypes
            from ctypes import windll, wintypes
            CSIDL_PERSONAL = 5  # Meus Documentos
            SHGFP_TYPE_CURRENT = 0
            buf = ctypes.create_unicode_buffer(wintypes.MAX_PATH)
            windll.shell32.SHGetFolderPathW(0, CSIDL_PERSONAL, 0, SHGFP_TYPE_CURRENT, buf)
            documents = Path(buf.value)
            downloads = documents / "Downloads"
            if downloads.exists():
                return downloads
        except Exception:
            pass
    
    elif sistema == "Darwin":  # macOS
        downloads = home / "Library" / "CloudStorage" / "Downloads"
        if downloads.exists() and downloads.is_dir():
            return downloads
    
    # Se tudo falhar, retorna o diretório home com uma pasta Downloads
    downloads = home / "Downloads"
    if not downloads.exists():
        try:
            downloads.mkdir(parents=True, exist_ok=True)
        except Exception:
            # Se não conseguir criar, usa o diretório atual
            return Path.cwd()
    
    return downloads

class RelatorioPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.WIDTH = 210
        self.HEIGHT = 297
        
        # Cores
        self.cor_primaria = (31, 73, 125)  # RGB: #1F497D
        self.cor_secundaria = (68, 114, 196)  # RGB: #4472C4
        self.cor_destaque = (237, 125, 49)  # RGB: #ED7D31
        self.cor_sucesso = (112, 173, 71)  # RGB: #70AD47
        self.cor_aviso = (255, 192, 0)  # RGB: #FFC000
        self.cor_erro = (192, 0, 0)  # RGB: #C00000
        
    def header(self):
        # Logo (se tivesse uma)
        # self.image('logo.png', 10, 8, 33)
        
        # Título do relatório
        self.set_font('Arial', 'B', 16)
        self.set_text_color(*self.cor_primaria)
        self.cell(0, 10, 'RELATÓRIO DE DESEMPENHO DO SISTEMA', 0, 1, 'C')
        
        # Subtítulo com data
        self.set_font('Arial', '', 12)
        self.set_text_color(100, 100, 100)
        data_atual = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        self.cell(0, 10, f'Gerado em: {data_atual}', 0, 1, 'C')
        
        # Linha separadora
        self.set_draw_color(*self.cor_secundaria)
        self.set_line_width(0.5)
        self.line(10, 30, 200, 30)
        self.ln(10)
        
    def footer(self):
        # Posicionar a 1.5 cm do final da página
        self.set_y(-15)
        
        # Linha separadora
        self.set_draw_color(*self.cor_secundaria)
        self.set_line_width(0.3)
        self.line(10, self.get_y(), 200, self.get_y())
        
        # Informações do rodapé
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Página {self.page_no()}/{{nb}}', 0, 0, 'C')
        
    def titulo_secao(self, titulo):
        self.set_font('Arial', 'B', 14)
        self.set_text_color(*self.cor_primaria)
        self.cell(0, 10, titulo, 0, 1, 'L')
        self.ln(2)
        
    def subtitulo_secao(self, titulo):
        self.set_font('Arial', 'B', 12)
        self.set_text_color(*self.cor_secundaria)
        self.cell(0, 8, titulo, 0, 1, 'L')
        self.ln(2)
        
    def texto_normal(self, texto):
        self.set_font('Arial', '', 10)
        self.set_text_color(0, 0, 0)
        self.multi_cell(0, 5, texto)
        self.ln(3)
        
    def texto_destaque(self, texto):
        self.set_font('Arial', 'B', 10)
        self.set_text_color(*self.cor_destaque)
        self.multi_cell(0, 5, texto)
        self.ln(3)
        
    def adicionar_tabela(self, cabecalho, dados, larguras=None):
        # Configurações da tabela
        if larguras is None:
            larguras = [self.WIDTH / len(cabecalho) - 20] * len(cabecalho)
            
        # Cabeçalho da tabela
        self.set_font('Arial', 'B', 10)
        self.set_fill_color(*self.cor_secundaria)
        self.set_text_color(255, 255, 255)
        
        for i, col in enumerate(cabecalho):
            self.cell(larguras[i], 7, col, 1, 0, 'C', True)
        self.ln()
        
        # Dados da tabela
        self.set_font('Arial', '', 9)
        self.set_text_color(0, 0, 0)
        
        fill = False
        for row in dados:
            if fill:
                self.set_fill_color(230, 239, 249)  # Cor de fundo alternada
            else:
                self.set_fill_color(255, 255, 255)  # Branco
                
            for i, col in enumerate(row):
                self.cell(larguras[i], 6, str(col), 1, 0, 'C', fill)
            self.ln()
            fill = not fill
            
        self.ln(5)
        
    def adicionar_alerta(self, texto, tipo="info"):
        # Definir cores com base no tipo
        cores = {
            "info": (225, 245, 254),  # Azul claro
            "sucesso": (232, 245, 233),  # Verde claro
            "aviso": (255, 248, 225),  # Amarelo claro
            "erro": (255, 235, 238)  # Vermelho claro
        }
        
        bordas = {
            "info": (3, 169, 244),  # Azul
            "sucesso": (76, 175, 80),  # Verde
            "aviso": (255, 152, 0),  # Laranja
            "erro": (244, 67, 54)  # Vermelho
        }
        
        titulos = {
            "info": "INFORMAÇÃO",
            "sucesso": "SUCESSO",
            "aviso": "ATENÇÃO",
            "erro": "ALERTA"
        }
        
        cor_fundo = cores.get(tipo, cores["info"])
        cor_borda = bordas.get(tipo, bordas["info"])
        titulo = titulos.get(tipo, titulos["info"])
        
        # Salvar posição atual
        x = self.get_x()
        y = self.get_y()
        
        # Desenhar retângulo de fundo
        self.set_fill_color(*cor_fundo)
        self.set_draw_color(*cor_borda)
        self.rect(x, y, 190, 20, 'DF')
        
        # Adicionar título
        self.set_xy(x + 5, y + 5)
        self.set_font('Arial', 'B', 10)
        self.set_text_color(*cor_borda)
        self.cell(0, 5, titulo, 0, 1, 'L')
        
        # Adicionar texto
        self.set_xy(x + 5, y + 10)
        self.set_font('Arial', '', 9)
        self.set_text_color(0, 0, 0)
        self.multi_cell(180, 4, texto)
        
        # Ajustar posição após o alerta
        self.set_y(y + 25)
        
    def adicionar_grafico(self, plt_figura, largura=190, altura=100):
        # Salvar a figura em um buffer
        buf = io.BytesIO()
        plt_figura.savefig(buf, format='png', dpi=300, bbox_inches='tight')
        buf.seek(0)
        
        # Adicionar a imagem ao PDF
        self.image(buf, x=10, y=None, w=largura)
        buf.close()
        self.ln(5)

def obter_info_sistema():
    info = {}
    
    # Informações do sistema operacional
    info['sistema'] = {
        'sistema': platform.system(),
        'versao': platform.version(),
        'arquitetura': platform.architecture()[0],
        'processador': platform.processor(),
        'nome_maquina': socket.gethostname(),
        'usuario': os.getlogin() if hasattr(os, 'getlogin') else 'N/A',
        'python_versao': platform.python_version(),
        'tempo_ativo': datetime.timedelta(seconds=int(time.time() - psutil.boot_time()))
    }
    
    # Informações de CPU
    info['cpu'] = {
        'nucleos_fisicos': psutil.cpu_count(logical=False),
        'nucleos_logicos': psutil.cpu_count(logical=True),
        'frequencia_max': psutil.cpu_freq().max if psutil.cpu_freq() else 'N/A',
        'uso_atual': psutil.cpu_percent(interval=1),
        'uso_por_nucleo': psutil.cpu_percent(interval=1, percpu=True)
    }
    
    # Informações de memória
    mem = psutil.virtual_memory()
    info['memoria'] = {
        'total': mem.total,
        'disponivel': mem.available,
        'percentual_uso': mem.percent,
        'usado': mem.used,
        'livre': mem.free
    }
    
    # Informações de disco
    discos = []
    for particao in psutil.disk_partitions():
        try:
            uso = psutil.disk_usage(particao.mountpoint)
            discos.append({
                'dispositivo': particao.device,
                'ponto_montagem': particao.mountpoint,
                'sistema_arquivos': particao.fstype,
                'total': uso.total,
                'usado': uso.used,
                'livre': uso.free,
                'percentual_uso': uso.percent
            })
        except (PermissionError, FileNotFoundError):
            # Algumas partições podem não ser acessíveis
            continue
    info['discos'] = discos
    
    # Informações de rede
    interfaces = []
    for nome, enderecos in psutil.net_if_addrs().items():
        for endereco in enderecos:
            if endereco.family == socket.AF_INET:  # IPv4
                interfaces.append({
                    'interface': nome,
                    'endereco': endereco.address,
                    'mascara': endereco.netmask,
                    'broadcast': endereco.broadcast
                })
    info['rede'] = interfaces
    
    # Estatísticas de rede
    io_inicio = psutil.net_io_counters()
    time.sleep(1)  # Espera 1 segundo para calcular a taxa
    io_fim = psutil.net_io_counters()
    
    info['rede_stats'] = {
        'bytes_enviados': io_fim.bytes_sent,
        'bytes_recebidos': io_fim.bytes_recv,
        'taxa_envio': io_fim.bytes_sent - io_inicio.bytes_sent,
        'taxa_recebimento': io_fim.bytes_recv - io_inicio.bytes_recv
    }
    
    # Processos
    processos = []
    for proc in psutil.process_iter(['pid', 'name', 'username', 'memory_percent', 'cpu_percent']):
        try:
            pinfo = proc.info
            processos.append({
                'pid': pinfo['pid'],
                'nome': pinfo['name'],
                'usuario': pinfo['username'],
                'memoria': pinfo['memory_percent'],
                'cpu': pinfo['cpu_percent']
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    
    # Ordenar por uso de memória (descendente)
    processos.sort(key=lambda x: x['memoria'], reverse=True)
    info['processos'] = processos[:10]  # Top 10 processos
    
    # Histórico de CPU (simulado para este exemplo)
    # Em um caso real, você teria que coletar esses dados ao longo do tempo
    info['historico_cpu'] = [psutil.cpu_percent(interval=0.1) for _ in range(60)]
    
    # Histórico de memória (simulado para este exemplo)
    info['historico_memoria'] = [psutil.virtual_memory().percent for _ in range(60)]
    
    return info

def bytes_para_gb(bytes_valor):
    return bytes_valor / (1024 ** 3)

def bytes_para_mb(bytes_valor):
    return bytes_valor / (1024 ** 2)

def criar_grafico_cpu(info):
    fig, ax = plt.subplots(figsize=(10, 5))
    
    # Gráfico de uso por núcleo
    nucleos = info['cpu']['uso_por_nucleo']
    x = np.arange(len(nucleos))
    ax.bar(x, nucleos, color='#4472C4')
    
    ax.set_title('Uso de CPU por Núcleo', fontsize=14, color='#1F497D')
    ax.set_xlabel('Núcleo', fontsize=12)
    ax.set_ylabel('Uso (%)', fontsize=12)
    ax.set_xticks(x)
    ax.set_xticklabels([f'Core {i+1}' for i in range(len(nucleos))])
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Adicionar valor em cada barra
    for i, v in enumerate(nucleos):
        ax.text(i, v + 1, f"{v:.1f}%", ha='center', fontsize=9)
    
    plt.tight_layout()
    return fig

def criar_grafico_memoria(info):
    fig, ax = plt.subplots(figsize=(8, 8))
    
    # Dados para o gráfico de pizza
    mem = info['memoria']
    usado_gb = bytes_para_gb(mem['usado'])
    livre_gb = bytes_para_gb(mem['livre'])
    
    # Criar gráfico de pizza
    labels = [f'Usado ({usado_gb:.2f} GB)', f'Livre ({livre_gb:.2f} GB)']
    sizes = [mem['percentual_uso'], 100 - mem['percentual_uso']]
    colors = ['#4472C4', '#70AD47']
    explode = (0.1, 0)  # Destacar a primeira fatia
    
    ax.pie(sizes, explode=explode, labels=labels, colors=colors,
           autopct='%1.1f%%', shadow=True, startangle=90)
    ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
    ax.set_title('Uso de Memória', fontsize=14, color='#1F497D')
    
    plt.tight_layout()
    return fig

def criar_grafico_disco(info):
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Preparar dados
    discos = info['discos']
    nomes = [d['ponto_montagem'] for d in discos]
    percentuais = [d['percentual_uso'] for d in discos]
    
    # Criar barras horizontais
    y_pos = np.arange(len(nomes))
    ax.barh(y_pos, percentuais, color='#ED7D31')
    
    # Personalizar gráfico
    ax.set_yticks(y_pos)
    ax.set_yticklabels(nomes)
    ax.invert_yaxis()  # Inverter para que o primeiro disco fique no topo
    ax.set_xlabel('Uso (%)')
    ax.set_title('Uso de Disco por Partição', fontsize=14, color='#1F497D')
    ax.grid(axis='x', linestyle='--', alpha=0.7)
    
    # Adicionar valor em cada barra
    for i, v in enumerate(percentuais):
        ax.text(v + 1, i, f"{v:.1f}%", va='center', fontsize=9)
    
    # Adicionar linhas de referência
    ax.axvline(x=70, color='#FFC000', linestyle='--', alpha=0.7)  # Aviso
    ax.axvline(x=90, color='#C00000', linestyle='--', alpha=0.7)  # Crítico
    
    plt.tight_layout()
    return fig

def criar_grafico_historico(info):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
    
    # Dados para os gráficos
    tempo = list(range(len(info['historico_cpu'])))
    cpu_dados = info['historico_cpu']
    memoria_dados = info['historico_memoria']
    
    # Gráfico de CPU
    ax1.plot(tempo, cpu_dados, 'o-', color='#4472C4', linewidth=2)
    ax1.set_title('Histórico de Uso de CPU', fontsize=14, color='#1F497D')
    ax1.set_ylabel('Uso (%)')
    ax1.grid(True, linestyle='--', alpha=0.7)
    ax1.set_ylim(0, 100)
    
    # Gráfico de Memória
    ax2.plot(tempo, memoria_dados, 'o-', color='#ED7D31', linewidth=2)
    ax2.set_title('Histórico de Uso de Memória', fontsize=14, color='#1F497D')
    ax2.set_xlabel('Tempo (segundos)')
    ax2.set_ylabel('Uso (%)')
    ax2.grid(True, linestyle='--', alpha=0.7)
    ax2.set_ylim(0, 100)
    
    plt.tight_layout()
    return fig

def criar_grafico_processos(info):
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Preparar dados
    processos = info['processos'][:5]  # Top 5 processos
    nomes = [f"{p['nome']} (PID: {p['pid']})" for p in processos]
    memoria = [p['memoria'] for p in processos]
    cpu = [p['cpu'] for p in processos]
    
    # Criar barras
    x = np.arange(len(nomes))
    width = 0.35
    
    ax.bar(x - width/2, memoria, width, label='Memória (%)', color='#4472C4')
    ax.bar(x + width/2, cpu, width, label='CPU (%)', color='#ED7D31')
    
    # Personalizar gráfico
    ax.set_title('Top 5 Processos por Uso de Recursos', fontsize=14, color='#1F497D')
    ax.set_ylabel('Uso (%)')
    ax.set_xticks(x)
    ax.set_xticklabels(nomes, rotation=45, ha='right')
    ax.legend()
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    return fig

def criar_relatorio_sistema():
    # Obter o diretório de Downloads
    pasta_downloads = obter_pasta_downloads()
    
    # Gerar nome do arquivo com timestamp para evitar sobrescrever arquivos existentes
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_arquivo = f"relatorio_sistema_{timestamp}.pdf"
    caminho_completo = pasta_downloads / nome_arquivo
    
    print(f"Gerando relatório em: {caminho_completo}")
    
    # Obter informações do sistema
    print("Coletando informações do sistema...")
    info = obter_info_sistema()
    
    # Criar gráficos
    print("Gerando gráficos...")
    grafico_cpu = criar_grafico_cpu(info)
    grafico_memoria = criar_grafico_memoria(info)
    grafico_disco = criar_grafico_disco(info)
    grafico_historico = criar_grafico_historico(info)
    grafico_processos = criar_grafico_processos(info)
    
    # Criar PDF
    print("Gerando relatório PDF...")
    pdf = RelatorioPDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    
    # Sumário Executivo
    pdf.titulo_secao("Sumário Executivo")
    
    # Informações básicas do sistema
    sistema = info['sistema']
    texto_sumario = (
        f"Este relatório apresenta uma análise detalhada do desempenho do sistema {sistema['sistema']} "
        f"versão {sistema['versao']} ({sistema['arquitetura']}). "
        f"O sistema está ativo há {sistema['tempo_ativo']} e está operando com {info['cpu']['nucleos_fisicos']} "
        f"núcleos físicos de CPU ({info['cpu']['nucleos_logicos']} núcleos lógicos)."
    )
    pdf.texto_normal(texto_sumario)
    
    # Alertas importantes
    cpu_atual = info['cpu']['uso_atual']
    mem_atual = info['memoria']['percentual_uso']
    
    if cpu_atual > 80:
        pdf.adicionar_alerta(
            f"O uso de CPU está em {cpu_atual}%, o que indica uma possível sobrecarga do sistema. "
            "Considere encerrar processos não essenciais ou investigar possíveis gargalos.",
            "erro"
        )
    elif cpu_atual > 60:
        pdf.adicionar_alerta(
            f"O uso de CPU está em {cpu_atual}%, o que está acima do ideal para operação contínua. "
            "Monitore o sistema para garantir que não haja degradação de desempenho.",
            "aviso"
        )
        
    if mem_atual > 80:
        pdf.adicionar_alerta(
            f"O uso de memória está em {mem_atual}%, o que pode causar lentidão no sistema. "
            "Considere encerrar aplicações que consomem muita memória ou aumentar a RAM disponível.",
            "erro"
        )
    elif mem_atual > 60:
        pdf.adicionar_alerta(
            f"O uso de memória está em {mem_atual}%, o que está acima do ideal. "
            "Monitore o sistema para garantir que não haja problemas de desempenho.",
            "aviso"
        )
    
    # Verificar discos críticos
    for disco in info['discos']:
        if disco['percentual_uso'] > 90:
            pdf.adicionar_alerta(
                f"O disco {disco['ponto_montagem']} está com {disco['percentual_uso']}% de uso. "
                f"Apenas {bytes_para_gb(disco['livre']):.2f} GB livres. "
                "Libere espaço para evitar problemas de desempenho e falhas.",
                "erro"
            )
        elif disco['percentual_uso'] > 75:
            pdf.adicionar_alerta(
                f"O disco {disco['ponto_montagem']} está com {disco['percentual_uso']}% de uso. "
                f"Apenas {bytes_para_gb(disco['livre']):.2f} GB livres. "
                "Considere liberar espaço em breve.",
                "aviso"
            )
    
    # Informações do Sistema
    pdf.add_page()
    pdf.titulo_secao("Informações do Sistema")
    
    # Tabela com informações do sistema
    cabecalho = ["Parâmetro", "Valor"]
    dados = [
        ["Sistema Operacional", sistema['sistema']],
        ["Versão", sistema['versao']],
        ["Arquitetura", sistema['arquitetura']],
        ["Processador", sistema['processador']],
        ["Nome da Máquina", sistema['nome_maquina']],
        ["Usuário", sistema['usuario']],
        ["Versão do Python", sistema['python_versao']],
        ["Tempo Ativo", str(sistema['tempo_ativo'])]
    ]
    
    pdf.adicionar_tabela(cabecalho, dados, [60, 130])
    
    # Análise de CPU
    pdf.subtitulo_secao("Análise de CPU")
    
    cpu = info['cpu']
    texto_cpu = (
        f"O sistema possui {cpu['nucleos_fisicos']} núcleos físicos e {cpu['nucleos_logicos']} núcleos lógicos. "
        f"A frequência máxima do processador é de {cpu['frequencia_max']} MHz. "
        f"Atualmente, o uso médio de CPU está em {cpu['uso_atual']}%."
    )
    pdf.texto_normal(texto_cpu)
    
    # Adicionar gráfico de CPU
    pdf.adicionar_grafico(grafico_cpu)
    
    # Análise de Memória
    pdf.subtitulo_secao("Análise de Memória")
    
    mem = info['memoria']
    texto_memoria = (
        f"O sistema possui {bytes_para_gb(mem['total']):.2f} GB de memória RAM total. "
        f"Atualmente, {bytes_para_gb(mem['usado']):.2f} GB estão em uso ({mem['percentual_uso']}%) "
        f"e {bytes_para_gb(mem['livre']):.2f} GB estão livres."
    )
    pdf.texto_normal(texto_memoria)
    
    # Adicionar gráfico de memória
    pdf.adicionar_grafico(grafico_memoria)
    
    # Nova página para análise de disco
    pdf.add_page()
    pdf.titulo_secao("Análise de Armazenamento")
    
    # Tabela com informações de disco
    cabecalho = ["Ponto de Montagem", "Total (GB)", "Usado (GB)", "Livre (GB)", "Uso (%)"]
    dados = []
    
    for disco in info['discos']:
        dados.append([
            disco['ponto_montagem'],
            f"{bytes_para_gb(disco['total']):.2f}",
            f"{bytes_para_gb(disco['usado']):.2f}",
            f"{bytes_para_gb(disco['livre']):.2f}",
            f"{disco['percentual_uso']}"
        ])
    
    pdf.adicionar_tabela(cabecalho, dados)
    
    # Adicionar gráfico de disco
    pdf.adicionar_grafico(grafico_disco)
    
    # Análise de Rede
    pdf.subtitulo_secao("Análise de Rede")
    
    # Tabela com informações de rede
    cabecalho = ["Interface", "Endereço IP", "Máscara", "Broadcast"]
    dados = []
    
    for interface in info['rede']:
        dados.append([
            interface['interface'],
            interface['endereco'],
            interface['mascara'] or "N/A",
            interface['broadcast'] or "N/A"
        ])
    
    pdf.adicionar_tabela(cabecalho, dados)
    
    # Estatísticas de rede
    rede_stats = info['rede_stats']
    texto_rede = (
        f"Total de dados enviados: {bytes_para_mb(rede_stats['bytes_enviados']):.2f} MB\n"
        f"Total de dados recebidos: {bytes_para_mb(rede_stats['bytes_recebidos']):.2f} MB\  MB\n"
        f"Total de dados recebidos: {bytes_para_mb(rede_stats['bytes_recebidos']):.2f} MB\n"
        f"Taxa de envio atual: {bytes_para_mb(rede_stats['taxa_envio']):.2f} MB/s\n"
        f"Taxa de recebimento atual: {bytes_para_mb(rede_stats['taxa_recebimento']):.2f} MB/s"
    )
    pdf.texto_normal(texto_rede)
    
    # Nova página para processos e histórico
    pdf.add_page()
    pdf.titulo_secao("Processos e Histórico")
    
    # Top processos
    pdf.subtitulo_secao("Top 10 Processos por Uso de Memória")
    
    # Tabela com informações de processos
    cabecalho = ["PID", "Nome", "Usuário", "Memória (%)", "CPU (%)"]
    dados = []
    
    for proc in info['processos']:
        dados.append([
            proc['pid'],
            proc['nome'],
            proc['usuario'] or "N/A",
            f"{proc['memoria']:.2f}",
            f"{proc['cpu']:.2f}"
        ])
    
    pdf.adicionar_tabela(cabecalho, dados)
    
    # Adicionar gráfico de processos
    pdf.adicionar_grafico(grafico_processos)
    
    # Histórico de uso
    pdf.subtitulo_secao("Histórico de Uso (Último Minuto)")
    pdf.adicionar_grafico(grafico_historico)
    
    # Recomendações
    pdf.add_page()
    pdf.titulo_secao("Recomendações e Conclusões")
    
    # Gerar recomendações com base nos dados
    recomendacoes = []
    
    if cpu_atual > 70:
        recomendacoes.append(
            "Investigar processos que estão consumindo muita CPU e considerar otimizá-los ou substituí-los."
        )
    
    if mem_atual > 70:
        recomendacoes.append(
            "Aumentar a quantidade de memória RAM disponível ou otimizar aplicações para usar menos memória."
        )
    
    for disco in info['discos']:
        if disco['percentual_uso'] > 80:
            recomendacoes.append(
                f"Liberar espaço no disco {disco['ponto_montagem']} que está com {disco['percentual_uso']}% de uso."
            )
    
    if not recomendacoes:
        recomendacoes.append(
            "O sistema está operando dentro dos parâmetros normais. Continue monitorando regularmente."
        )
        
    # Adicionar recomendações ao PDF
    for i, rec in enumerate(recomendacoes, 1):
        pdf.texto_normal(f"{i}. {rec}")
    
    # Conclusão
    pdf.texto_normal("\nConclusão:")
    
    if cpu_atual > 80 or mem_atual > 80 or any(d['percentual_uso'] > 90 for d in info['discos']):
        pdf.texto_destaque(
            "O sistema apresenta sinais de sobrecarga e requer atenção imediata para evitar degradação "
            "de desempenho ou possíveis falhas."
        )
    elif cpu_atual > 60 or mem_atual > 60 or any(d['percentual_uso'] > 75 for d in info['discos']):
        pdf.texto_destaque(
            "O sistema está operando com carga moderada. Recomenda-se monitoramento contínuo e "
            "implementação das recomendações para otimizar o desempenho."
        )
    else:
        pdf.texto_destaque(
            "O sistema está operando normalmente, com recursos adequados para as demandas atuais. "
            "Continue com o monitoramento regular para manter o desempenho ideal."
        )
    
    # Adicionar alerta final
    pdf.adicionar_alerta(
        "Este relatório foi gerado automaticamente e representa o estado do sistema no momento da "
        "execução. Para uma análise mais completa, considere monitorar o sistema por um período mais longo.",
        "info"
    )
    
    # Salvar o PDF na pasta de Downloads
    pdf.output(str(caminho_completo))
    print(f"Relatório gerado com sucesso: {caminho_completo}")
    
    return str(caminho_completo)

# Executar a função para criar o relatório
if __name__ == "__main__":
    criar_relatorio_sistema()

    # try:
    #     caminho_relatorio = criar_relatorio_sistema()
    #     print(f"\nRelatório salvo com sucesso na pasta de Downloads: {caminho_relatorio}")
    #     print("\nVocê pode abrir este arquivo para visualizar o relatório completo.")
    # except Exception as e:
    #     print(f"Erro ao gerar o relatório: {e}")