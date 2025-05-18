import subprocess
import questionary
import os
from rich.console import Console

console = Console()

def nextjs():
    nome = input("Digite o nome do projeto: ")
    documentos = os.path.join(os.path.expanduser("~"), "Documents")
    caminho_projeto = os.path.join(documentos, nome)

    if not os.path.exists(documentos):
        print("Pasta 'Documentos' não encontrada.")
        return

    # Criar o projeto Next.js com as opções desejadas
    comando = (
        f"npx create-next-app@latest {nome} "
        "--typescript "
        "--no-eslint "
        "--no-tailwind "
        "--src-dir "
        "--app "
        "--no-turbo"
        '--import-alias "@/*"'
    )

    subprocess.run(comando, cwd=documentos, shell=True)

    if os.path.exists(caminho_projeto):
        subprocess.run(
            ["npm", "install", "tailwindcss", "@tailwindcss/postcss", "postcss"],
            cwd=caminho_projeto,
            shell=True
        )

        print(f"\n✅ Projeto '{nome}' criado com sucesso em {caminho_projeto}")
        console.print("[red]Create a 'postcss.config.mjs' file in the root of your project and paste de following code[/]:")
        console.print("const [purple]config[/] = {\n",
              "   plugins: {\n",
              '     [cyan]"@tailwindcss/postcss:"[/] {},\n',
              '   },\n',
              '};\n',
              'export default [purple]config[/];\n')
        console.print("And import Tailwind CSS in the [purple]app/globals.css[/] file:")
        console.print('@import [cyan]"tailwindcss"[/];')

    else:
        print("❌ Erro: o projeto não foi criado corretamente.")

def nextjs_tailwind():
    print("Criando projeto Next.js com Tailwind CSS...")

def vite_react():
    print("Criando projeto Vite com React...")

def vite_react_tailwind():
    print("Criando projeto Vite com React e Tailwind CSS...")

def main():
    choice = questionary.select(
        "Selecione o tipo de projeto:",
        choices = [
            "Next.js + Tailwind CSS",
            "Vite + React",
            "Vite + React + Tailwind CSS",
        ]
    ).ask()

    match choice:
        case "Next.js + Tailwind CSS":
            nextjs_tailwind()
        case "Vite + React":
            vite_react()
        case "Vite + React + Tailwind CSS":
            vite_react_tailwind()

if __name__ == "__main__":
    main()
