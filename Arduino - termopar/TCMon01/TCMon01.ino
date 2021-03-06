#include <PID_v1.h>
#include <SPI.h>
#include "NanoshieldTermoparMod.h"

// Termopar Nanoshield on CS pin D8, type T thermocouple, no averaging
NanoshieldTermoparMod tc(8, TC_TYPE_T, TC_AVG_OFF);

//Define Variables for PID controller
double Setpoint, Input, Output;

//Specify PID initial constants - ki, kp, kd, and directon
PID PID_controller(&Input, &Output, &Setpoint, 10, 5, 0, REVERSE);

uint32_t lpc;
uint16_t cj;
uint16_t pressao;

void setup()
{
    Serial.begin(19200,SERIAL_8N1);
    tc.beginManualMode();
    pinMode(9, OUTPUT);
    pinMode(6, OUTPUT);    
    pinMode(5, OUTPUT);
    
    pinMode(4, OUTPUT);
    digitalWrite(4,HIGH);
    pressao = analogRead(5);

    //Pino 3 de Saída PWM 490.2 Hz
    pinMode(3, OUTPUT);
    
    //Garantindo que a placa está desligada
    digitalWrite(3, HIGH);
    
    //Alterando a frequancia do PWM para 30.64 Hz
    TCCR2B = TCCR2B & B11111000 | B00000111;

    Setpoint = 10;
    Output = 255;
    
    //turn the PID on
    //PID_controller.SetMode(AUTOMATIC);

    
}

void setaMux(char c) {    
     c = c - 0x30;
     digitalWrite(5, c & 0x01);
     digitalWrite(6, (c & 0x02) >> 1);    
     digitalWrite(9, (c & 0x04) >> 2);                   
     delay(10); 
}

void printErrors() {
    Serial.write(0x80);
    Serial.write(0x00);
    
    if (tc.isOpen()) {
        Serial.write(0x00);
    } else if (tc.isOverUnderVoltage()) {
        Serial.write(0x01);
    } else if (tc.isInternalOutOfRange()) {
        Serial.write(0x02);
    } else if (tc.isExternalOutOfRange()) {
        Serial.write(0x04);
    } 
    
    Serial.write(cj >> 8);
    Serial.write(cj & 0xFF);
}

void printData() {
    lpc = tc.getExternalBytes();
    cj = tc.getInternalBytes();
                   
    Serial.write(lpc >> 24);
    Serial.write((lpc >> 16) & 0xFF);
    Serial.write((lpc >> 8) & 0xFF);

    Serial.write(cj >> 8);
    Serial.write(cj & 0xFF); 

}

void set_pid_constants(){
    
    float kp = readFloat();
    float ki = readFloat();
    float kd = readFloat();

    PID_controller.SetTunings(kp, ki, kd);

}

void control(int sensor){
    
    setaMux(sensor);
    tc.manualRead();
    if (tc.hasError()) {
        //Desligando placa
        Output = 255;
        
    } else {  
        lpc = tc.getExternalBytes(); 
        Input = (double) lpc/pow(2,20);
        PID_controller.Compute();
    }
    
}

double readFloat(){
  char inBytes;
  float number = 0.0;
  int i;
  int n_Bytes = 2;

  for(i=0; i<n_Bytes; i++){
      inBytes = Serial.read();
      number += inBytes*pow(10,-i);  
    }
  return number;
}


char data;
void loop()
{   

    if (Serial.available() > 0) {
  
       data = Serial.read();
       
       if (data == 'h') { // Handshake
        
            Serial.write('k');
             
       } else if (data == 'r') { // Read termocouple 
         
            delay(5);
            data = Serial.read();
            setaMux(data); // TODO: Acertar delay          
            tc.manualRead();  
            if (tc.hasError()) {
                printErrors();
            } else {  
                printData();
            }                           
            
        } else if (data == 'c') { // Read cold junction 
          
            tc.read();
            cj = tc.getInternalBytes();
            Serial.write(cj >> 8);
            Serial.write(cj & 0xFF); 
            
        } else if (data == 's') {

            delay(5);
            data = Serial.read();
            switch (data) {
                case 'T': tc.setType(TC_TYPE_T); break;
                case 'B': tc.setType(TC_TYPE_B); break;
                case 'E': tc.setType(TC_TYPE_E); break;
                case 'J': tc.setType(TC_TYPE_J); break;
                case 'K': tc.setType(TC_TYPE_K); break;
                case 'N': tc.setType(TC_TYPE_N); break;
                case 'R': tc.setType(TC_TYPE_R); break;
                case 'S': tc.setType(TC_TYPE_S); break;
                default: tc.setType(TC_TYPE_T);
            }            
            
        } else if (data == 'p') {
            
            pressao = analogRead(5);
            Serial.write(pressao >> 8);
            Serial.write(pressao & 0xFF);  
        
        } else if (data == 'j'){
 
            set_pid_constants();
            //Eco
            Serial.println(PID_controller.GetKp());

        }
         else if (data == 'a'){
     
              delay(5);
              Setpoint = (double)Serial.read();
              control(3);
              PID_controller.SetMode(AUTOMATIC);           
              analogWrite(3,(int)Output);
              
        } else if (data == 'm'){
              
              delay(5);
              Output = Serial.read();
              PID_controller.SetMode(AUTOMATIC);
              analogWrite(3,(int)Output);
  
        }
    
    } else{
      //Output = 255;
    
    }
          
    
    
    Serial.flush();
      
}
