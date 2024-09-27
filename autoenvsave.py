import os
import configparser

def getenv(name, defualt=''):
    value = ''

    conf = configparser.ConfigParser()
    conf.read('env.ini')

    osenv = os.getenv(name)
    if osenv:
        value = osenv
        if conf.get('env', name, fallback='') != osenv:
            if not conf.has_section('env'):
                conf.add_section('env')
            conf.set('env', name, value)
            with open('env.ini', 'w') as configfile:
                conf.write(configfile)
                configfile.close()
    else:
        value = conf.get('env', name, fallback='')

    if not value:
        value = defualt

    return value
