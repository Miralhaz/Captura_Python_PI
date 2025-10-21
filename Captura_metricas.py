import psutil
import pandas as pd
import time
from datetime import datetime
import mysql.connector as mysql

duracao = int(input("Digite a duração da captura: "))
contador = 0


arquivo_csv = "dados.csv"
processos = "processos.csv"

processos = []
data = []

print("Credenciais do banco de dados MySQL")


try:
    conexao = mysql.connect(
                host="localhost",      
                user='aluno',
                password='20212412Wi@',
                database='teste'
            )

except mysql.connector.Error as err:
    print(f"Erro ao conectar ao MySQL: {err}")
    exit()

cur = conexao.cursor()

print("\nIniciando monitoramento...")
print("\n------- CAPTURA DE CPU, RAM E DISCO -------")

while contador < duracao:
    user = psutil.users()[0].name
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cpu = psutil.cpu_percent()  
    ram = psutil.virtual_memory().percent  
    disco = psutil.disk_usage("/").percent  
    temperatura_cpu = psutil.sensors_temperatures(fahrenheit = False)
    temperatura_disco = psutil.sensors_temperatures(fahrenheit = False)
    memoria_swap = round(psutil.swap_memory().used / (1024 * 1024), 2)
    processos_maquina = psutil.process_iter()

    processos_list = list(processos_maquina)
    quantidade_processos = len(processos_list)

    local_cpu = temperatura_cpu['coretemp']
    cpu_sensor = local_cpu[0]
    temperatura_cpu_atual = cpu_sensor.current

    local_disco = temperatura_disco['nvme']
    disco_sensor = local_disco[0]
    temperatura_disco_atual = disco_sensor.current

    dado = {
        'user': user
        ,'timestamp':timestamp
        ,'cpu': cpu
        ,'ram': ram
        ,'disco': disco
        ,'temperatura_cpu': temperatura_cpu_atual
        ,'temperatura_disco': temperatura_disco_atual
        ,'memoria_swap': memoria_swap
        ,'quantidade_processos': quantidade_processos
    }
 
    # Salva no CSV
    data.append(dado)


    print(f"\n Usuário: {user} | {timestamp} | CPU: {cpu}% | RAM: {ram}% | Disco: {disco}% | Temperatura CPU: {temperatura_cpu_atual}ºC | Temperatura Disco: {temperatura_disco_atual}ºC | Memória Swap: {memoria_swap}% | Quantidade de processos: {quantidade_processos}")
  

    for proc in psutil.process_iter():
        dado = {
        'timestamp':timestamp
        ,'processo': proc.name()
        ,'pid': proc.pid
        ,'cpu':proc.cpu_percent()
        ,'ram': round(proc.memory_percent(),4)
    }
        processos.append(dado)

    # DADOS CPU
    cur.execute(f"insert into medicao (nome_medicao, medicao, unidade_medida, fk_componente) select 'Temperatura', '{temperatura_cpu_atual}', '°C', id from componente where tipo = 'CPU'")
    conexao.commit()
    cur.execute(f"insert into medicao (nome_medicao, medicao, unidade_medida, fk_componente) select 'Uso', '{cpu}', '%', id from componente where tipo = 'CPU'")
    conexao.commit()
    # DADOS RAM
    cur.execute(f"insert into medicao (nome_medicao, medicao, unidade_medida, fk_componente) select 'RAM', '{ram}','%', id from componente where tipo = 'CPU'")
    conexao.commit()
    # DADOS DISCO
    cur.execute(f"insert into medicao (nome_medicao, medicao, unidade_medida, fk_componente) select 'Temperatura', '{temperatura_disco_atual}', '°C', id from componente where tipo = 'DISCO'")
    conexao.commit()
    cur.execute(f"insert into medicao (nome_medicao, medicao, unidade_medida, fk_componente) select 'Uso', '{disco}', '%', id from componente where tipo = 'DISCO'")
    conexao.commit()
    contador+=1
    time.sleep(1)

    

df1 = pd.DataFrame(data = data)

df1.to_csv('data.csv',sep=';')

df = pd.DataFrame(data = processos)

df.to_csv('processos.csv',sep=';')

print("\n------- CAPTURA DE PROCESSOS -------\n")
print(df) 


print("Finalizando monitoramento...")