import sys
import os
import platform
import subprocess
import autopep8
import jedi
#from flake8.api import legacy as flake8
from multiprocessing import freeze_support  
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QFileDialog,
    QVBoxLayout,
    QWidget,
    QAction,
    QMessageBox,
    QMenu, 
    QDialog, 
    QCheckBox,
    QProgressDialog, 
    QPlainTextEdit, 
    QTabWidget, 
    QPushButton, 
    QListWidget, 
    QLineEdit, 
    QTextEdit, 
    QLabel, 
    QCompleter, 
    QListView, 
    QTreeView, 
    QFileSystemModel,
    QVBoxLayout, 
    QSplitter, 
    QShortcut
)

from PyQt5.QtGui import QFont, QColor, QTextCharFormat, QSyntaxHighlighter, QFontMetrics, QPalette, QKeySequence, QTextCursor
from PyQt5.QtCore import QRegularExpression, QStringListModel, pyqtSignal, Qt, QDir, QSharedMemory

shared_memory = QSharedMemory("AutoPyxApp")

if not shared_memory.create(1):
    print("A aplicação já está em execução.")
    sys.exit(0)

  # Determina o caminho base (útil para PyInstaller)
def resource_path(relative_path):
    """Obtem o caminho absoluto para o recurso, funcionando com PyInstaller."""
    try:
    # Caminho para _MEIPASS usado pelo PyInstaller
    # Necessário para acessar recursos embutidos no executável PyInstaller
        base_path = sys._MEIPASS
    except AttributeError:
        # Caminho local para execução normal
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class RealceSintaxePython(QSyntaxHighlighter):
    def __init__(self, documento):
        super().__init__(documento)
        self.formato_palavra_chave_especial = self.criar_formato("#569CD6", bold=True)
        self.formato_palavra_chave_especial2 = self.criar_formato("#00A86B", bold=True)
        self.formato_palavra_chave_boleano = self.criar_formato("#6A63D6", bold=False)
        self.formato_palavra_chave_rosa = self.criar_formato("#FF66B2", bold=True)
        self.formato_palavra_chave = self.criar_formato("#569CD6")
        self.formato_operador_logico = self.criar_formato("#4078F2")
        self.formato_funcao_builtin = self.criar_formato("#D19A66")
        self.formato_classe = self.criar_formato("#4EC9B0", bold=True)
        self.formato_string = self.criar_formato("#CE9178")
        self.formato_comentario = self.criar_formato("#6A9955", italic=True)
        self.formato_numero = self.criar_formato("#B5CEA8")
        self.formato_conteudo_parenteses_chaves = self.criar_formato("#D19A66")  # Amarelo para conteúdo dentro de parênteses ou chaves
        self.formato_operador_rosa = self.criar_formato("#FF1493")  # Rosa forte para operadores
        self.formato_estrutura = self.criar_formato("#FFEB3B")  # Amarelo para estruturas
        # Padrões de regex para realce de sintaxe
        self.comentario_linha = QRegularExpression(r'#.*')
        self.padrao_string = QRegularExpression(r'".*?"|\'.*?\'')
        self.padrao_funcao_builtin = QRegularExpression(r'\b(print|len|str|int|float|list|dict|set|tuple|range)\b')
        self.regras = [
            (QRegularExpression(r'\bclass\s+([A-Za-z_][A-Za-z0-9_]*)'), self.formato_classe),
            (self.padrao_funcao_builtin, self.formato_funcao_builtin),
            (self.comentario_linha, self.formato_comentario),
            (self.padrao_string, self.formato_string),
            (QRegularExpression(r'\bimport\b|\bfrom\b|\bdef\b|\bclass\b'), self.formato_palavra_chave_especial),
            (QRegularExpression(r'\bmain\b|\b__name__\b'), self.formato_palavra_chave_especial2),
            (QRegularExpression(r'\bTrue\b|\bFalse\b'), self.formato_palavra_chave_boleano),
            (QRegularExpression(r'\b(if|elif|else|try|except)\b'), self.formato_palavra_chave_rosa),
            (QRegularExpression(r'\b(finally|for|while|as|return|with|yield|assert|break|continue|del|global|lambda|pass|raise|nonlocal|self)\b'), self.formato_palavra_chave),
            (QRegularExpression(r'\b(and|or|not|is|in)\b'), self.formato_operador_logico),
            (QRegularExpression(r'(\=|\=\=|\<|\>|\!=|\+|\-|\%|\*|\*\*|\&)'), self.formato_operador_rosa),
            # Realce para conteúdo dentro de parênteses ou chaves
            #(QRegularExpression(r'[\(\{].*?[\)\}]'), self.formato_conteudo_parenteses_chaves),  # Adicionada vírgula antes desta linha
            (QRegularExpression(r'[\(\{\[]'), self.formato_estrutura),  # Realce para abertura de parênteses, chaves e colchetes
            (QRegularExpression(r'[\)\}\]]'), self.formato_estrutura),  # Realce para fechamento de parênteses, chaves e colchetes
        ]


    def criar_formato(self, cor, bold=False, italic=False):
        formato = QTextCharFormat()
        formato.setForeground(QColor(cor))
        if bold:
            formato.setFontWeight(QFont.Bold)
        if italic:
            formato.setFontItalic(True)
        return formato

    def highlightBlock(self, texto):
        for padrao, formato in self.regras:
            iterador = padrao.globalMatch(texto)
            while iterador.hasNext():
                match = iterador.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), formato)

class AssistenteProjeto(QDialog):
    projeto_criado = pyqtSignal(str)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Assistente de Criação de Projeto")
        self.setGeometry(100, 100, 400, 300)

        self.aplicar_tema_escuro()  # Aplique o tema escuro aqui

        # Layout principal
        layout = QVBoxLayout()

        # Campo para o nome do projeto
        self.label_nome = QLabel("Nome do Projeto:")
        self.input_nome = QLineEdit()
        layout.addWidget(self.label_nome)
        layout.addWidget(self.input_nome)

        # Campo para o local do projeto
        self.label_localizacao = QLabel("Localização do Projeto:")
        self.input_localizacao = QLineEdit()
        self.botao_localizacao = QPushButton("Escolher Localização")
        self.botao_localizacao.clicked.connect(self.escolher_localizacao)
        layout.addWidget(self.label_localizacao)
        layout.addWidget(self.input_localizacao)
        layout.addWidget(self.botao_localizacao)

        # Checkbox para ambiente virtual
        self.checkbox_virtualenv = QCheckBox("Criar Ambiente Virtual (venv)")
        layout.addWidget(self.checkbox_virtualenv)

        # Botão para criar o projeto
        self.botao_criar = QPushButton("Criar Projeto")
        self.botao_criar.clicked.connect(self.criar_projeto)
        layout.addWidget(self.botao_criar)

        self.setLayout(layout)

    def aplicar_tema_escuro(self):
        dark_stylesheet = """
        QDialog {
            background-color: #2B2B2B;
            color: #FFFFFF;
        }
        QLabel {
            color: #FFFFFF;
        }
        QLineEdit {
            background-color: #3C3F41;
            color: #FFFFFF;
            border: 1px solid #555555;
            border-radius: 4px;
            padding: 4px;
        }
        QPushButton {
            background-color: #555555;
            color: #FFFFFF;
            border: none;
            padding: 6px 12px;
            border-radius: 4px;
        }
        QPushButton:hover {
            background-color: #6A6A6A;
        }
        QCheckBox {
            color: #FFFFFF;
        }
        """
        self.setStyleSheet(dark_stylesheet)

    def escolher_localizacao(self):
        """Abre um diálogo para escolher a pasta onde o projeto será criado."""
        localizacao = QFileDialog.getExistingDirectory(self, "Escolher Localização")
        if localizacao:
            self.input_localizacao.setText(localizacao)

    def criar_projeto(self):
        """Cria o projeto e emite o caminho."""
        nome_projeto = self.input_nome.text().strip()
        localizacao = self.input_localizacao.text().strip()
        criar_venv = self.checkbox_virtualenv.isChecked()

        if not nome_projeto or not localizacao:
            QMessageBox.warning(self, "Erro", "Por favor, preencha todos os campos.")
            return

        # Caminho do projeto
        caminho_projeto = os.path.join(localizacao, nome_projeto)

        try:
            # Criar diretórios do projeto
            os.makedirs(caminho_projeto)
            os.makedirs(os.path.join(caminho_projeto, "src"))
            os.makedirs(os.path.join(caminho_projeto, "tests"))

            # Criar arquivos básicos
            with open(os.path.join(caminho_projeto, "README.md"), "w") as readme:
                readme.write(f"# {nome_projeto}\n\nDescrição do projeto.")
            with open(os.path.join(caminho_projeto, "src", "main.py"), "w") as main:
                main.write("if __name__ == '__main__':\n    print('Hello, World!')\n")

            # Criar ambiente virtual
            if criar_venv:
                self.mostrar_loading("Criando ambiente virtual...")
                venv_path = os.path.join(caminho_projeto, "venv")
                subprocess.run([sys.executable, "-m", "venv", venv_path], check=True)

            QMessageBox.information(self, "Sucesso", "Projeto criado com sucesso!")
            self.projeto_criado.emit(caminho_projeto)  # Emite o caminho do projeto criado
            self.close()

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao criar o projeto: {e}")

    def mostrar_loading(self, mensagem):
        """Exibe um diálogo de carregamento enquanto o ambiente virtual é criado."""
        progress_dialog = QProgressDialog(mensagem, None, 0, 0, self)
        progress_dialog.setWindowTitle("Carregando")
        progress_dialog.setWindowModality(Qt.ApplicationModal)
        progress_dialog.setCancelButton(None)
        progress_dialog.show()

        # Simular um carregamento (necessário para que a janela seja exibida)
        QApplication.processEvents()


class AbaArquivos(QWidget):
    def __init__(self, abas):
        super().__init__()
        self.abas = abas
        self.modelo_arquivos = QFileSystemModel()
        self.modelo_arquivos.setRootPath(QDir.rootPath())  # Define o diretório raiz inicial
        self.arvore_arquivos = QTreeView()
        self.arvore_arquivos.setModel(self.modelo_arquivos)
        self.arvore_arquivos.setRootIndex(self.modelo_arquivos.index(QDir.rootPath()))
        self.arvore_arquivos.setColumnWidth(0, 250)
        self.arvore_arquivos.setSortingEnabled(True)
        self.arvore_arquivos.doubleClicked.connect(self.abrir_arquivo)

        # Adiciona evento de menu de contexto
        self.arvore_arquivos.setContextMenuPolicy(Qt.CustomContextMenu)
        self.arvore_arquivos.customContextMenuRequested.connect(self.exibir_menu_contexto)

        # Estilo para o cabeçalho do QTreeView
        self.arvore_arquivos.header().setStyleSheet("""
            QHeaderView::section {
                background-color: #333333;
                color: #D4D4D4;
                padding: 4px;
                border: none;
            }
        """)

        layout = QVBoxLayout()
        layout.addWidget(self.arvore_arquivos)
        self.setLayout(layout)

    def definir_pasta_raiz(self, caminho):
        """Define a pasta raiz do navegador de arquivos e atualiza o modelo."""
        if os.path.exists(caminho) and os.path.isdir(caminho):
            self.modelo_arquivos.setRootPath(caminho)  # Atualiza o modelo com o novo caminho
            self.arvore_arquivos.setRootIndex(self.modelo_arquivos.index(caminho))
        else:
            QMessageBox.warning(self, "Erro", "Caminho inválido ou inexistente.")

    def exibir_menu_contexto(self, posicao):
        """Exibe o menu de contexto ao clicar com o botão direito no navegador de arquivos."""
        index = self.arvore_arquivos.indexAt(posicao)
        if index.isValid():
            menu = QMenu()
            caminho = self.modelo_arquivos.filePath(index)

            # Adicionar opções ao menu
            abrir_arquivo = QAction("Abrir", self)
            abrir_arquivo.triggered.connect(lambda: self.abrir_arquivo(index))
            menu.addAction(abrir_arquivo)

            copiar_caminho = QAction("Copiar Caminho Absoluto", self)
            copiar_caminho.triggered.connect(lambda: self.copiar_caminho(caminho))
            menu.addAction(copiar_caminho)

            menu.exec_(self.arvore_arquivos.viewport().mapToGlobal(posicao))

    def abrir_arquivo(self, index):
        """Abre o arquivo selecionado no editor."""
        caminho = self.modelo_arquivos.filePath(index)

        # Verifica se é um arquivo antes de abrir
        if not os.path.isdir(caminho):
            try:
                with open(caminho, "r", encoding="utf-8") as arquivo:
                    conteudo = arquivo.read()
                    editor = EditorCodigo()
                    editor.setPlainText(conteudo)
                    self.abas.addTab(editor, os.path.basename(caminho))
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao abrir o arquivo:\n{e}")

    def copiar_caminho(self, caminho):
        """Copia o caminho absoluto para a área de transferência."""
        clipboard = QApplication.clipboard()
        clipboard.setText(caminho)



class EditorCodigo(QPlainTextEdit):
    def __init__(self):
        super().__init__()
        self.setFont(QFont("Consolas", 12))
        self.setTabStopDistance(QFontMetrics(self.font()).horizontalAdvance(' ') * 4)
        self.realce = RealceSintaxePython(self.document())
        self.definir_tema('escuro')
        
        # Variável para controlar a ativação do Jedi, desativada por padrão
        self.jedi_ativo = False

        self.completador = QCompleter(self)
        self.completador.setModel(QStringListModel())
        self.completador.setWidget(self)
        self.completador.setCompletionMode(QCompleter.PopupCompletion)
        self.completador.activated.connect(self.inserir_completacao)

        self.cursorPositionChanged.connect(self.atualizar_completacoes)

         # Inicializar campo de pesquisa
        self.campo_pesquisa = QLineEdit(self)
        self.campo_pesquisa.setPlaceholderText("Digite para pesquisar...")
        self.campo_pesquisa.setFixedWidth(200)
        self.campo_pesquisa.setVisible(False)
        self.campo_pesquisa.returnPressed.connect(self.pesquisar_texto)

        # Atalho Ctrl + F para exibir a barra de pesquisa
        self.atalho_pesquisa = QShortcut(QKeySequence("Ctrl+F"), self)
        self.atalho_pesquisa.activated.connect(self.exibir_campo_pesquisa)

        # Atalho Esc para ocultar a barra de pesquisa
        self.atalho_ocultar_pesquisa = QShortcut(QKeySequence("Esc"), self)
        self.atalho_ocultar_pesquisa.activated.connect(self.ocultar_campo_pesquisa)

    def exibir_campo_pesquisa(self):
        """Exibe o campo de pesquisa e foca nele."""
        self.campo_pesquisa.setVisible(True)
        self.campo_pesquisa.setFocus()

    def ocultar_campo_pesquisa(self):
        """Oculta o campo de pesquisa e limpa o texto de pesquisa."""
        self.campo_pesquisa.clear()
        self.campo_pesquisa.setVisible(False)
        self.moveCursor(QTextCursor.Start)  # Move o cursor para o início após ocultar a pesquisa

    def pesquisar_texto(self):
        """Pesquisa o texto inserido no campo de pesquisa e destaca as ocorrências."""
        termo_pesquisa = self.campo_pesquisa.text()
        self.moveCursor(QTextCursor.Start)  # Inicia a pesquisa do começo
        formato = QTextCharFormat()
        formato.setBackground(QColor("yellow"))  # Cor de destaque

        # Limpa o destaque anterior
        self.setExtraSelections([])

        if termo_pesquisa:
            selecoes = []
            while self.find(termo_pesquisa):
                selecao = QTextEdit.ExtraSelection()
                selecao.cursor = self.textCursor()
                selecao.format = formato
                selecoes.append(selecao)
            self.setExtraSelections(selecoes)

    def keyPressEvent(self, evento):
        if evento.key() == Qt.Key_Tab:
            self.insertPlainText(" " * 4)  # Insere 4 espaços ao pressionar Tab
        else:
            super().keyPressEvent(evento)
            
    def converter_tabs_para_espacos(self):
        texto = self.toPlainText()
        texto_convertido = texto.replace('\t', ' ' * 4)  # Substitui tabs por 4 espaços
        self.setPlainText(texto_convertido)


    def definir_tema(self, tema):
        if tema == 'escuro':
            self.setStyleSheet("""
                background-color: #1E1E1E; color: #D4D4D4;
                selection-background-color: #264F78;
            """)
        elif tema == 'claro':
            self.setStyleSheet("""
                background-color: #FFFFFF; color: #000000;
                selection-background-color: #ADD6FF;
            """)
        elif tema == "Cinza":
            self.setStyleSheet("""
                background-color: #262730; color: #D4D4D4;
                selection-background-color: #264F78;
            """)
        elif tema == "Azul":
            self.setStyleSheet("""
                background-color: #122852; color: #D4D4D4;
                selection-background-color: #264F78;
            """)
        elif tema == "Roxo":
            self.setStyleSheet("""
                background-color: #1f2031; color: #D4D4D4;
                selection-background-color: #264F78;
            """)
        elif tema == "Verde":
            self.setStyleSheet("""
                background-color: #183e47; color: #D4D4D4;
                selection-background-color: #264F78;
            """)
   

    def estilizar_completador(self):
        lista_completador = QListView()
        self.completador.setPopup(lista_completador)
        
        paleta = QPalette()
        paleta.setColor(QPalette.Base, QColor("#1E1E1E"))
        paleta.setColor(QPalette.Text, QColor("#D4D4D4"))
        paleta.setColor(QPalette.Highlight, QColor("#264F78"))
        paleta.setColor(QPalette.HighlightedText, QColor("#FFFFFF"))
        lista_completador.setPalette(paleta)

        lista_completador.setStyleSheet("""
            QListView {
                background-color: #1E1E1E;
                color: #D4D4D4;
                selection-background-color: #264F78;
                selection-color: #FFFFFF;
                font-size: 12pt;
            }
        """)

    def inserir_completacao(self, completacao):
        cursor = self.textCursor()
        cursor.movePosition(cursor.Left, cursor.KeepAnchor, len(self.completador.completionPrefix()))
        cursor.insertText(completacao)
    
        # Move o cursor para o final da linha após inserir a sugestão
        cursor.movePosition(cursor.EndOfLine)
        self.setTextCursor(cursor)
    
    def atualizar_completacoes(self):
        if not self.jedi_ativo:
            # Se Jedi estiver desativado, não fazer autocompletar
            self.completador.popup().hide()
            return

        cursor = self.textCursor()
        cursor.select(cursor.WordUnderCursor)
        prefixo = cursor.selectedText()
        
        if len(prefixo) < 2:
            self.completador.popup().hide()
            return

        try:
            linha = cursor.blockNumber() + 1
            coluna = cursor.columnNumber()
            script = jedi.Script(self.toPlainText())
            completacoes = script.complete(linha, coluna)

            sugestoes = [completacao.name for completacao in completacoes]
            self.completador.model().setStringList(sugestoes)
            self.completador.setCompletionPrefix(prefixo)
            self.completador.complete()
        
        except Exception as e:
            print(f"Erro ao obter sugestões de autocompletar: {e}")

    


class GerenciadorBibliotecas(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()

        # Título
        self.rotulo = QLabel("AutoPyx")
        self.layout.addWidget(self.rotulo)

        # Área para exibir as bibliotecas instaladas
        self.lista_bibliotecas = QListWidget()
        self.lista_bibliotecas.setStyleSheet("""
            background-color: #1E1E1E;  /* Cor de fundo da área de listagem */
            color: #D4D4D4;
            font-size: 12pt;
            border: none;
        """)
        self.layout.addWidget(self.lista_bibliotecas)

        # Campo de entrada para comandos pip
        self.campo_input = QLineEdit()
        self.campo_input.setPlaceholderText("Digite o comando (install/remove/update nome_da_biblioteca)...")
        self.layout.addWidget(self.campo_input)

        # Botão de processamento
        self.botao_processar = QPushButton("Processar Comando")
        self.botao_processar.clicked.connect(self.processar_comando)
        self.layout.addWidget(self.botao_processar)

        self.setLayout(self.layout)
        
        # Carregar a lista inicial de bibliotecas instaladas
        self.listar_bibliotecas_instaladas()

    def listar_bibliotecas_instaladas(self):
        """Lista todas as bibliotecas instaladas usando pip."""
        self.lista_bibliotecas.clear()
        python_executable = sys.executable  # PyInstaller define sys.executable corretamente
        resultado = subprocess.run(
            [python_executable, '-m', 'pip', 'list'], 
            check=True, capture_output=True, text=True)
        bibliotecas = resultado.stdout.splitlines()[2:]  # Ignora as duas primeiras linhas de cabeçalho
    
        self.bibliotecas_instaladas = bibliotecas  # Armazena a lista completa para o filtro
        self.lista_bibliotecas.addItems(bibliotecas)

    def filtrar_bibliotecas(self):
        """Filtra as bibliotecas instaladas com base no texto de pesquisa."""
        termo_pesquisa = self.campo_pesquisa.text().lower()
        self.lista_bibliotecas.clear()
        for biblioteca in self.bibliotecas_instaladas:
            if termo_pesquisa in biblioteca.lower():
                self.lista_bibliotecas.addItem(biblioteca)

    def processar_comando(self):
        """Processa o comando pip inserido no campo de entrada."""
        comando_texto = self.campo_input.text().strip()
        if comando_texto:
            partes_comando = comando_texto.split()
            if len(partes_comando) >= 2:
                acao = partes_comando[0].lower()
                nome_biblioteca = partes_comando[1]

                if acao == 'install':
                    self.executar_comando_pip(['install', nome_biblioteca])
                elif acao == 'remove':
                    self.executar_comando_pip(['uninstall', '-y', nome_biblioteca])
                elif acao == 'update':
                    self.executar_comando_pip(['install', '--upgrade', nome_biblioteca])
                else:
                    QMessageBox.warning(self, "Comando Inválido", "Use 'install', 'remove' ou 'update' seguido do nome da biblioteca.")
                self.campo_input.clear()

    def executar_comando_pip(self, comando_args):
        """Executa um comando pip em um terminal separado."""
        if sys.platform == "win32":
            # Comando para abrir em terminal separado no Windows
            comando = ["start", "cmd", "/k", "python", "-m", "pip"] + comando_args
            subprocess.run(comando, shell=True)
        elif sys.platform == "linux":
            # Comando para abrir em terminal separado no Linux (gnome-terminal)
            comando = ["gnome-terminal", "--", "python3", "-m", "pip"] + comando_args
            subprocess.run(comando)
        elif sys.platform == "darwin":
            # Comando para abrir em terminal separado no macOS
            comando = ["open", "-a", "Terminal.app", "python3", "-m", "pip"] + comando_args
            subprocess.run(comando)
        else:
            QMessageBox.critical(self, "Erro", "Sistema operacional não suportado para abertura de terminal.")


class IDE(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("IDE Python AutoPyx")
        self.setGeometry(50, 50, 1200, 800)

        # Criação do QSplitter para dividir navegação e editor
        splitter = QSplitter(Qt.Horizontal)

        # Criação da aba de navegação de arquivos
        self.abas = QTabWidget()
        self.aba_arquivos = AbaArquivos(self.abas)
        splitter.addWidget(self.aba_arquivos)  # Aba de arquivos à esquerda

        # Adiciona o QTabWidget ao splitter
        splitter.addWidget(self.abas)  # Abas de editor e gerenciador de bibliotecas
        splitter.setStretchFactor(1, 3)  # Dá mais espaço ao editor

        # Criação do botão "Executar Código"
        self.botao_executar = QPushButton("Executar Código")
        self.botao_executar.clicked.connect(self.executar_codigo)

        # Layout principal
        layout_principal = QVBoxLayout()
        layout_principal.addWidget(self.botao_executar)  # Adiciona o botão de execução
        layout_principal.addWidget(splitter)

        # Container principal
        container = QWidget()
        container.setLayout(layout_principal)
        self.setCentralWidget(container)

        # Menu e botões
        self.criar_menu()
        self.definir_tema('escuro')  # Aplica o tema escuro como padrão

        # Aba de gerenciamento de bibliotecas
        self.gerenciador_bibliotecas = GerenciadorBibliotecas()
        self.abas.addTab(self.gerenciador_bibliotecas, "Gerenciador de Bibliotecas")

        # Aba do editor de código
        self.editor = EditorCodigo()
        self.abas.addTab(self.editor, "Editor de Código")
    

    def abrir_assistente_projeto(self):
        assistente = AssistenteProjeto(self)
        assistente.projeto_criado.connect(self.carregar_novo_projeto)  # Conecta o sinal
        assistente.exec_()

    def carregar_novo_projeto(self, caminho_projeto):
        """Define o novo projeto como a pasta raiz no gerenciador de arquivos."""
        self.aba_arquivos.definir_pasta_raiz(caminho_projeto)
        QMessageBox.information(self, "Novo Projeto", f"O projeto foi carregado no gerenciador de arquivos:\n{caminho_projeto}")
    
    def executar_codigo(self):
        editor_atual = self.abas.currentWidget()
        if isinstance(editor_atual, EditorCodigo):
            codigo = editor_atual.toPlainText()
            with open("temp_script.py", "w", encoding='utf-8') as arquivo_temp:
                arquivo_temp.write(codigo)
            try:
                if platform.system() == "Windows":
                    subprocess.run(["start", "cmd", "/k", f"python temp_script.py"], shell=True)
                elif platform.system() == "Linux":
                    subprocess.run(["gnome-terminal", "--", "python3", "temp_script.py"])
                elif platform.system() == "Darwin":
                    subprocess.run(["open", "-a", "Terminal.app", "python3", "temp_script.py"])
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao executar o código:\n{e}")

    def criar_menu(self):
        barra_menu = self.menuBar()
        menu_arquivo = barra_menu.addMenu("Arquivo")
        menu_visualizar = barra_menu.addMenu("Visualizar")
        menu_linting = barra_menu.addMenu("Ferramentas")

        acao_novo = QAction("Novo", self)
        acao_novo.triggered.connect(self.novo_arquivo)
        menu_arquivo.addAction(acao_novo)

        #Ação para abrir um novo projeto 
        acao_assistente_projeto = QAction("Novo Projeto", self)
        acao_assistente_projeto.triggered.connect(self.abrir_assistente_projeto)
        menu_arquivo.addAction(acao_assistente_projeto)

        acao_abrir = QAction("Abrir", self)
        acao_abrir.triggered.connect(self.abrir_arquivo)
        menu_arquivo.addAction(acao_abrir)

        acao_abrir = QAction("Abrir Pasta", self)
        acao_abrir.triggered.connect(self.abrir_pasta)
        menu_arquivo.addAction(acao_abrir)

        acao_salvar = QAction("Salvar", self)
        acao_salvar.triggered.connect(self.salvar_arquivo)
        menu_arquivo.addAction(acao_salvar)

        # Ação para fechar a aba atual
        acao_fechar_aba = QAction("Fechar Aba Atual", self)
        acao_fechar_aba.triggered.connect(self.fechar_aba_atual)
        menu_arquivo.addAction(acao_fechar_aba)
        
        # Ação definir temas na IDE
        acao_tema_escuro = QAction("Tema Escuro", self)
        acao_tema_escuro.triggered.connect(lambda: self.definir_tema('escuro'))
        menu_visualizar.addAction(acao_tema_escuro)

        acao_tema_claro = QAction("Tema Claro", self)
        acao_tema_claro.triggered.connect(lambda: self.definir_tema('claro'))
        menu_visualizar.addAction(acao_tema_claro)

        acao_tema_roxo = QAction("Tema Cinza", self)
        acao_tema_roxo.triggered.connect(lambda: self.definir_tema('Cinza'))
        menu_visualizar.addAction(acao_tema_roxo)

        acao_tema_azul = QAction("Tema Azul", self)
        acao_tema_azul.triggered.connect(lambda: self.definir_tema('Azul'))
        menu_visualizar.addAction(acao_tema_azul)

        acao_tema_roxo = QAction("Tema Roxo", self)
        acao_tema_roxo.triggered.connect(lambda: self.definir_tema('Roxo'))
        menu_visualizar.addAction(acao_tema_roxo)

        acao_tema_verde = QAction("Tema Verde", self)
        acao_tema_verde.triggered.connect(lambda: self.definir_tema('Verde'))
        menu_visualizar.addAction(acao_tema_verde)


        # Ação para chamar o Flake8
        acao_linting_flake8 = QAction("Verificar código com Flake8", self)
        acao_linting_flake8.triggered.connect(self.verificar_codigo_com_flake8)
        menu_linting.addAction(acao_linting_flake8)

        # Ação para chamar o Black
        acao_formatar_autopep8 = QAction("Formatar código com autopep8", self)
        acao_formatar_autopep8.triggered.connect(self.formatar_codigo_com_autopep8)
        menu_linting.addAction(acao_formatar_autopep8)
        
        # Ação para chamar o Pylint
        acao_linting_pylint = QAction("Verificar código com Pylint", self)
        acao_linting_pylint.triggered.connect(self.verificar_codigo_com_pylint)
        menu_linting.addAction(acao_linting_pylint)

        # Ação para chamar o Mypy
        acao_linting_mypy = QAction("Verificar código com Mypy", self)
        acao_linting_mypy.triggered.connect(self.verificar_codigo_com_mypy)
        menu_linting.addAction(acao_linting_mypy)


        # Ação para ativar o Auto Complite com Jedi, desativado por padrão
        opcao_jedi = QAction("Ativar Jedi Autocomplete", self, checkable=True)
        opcao_jedi.setChecked(False)  # Jedi começa desativado
        opcao_jedi.triggered.connect(self.toggle_jedi)
        menu_linting.addAction(opcao_jedi)


    def toggle_jedi(self, state):
        # Alterna a ativação/desativação do Jedi
        self.editor.jedi_ativo = state

    def aplicar_estilos(self):
        self.abas.setStyleSheet("""
            QTabWidget { background-color: #1E1E1E; color: #D4D4D4; }
            QTabBar::tab { background-color: #333333; color: #D4D4D4; padding: 10px; }
            QTabBar::tab:selected { background-color: #264F78; }
            QTabBar::tab:hover { background-color: #505050; }
        """)

    def novo_arquivo(self):
        novo_editor = EditorCodigo()
        self.abas.addTab(novo_editor, "Sem título")
        self.abas.setCurrentWidget(novo_editor)

    def abrir_arquivo(self):
        nome_arquivo, _ = QFileDialog.getOpenFileName(self, "Abrir Arquivo", "", "Arquivos Python (*.py);;Todos os Arquivos (*)")
        if nome_arquivo:
            novo_editor = EditorCodigo()
            with open(nome_arquivo, 'r', encoding='utf-8') as arquivo:
                novo_editor.setPlainText(arquivo.read())
            self.abas.addTab(novo_editor, nome_arquivo.split('/')[-1])
            self.abas.setCurrentWidget(novo_editor)
    
    def abrir_pasta(self):
        """Abre um diálogo para selecionar uma pasta e define como a pasta raiz no navegador de arquivos."""
        caminho_pasta = QFileDialog.getExistingDirectory(self, "Selecionar Pasta", QDir.rootPath())
        if caminho_pasta:
            self.aba_arquivos.definir_pasta_raiz(caminho_pasta)

    def salvar_arquivo(self):
        editor_atual = self.abas.currentWidget()
        if isinstance(editor_atual, EditorCodigo):
            nome_arquivo, _ = QFileDialog.getSaveFileName(self, "Salvar Arquivo", "", "Arquivos Python (*.py);;Todos os Arquivos (*)")
            if nome_arquivo:
                with open(nome_arquivo, 'w', encoding='utf-8') as arquivo:
                    arquivo.write(editor_atual.toPlainText())
                self.abas.setTabText(self.abas.currentIndex(), nome_arquivo.split('/')[-1])

    def fechar_aba_atual(self):
        """Fecha a aba atualmente selecionada."""
        indice_aba_atual = self.abas.currentIndex()
        if indice_aba_atual != -1:
            self.abas.removeTab(indice_aba_atual)

    def toggle_jedi(self, state):
        # Alterna a ativação/desativação do Jedi no editor atual
        editor_atual = self.abas.currentWidget()
        if isinstance(editor_atual, EditorCodigo):
            editor_atual.jedi_ativo = state

    def definir_tema(self, tema):
        for i in range(self.abas.count()):
            editor = self.abas.widget(i)
            if isinstance(editor, EditorCodigo):
                editor.definir_tema(tema)

    def executar_codigo(self):
        editor_atual = self.abas.currentWidget()
        if isinstance(editor_atual, EditorCodigo):
            editor_atual.atualizar_completacoes()
            codigo = editor_atual.toPlainText()
        with open("temp_script.py", "w", encoding='utf-8') as arquivo_temp:
            arquivo_temp.write(codigo)
        try:
            if platform.system() == "Windows":
                subprocess.run(["start", "cmd", "/k", f"python temp_script.py"], shell=True)
        except Exception as e:
            QMessageBox.critical(self, "Erro", str(e))

    def formatar_codigo_com_autopep8(self):
        editor_atual = self.abas.currentWidget()
        if isinstance(editor_atual, EditorCodigo):
            codigo = editor_atual.toPlainText()
        try:
            codigo_formatado = autopep8.fix_code(codigo)
            editor_atual.setPlainText(codigo_formatado)
            QMessageBox.information(self, "Formatador", "Código formatado com sucesso pelo Autopep8.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao formatar código com Autopep8:\n{e}")

    def verificar_codigo_com_flake8(self):
        editor_atual = self.abas.currentWidget()
        if editor_atual:
            codigo = editor_atual.toPlainText()
        with open("temp_script.py", "w", encoding='utf-8') as arquivo_temp:
            arquivo_temp.write(codigo)

        try:
            if platform.system() == "Windows":
                # Executa o Flake8 em um novo terminal no Windows usando `python -m flake8`
                subprocess.run(["start", "cmd", "/k", f"python -m flake8 temp_script.py"], shell=True)
            elif platform.system() == "Linux":
                subprocess.run(["gnome-terminal", "--", "python3", "-m", "flake8", "temp_script.py"])
            elif platform.system() == "Darwin":
                subprocess.run(["open", "-a", "Terminal.app", "python3", "-m", "flake8", "temp_script.py"])
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao executar Flake8 em um terminal separado:\n{e}")

    
    def verificar_codigo_com_pylint(self):
        editor_atual = self.abas.currentWidget()
        if editor_atual:
            codigo = editor_atual.toPlainText()
            with open("temp_script.py", "w", encoding='utf-8') as arquivo_temp:
                arquivo_temp.write(codigo)
        try:
            if platform.system() == "Windows":
                subprocess.run(["start", "cmd", "/k", f"python -m pylint temp_script.py"], shell=True)
            elif platform.system() == "Linux":
                subprocess.run(["gnome-terminal", "--", "pylint", "temp_script.py"])
            elif platform.system() == "Darwin":
                subprocess.run(["open", "-a", "Terminal.app", "pylint temp_script.py"])
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao executar Pylint em um terminal separado:\n{e}")

    def verificar_codigo_com_mypy(self):
        editor_atual = self.abas.currentWidget()
        if editor_atual:
            codigo = editor_atual.toPlainText()
            with open("temp_script.py", "w", encoding='utf-8') as arquivo_temp:
                arquivo_temp.write(codigo)
        try:
            if platform.system() == "Windows":
                subprocess.run(["start", "cmd", "/k", f"python -m mypy temp_script.py"], shell=True)
            elif platform.system() == "Linux":
                subprocess.run(["gnome-terminal", "--", "mypy", "temp_script.py"])
            elif platform.system() == "Darwin":
                subprocess.run(["open", "-a", "Terminal.app", "mypy temp_script.py"])
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao executar Mypy em um terminal separado:\n{e}")


    def closeEvent(self, evento):
        resposta = QMessageBox.question(self, 'Sair', 'Tem certeza de que deseja sair?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if resposta == QMessageBox.Yes:
            evento.accept()
        else:
            evento.ignore()


if __name__ == "__main__":
    freeze_support()  # Necessário para PyInstaller no Windows
    app = QApplication(sys.argv)
    app.setStyleSheet("""
        QMainWindow { background-color: #1E1E1E; }
        QMenuBar { background-color: #333333; color: #D4D4D4; }
        QMenu { background-color: #333333; color: #D4D4D4; }
        QMenu::item:selected { background-color: #444444; }
        QPushButton { background-color: #3C3C3C; color: #D4D4D4; }
        QPushButton:hover { background-color: #505050; }
        QPlainTextEdit { background-color: #2E2E2E; color: #D4D4D4; }
        QTabWidget::pane { background: #1E1E1E; border: 1px solid #333333; }
        QTabBar::tab { background-color: #333333; color: #D4D4D4; padding: 10px; }
        QTabBar::tab:selected { background-color: #264F78; }
        QTabBar::tab:hover { background-color: #505050; }
        QTreeView { background-color: #1E1E1E; color: #D4D4D4; }
        QTreeView::item:selected { background-color: #264F78; color: #FFFFFF; }
        QSplitter::handle { background-color: #333333; }
        
        /* Estilos para as barras de rolagem */
        QScrollBar:vertical {
            border: none;
            background: #2E2E2E;
            width: 10px;
            margin: 0px 0px 0px 0px;
        }
        QScrollBar::handle:vertical {
            background: #666666;
            min-height: 20px;
            border-radius: 5px;
        }
        QScrollBar::handle:vertical:hover {
            background: #888888;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
            width: 0px;
        }

        QScrollBar:horizontal {
            border: none;
            background: #2E2E2E;
            height: 10px;
            margin: 0px 0px 0px 0px;
        }
        QScrollBar::handle:horizontal {
            background: #666666;
            min-width: 20px;
            border-radius: 5px;
        }
        QScrollBar::handle:horizontal:hover {
            background: #888888;
        }
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
            height: 0px;
            width: 0px;
        }
    """)

    ide = IDE()
    ide.show()
    sys.exit(app.exec_())