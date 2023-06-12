#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import anrot_module
import time


log_file = 'chlog.csv'

if __name__ == '__main__':

    m_IMU = anrot_module.anrot_module('./config.json')

    while True:
        try:
            data = m_IMU.get_module_data(10)
            Y_rot = data['euler'][0]['Roll']
            X_rot = data['euler'][0]['Pitch']
            Z_rot = data['euler'][0]['Yaw']
            print(f'{Y_rot}, {X_rot}, {Z_rot}')          

        except KeyboardInterrupt:
            print("Serial is closed.")
            m_IMU.close()
            break  
        except:   
            print("Error")
            pass