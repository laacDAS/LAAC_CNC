import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import piexif
import exifread
import os
import re

class VisualizadorMetadadosLimpo:
    def __init__(self, root):
        self.root = root
        self.root.title("🔍 METADADOS COMPLETOS - FORMATO LIMPO")
        self.root.geometry("1400x900")
        self.arquivo_selecionado = None
        self.setup_ui()
    
    def setup_ui(self):
        # Header limpo
        header_frame = ttk.Frame(self.root)
        header_frame.pack(fill=tk.X, padx=15, pady=15)
        
        ttk.Button(header_frame, text="📁 ABRIR IMAGEM", 
                  command=self.selecionar_imagem, width=18).pack(side=tk.LEFT)
        
        self.info_label = ttk.Label(header_frame, text="Selecione uma imagem...", 
                                   font=('Segoe UI', 11, 'bold'))
        self.info_label.pack(side=tk.LEFT, padx=(20,0))
        
        ttk.Button(header_frame, text="🔄 ANALISAR", 
                  command=self.analisar_tudo).pack(side=tk.RIGHT)
        
        # Notebook com abas organizadas
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0,15))
        
        # Aba principal formatada
        main_frame = ttk.Frame(notebook)
        notebook.add(main_frame, text="📋 METADADOS ORGANIZADOS")
        
        # Treeview para tabela limpa
        columns = ('GRUPO', 'TAG', 'VALOR')
        self.tree = ttk.Treeview(main_frame, columns=columns, show='headings', height=30)
        
        self.tree.heading('GRUPO', text='GRUPO')
        self.tree.heading('TAG', text='TAG')
        self.tree.heading('VALOR', text='VALOR')
        
        self.tree.column('GRUPO', width=150)
        self.tree.column('TAG', width=250)
        self.tree.column('VALOR', width=900)
        
        # Scrollbars
        v_scroll = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.tree.yview)
        h_scroll = ttk.Scrollbar(main_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0,5), pady=10)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X, padx=(0,0), pady=(0,10))
        
        # Aba coordenadas
        coords_frame = ttk.Frame(notebook)
        notebook.add(coords_frame, text="📍 COORDENADAS CNC")
        self.setup_coordenadas(coords_frame)
    
    def setup_coordenadas(self, parent):
        frame = ttk.LabelFrame(parent, text="X-LAT / Y-LONG", padding=20)
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Labels grandes
        ttk.Label(frame, text="X-LAT:", font=('Arial', 16, 'bold')).pack(anchor='w', pady=(0,5))
        self.entry_xlat = ttk.Entry(frame, font=('Arial', 16), width=25)
        self.entry_xlat.pack(fill=tk.X, pady=(0,20))
        
        ttk.Label(frame, text="Y-LONG:", font=('Arial', 16, 'bold')).pack(anchor='w', pady=(0,5))
        self.entry_ylong = ttk.Entry(frame, font=('Arial', 16), width=25)
        self.entry_ylong.pack(fill=tk.X, pady=(0,20))
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X)
        ttk.Button(btn_frame, text="💾 SALVAR", command=self.salvar_coordenadas, width=20).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="📋 COPIAR", command=self.copiar_coords, width=20).pack(side=tk.LEFT, padx=(10,0))
    
    def limpar_tabela(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
    
    def adicionar_linha(self, grupo, tag, valor):
        self.tree.insert('', 'end', values=(grupo, tag, valor))
    
    def selecionar_imagem(self):
        arquivo = filedialog.askopenfilename(
            filetypes=[("JPG", "*.jpg *.jpeg"), ("Todas", "*.*")]
        )
        if arquivo:
            self.arquivo_selecionado = arquivo
            nome = os.path.basename(arquivo)
            tamanho = os.path.getsize(arquivo)
            self.info_label.config(text=f"✅ {nome} | {tamanho:,} bytes")
            self.analisar_tudo()
    
    def analisar_tudo(self):
        if not self.arquivo_selecionado:
            return
        
        self.limpar_tabela()
        
        # INFO BÁSICA
        self.adicionar_info_basica()
        
        # PIL EXIF
        self.extrair_pil_exif()
        
        # PIEXIF (MAIS IMPORTANTE)
        self.extrair_piexif_completo()
        
        # EXIFREAD corrigido
        self.extrair_exifread()
        
        # Extrair coordenadas
        self.extrair_coordenadas()
    
    def adicionar_info_basica(self):
        try:
            st = os.stat(self.arquivo_selecionado)
            img = Image.open(self.arquivo_selecionado)
            
            self.adicionar_linha("📁 ARQUIVO", "Nome", os.path.basename(self.arquivo_selecionado))
            self.adicionar_linha("📁 ARQUIVO", "Tamanho", f"{st.st_size:,} bytes")
            self.adicionar_linha("📁 ARQUIVO", "Criado", datetime.fromtimestamp(st.st_ctime).strftime('%Y-%m-%d %H:%M:%S'))
            self.adicionar_linha("📁 ARQUIVO", "Modificado", datetime.fromtimestamp(st.st_mtime).strftime('%Y-%m-%d %H:%M:%S'))
            self.adicionar_linha("🖼️ IMAGEM", "Resolução", f"{img.size[0]}x{img.size[1]}")
            self.adicionar_linha("🖼️ IMAGEM", "Modo", img.mode)
            self.adicionar_linha("🖼️ IMAGEM", "Formato", img.format)
        except:
            pass
    
    def extrair_pil_exif(self):
        try:
            img = Image.open(self.arquivo_selecionado)
            exif = img.getexif()
            if exif:
                self.adicionar_linha("PIL EXIF", "Total Tags", str(len(exif)))
                for tag_id, valor in exif.items():
                    tag_nome = TAGS.get(tag_id, f"Tag_{tag_id}")
                    valor_str = str(valor)
                    self.adicionar_linha("PIL EXIF", tag_nome, valor_str)
        except:
            self.adicionar_linha("PIL EXIF", "Status", "Erro de leitura")
    
    def extrair_piexif_completo(self):
        try:
            exif_dict = piexif.load(self.arquivo_selecionado)
            
            for ifd_name, ifd_data in exif_dict.items():
                if ifd_data and ifd_name != 'thumbnail':
                    grupo = f"PIEXIF {ifd_name}"
                    self.adicionar_linha(grupo, "Total Tags", str(len(ifd_data)))
                    
                    for tag_id, valor_raw in ifd_data.items():
                        try:
                            tag_info = piexif.TAGS.get(ifd_name, {}).get(tag_id, f"0x{tag_id:04x}")
                            
                            # ✅ LIMPA O VALOR
                            if isinstance(valor_raw, bytes):
                                try:
                                    valor = valor_raw.decode('utf-8').strip()
                                except:
                                    valor = f"b'{valor_raw[:50]}...'"
                            elif isinstance(valor_raw, (tuple, list)):
                                valor = str(valor_raw)
                            else:
                                valor = str(valor_raw)
                            
                            self.adicionar_linha(grupo, tag_info, valor)
                        except:
                            continue
        except Exception as e:
            self.adicionar_linha("PIEXIF", "Erro", str(e))
    
    def extrair_exifread(self):
        # ✅ CORRIGIDO: remove stop_tagdict
        try:
            with open(self.arquivo_selecionado, 'rb') as f:
                tags = exifread.process_file(f)  # Sem parâmetro problemático
            if tags:
                self.adicionar_linha("EXIFREAD", "Total Tags", str(len(tags)))
                for tag_name in sorted(tags.keys()):
                    valor = str(tags[tag_name])
                    self.adicionar_linha("EXIFREAD", tag_name, valor)
        except Exception as e:
            self.adicionar_linha("EXIFREAD", "Erro", str(e))
    
    def extrair_coordenadas(self):
        try:
            exif_dict = piexif.load(self.arquivo_selecionado)
            
            # Procura X-LAT e Y-LONG no UserComment
            if 'Exif' in exif_dict and piexif.ExifIFD.UserComment in exif_dict['Exif']:
                raw_comment = exif_dict['Exif'][piexif.ExifIFD.UserComment]
                comentario = ''
                if isinstance(raw_comment, bytes):
                    # Trata prefixo de codificação EXIF (8 bytes), se presente
                    prefix = raw_comment[:8]
                    if prefix.startswith(b'ASCII') or prefix.startswith(b'UNICODE') or prefix.startswith(b'JIS'):
                        try:
                            comentario = raw_comment[8:].decode('utf-8', errors='ignore')
                        except:
                            comentario = raw_comment[8:].decode('latin-1', errors='ignore')
                    else:
                        comentario = raw_comment.decode('utf-8', errors='ignore')
                else:
                    comentario = str(raw_comment)
                
                # Extrai coordenadas
                x_match = re.search(r'X[-_]?LAT[:\s]*([-\d.]+)', comentario, re.IGNORECASE)
                y_match = re.search(r'Y[-_]?LONG[:\s]*([-\d.]+)', comentario, re.IGNORECASE)
                
                if x_match:
                    self.entry_xlat.delete(0, tk.END)
                    self.entry_xlat.insert(0, x_match.group(1))
                
                if y_match:
                    self.entry_ylong.delete(0, tk.END)
                    self.entry_ylong.insert(0, y_match.group(1))
                    
                self.adicionar_linha("📍 COORDENADAS", "X-LAT", x_match.group(1) if x_match else "N/A")
                self.adicionar_linha("📍 COORDENADAS", "Y-LONG", y_match.group(1) if y_match else "N/A")
                
        except:
            pass
    
    def salvar_coordenadas(self):
        xlat = self.entry_xlat.get().strip()
        ylong = self.entry_ylong.get().strip()
        
        if not xlat or not ylong:
            messagebox.showwarning("AVISO", "Preencha ambas coordenadas!")
            return
        
        try:
            exif_dict = piexif.load(self.arquivo_selecionado)
            
            # Salva coordenadas no UserComment
            comentario = f"X-LAT:{xlat};Y-LONG:{ylong};CNC-METADATA"
            # Escreve UserComment com prefixo de codificação ASCII (8 bytes)
            exif_dict['Exif'][piexif.ExifIFD.UserComment] = b'ASCII\x00\x00\x00' + comentario.encode('utf-8')
            
            # Também na descrição
            exif_dict['0th'][piexif.ImageIFD.ImageDescription] = f"CNC X:{xlat} Y:{ylong}".encode('utf-8')
            
            exif_bytes = piexif.dump(exif_dict)
            piexif.insert(exif_bytes, self.arquivo_selecionado)
            
            messagebox.showinfo("✅ SALVO", f"X-LAT: {xlat}\nY-LONG: {ylong}")
            self.analisar_tudo()
            
        except Exception as e:
            messagebox.showerror("ERRO", str(e))
    
    def copiar_coords(self):
        coords = f"X-LAT:{self.entry_xlat.get()}, Y-LONG:{self.entry_ylong.get()}"
        self.root.clipboard_clear()
        self.root.clipboard_append(coords)
        messagebox.showinfo("COPIADO", "Coordenadas copiadas!")

if __name__ == "__main__":
    from datetime import datetime
    root = tk.Tk()
    app = VisualizadorMetadadosLimpo(root)
    root.mainloop()
