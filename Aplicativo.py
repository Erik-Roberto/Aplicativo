# -*- coding: utf-8 -*-
"""
Created on Thu Aug 26 11:44:56 2021

@author: Erik
"""

import os
import xlsxwriter
import time
import tkinter as tk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import filedialog, messagebox
from tkinter.simpledialog import askinteger, askfloat, Dialog

import Leitura_Arduino


class AskFloat(Dialog):
    errormessage = "Not a floating point value."
    
    def __init__(self, titulo, numero_entradas = 1, *args, valor_inicial = None,
                 minvalue = None, maxvalue = None, parent = None):
       
        self.minvalue = minvalue
        self.maxvalue = maxvalue
       
        self.initialvalue = valor_inicial
        self.numero_entradas = numero_entradas
        
        if args:
            self.lista_label = [nome for nome in args]
            
        else:
            self.lista_label = None
        
        super().__init__(parent, titulo)
        
    def destroy(self):
        self.entry = None
        Dialog.destroy(self)
    
    def body(self, master):
        
        self.labels = []
        self.entry = []
        for i in range(self.numero_entradas):
            label = tk.Label(master = master, text = f'Entrada {i+1}', justify = tk.LEFT)
            label.grid(row = i, column = 0, padx = 5, sticky = tk.W)
            self.labels.append(label)
            
            entrada = tk.Entry(master = master, name = f'entry{i+1}')
            entrada.grid(row=i, column = 1, padx=5, sticky=tk.W+tk.E)
            
            if self.initialvalue is not None:
                entrada.insert(0, self.initialvalue)
                entrada.select_range(0, tk.END)
       
            self.entry.append(entrada)
        
        self.update_labels()
        
        return self.entry[0]
    
    def validate(self):
        try:
            result = self.getresult()
        
        except ValueError:
            messagebox.showwarning(
                "Illegal value",
                self.errormessage + "\nPlease try again",
                parent = self
            )
            return 0

        if self.minvalue is not None and max(result) < self.minvalue:
            messagebox.showwarning(
                "Too small",
                "The allowed minimum value is %s. "
                "Please try again." % self.minvalue,
                parent = self
            )
            return 0

        if self.maxvalue is not None and min(result) > self.maxvalue:
            messagebox.showwarning(
                "Too large",
                "The allowed maximum value is %s. "
                "Please try again." % self.maxvalue,
                parent = self
            )
            return 0

        self.result = result

        return 1
    
    
    def getresult(self):
        
        return [self.getdouble(valor.get()) for valor in self.entry]
            
    def update_labels(self):
       
        if self.lista_label is not None: 
            if len(self.lista_label) <= self.numero_entradas:
                for i, label in enumerate(self.lista_label):
                    self.labels[i]['text'] = label

            else:    
               for i, label in enumerate(self.labels):
                   label['text'] = self.lista_label[i]    
                  
        else:
            print('Sem nomes')
        
class FrameGrafico(tk.Frame):
    
    def __init__(self, master):
        super().__init__(master)
        self.set_plot()
        
    def set_plot(self):
        '''Cria o widget e a figura do plot'''
        
        self.figura_plot = plt.Figure(figsize = (6,5), dpi = 100)
        self.subplot = self.figura_plot.add_subplot(111)
        self.grafico = FigureCanvasTkAgg(self.figura_plot, self)
        self.plot = self.grafico.get_tk_widget()
        self.plot.grid(row = 0, column = 0, pady = 10,
                       sticky = tk.E + tk.N + tk.S + tk.W)
        

    def plotar(self, valores, sensores_ativos):
        '''Gerando os plots e os desenha no widget criado
        ----------
        valores (lista): Lista contendo os np.arrays dos pares ordenados de 
        cada sensor
        sensores_ativos (lista): Lista contendo os checkbox ativados 
        '''
        
        self.subplot.clear()
        if len(sensores_ativos) > 0:
            for i, sensor in enumerate(sensores_ativos):
               self.subplot.plot(valores[i][0],
                            valores[i][1],
                            label = f'Sensor {sensor+1}' )
               
               # if len(valores[i][0]) > 2:
               #     dt = valores[i][0][-1] - valores[i][0][-2]
               #     print(f'Sensor {sensor+1} -> dt = {dt}')
               
            self.subplot.legend()
            self.grafico.draw()

class FrameInformacoes(tk.Frame):

    def __init__(self, master):
        super().__init__(master)
        self.numero_checkboxes = 8
        self.checkboxes = []
        self.checkboxes_variables = []
        self.labels_temperatura = []
        self.sensores_ativos = []        
        self.variavel_checkbox_pressao = tk.IntVar()
        self.adicionar_objetos()
    
    def adicionar_objetos(self):
        '''Cria e posiciona todos os objetos contidos no frame'''
        self.gerar_widgets()
        self.posicionar_widgets(self.checkboxes, 0, 0, 0, 5)
        self.posicionar_widgets(self.labels_temperatura, 0, 1, 0, 5)
        self.checkbox_pressao.grid(row = self.numero_checkboxes + 4, column = 0, padx = 0, pady = 5)
        self.label_pressao.grid(row = self.numero_checkboxes + 4, column = 1, padx = 0, pady = 5)
        
    def gerar_widgets(self):
        '''Função responsável por gerar os checkboxes e rótulos de cada sensor'''
        
        for i in range(0, self.numero_checkboxes):
            self.checkboxes_variables.append(tk.IntVar())
            self.checkbox = tk.Checkbutton(master = self,
                                           text = f'Sensor {i+1}',
                                           variable = self.checkboxes_variables[i])
           
            self.label = tk.Label(self, text = '  Temperatura = None')
            self.labels_temperatura.append(self.label)
            self.checkboxes.append(self.checkbox)
    
        self.checkbox_pressao = tk.Checkbutton(master = self,
                                               text = 'Sensor Pressão',
                                               variable = self.variavel_checkbox_pressao)
        self.label_pressao = tk.Label(master = self, text = '      Pressão = None' )
        
    def posicionar_widgets(self, lista_widgets, linha, coluna, espacamentox = 0, espacamentoy = 0):
        '''Posiciona n objetos pelo método grid
        ----------
        lista_widgets (lista): Lista de objetos que serão posicionados
        coluna (int): Conluna na qual serão posicionados os widgets
        espacamentox (int): Opcional, padrão: 0, espaçamento horizontal
        espacamentoy (int): Opcional, padrão: 0, espaçamento vertical
        '''
        
        for i, widget in enumerate(lista_widgets):
            widget.grid(row = linha+i, column = coluna, padx = espacamentox, pady = espacamentoy)
    
    
    def atualizar_valores_temperatura(self, lista_temperaturas, sensores_ativos):
        '''Atualiza os valores de temperaturas nos labels
        ----------
        lista_temperaturas (lista): Lista de n temperaturas, sendo n a 
        quantidade dos sensores ativos
        sensores_ativos (lista): Lista com a posição dos n sensores que estão ativos
        '''
        
        for i, temperatura in enumerate(lista_temperaturas):
            self.labels_temperatura[sensores_ativos[i]]['text'] = f'  Temperatura = {temperatura} oC'
     
    def atualizar_valor_pressao(self, pressao):
        self.label_pressao['text'] = f'      Pressão = {pressao}'
            
    def obter_sensores_ativos(self):
        '''Obtém as posições dos sensores que foram selecionados'''
        
        lista_sensores_ativos = []
        for i, check_variable in enumerate(self.checkboxes_variables):
            if check_variable.get() == 1:
                lista_sensores_ativos.append(i)
        
        self.sensores_ativos = lista_sensores_ativos

    def alterar_checkboxes(self, estado):
        '''Desabilita/Habilita as checkboxes enquanto a coleta de dados está ativa'''
        
        for checkbox in self.checkboxes:
            checkbox.config(state = estado)
        
        self.checkbox_pressao.config(state = estado)

class FrameCaixaMensagem(tk.LabelFrame):

    def __init__(self, master, text):
        super().__init__(master)
        self['text'] = text
        self.mensagens = []
        
        self.criar_caixa_texto()
        
    def criar_caixa_texto(self):
        '''Cria e posiciona o label que exibirá as mensagens'''
        
        self.caixa_mensagem = tk.Label(self,
                                       text = '',
                                       anchor = tk.W, 
                                       justify = tk.LEFT,
                                       height = 6)

        self.caixa_mensagem.grid(row = 0,
                                 column = 0,
                                 pady = 10,
                                 sticky = tk.N)
    
    def print_texto(self, texto):
        '''Exibe mensagens na janela
        ----------
        texto (string): Mensagem que será exibida 
        '''
        
        aux = ''
        self.mensagens.append(texto)
        if len(self.mensagens) > 10:
            self.mensagens.pop(0)
            
        for msg in self.mensagens:
            aux = aux + '\n' + msg
            
        self.caixa_mensagem['text'] = aux
       
class Menu(tk.Menu):
    
    def __init__(self, master):
        super().__init__(master)
        self.num_portas_COM = 13
        
        self.tipos_tc = { 
            'Tipo T': 'T',
            'Tipo B': 'B',
            'Tipo E': 'E',
            'Tipo J': 'J',
            'Tipo K': 'K',
            'Tipo N': 'N',
            'Tipo R': 'R',
            'Tipo S': 'S'
            }
        
        self.criar_submenu_principal()
        self.criar_submenu_configuracao()
        self.criar_submenu_controle()
        
    def criar_submenu_principal(self):
        '''Cria o submenu principal do programa. Lida com arquivos, dados, salvamentos'''
        
        self.submenu_principal = tk.Menu(self, tearoff=0)
        self.submenu_principal.add_command(label = 'Salvar', command = self.salvar_dados)
        self.submenu_principal.add_command(label = 'Apagar dados',
                                           command =  self.apagar_dados)
        self.submenu_principal.add_separator()
        self.submenu_principal.add_command(label = 'Sair', command = self.sair)
        self.add_cascade(label = 'Arquivo', menu = self.submenu_principal)

    def criar_submenu_configuracao(self):
        '''Cria o submenu de configuração. Lida com as configurações de coleta 
        de dados e comunicação com o arduino'''
        
        self.submenu_config = tk.Menu(self, tearoff = 0)
        self.submenu_portas_COM = tk.Menu(self, tearoff = 0)
        self.submenu_portas_COM.add_command(label = 'Atual: COM3', state = tk.DISABLED)
        self.submenu_portas_COM.add_separator()
        
        for i in range(0, self.num_portas_COM):
            self.submenu_portas_COM.add_command(label = f'COM{i}',
                                                command = lambda i=i:
                                                    self.portas_com(i))
        
        self.submenu_config.add_cascade(label = 'Porta COM', menu = self.submenu_portas_COM)        
        
        self.submenu_tipo_tc = tk.Menu(self, tearoff = 0)
        for nome, tipo in self.tipos_tc.items():
            self.submenu_tipo_tc.add_command(label = nome,
                                             command = lambda tipo=tipo: self.definir_tipo_tc(tipo))
        
        self.submenu_config.add_cascade(label = 'Tipo do Termopar', menu = self.submenu_tipo_tc)
        
        self.submenu_config.add_command(label = 'Velocidade de Conexão') # Sem função definida

        self.submenu_config.add_command(label = 'Intervalo de Leitura',
                                        command = self.definir_intervalo_leitura)

        self.add_cascade(label = 'Configurações', menu = self.submenu_config)
    
    def criar_submenu_controle(self):
        
        self.submenu_controle =  tk.Menu(self, tearoff = 0)
        
        self.submenu_controle.add_command(label = 'Setpoint temperatura',
                                          command = self.definir_setpoint)
        
        self.submenu_controle.add_command(label = 'Constantes PID',
                                                command = self.definir_constantes_pid)
        
        self.submenu_controle.add_command(label = 'Controle Automático',
                                          command = self.definir_controle_automatico)
        
        self.submenu_controle.add_command(label = 'Controle Manual',
                                          command = self.definir_controle_manual)
        
        self.add_cascade(label = 'Controle', menu = self.submenu_controle)
        
        
    
    def apagar_dados(self):
        '''Apaga os dados armazendados
        '''
        self.fonte_dados.reset_memoria()
        self.master.pode_iniciar = True
    
    def portas_com(self,num_porta):
        '''Redefine o nome da porta na qual será iniciada a conexão serial
        ----------
        num_porta (int): Número da porta
        '''
        label_atual = f'Atual: {self.fonte_dados.porta_COM}'
        self.submenu_portas_COM.entryconfigure(label_atual, label = f'Atual: COM{num_porta}')
        self.fonte_dados.set_porta_COM(f'COM{num_porta}')
        
        self.print_texto(f'Porta atualizada para COM{num_porta}')
        print(f'Porta atualizada para COM{num_porta}')
      
    def definir_origem_dados(self, fonte_dados):
        '''Método responsável por estabelecer qual classe vai gerar os dados
        ----------
        fonte_dados (classe): Classe que fornecerá os dados
        '''
        self.fonte_dados = fonte_dados
        
    def definir_intervalo_leitura(self):

        intervalo = askinteger('Entrada do intervalo de leitura',
                               'Intervalo entre leituras / segundos')
        
        if intervalo:
            self.fonte_dados.intervalo_leitura = intervalo
    
    def definir_setpoint(self):
        self.fonte_dados.setpoint = askfloat('Setpoint Temperatura', 'Temperatura / ºC')
        
        if self.fonte_dados.gerando:
            func = self.fonte_dados.set_point
            self.fonte_dados.buffer.append(func)
        
    def definir_tipo_tc(self, tipo):
        
        self.fonte_dados.tipo_tc = tipo
        self.print_texto(f'Termopar tipo {tipo}')
    
    def definir_constantes_pid(self):
        
        dialog = AskFloat('Constantes controlador PID', 3, 
                          'Kp:', 'Ki:', 'Kd:')
        constantes = dialog.result
        if constantes is not None:
            self.fonte_dados.constantes_pid = constantes
            
            if self.fonte_dados.gerando:
                func = self.fonte_dados.set_constantes_pid
                self.fonte_dados.buffer.append(func)
            
        else:
            self.print_texto('Nenhum valor adicionado')
    
    def definir_controle_automatico(self):
        
        func = self.fonte_dados.set_controle_automatico
        self.fonte_dados.buffer.append(func)
        
    def definir_controle_manual(self):
        
        pwm = askinteger('Banda PWM', 'PWM: 0 - 255')
        func = lambda: self.fonte_dados.set_controle_manual(pwm)
        self.fonte_dados.buffer.append(func)
    
    
    def definir_func_print(self, func):
        '''Define a função responsável por imprimir mensagens na janela'''
        
        self.print_texto = func
    
    def salvar_dados(self):
        
        nome_dir_inicial = os.path.join(os.environ['USERPROFILE'], 'Desktop')
        nome_dir = filedialog.asksaveasfilename(initialdir = nome_dir_inicial, 
                                        title ='Salvar como',
                                        filetypes = (('Arquivos xlsx', '*.xlsx'),
                                                     ('Todos tipos', '*.*')))
        
        if nome_dir is None:
            return
        
        elif nome_dir == '':
            return
        
        else:
            if not nome_dir.endswith('.xlsx'):       
                nome_dir_T = f'{nome_dir}.xlsx'
             
                self.salvar_temperatura(nome_dir_T)
                
                if self.fonte_dados.leitura_pressao_ativada:
                    nome_dir_P = f'{nome_dir} - Pressao.xlsx'
                    self.salvar_pressao(nome_dir_P)
                
        self.apagar_dados()
        self.master.pode_iniciar = True
        
    def salvar_pressao(self, nome_dir):
        
        workbook = xlsxwriter.Workbook(nome_dir)
        worksheet = workbook.add_worksheet()
    
        dados = self.fonte_dados.get_pressao()
        
        pressao = dados
        
        if len(pressao) > 0:
            #worksheet.write(0, 0, 'Tempo / (s)')
            worksheet.write(0, 1, 'Pressão')
            for i, leitura in enumerate(pressao):
            #    worksheet.write(i+1, 0, tempo[i])
                worksheet.write(i+1, 1, leitura)
                
            workbook.close()  
        
    def salvar_temperatura(self, nome_dir):
        '''Responsável por salvar os dados no diretório escolhido pelo usuário, documento salvo 
        no formato .xlsx '''      

        workbook = xlsxwriter.Workbook(nome_dir)
        worksheet = workbook.add_worksheet()
    
        dados = self.fonte_dados.get_dados()
        
        sensores = self.master.frame_info.sensores_ativos
        tempos = dados[0]
        temperaturas = dados[1]
        
        if len(tempos) > 0:
            for k, sensor in enumerate(sensores):
                worksheet.write(0, k*2, 'Tempo / (s)')
                worksheet.write(0, k*2+1, f'Temperatura termopar {sensor+1} / (ºC)')
                for i, temperatura_sensor_k in enumerate(temperaturas[k]):
                    worksheet.write(i+1, k*2, tempos[k][i])
                    worksheet.write(i+1, k*2+1, temperatura_sensor_k)
                    
            workbook.close()     

    def sair(self):
        '''Método responsável por lidar acom a ação de fechar o aplicativo. Testa se
        alguns processos estão rodando e impede o fechamento caso estejam, caso contrário verifica
        se ha necessidade de salvamento dos dados'''
        
        if self.master.animando:
            self.print_texto('É necessário terminar a coleta dos dados antes de sair.')
            print('É necessário terminar a coleta dos dados antes de sair.')
        
        else:
            dados = self.fonte_dados.get_dados()
            if len(dados[0]) == 0:
                self.master.destroy()
            
            else:   
                resposta = tk.messagebox.askyesno(title = 'Aplicativo de Aquisicao e Controle de Temperatura',
                                                  message = 'Deseja sair sem salvar?')
                if resposta:
                    self.apagar_dados()
                    self.master.destroy()
                
                else:
                    self.salvar_dados()
                    time.sleep(0.100)
                    self.master.destroy()
   
class JanelaPrincipal(tk.Tk):
    
    def __init__(self, nome_janela = 'Titulo', tamanho_inicial_janela = '500x500'):
        super().__init__()
        self.title(nome_janela)
        self.geometry(tamanho_inicial_janela)
        self.minsize(900, 550)
        
        self.animando = False    # Define se a animação está rodando ou não
        self.pode_iniciar = True # Controla o inicio do plot e leitura de dados, previne erros quanto
                                 # a inconsistencia entre os dados pela alteração do numero de sensores
        self.criar_frames()
        self.configuracao_frames()
        
        # Colocando uma função no botão que fecha o aplicativo
        self.protocol('WM_DELETE_WINDOW', self.menu.sair)
        
    def criar_frames(self):
        '''Cria os frames que compõem a janela'''
        
        self.frame_grafico = FrameGrafico(self)
        self.frame_info = FrameInformacoes(self)
        self.frame_caixa_texto = FrameCaixaMensagem(self, 'Mensagens')
        self.print_texto = self.frame_caixa_texto.print_texto
        self.criar_botoes()
        
        self.menu = Menu(self)
        self.menu.definir_func_print(self.print_texto)
        self.config(menu = self.menu)
        
    def configuracao_frames(self):
        '''Configura o redimensionamento e posicionamento dos frames'''
        
        self.frame_info.grid(row = 0, column = 0, padx = 20)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.frame_grafico.grid(row = 0, column = 1, padx = 10, rowspan = 2,
                                sticky = tk.E + tk.N + tk.S + tk.W)
        
        self.frame_grafico.columnconfigure(0, weight=1)
        self.frame_grafico.rowconfigure(0, weight=1)
        self.frame_caixa_texto.grid(row = 1, column = 0, padx = 10, pady = 10,
                                    sticky = 'sewn')
        
        self.frame_caixa_texto.columnconfigure(0, weight=1)
        self.frame_caixa_texto.rowconfigure(0, weight=1)
        
    def criar_botoes(self):
        self.botao_iniciar = tk.Button(self.frame_info,
                                       text = 'Iniciar',
                                       command = self.comando_botao_iniciar)
        
        self.botao_parar = tk.Button(self.frame_info,
                                     text = 'Parar', 
                                     command = self.comando_botao_parar)
        
        self.botao_iniciar.grid(row = 10, column = 0, pady = 10)
        self.botao_parar.grid(row = 10, column = 1, pady = 10)
        
    def iniciar_animacao(self):
        '''Inicia a animação da interface'''
        self.animando = True
        self.animacao()

    def terminar_animacao(self):
        '''Interrompe a animação'''
        self.animando = False
        self.print_texto('Animação interrompida.')
        print('Animação interrompida.')

    def animacao(self):
        '''Método responsável por controlar as animações - atualizacão da T e plots dinâmicos'''    
        
        if self.animando:   
            dados = self.menu.fonte_dados.get_dados()
            dados = self.obter_nparray(dados)
            
            valores_labels = []
            
            for dados_sensor_n in dados:
                if len(dados_sensor_n[1])>0:
                    ultimo_valor = round(dados_sensor_n[1][-1], 3)
                    valores_labels.append(ultimo_valor) 
                        
                self.frame_info.atualizar_valores_temperatura(valores_labels,
                                                              self.frame_info.sensores_ativos)
                
                if self.frame_info.variavel_checkbox_pressao.get():
                    valores_pressao = self.menu.fonte_dados.get_pressao() 
                    if len(valores_pressao) > 0:
                        valor_label_pressao = round(valores_pressao[-1],3)
                        self.frame_info.atualizar_valor_pressao(valor_label_pressao)
                
            self.frame_grafico.plotar(dados, self.frame_info.sensores_ativos)
            self.after(1000, self.animacao)
    
    def obter_nparray(self, lista_valores):
        '''Arruma os dados recebidos do arduino e os retorna como uma lista de arrays do numpy
        ------------
        lista_valores (lista): Lista contendo os valores de tempo e temperatura 
        para cada sensor
        '''
        
        lista_nparray = []
        for i, valores in enumerate(lista_valores[0]):
            lista_nparray.append(np.array([valores, lista_valores[1][i]]))
        
        return lista_nparray
    
    def comando_botao_iniciar(self):
        '''Função que comando o inicio dos processos envolvendo a animação e leitura de dados'''
        if self.pode_iniciar:
            self.frame_info.obter_sensores_ativos()
            if len(self.frame_info.sensores_ativos) > 0:
                if self.menu.fonte_dados.criar_conexao():
                    if self.menu.fonte_dados.verificar_conexao():
                        
                        sensores_ativos = self.frame_info.sensores_ativos                
                        self.menu.fonte_dados.set_sensores_ativos(sensores_ativos)
                        
                        pressao_ativada = self.frame_info.variavel_checkbox_pressao.get()
                        if pressao_ativada:
                            self.menu.fonte_dados.set_leitura_pressao()
                        
                        self.menu.fonte_dados.configurar_arduino()
                        
                        self.menu.submenu_principal.entryconfigure('Salvar', state = tk.DISABLED)
                        self.menu.fonte_dados.inicializar_thread()
                        self.frame_info.alterar_checkboxes(tk.DISABLED)
                        self.iniciar_animacao()
            
            else:
                self.print_texto('Nenhum sensor selecionado!')
                print('Nenhum sensor selecionado!')
        else:
            self.print_texto('É necessário salvar os dados antes.')
            print('É necessário salvar os dados antes.')
            
    def comando_botao_parar(self):
        '''Função que termina os processos envolvendo a animação e leitura de dados
        '''
        
        if self.pode_iniciar and self.animando:
            self.terminar_animacao()
            self.menu.fonte_dados.terminar_thread()
            time.sleep(1)
            self.menu.fonte_dados.fechar_conexao() 
            self.menu.submenu_principal.entryconfigure('Salvar', state = tk.NORMAL)
            self.frame_info.alterar_checkboxes(tk.NORMAL)
            self.pode_iniciar = False
    
def main():
    root = JanelaPrincipal()
    fonte = Leitura_Arduino.Arduino()
    fonte.set_func_print(root.frame_caixa_texto.print_texto)
    
    root.menu.definir_origem_dados(fonte)
    
    root.mainloop()


if __name__ == '__main__':
    main()
