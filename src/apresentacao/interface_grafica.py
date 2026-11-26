"""Interface desktop do sistema de controle de acesso RFID."""

import queue
import threading
import time
import tkinter as tk
from tkinter import messagebox, ttk

import serial

from src.aplicacao.servicos.autenticacao import ServicoAutenticacao
from src.infraestrutura.hardware.leitor_rfid import LeitorRFID
from src.infraestrutura.persistencia.banco_dados import RepositorioRFID


AZUL = "#2563EB"
AZUL_ESCURO = "#1E40AF"
VERMELHO = "#DC2626"
VERDE = "#15803D"
FUNDO = "#F4F7FB"
BRANCO = "#FFFFFF"
TEXTO = "#172033"
CINZA = "#64748B"


class InterfaceRFID(tk.Tk):
    def __init__(self, porta="COM11", velocidade=9600):
        super().__init__()
        self.title("Controle de Acesso RFID")
        self.geometry("1080x720")
        self.minsize(900, 620)
        self.configure(bg=FUNDO)

        self.porta_var = tk.StringVar(value=porta)
        self.repositorio = RepositorioRFID()
        self.autenticador = ServicoAutenticacao(self.repositorio)
        self.velocidade = velocidade
        self._fila_leitura = queue.Queue()
        self._lendo_cartao = False
        self._callback_leitura = None
        self._selected_profile_id = None
        self._area_vars = {}
        self._profile_labels = {}
        self._card_profile_labels = {}

        self.repositorio.criar_tabelas()
        self._configurar_estilos()
        self._montar_tela()
        self._atualizar_tudo()

    def _configurar_estilos(self):
        estilo = ttk.Style(self)
        try:
            estilo.theme_use("clam")
        except tk.TclError:
            pass
        estilo.configure("TFrame", background=FUNDO)
        estilo.configure("Card.TFrame", background=BRANCO)
        estilo.configure("TLabel", background=FUNDO, foreground=TEXTO, font=("Segoe UI", 10))
        estilo.configure("Title.TLabel", background=AZUL, foreground=BRANCO, font=("Segoe UI", 20, "bold"))
        estilo.configure("Subtitle.TLabel", background=AZUL, foreground="#DBEAFE", font=("Segoe UI", 10))
        estilo.configure("Section.TLabel", background=BRANCO, foreground=TEXTO, font=("Segoe UI", 13, "bold"))
        estilo.configure("Muted.TLabel", background=BRANCO, foreground=CINZA)
        estilo.configure("TNotebook", background=FUNDO, borderwidth=0)
        estilo.configure("TNotebook.Tab", padding=(18, 10), font=("Segoe UI", 10, "bold"))
        estilo.map("TNotebook.Tab", background=[("selected", BRANCO)], foreground=[("selected", AZUL_ESCURO)])
        estilo.configure("Treeview", rowheight=30, font=("Segoe UI", 10), background=BRANCO, fieldbackground=BRANCO)
        estilo.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))
        estilo.configure("TCheckbutton", background=BRANCO, foreground=TEXTO, font=("Segoe UI", 10))
        estilo.configure("TCombobox", padding=5)

    def _botao(self, pai, texto, comando, cor=AZUL, largura=None):
        return tk.Button(
            pai,
            text=texto,
            command=comando,
            bg=cor,
            fg=BRANCO,
            disabledforeground=BRANCO,
            activebackground=AZUL_ESCURO if cor == AZUL else cor,
            activeforeground=BRANCO,
            relief="flat",
            cursor="hand2",
            font=("Segoe UI", 10, "bold"),
            padx=14,
            pady=8,
            width=largura,
        )

    def _montar_tela(self):
        tk.Frame(self, bg=VERMELHO, height=4).pack(fill="x")
        cabecalho = tk.Frame(self, bg=AZUL, padx=24, pady=18)
        cabecalho.pack(fill="x")
        ttk.Label(cabecalho, text="Controle de Acesso RFID", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            cabecalho,
            text="Cartões, perfis e permissões por área",
            style="Subtitle.TLabel",
        ).pack(anchor="w", pady=(3, 0))

        barra = tk.Frame(self, bg=FUNDO, padx=20, pady=10)
        barra.pack(fill="x")
        tk.Label(barra, text="Porta do Arduino", bg=FUNDO, fg=TEXTO, font=("Segoe UI", 10, "bold")).pack(side="left")
        tk.Entry(barra, textvariable=self.porta_var, width=12, font=("Segoe UI", 10)).pack(side="left", padx=(8, 18))
        tk.Label(barra, text="9600 baud", bg=FUNDO, fg=CINZA, font=("Segoe UI", 9)).pack(side="left")
        self.status_var = tk.StringVar(value="Pronto")
        tk.Label(barra, textvariable=self.status_var, bg=FUNDO, fg=CINZA, font=("Segoe UI", 10, "bold")).pack(side="right")

        self.abas = ttk.Notebook(self)
        self.abas.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        self.aba_acesso = ttk.Frame(self.abas, padding=20)
        self.aba_cartoes = ttk.Frame(self.abas, padding=20)
        self.aba_perfis = ttk.Frame(self.abas, padding=20)
        self.abas.add(self.aba_acesso, text="Controle de acesso")
        self.abas.add(self.aba_cartoes, text="Cartões")
        self.abas.add(self.aba_perfis, text="Perfis e áreas")
        self._montar_aba_acesso()
        self._montar_aba_cartoes()
        self._montar_aba_perfis()

    def _montar_aba_acesso(self):
        ttk.Label(self.aba_acesso, text="Verificar permissão", style="Section.TLabel").pack(anchor="w")
        ttk.Label(
            self.aba_acesso,
            text="Escolha a área e aproxime o cartão para consultar o perfil de acesso.",
        ).pack(anchor="w", pady=(4, 18))

        painel = ttk.Frame(self.aba_acesso, style="Card.TFrame", padding=22)
        painel.pack(fill="x", anchor="n")
        ttk.Label(painel, text="Área", style="Muted.TLabel").grid(row=0, column=0, sticky="w")
        self.area_acesso_var = tk.StringVar()
        self.area_acesso_combo = ttk.Combobox(painel, textvariable=self.area_acesso_var, state="readonly", width=42)
        self.area_acesso_combo.grid(row=1, column=0, sticky="w", pady=(5, 18))
        self.botao_verificar = self._botao(painel, "Ler cartão e verificar", self._verificar_acesso)
        self.botao_verificar.grid(row=1, column=1, padx=(14, 0), pady=(5, 18))

        self.resultado_acesso = tk.Label(
            self.aba_acesso,
            text="Aguardando verificação",
            bg=BRANCO,
            fg=CINZA,
            font=("Segoe UI", 18, "bold"),
            padx=24,
            pady=22,
            anchor="w",
        )
        self.resultado_acesso.pack(fill="x", pady=(18, 0))
        self.detalhe_acesso = tk.StringVar(value="O resultado da leitura aparecerá aqui.")
        tk.Label(self.aba_acesso, textvariable=self.detalhe_acesso, bg=FUNDO, fg=CINZA, font=("Segoe UI", 10)).pack(anchor="w", pady=10)

    def _montar_aba_cartoes(self):
        ttk.Label(self.aba_cartoes, text="Usuários e cartões", style="Section.TLabel").pack(anchor="w")
        ttk.Label(
            self.aba_cartoes,
            text="Selecione uma linha para editar o usuário, mudar o perfil ou excluir registros.",
        ).pack(anchor="w", pady=(4, 10))

        formulario = ttk.Frame(self.aba_cartoes, style="Card.TFrame", padding=10)
        formulario.pack(fill="x", pady=(0, 8))
        ttk.Label(formulario, text="Nome do usuário", style="Muted.TLabel").grid(row=0, column=0, sticky="w")
        self.identificacao_var = tk.StringVar()
        tk.Entry(formulario, textvariable=self.identificacao_var, width=32, font=("Segoe UI", 10)).grid(row=1, column=0, padx=(0, 10), pady=(4, 0), sticky="w")
        ttk.Label(formulario, text="UID do cartão", style="Muted.TLabel").grid(row=0, column=1, sticky="w")
        self.uid_var = tk.StringVar()
        tk.Entry(formulario, textvariable=self.uid_var, width=28, font=("Segoe UI", 10)).grid(row=1, column=1, padx=(0, 10), pady=(4, 0), sticky="w")
        self._botao(formulario, "Ler UID", self._ler_uid_para_cadastro).grid(row=1, column=2, padx=5)
        self._botao(formulario, "Cadastrar usuário", self._cadastrar_cartao).grid(row=1, column=3, padx=5)

        acoes = ttk.Frame(self.aba_cartoes, style="Card.TFrame", padding=10)
        acoes.pack(fill="x", pady=(0, 8))
        self.cartao_selecionado_var = tk.StringVar(value="Selecione uma linha na tabela para ativar as ações.")
        tk.Label(
            acoes,
            textvariable=self.cartao_selecionado_var,
            bg=BRANCO,
            fg=AZUL_ESCURO,
            font=("Segoe UI", 10, "bold"),
            anchor="w",
        ).pack(fill="x", pady=(0, 7))

        linha_usuario = ttk.Frame(acoes, style="Card.TFrame")
        linha_usuario.pack(fill="x", pady=(0, 6))
        ttk.Label(linha_usuario, text="Nome do usuário (selecione uma linha para editar):", style="Muted.TLabel").pack(side="left")
        self.nome_usuario_edicao_var = tk.StringVar()
        self.entrada_nome_usuario = tk.Entry(
            linha_usuario,
            textvariable=self.nome_usuario_edicao_var,
            width=25,
            font=("Segoe UI", 10),
        )
        self.entrada_nome_usuario.pack(side="left", padx=(8, 6))
        self.botao_salvar_nome = self._botao(linha_usuario, "Salvar nome", self._salvar_nome_usuario)
        self.botao_salvar_nome.pack(side="left", padx=4)
        self.botao_excluir_usuario = self._botao(
            linha_usuario,
            "Excluir usuário",
            self._excluir_usuario,
            cor=VERMELHO,
        )
        self.botao_excluir_usuario.pack(side="left", padx=4)
        self.botao_salvar_nome.configure(state="disabled")
        self.botao_excluir_usuario.configure(state="disabled")

        linha_cartao = ttk.Frame(acoes, style="Card.TFrame")
        linha_cartao.pack(fill="x")
        ttk.Label(linha_cartao, text="Perfil deste cartão:", style="Muted.TLabel").pack(side="left")
        self.perfil_cartao_var = tk.StringVar()
        self.perfil_cartao_combo = ttk.Combobox(
            linha_cartao,
            textvariable=self.perfil_cartao_var,
            state="readonly",
            width=23,
        )
        self.perfil_cartao_combo.pack(side="left", padx=(8, 6))
        self.botao_alterar_perfil = self._botao(linha_cartao, "Alterar perfil", self._atribuir_perfil)
        self.botao_alterar_perfil.pack(side="left", padx=4)
        self.botao_status_cartao = self._botao(
            linha_cartao,
            "Bloquear cartão",
            self._alternar_status_cartao,
            cor=VERMELHO,
        )
        self.botao_status_cartao.pack(side="left", padx=4)
        self.botao_excluir_cartao = self._botao(
            linha_cartao,
            "Excluir cartão",
            self._excluir_cartao,
            cor=VERMELHO,
        )
        self.botao_excluir_cartao.pack(side="left", padx=4)
        self.botao_alterar_perfil.configure(state="disabled")
        self.botao_status_cartao.configure(state="disabled")
        self.botao_excluir_cartao.configure(state="disabled")

        colunas = ("identificacao", "uid", "perfil", "status")
        self.tabela_cartoes = ttk.Treeview(
            self.aba_cartoes,
            columns=colunas,
            show="headings",
            height=6,
            selectmode="browse",
        )
        for coluna, titulo, largura in (
            ("identificacao", "Usuário", 230),
            ("uid", "UID", 180),
            ("perfil", "Perfil", 220),
            ("status", "Status", 110),
        ):
            self.tabela_cartoes.heading(coluna, text=titulo)
            self.tabela_cartoes.column(coluna, width=largura, anchor="w")
        self.tabela_cartoes.pack(fill="both", expand=True)
        self.tabela_cartoes.bind("<<TreeviewSelect>>", self._cartao_selecionado)

    def _montar_aba_perfis(self):
        ttk.Label(self.aba_perfis, text="Perfis e áreas permitidas", style="Section.TLabel").pack(anchor="w")
        ttk.Label(self.aba_perfis, text="Marque as áreas que cada perfil pode acessar.").pack(anchor="w", pady=(4, 14))
        conteudo = ttk.Frame(self.aba_perfis)
        conteudo.pack(fill="both", expand=True)

        painel_lista = ttk.Frame(conteudo, style="Card.TFrame", padding=12)
        painel_lista.pack(side="left", fill="y", padx=(0, 12))
        ttk.Label(painel_lista, text="Perfis", style="Section.TLabel").pack(anchor="w", pady=(0, 8))
        self.tabela_perfis = ttk.Treeview(painel_lista, columns=("nome", "status"), show="headings", height=7, selectmode="browse")
        self.tabela_perfis.heading("nome", text="Nome")
        self.tabela_perfis.heading("status", text="Status")
        self.tabela_perfis.column("nome", width=180)
        self.tabela_perfis.column("status", width=80)
        self.botao_novo_perfil = self._botao(painel_lista, "Novo perfil", self._novo_perfil)
        self.botao_novo_perfil.pack(fill="x", pady=(8, 0))
        self.botao_status_perfil = self._botao(painel_lista, "Ativar / desativar", self._alternar_status_perfil, cor=VERMELHO)
        self.botao_status_perfil.pack(fill="x", pady=(5, 0))
        self.botao_excluir_perfil = self._botao(painel_lista, "Excluir perfil", self._excluir_perfil, cor=VERMELHO)
        self.botao_excluir_perfil.pack(fill="x", pady=(5, 0))
        self.botao_status_perfil.configure(state="disabled")
        self.botao_excluir_perfil.configure(state="disabled")
        self.tabela_perfis.pack(fill="both", expand=True, pady=(8, 0))
        self.tabela_perfis.bind("<<TreeviewSelect>>", self._perfil_selecionado)

        painel_edicao = ttk.Frame(conteudo, style="Card.TFrame", padding=16)
        painel_edicao.pack(side="left", fill="both", expand=True)
        ttk.Label(painel_edicao, text="Criar ou modificar perfil", style="Section.TLabel").pack(anchor="w")
        ttk.Label(painel_edicao, text="Nome do perfil", style="Muted.TLabel").pack(anchor="w", pady=(12, 3))
        self.nome_perfil_var = tk.StringVar()
        tk.Entry(painel_edicao, textvariable=self.nome_perfil_var, font=("Segoe UI", 10)).pack(fill="x")
        ttk.Label(painel_edicao, text="Descrição", style="Muted.TLabel").pack(anchor="w", pady=(10, 3))
        self.descricao_perfil_var = tk.StringVar()
        tk.Entry(painel_edicao, textvariable=self.descricao_perfil_var, font=("Segoe UI", 10)).pack(fill="x")
        ttk.Label(painel_edicao, text="Áreas permitidas", style="Section.TLabel").pack(anchor="w", pady=(12, 5))
        self.botao_salvar_perfil = self._botao(painel_edicao, "Criar perfil", self._salvar_perfil)
        self.botao_salvar_perfil.pack(anchor="w", pady=(0, 6))
        self.checkboxes_areas = ttk.Frame(painel_edicao, style="Card.TFrame")
        self.checkboxes_areas.pack(fill="both", expand=True)

        cadastro_area = ttk.Frame(self.aba_perfis, style="Card.TFrame", padding=12)
        cadastro_area.pack(fill="x", pady=(12, 0))
        ttk.Label(cadastro_area, text="Adicionar área", style="Section.TLabel").pack(side="left", padx=(0, 10))
        self.nome_area_var = tk.StringVar()
        tk.Entry(cadastro_area, textvariable=self.nome_area_var, width=30, font=("Segoe UI", 10)).pack(side="left", padx=5)
        self.descricao_area_var = tk.StringVar()
        tk.Entry(cadastro_area, textvariable=self.descricao_area_var, width=38, font=("Segoe UI", 10)).pack(side="left", padx=5)
        self._botao(cadastro_area, "Adicionar", self._adicionar_area).pack(side="left", padx=5)

    def _atualizar_tudo(self):
        self._atualizar_areas()
        self._atualizar_cartoes()
        self._atualizar_perfis()

    def _atualizar_areas(self):
        self.areas = self.repositorio.listar_areas()
        self.area_acesso_opcoes = {
            f"{area[2]} (#{area[0]})": area[0]
            for area in self.areas if area[4] == 1
        }
        self.area_acesso_combo["values"] = list(self.area_acesso_opcoes)
        if self.area_acesso_opcoes and self.area_acesso_var.get() not in self.area_acesso_opcoes:
            self.area_acesso_var.set(next(iter(self.area_acesso_opcoes)))
        elif not self.area_acesso_opcoes:
            self.area_acesso_var.set("")

    def _atualizar_cartoes(self):
        selecionado = self._uid_cartao_selecionado()
        self.tabela_cartoes.delete(*self.tabela_cartoes.get_children())
        for cartao in self.repositorio.listar_cartoes():
            id_cartao, identificacao, uid, ativo, data = cartao
            perfil = self.repositorio.listar_perfil_dispositivo(uid)
            nome_perfil = perfil[2] if perfil else "Sem perfil"
            self.tabela_cartoes.insert(
                "", "end", iid=uid,
                values=(identificacao, uid, nome_perfil, "Ativo" if ativo else "Bloqueado"),
            )
        if selecionado and self.tabela_cartoes.exists(selecionado):
            self.tabela_cartoes.selection_set(selecionado)
        self._atualizar_perfis_combo()
        self._cartao_selecionado()

    def _atualizar_perfis_combo(self):
        self._card_profile_labels = {"Sem perfil": 0}
        for perfil in self.repositorio.listar_perfis():
            if perfil[4] == 1:
                self._card_profile_labels[f"{perfil[2]} (#{perfil[0]})"] = perfil[0]
        self.perfil_cartao_combo["values"] = list(self._card_profile_labels)
        if self.perfil_cartao_var.get() not in self._card_profile_labels:
            self.perfil_cartao_var.set("")

    def _atualizar_perfis(self, manter_id=None):
        if manter_id is None:
            manter_id = self._selected_profile_id
        self.tabela_perfis.delete(*self.tabela_perfis.get_children())
        for perfil in self.repositorio.listar_perfis():
            id_perfil, codigo, nome, descricao, ativo = perfil
            self.tabela_perfis.insert(
                "", "end", iid=str(id_perfil),
                values=(nome, "Ativo" if ativo else "Inativo"),
            )
        self._atualizar_perfis_combo()
        if manter_id is not None and self.tabela_perfis.exists(str(manter_id)):
            self.tabela_perfis.selection_set(str(manter_id))
            self.tabela_perfis.see(str(manter_id))
            self._carregar_perfil(int(manter_id))
        else:
            self._selected_profile_id = None
            self._renderizar_checkboxes(set())

    def _renderizar_checkboxes(self, selecionadas):
        for filho in self.checkboxes_areas.winfo_children():
            filho.destroy()
        self._area_vars.clear()
        if not self.areas:
            ttk.Label(self.checkboxes_areas, text="Cadastre uma área para configurar permissões.", style="Muted.TLabel").pack(anchor="w")
            return
        for area in self.areas:
            id_area, codigo, nome, descricao, ativo = area
            var = tk.IntVar(value=1 if id_area in selecionadas else 0)
            linha = ttk.Frame(self.checkboxes_areas, style="Card.TFrame")
            linha.pack(fill="x", pady=2)
            chk = ttk.Checkbutton(linha, text=nome, variable=var)
            chk.pack(side="left")
            if not ativo:
                ttk.Label(linha, text="(inativa)", style="Muted.TLabel").pack(side="left", padx=5)
                chk.state(["disabled"])
            self._area_vars[id_area] = var

    def _perfil_selecionado(self, _evento=None):
        selecionados = self.tabela_perfis.selection()
        if selecionados:
            self._carregar_perfil(int(selecionados[0]))

    def _carregar_perfil(self, id_perfil):
        perfil = next((p for p in self.repositorio.listar_perfis() if p[0] == id_perfil), None)
        if perfil is None:
            return
        self._selected_profile_id = id_perfil
        self.botao_salvar_perfil.configure(text="Salvar alterações")
        self.botao_status_perfil.configure(state="normal")
        self.botao_excluir_perfil.configure(state="normal")
        self.nome_perfil_var.set(perfil[2])
        self.descricao_perfil_var.set(perfil[3] or "")
        areas_permitidas = {a[0] for a in self.repositorio.listar_areas_perfil(id_perfil)}
        self._renderizar_checkboxes(areas_permitidas)

    def _novo_perfil(self):
        self._selected_profile_id = None
        selecionados = self.tabela_perfis.selection()
        if selecionados:
            self.tabela_perfis.selection_remove(*selecionados)
        self.botao_salvar_perfil.configure(text="Criar perfil")
        self.botao_status_perfil.configure(state="disabled")
        self.botao_excluir_perfil.configure(state="disabled")
        self.nome_perfil_var.set("")
        self.descricao_perfil_var.set("")
        self._renderizar_checkboxes(set())

    def _salvar_perfil(self):
        nome = self.nome_perfil_var.get().strip()
        descricao = self.descricao_perfil_var.get().strip()
        if not nome:
            messagebox.showwarning("Perfil", "Informe o nome do perfil.", parent=self)
            return
        if self._selected_profile_id is None:
            sucesso, mensagem = self.repositorio.cadastrar_perfil(nome, descricao)
            if not sucesso:
                messagebox.showerror("Perfil", mensagem, parent=self)
                return
            perfil = next((p for p in self.repositorio.listar_perfis() if p[2] == nome), None)
            if perfil is None:
                messagebox.showerror("Perfil", "Não foi possível localizar o perfil cadastrado.", parent=self)
                return
            self._selected_profile_id = perfil[0]
        else:
            sucesso, mensagem = self.repositorio.editar_perfil(self._selected_profile_id, nome, descricao)
            if not sucesso:
                messagebox.showerror("Perfil", mensagem, parent=self)
                return
        ids = {id_area for id_area, var in self._area_vars.items() if var.get() == 1}
        sucesso, mensagem = self.repositorio.atualizar_areas_perfil(self._selected_profile_id, ids)
        if not sucesso:
            messagebox.showerror("Permissões", mensagem, parent=self)
            return
        messagebox.showinfo("Perfil", "Perfil e áreas permitidas salvos.", parent=self)
        self._atualizar_perfis(self._selected_profile_id)
        self._atualizar_cartoes()

    def _excluir_perfil(self):
        selecionados = self.tabela_perfis.selection()
        if not selecionados:
            messagebox.showwarning("Perfil", "Selecione um perfil.", parent=self)
            return
        id_perfil = int(selecionados[0])
        perfil = next((p for p in self.repositorio.listar_perfis() if p[0] == id_perfil), None)
        if perfil is None:
            messagebox.showerror("Perfil", "Não foi possível localizar o perfil selecionado.", parent=self)
            return
        confirmar = messagebox.askyesno(
            "Excluir perfil",
            f"Excluir o perfil {perfil[2]}?\n\n"
            "Os cartões que usam esse perfil ficarão sem perfil associado.",
            parent=self,
        )
        if not confirmar:
            return
        sucesso = self.repositorio.excluir_perfil(id_perfil)
        if not sucesso:
            messagebox.showerror("Perfil", "Não foi possível excluir o perfil.", parent=self)
            return
        self._selected_profile_id = None
        self._atualizar_perfis()
        self._novo_perfil()
        self._atualizar_cartoes()
        messagebox.showinfo("Perfil", f"Perfil {perfil[2]} excluído.", parent=self)

    def _alternar_status_perfil(self):
        selecionados = self.tabela_perfis.selection()
        if not selecionados:
            messagebox.showwarning("Perfil", "Selecione um perfil.", parent=self)
            return
        perfil = next(p for p in self.repositorio.listar_perfis() if p[0] == int(selecionados[0]))
        novo_status = 0 if perfil[4] else 1
        sucesso, mensagem = self.repositorio.alterar_status_perfil(perfil[0], novo_status)
        if sucesso:
            self._atualizar_perfis(perfil[0])
            self._atualizar_cartoes()
        else:
            messagebox.showerror("Perfil", mensagem, parent=self)

    def _adicionar_area(self):
        nome = self.nome_area_var.get().strip()
        descricao = self.descricao_area_var.get().strip()
        if not nome:
            messagebox.showwarning("Área", "Informe o nome da área.", parent=self)
            return
        sucesso, mensagem = self.repositorio.cadastrar_area(nome, descricao)
        if not sucesso:
            messagebox.showerror("Área", mensagem, parent=self)
            return
        self.nome_area_var.set("")
        self.descricao_area_var.set("")
        self._atualizar_areas()
        if self._selected_profile_id is not None:
            self._carregar_perfil(self._selected_profile_id)
        else:
            self._renderizar_checkboxes(set())
        messagebox.showinfo("Área", mensagem, parent=self)

    def _perfil_selecionado_para_cartao(self):
        selecionados = self.tabela_cartoes.selection()
        if not selecionados:
            return None
        return selecionados[0]

    def _uid_cartao_selecionado(self):
        return self._perfil_selecionado_para_cartao()

    def _cartao_selecionado(self, _evento=None):
        uid = self._uid_cartao_selecionado()
        if not uid:
            self.cartao_selecionado_var.set("Selecione um cadastro na lista para gerenciar.")
            self.nome_usuario_edicao_var.set("")
            self.perfil_cartao_var.set("")
            self.entrada_nome_usuario.configure(state="normal")
            self.botao_salvar_nome.configure(state="disabled")
            self.botao_alterar_perfil.configure(state="disabled")
            self.botao_status_cartao.configure(text="Bloquear cartão", state="disabled", bg=VERMELHO)
            self.botao_excluir_cartao.configure(state="disabled")
            self.botao_excluir_usuario.configure(state="disabled")
            return

        cartao = next((c for c in self.repositorio.listar_cartoes() if c[2] == uid), None)
        if cartao is None:
            return
        _id_cartao, identificacao, _uid, ativo, _data = cartao
        usuario = self.repositorio.consultar_usuario(uid)
        if usuario is None:
            return
        id_usuario, nome_usuario, _uid_usuario, _ativo_usuario, _data_usuario = usuario
        perfil = self.repositorio.listar_perfil_dispositivo(uid)
        nome_perfil = perfil[2] if perfil else "Sem perfil"
        label_perfil = next(
            (nome for nome, id_perfil in self._card_profile_labels.items() if perfil and id_perfil == perfil[0]),
            "Sem perfil",
        )
        self.perfil_cartao_var.set(label_perfil)
        estado = "Ativo" if ativo else "Bloqueado"
        self.nome_usuario_edicao_var.set(nome_usuario)
        self.cartao_selecionado_var.set(
            f"Usuário: {nome_usuario}  •  Cartão: {uid}  •  Perfil do cartão: {nome_perfil}  •  {estado}"
        )
        self.entrada_nome_usuario.configure(state="normal")
        self.botao_salvar_nome.configure(state="normal")
        self.botao_alterar_perfil.configure(state="normal")
        self.botao_status_cartao.configure(
            text="Bloquear cartão" if ativo else "Reativar cartão",
            state="normal",
            bg=VERMELHO if ativo else AZUL,
            activebackground=VERMELHO if ativo else AZUL_ESCURO,
        )
        self.botao_excluir_cartao.configure(state="normal")
        self.botao_excluir_usuario.configure(state="normal")

    def _salvar_nome_usuario(self):
        uid = self._uid_cartao_selecionado()
        nome = self.nome_usuario_edicao_var.get().strip()
        if not uid:
            messagebox.showwarning("Usuário", "Selecione um usuário na lista.", parent=self)
            return
        if not nome:
            messagebox.showwarning("Usuário", "Informe o nome do usuário.", parent=self)
            return
        if not self.repositorio.renomear_usuario(uid, nome):
            messagebox.showerror("Usuário", "Não foi possível atualizar o nome do usuário.", parent=self)
            return
        self._atualizar_cartoes()
        messagebox.showinfo("Usuário", "Nome do usuário atualizado.", parent=self)

    def _cadastrar_cartao(self):
        identificacao = self.identificacao_var.get().strip()
        uid = self.uid_var.get().strip().upper()
        if not identificacao or not uid:
            messagebox.showwarning("Cartão", "Informe a identificação e leia ou digite a UID.", parent=self)
            return
        sucesso, mensagem = self.repositorio.cadastrar_cartao(identificacao, uid)
        if not sucesso:
            messagebox.showerror("Cartão", mensagem, parent=self)
            return
        self.identificacao_var.set("")
        self.uid_var.set("")
        self._atualizar_cartoes()
        messagebox.showinfo("Cartão", mensagem, parent=self)

    def _ler_uid_para_cadastro(self):
        self._iniciar_leitura(lambda uid, erro: self.uid_var.set(uid) if uid else self._mostrar_erro_leitura(erro))

    def _atribuir_perfil(self):
        uid = self._uid_cartao_selecionado()
        label = self.perfil_cartao_var.get()
        if not uid:
            messagebox.showwarning("Cartão", "Selecione um cartão.", parent=self)
            return
        id_perfil = self._card_profile_labels.get(label)
        if id_perfil is None:
            messagebox.showwarning("Perfil", "Escolha um perfil ativo.", parent=self)
            return
        if id_perfil == 0:
            sucesso = self.repositorio.remover_perfil_dispositivo(uid)
            mensagem = "Perfil removido do cartão." if sucesso else "O cartão já estava sem perfil."
        else:
            sucesso, mensagem = self.repositorio.definir_perfil_dispositivo(uid, id_perfil)
        if sucesso:
            self._atualizar_cartoes()
        messagebox.showinfo("Cartão", mensagem, parent=self) if sucesso else messagebox.showerror("Cartão", mensagem, parent=self)

    def _alternar_status_cartao(self):
        uid = self._uid_cartao_selecionado()
        if not uid:
            messagebox.showwarning("Cartão", "Selecione um cartão.", parent=self)
            return
        cartao = next((c for c in self.repositorio.listar_cartoes() if c[2] == uid), None)
        if cartao is None:
            return
        novo_status = 0 if cartao[3] else 1
        if self.repositorio.alterar_status_cartao(uid, novo_status):
            self._atualizar_cartoes()

    def _excluir_cartao(self):
        uid = self._uid_cartao_selecionado()
        if not uid:
            messagebox.showwarning("Cartão", "Selecione um cartão.", parent=self)
            return
        cartao = next((c for c in self.repositorio.listar_cartoes() if c[2] == uid), None)
        identificacao = cartao[1] if cartao else "usuário"
        if not messagebox.askyesno(
            "Excluir cartão",
            f"Excluir somente o cartão {uid} de {identificacao}?",
            parent=self,
        ):
            return
        if self.repositorio.excluir_cartao(uid):
            self._atualizar_cartoes()

    def _excluir_usuario(self):
        uid = self._uid_cartao_selecionado()
        if not uid:
            messagebox.showwarning("Usuário", "Selecione um usuário na lista.", parent=self)
            return
        usuario = self.repositorio.consultar_usuario(uid)
        if usuario is None:
            messagebox.showerror("Usuário", "Não foi possível localizar o usuário selecionado.", parent=self)
            return
        id_usuario, nome_usuario = usuario[0], usuario[1]
        quantidade = self.repositorio.contar_cartoes_usuario(id_usuario)
        confirmacao = messagebox.askyesno(
            "Excluir usuário",
            f"Excluir o usuário {nome_usuario} e todos os cartões associados ({quantidade})?\n\n"
            "Essa ação não pode ser desfeita.",
            parent=self,
        )
        if not confirmacao:
            return
        if self.repositorio.excluir_usuario_por_id(id_usuario):
            self._atualizar_cartoes()
            messagebox.showinfo("Usuário", f"Usuário {nome_usuario} excluído.", parent=self)
        else:
            messagebox.showerror("Usuário", "Não foi possível excluir o usuário.", parent=self)

    def _verificar_acesso(self):
        label = self.area_acesso_var.get()
        id_area = self.area_acesso_opcoes.get(label)
        if id_area is None:
            messagebox.showwarning("Acesso", "Cadastre e selecione uma área ativa.", parent=self)
            return
        self._iniciar_leitura(lambda uid, erro: self._resultado_leitura_acesso(uid, id_area, erro))

    def _resultado_leitura_acesso(self, uid, id_area, erro):
        if not uid:
            self._mostrar_erro_leitura(erro)
            return
        resultado = self.autenticador.verificar_acesso(uid, id_area)
        autorizado = resultado["autorizado"]
        cor = VERDE if autorizado else VERMELHO
        estado = "ACESSO AUTORIZADO" if autorizado else "ACESSO NEGADO"
        self.resultado_acesso.configure(text=estado, fg=cor)
        identificacao = resultado.get("usuario") or "Cartão não identificado"
        area = resultado.get("area") or self.area_acesso_var.get()
        self.detalhe_acesso.set(f"Cartão: {identificacao}   •   Área: {area}   •   UID: {uid}")

    def _iniciar_leitura(self, callback):
        if self._lendo_cartao:
            return
        porta = self.porta_var.get().strip()
        if not porta:
            messagebox.showwarning("Leitor RFID", "Informe a porta serial do Arduino.", parent=self)
            return
        self._lendo_cartao = True
        self._callback_leitura = callback
        self.status_var.set(f"Aguardando cartão em {porta}…")
        threading.Thread(target=self._ler_uid_em_segundo_plano, args=(porta,), daemon=True).start()
        self.after(100, self._consultar_fila_leitura)

    def _ler_uid_em_segundo_plano(self, porta):
        try:
            with serial.Serial(porta, self.velocidade, timeout=1) as conexao:
                time.sleep(2)
                uid = LeitorRFID.ler_uid(conexao, timeout_segundos=30)
            self._fila_leitura.put((uid, None))
        except Exception as erro:
            self._fila_leitura.put((None, str(erro)))

    def _consultar_fila_leitura(self):
        try:
            uid, erro = self._fila_leitura.get_nowait()
        except queue.Empty:
            if self._lendo_cartao:
                self.after(100, self._consultar_fila_leitura)
            return
        self._lendo_cartao = False
        self.status_var.set("Pronto")
        callback = self._callback_leitura
        self._callback_leitura = None
        if callback:
            callback(uid, erro)

    def _mostrar_erro_leitura(self, erro):
        mensagem = erro or "Não foi possível ler o cartão."
        messagebox.showerror("Leitor RFID", mensagem, parent=self)
        self.status_var.set("Pronto")


if __name__ == "__main__":
    InterfaceRFID().mainloop()
