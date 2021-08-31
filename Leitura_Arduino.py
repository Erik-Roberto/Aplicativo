# -*- coding: utf-8 -*-
"""
Created on Sat Apr 24 11:57:22 2021

@author: Erik
"""
#==============================================================================
'''Ajustar valores de tempo para maior precisão
'''
#==============================================================================


import time
import threading
import serial

class Arduino():
    
    def __init__(self):
        self.timeout = 0.9
        self.intervalo_entre_leituras = 0.2 # Em segundos
        self.temperaturas = []
        self.tempo = []
        self.gerando = False
        self.conexao_ligada = False
        self.leitura_pressao_ativada = False
        self.inicio = time.time()
        self.porta_COM = 'COM3'
        self.velocidade_conexao = 19200 
        
    def criar_conexao(self):
        '''Cria a conexão serial com o Arduino
        ----------
        return: Retorna True caso haja sucesso e False caso tenha ocorrido algum erro
        '''
        try:
            self.porta_serial = serial.Serial(self.porta_COM,
                                              self.velocidade_conexao,
                                              timeout = self.timeout)
            return True
       
        except:
            self.print_mensagem('Erro ao abrir a porta, verifique a conexão USB.')
            print('Erro ao abrir a porta, verifique a conexão USB.')
            return False
    
    def verificar_conexao(self):
        '''Verifica se a conexão com o arduino está funcional enviando uma string e recebendo sua resposta
        ----------
        return: Retorna True caso a comunicação seja bem sucedida e False caso contrário
        '''
        tempo_espera = 1.6 #Espera x segundos antes de iniciar comunicação
        
        time.sleep(tempo_espera)
        
        if self.porta_serial.isOpen():
            self.enviar_dados('h')  #Enviando o handshake
            time.sleep(0.01)
            retorno = self.porta_serial.read(size = 8)
            retorno = retorno.decode()
            
            if retorno == 'k':
                self.conexao_ligada = True
                self.print_mensagem('Conexão estabelecida.')
                print('Conexão estabelecida.')
                return True
           
            else:
                self.print_mensagem(f'Falha na comunicação, foi recebido: {retorno}')
                print(f'Falha na comunicação, foi recebido: {retorno}')
                return False
        
        else:
            self.print_mensagem('Falha na abertura da conexão.')
            print('Falha na abertura da conexão.')
            return False
    
    def fechar_conexao(self):
        '''Fecha a conexão com o Arduino, liberando a porta serial
        -------
        '''
        if self.porta_serial.isOpen():
            self.porta_serial.close()
            self.print_mensagem('Conexão fechada.')
            print('Conexão fechada.')
        
        else:
            self.print_mensagem('Conexão já está fechada.')
            print('Conexão já está fechada.')
    
    def enviar_dados(self, dados):
        '''Função responsável por enviar dados para o arduino
        ----------
        dados (string): Dados que serão enviados para o arduino
        '''
        dados = dados.encode()
        
        if self.porta_serial.isOpen():
            self.porta_serial.write(dados)
        
        else:
            self.print_mensagem('Conexão não estabelecida.')
            print('Conexão não estabelecida.')
   
    def set_sensores_ativos(self, sensores_ativos):
        '''Define internamente e no arduino o número de sensores que deverão ser lidos
        ----------
        sensores_ativos [lista] : Lista contendo o índice dos sensores selecionados
        '''
        self.sensores_ativos = sensores_ativos
        for _ in sensores_ativos:
            self.temperaturas.append([])
            self.tempo.append([])
            
    def reset_memoria(self):
        '''Apaga os valores armazenados durante a leitura
        '''
        self.tempo.clear()
        self.temperaturas.clear()
    
    def inicializar_thread(self):
        '''Inicializa a thread responsáveel pela leitura dos dados
        '''
        self.gerando = True
        self.thread = threading.Thread(target = self.ler_dados)
        self.thread.start()        
        self.inicio = time.time()
        
    def terminar_thread(self):
        '''Finaliza a thread responsáveel pela leitura dos dados
        '''
        self.gerando = False
        self.print_mensagem('Thread terminada.')
        print('Thread terminada.')
    
    def ler_temperaturas(self, indice_sensor):
        
    
        self.enviar_dados(f'{indice_sensor}')
        leitura = self.porta_serial.read(size = 32).decode()
        leitura = leitura.split('\r\n')[0]
    
        try:
            temperatura = float(leitura)/1000000
            return temperatura
        
        except:
            
            if leitura == 'U':
                self.print_mensagem('Erro: 1')
                return False
            
            elif leitura == 'D':
                self.print_mensagem('Erro: 2')
                return False
            
            elif leitura == 'T':
                self.print_mensagem('Erro: 3')
                return False
            
            elif leitura == 'Q':
                self.print_mensagem('Erro: 4')
                return False
            
            else:
                self.print_mensagem('Erro: Leitura desconhecida')
                return False

     
    def ler_tempo(self):

        tempo = (time.time() - self.inicio)    
        
        return tempo    
    
    def ler_pressao(self):
        pass
    
    
    def ler_dados(self):
        '''Lê os dados do arduino em um loop infinito e os armazena
        '''
        while self.gerando:
            
            for i, sensor in enumerate(self.sensores_ativos):
                self.enviar_dados('r')
                temperatura = self.ler_temperaturas(sensor)
                
                if temperatura:
                    self.temperaturas[i].append(temperatura)
                    
                    tempo = self.ler_tempo()
                    self.tempo[i].append(tempo)
                    
            if self.leitura_pressao_ativada:
                self.ler_pressao()
            
            time.sleep(self.intervalo_entre_leituras)
     
        
    def get_dados(self):
        '''Retorna os valores de temperatura e tempo armazenados
        '''
        return [self.tempo, self.temperaturas]    
    
    def set_porta_COM(self, porta_COM):
        '''Define a porta COM na qual será criada a conexão serial, padrão: COM3
        ----------
        porta_COM (string): Nome da porta
        '''
        self.porta_COM = porta_COM
        
    def set_velocidade_conexao(self, velocidade_conexao):
        '''Define a velocidade de conexão serial, padrão: 9600
        ----------
        velocidade_conexao (int) : Inteiro que define a velocidade de conexão.
        '''
        self.velocidade_conexao = velocidade_conexao
        
    def considerar_offset_tempo(self):
        tempo_inicial = self.tempo
        
        for i in range(0,len(self.tempo)):
            self.tempo[i] = self.tempo[i] - tempo_inicial
            
    def print_mensagem(self, mensagem):
        '''Exibe, segundo o método definida previamente, a mensagem passada.
        ----------
        mensagem (string): Mensagem que será exibida.
        '''
        #self.func_print(mensagem)  # Alterado <-------------------------------------------
        print(mensagem)
        
    def set_func_print(self, func_print):
        '''Define o método que será utilizado para exibir mensagens
        ----------
        func_print (método): Método que exibirá as mensagens
        '''
        self.func_print = func_print


if __name__ == "__main__":
    
    fonte = Arduino()
    
    fonte.porta_COM = 'COM4'
    
    fonte.set_sensores_ativos([2, 3])
    
    #fonte.criar_conexao()
    #fonte.verificar_conexao()
     
     #fonte.inicializar_thread()
    
