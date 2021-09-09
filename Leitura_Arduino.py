# -*- coding: utf-8 -*-
"""
Created on Fry Aug 27 11:57:22 2021

@author: Erik
"""

import time
import threading
import serial
import struct

class Arduino():
    
    def __init__(self):
        self.timeout = 0.9
        self.intervalo_entre_leituras = 1 # Em segundos
        self.temperaturas = []
        self.tempo = []
        self.gerando = False
        self.conexao_ligada = False
        self.leitura_pressao_ativada = False
        self.inicio = 0
        self.porta_COM = 'COM3'
        self.velocidade_conexao = 19200 
       
        self.tipo_tc = 'T'
        self.setpoint = 25
        self.constantes_pid = [1, 1, 0]
        self.controle_automatico = True
        self.pwm = 255;
        
        self.constante_tempo_leitura = 0.190444
        self.comunicacao = {
            'handshake': 'h',
            'leitura': 'r',
            'leitura_cj': 'c',
            'pressao': 'p',
            'tipo_TC': 's',
            'setpoint': 't',
            'constantes': 'j',
            'automatico': 'a',
            'manual': 'm',
            'retorno':'k'
            
            }
        
        self.buffer = []
        
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
            self.enviar_dados(self.comunicacao['handshake'])
            time.sleep(0.01)
            retorno = self.porta_serial.read(size = 8)
            retorno = retorno.decode()
            
            if retorno == self.comunicacao['retorno']:
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
    
    def configurar_arduino(self):
        self.set_tipo_termopar()
        self.set_point()
        self.set_constantes_pid()
        
        
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
        
            
        if self.porta_serial.isOpen():
            
            if type(dados) == str:
                dados = dados.encode()
            
                self.porta_serial.write(dados)
               
            else:
                dados_1 = int(dados)
                dados_2 = int((dados - dados_1)*10)
                
                dados_1 = bytes([dados_1])
                dados_2 = bytes([dados_2])
                        
                self.porta_serial.write(dados_1)
                self.porta_serial.write(dados_2)
        
        else:
            self.print_mensagem('Conexão não estabelecida.')
            print('Conexão não estabelecida.')
    
    def enviar_buffer(self):
        
        if self.buffer:
            funcao = self.buffer.pop(0)
            funcao()
    
    def reset_memoria(self):
        '''Apaga os valores armazenados durante a leitura
        '''
        self.tempo.clear()
        self.temperaturas.clear()
        self.tempo_ini.clear()
        self.intervalo_entre_leituras = 1
        if self.leitura_pressao_ativada:
            self.pressao.clear()
        
    
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
    
    def erros(self, leitura):
        
        if leitura == '\x00':
            self.print_mensagem('Erro: 1')
        
        elif leitura == '\x01':
            self.print_mensagem('Erro: 2')

        elif leitura == '\x02':
            self.print_mensagem('Erro: 3')
     
        elif leitura == '\x04':
            self.print_mensagem('Erro: 4')
  
        else:
            self.print_mensagem(f'Erro: Leitura desconhecida. Foi recebido: {leitura}')
        
    def ler_temperaturas(self, indice_sensor):
        '''Le as temperaturas da porta serial e, caso exista algum erro, imprime o
        erro obtido, retornando False'''
        
        self.enviar_dados(f'{indice_sensor}')
        
        leitura_junta_quente = self.porta_serial.read(size = 3)
        leitura_junta_fria = self.porta_serial.read(size = 2)
        
        
        leitura_junta_quente = leitura_junta_quente + b'\x00'
        
        if leitura_junta_quente[0:2] != b'\x80\x00':
            
            [junta_quente] = struct.unpack('>l', leitura_junta_quente)
            
            [junta_fria] = struct.unpack('>h', leitura_junta_fria)
            
            temperatura = (junta_quente + junta_fria)/1000000
            #print(temperatura)
            return temperatura
        
        else:
            leitura = leitura_junta_quente[2:3].decode()
            self.erros(leitura)
            
            return False
    
    def ler_junta_fria(self):
        leitura_junta_fria = self.porta_serial.read(size=2)
        [junta_fria] = struct.unpack('>h', leitura_junta_fria)
        
        return junta_fria
    
    def ler_tempo(self, sensor):
        '''Calcula o tempo passado desde o inicio da comunicação'''
        
        tempo = (time.time() - self.tempo_ini[sensor])
        
        return tempo    
    
    def ler_pressao(self):
        self.enviar_dados(self.comunicacao['pressao'])
        leitura_pressao = self.porta_serial.read(size = 2)
        
        [pressao] = struct.unpack('>h', leitura_pressao)
        print(pressao)
        self.pressao.append(pressao)
        
    
    def ler_dados(self):
        '''Lê os dados do arduino em um loop infinito e os armazena
        '''
        self.tempo_ini = [(time.time() - valor) for valor in self.tempo_ini ]
        while self.gerando:
            
            for i, sensor in enumerate(self.sensores_ativos):
                self.enviar_dados(self.comunicacao['leitura'])
                temperatura = self.ler_temperaturas(sensor)
                
                if temperatura:
                    self.temperaturas[i].append(temperatura)
                    
                    tempo = self.ler_tempo(i)
                    self.tempo[i].append(tempo)
                   
            if self.leitura_pressao_ativada:
                self.ler_pressao()
            
            self.enviar_buffer()
            
            time.sleep(self.intervalo_entre_leituras)
     
    def arrumar_tempo(self, tempo):
        
        return [(valor - tempo[0]) for valor in tempo]
    
    def get_dados(self):
        '''Retorna os valores de temperatura e tempo armazenados
        '''
        return [self.tempo, self.temperaturas]     
     
    def get_pressao(self):
        
        return self.pressao
     
    def set_sensores_ativos(self, sensores_ativos):
        '''Define internamente e no arduino o número de sensores que deverão ser lidos
        ----------
        sensores_ativos [lista] : Lista contendo o índice dos sensores selecionados
        '''
        self.tempo_ini = [] # <-------- Teste
        self.sensores_ativos = sensores_ativos
        for i in range(len(sensores_ativos)):
            self.temperaturas.append([])
            self.tempo.append([])
            
            self.tempo_ini.append(-(i+1)*self.constante_tempo_leitura) # <------- Teste
         
        self.intervalo_entre_leituras -= len(sensores_ativos)*self.constante_tempo_leitura # <----- Teste
            
    def set_leitura_pressao(self):
        self.leitura_pressao_ativada = True
        self.pressao = []
    
    def set_tipo_termopar(self):
        self.enviar_dados(self.comunicacao['tipo_TC'])
        self.enviar_dados(self.tipo_tc)
            
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
    
    def set_point(self):
        
        self.enviar_dados(self.comunicacao['setpoint'])
        self.enviar_dados(self.setpoint)
        resposta = self.porta_serial.readline()
        print(resposta)
    
    def set_constantes_pid(self):
        
        self.enviar_dados(self.comunicacao['constantes'])
        for valor in self.constantes_pid:
            self.enviar_dados(valor)
        
        resposta = self.porta_serial.readline()
        print(resposta)
      
    def set_controle_automatico(self):
       
        if self.gerando:
            self.enviar_dados(self.comunicacao['automatico'])
            self.controle_automatico = True
            resposta = self.porta_serial.readline()
            print(resposta)
            
    def set_controle_manual(self, pwm):
        self.pwm = pwm
        
        if self.gerando:
            self.enviar_dados(self.comunicacao['manual'])
            self.enviar_dados(self.pwm)
            resposta = self.porta_serial.readline()
            print(resposta)
            
    def set_func_print(self, func_print):
        '''Define o método que será utilizado para exibir mensagens
        ----------
        func_print (método): Método que exibirá as mensagens
        '''
        self.func_print = func_print
    
        
    
    def print_mensagem(self, mensagem):
        '''Exibe, segundo o método definida previamente, a mensagem passada.
        ----------
        mensagem (string): Mensagem que será exibida.
        '''
        #self.func_print(mensagem)  # Alterado <-------------------------------------------
        print(mensagem)

    
if __name__ == "__main__":
    
    fonte = Arduino()
    
    fonte.porta_COM = 'COM4'
    
    fonte.set_sensores_ativos([2,3])
    
    fonte.criar_conexao()
    fonte.verificar_conexao()
     
    fonte.inicializar_thread()
    
