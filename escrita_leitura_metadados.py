import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import piexif

class EditorEXIF:
    def __init__(self, root):
        self.root = root
        self.root.title("🖼️ Editor de Metadados EXIF + X-LAT/Y-LONG")
        self.root.geometry("1100x750")
        self.arquivo_selecionado = None
        
        self.setup_ui()
    
    def setup_ui(self):
        frame_top = ttk.Frame(self.root)
        frame_top.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(frame_top, text="📁 Selecionar Imagem", 
                  command=self.selecionar_imagem).pack(side=tk.LEFT, padx=(0,10))
        
        self.label_arquivo = ttk.Label(frame_top, text="Nenhuma imagem selecionada")
        self.label_arquivo.pack(side=tk.LEFT)
        
        ttk.Button(frame_top, text="🔄 Recarregar", 
                  command=self.ler_metadados).pack(side=tk.LEFT, padx=(10,0))
        
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0,10))
        
        self.frame_visualizar = ttk.Frame(self.notebook)
        self.notebook.add(self.frame_visualizar, text="📋 Visualizar")
        self.setup_visualizar()
        
        self.frame_editar = ttk.Frame(self.notebook)
        self.notebook.add(self.frame_editar, text="✏️ Editar")
        self.setup_editar()
    
    def setup_visualizar(self):
        self.text_area = scrolledtext.ScrolledText(self.frame_visualizar, wrap=tk.WORD, height=25)
        self.text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def setup_editar(self):
        # Campos padrão EXIF
        campos_padrao = [
            ('ImageDescription', 'Descrição da Imagem'),
            ('Make', 'Fabricante'),
            ('Model', 'Modelo da Câmera'),
            ('Software', 'Software'),
            ('Artist', 'Fotógrafo'),
            ('Copyright', 'Copyright'),
            ('DateTime', 'Data/Hora')
        ]
        
        # ✅ NOVOS CAMPOS X-LAT e Y-LONG
        campos_coordenadas = [
            ('X-LAT', 'Coordenada X (Latitude)'),
            ('Y-LONG', 'Coordenada Y (Longitude)')
        ]
        
        frame_campos = ttk.LabelFrame(self.frame_editar, text="Editar Campos EXIF")
        frame_campos.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.entries = {}
        
        # Campos padrão
        for campo_tecnico, campo_nome in campos_padrao:
            frame_campo = ttk.Frame(frame_campos)
            frame_campo.pack(fill=tk.X, padx=10, pady=3)
            ttk.Label(frame_campo, text=f"{campo_nome}:", width=22).pack(side=tk.LEFT)
            entry = ttk.Entry(frame_campo, width=50)
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10,0))
            self.entries[campo_tecnico] = entry
        
        # ✅ SEPARADOR para coordenadas
        ttk.Separator(frame_campos, orient='horizontal').pack(fill=tk.X, padx=10, pady=(10,5))
        ttk.Label(frame_campos, text="📍 COORDENADAS CNC (X-LAT/Y-LONG)", 
                 font=('Arial', 10, 'bold')).pack(pady=(5,5))
        
        for campo_tecnico, campo_nome in campos_coordenadas:
            frame_campo = ttk.Frame(frame_campos)
            frame_campo.pack(fill=tk.X, padx=10, pady=3)
            ttk.Label(frame_campo, text=f"{campo_nome}:", width=22).pack(side=tk.LEFT)
            entry = ttk.Entry(frame_campo, width=50)
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10,0))
            self.entries[campo_tecnico] = entry
        
        frame_botoes = ttk.Frame(self.frame_editar)
        frame_botoes.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(frame_botoes, text="💾 Salvar Todos Alterados", 
                  command=self.salvar_todos).pack(side=tk.LEFT, padx=(0,10))
        ttk.Button(frame_botoes, text="🗑️ Limpar Todos", 
                  command=self.limpar_todos).pack(side=tk.LEFT)
    
    def selecionar_imagem(self):
        arquivo = filedialog.askopenfilename(
            title="Selecionar Imagem",
            filetypes=[("Imagens JPG", "*.jpg *.jpeg"), ("Todas Imagens", "*.png *.tiff *.webp *.jpg *.jpeg")]
        )
        if arquivo:
            self.arquivo_selecionado = arquivo
            nome_arquivo = arquivo.split('/')[-1] if '/' in arquivo else arquivo.split('\\')[-1]
            self.label_arquivo.config(text=f"✅ {nome_arquivo}")
            self.ler_metadados()
    
    def ler_metadados(self):
        if not self.arquivo_selecionado:
            messagebox.showwarning("Aviso", "Selecione uma imagem primeiro!")
            return
        
        texto_pil = self.extrair_pil_exif(self.arquivo_selecionado)
        metadados_piexif = self.ler_metadados_piexif(self.arquivo_selecionado)
        
        texto = f"📁 Arquivo: {self.arquivo_selecionado.split('\\')[-1]}\n"
        texto += "\n=== METADADOS PIL ===\n"
        texto += texto_pil
        
        texto += "\n=== METADADOS PIEXIF ===\n"
        if 'erro' not in metadados_piexif:
            for grupo, tags in metadados_piexif.get('exif', {}).items():
                texto += f"\n📂 {grupo}:\n"
                for tag, valor in sorted(tags.items()):
                    texto += f"  {tag}: {valor}\n"
        
        self.text_area.delete(1.0, tk.END)
        self.text_area.insert(tk.END, texto)
        
        # ✅ Preenche TODOS os campos (incluindo X-LAT/Y-LONG)
        pil_exif = self.parse_pil_exif(texto_pil)
        piexif_exif = self.parse_piexif_exif(metadados_piexif)
        exif_completo = {**pil_exif, **piexif_exif}
        self.preencher_campos(exif_completo)
    
    def parse_piexif_exif(self, metadados):
        """Extrai X-LAT e Y-LONG do piexif"""
        exif_dict = {}
        if 'exif' in metadados:
            for grupo, tags in metadados['exif'].items():
                for tag, valor in tags.items():
                    if tag in ['X-LAT', 'Y-LONG']:
                        exif_dict[tag] = valor
        return exif_dict
    
    def extrair_pil_exif(self, caminho_imagem):
        try:
            img = Image.open(caminho_imagem)
            exif = img.getexif()
            texto = ""
            if exif:
                for tag_id, valor in exif.items():
                    tag = TAGS.get(tag_id, f"Tag_{tag_id}")
                    if isinstance(valor, bytes):
                        valor_str = valor.decode('utf-8', errors='replace')
                    else:
                        valor_str = str(valor)
                    texto += f"{tag}: {valor_str}\n"
            else:
                texto = "Nenhum EXIF encontrado.\n"
            return texto
        except Exception as e:
            return f"Erro PIL: {str(e)}\n"
    
    def parse_pil_exif(self, texto_pil):
        exif_dict = {}
        for linha in texto_pil.split('\n'):
            if ':' in linha:
                tag, valor = linha.split(':', 1)
                exif_dict[tag.strip()] = valor.strip()
        return exif_dict
    
    def ler_metadados_piexif(self, caminho_imagem):
        try:
            resultado = {'exif': {}}
            try:
                exif_dict = piexif.load(caminho_imagem)
            except:
                return resultado
            
            grupos = {
                0: 'ImageIFD (0th)',
                1: 'ThumbnailIFD (1st)', 
                piexif.ExifIFD: 'ExifIFD',
                piexif.GPSIFD: 'GPSIFD',
                piexif.InteropIFD: 'InteropIFD'
            }
            
            for ifd_id, dados in exif_dict.items():
                if dados and ifd_id != 'thumbnail':
                    grupo_nome = grupos.get(ifd_id, f"Grupo_{ifd_id}")
                    resultado['exif'][grupo_nome] = {}
                    
                    for tag_id, valor in dados.items():
                        try:
                            tag_info = piexif.TAGS.get(ifd_id, {}).get(tag_id, f"Tag_{tag_id}")
                            
                            if isinstance(valor, bytes):
                                valor_str = valor.decode('utf-8', errors='replace')
                            elif isinstance(valor, (tuple, list)):
                                valor_str = str(valor)
                            else:
                                valor_str = str(valor)
                            
                            resultado['exif'][grupo_nome][tag_info] = valor_str
                        except:
                            continue
            return resultado
        except Exception as e:
            return {'erro': str(e)}
    
    def preencher_campos(self, exif_dict):
        for campo, entry in self.entries.items():
            valor = exif_dict.get(campo, '')
            entry.delete(0, tk.END)
            entry.insert(0, valor)
    
    def limpar_todos(self):
        for entry in self.entries.values():
            entry.delete(0, tk.END)
    
    def salvar_todos(self):
        if not self.arquivo_selecionado:
            messagebox.showwarning("Aviso", "Selecione uma imagem primeiro!")
            return
        
        alterados = 0
        for campo, entry in self.entries.items():
            valor = entry.get().strip()
            resultado = self.escrever_campo_exif(self.arquivo_selecionado, campo, valor)
            if 'sucesso' in resultado:
                alterados += 1
        
        messagebox.showinfo("Salvo!", f"✅ {alterados} campos salvos com sucesso!\nIncluindo X-LAT e Y-LONG")
        self.ler_metadados()
    
    def escrever_campo_exif(self, caminho_imagem, campo, valor):
        """✅ Suporta X-LAT e Y-LONG como campos customizados"""
        try:
            exif_dict = piexif.load(caminho_imagem)
            
            mapeamento_padrao = {
                'ImageDescription': piexif.ImageIFD.ImageDescription,
                'Make': piexif.ImageIFD.Make,
                'Model': piexif.ImageIFD.Model,
                'Software': piexif.ImageIFD.Software,
                'Artist': piexif.ImageIFD.Artist,
                'Copyright': piexif.ImageIFD.Copyright,
                'DateTime': piexif.ImageIFD.DateTime
            }
            
            # ✅ CAMPOS CUSTOMIZADOS X-LAT e Y-LONG (usa UserComment)
            if campo == 'X-LAT':
                # Armazena como comentário do usuário com prefixo
                comentario_x = f"X-LAT:{valor}"
                exif_dict['Exif'][piexif.ExifIFD.UserComment] = comentario_x.encode('utf-8')
            elif campo == 'Y-LONG':
                comentario_y = f"Y-LONG:{valor}"
                exif_dict['Exif'][piexif.ExifIFD.UserComment] = comentario_y.encode('utf-8')
            elif campo in mapeamento_padrao:
                tag_id = mapeamento_padrao[campo]
                if valor.strip():
                    exif_dict['0th'][tag_id] = valor.encode('utf-8')
                else:
                    exif_dict['0th'].pop(tag_id, None)
            else:
                return {'erro': f'Campo {campo} não suportado'}
            
            exif_bytes = piexif.dump(exif_dict)
            piexif.insert(exif_bytes, caminho_imagem)
            return {'sucesso': True}
        except Exception as e:
            return {'erro': str(e)}

if __name__ == "__main__":
    root = tk.Tk()
    app = EditorEXIF(root)
    root.mainloop()
