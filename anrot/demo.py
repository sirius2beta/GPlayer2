#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import anrot_module
import time


log_file = 'chlog.csv'

if __name__ == '__main__':

    m_IMU = anrot_module.anrot_module('./config.json')
    print("Press Ctrl-C to terminate while statement.")

    #uncomment following line to enable csv logger
    #m_IMU.create_csv(log_file) #uncomment this line to enable
    
    while True:
        try:
            data = m_IMU.get_module_data(10)
            
            #uncomment following line to enable csv logger
            #m_IMU.write2csv(data, log_file) 
            
            
            print(data['euler'])  #print 'euler'. It can be replaced with 'id', 'timestamp', 'acc', 'gyr', 'mag', 'quat'.
            #print(data, end="\r") #print all          

        except KeyboardInterrupt:
            print("Serial is closed.")
            m_IMU.close()
            break  
        except:   
            print("Error")
            pass