import psutil
import platform
import pandas as pd
import mysql.connector as mysql
from datetime import datetime
import time
#Esse script pega o nome do servidor e joga para o bancoalun
print("Credenciais do banco de dados MySQL")
opcaouser = input("Digite seu usuario:")
opcaopassword = input("Digite sua senha:")
opcaodatabase = input("Digite o nome da db:")

try:
    conexao = mysql.connect(
                host="localhost",      
                user=opcaouser,
                password=opcaopassword,
                database=opcaodatabase,
            )

    cur = conexao.cursor()



except mysql.connector.Error as err:
    print(f"Erro ao conectar ao MySQL: {err}")
    exit()

print("\n")
print("\n=== Iniciando Captura de Servidor ===")
nomeMaquina = platform.node()
print(f"Nome da Máquina: {nomeMaquina}")
cur.execute(f"insert into servidor (nome_maquina) values ('{nomeMaquina}')")
conexao.commit()
print("\n=== Servidor Capturado ===")
#fim do script que captura e joga o nome do servidor para o banco

time.sleep(1)

#Esse script pega todos os componentes que estão em atividade e joga para o banco
# Informações do SO

nomeSo = platform.system()
realeaseSo = platform.release()
versaoSO = platform.version()
processador = platform.processor()
nucleosFisicos = psutil.cpu_count(logical=False)
nucleosLogicos = psutil.cpu_count(logical=True)
nomeMaquina = platform.node()

print(processador)

print("\n")
print("\n=== Iniciando Captura de componentes ===")


uso = psutil.cpu_percent(interval=1) 
ramTotal = round(psutil.virtual_memory().total / (1024**3),2)
ramUsada = psutil.virtual_memory().percent
discoTotal = round(psutil.disk_usage("/").total / (1024**3),2)
discoUsado = psutil.disk_usage("/").percent

print(f"Nome da Máquina: {nomeMaquina} | CPU: {uso}% | Ram total: {ramTotal}GB | Ram em Uso: {ramUsada}% | Disco total: {discoTotal}GB | Disco em uso: {discoUsado}%")




cur.execute(f"insert into componente (tipo, fk_servidor) select 'CPU', id from servidor where nome_maquina = '{nomeMaquina}';")
conexao.commit()
cur.execute(f"insert into componente (tipo, fk_servidor) select 'RAM', id from servidor where nome_maquina = '{nomeMaquina}';")
conexao.commit()
cur.execute(f"insert into componente (tipo, fk_servidor) select 'DISCO', id from servidor where nome_maquina = '{nomeMaquina}';")
conexao.commit()

print("\n=== Componentes capturados ===")
#fim do script que captura informações do componente

time.sleep(1)

#Esse script pega as especificações dos componentes, como quantidade de total de ram
contador = 1
qtdParticoes = 0
data = []

print("\n------- Iniciando Captura de Especificações de Hardware -------")


swapTotal = round(psutil.swap_memory().total / (1024**3),2)
ramTotal = round(psutil.virtual_memory().total / (1024**3),2)
discoTotal = round(psutil.disk_usage("/").total / (1024**3),2)
Particoes = psutil.disk_partitions()
nucleosFisicos = psutil.cpu_count(logical=False)
nucleosLogicos = psutil.cpu_count(logical=True)
timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

for item in Particoes:
    qtdParticoes += 1

print(f"Swap total: {swapTotal}")
print(f"Ram total: {ramTotal}")
print(f"Quantidade de CPUs: {nucleosFisicos}")
print(f"Quantidade de núcleos: {nucleosLogicos}")
print(f"Quantidade de partições: {qtdParticoes}")

cur.execute(f"insert into especificacao_componente (nome_especificacao, valor, fk_componente) select 'Swap total (GB)', '{swapTotal}', id from componente where tipo = 'DISCO';")
conexao.commit()
cur.execute(f"insert into especificacao_componente (nome_especificacao, valor, fk_componente) select 'Ram total (GB)', '{ramTotal}', id from componente where tipo = 'RAM';")
conexao.commit()
cur.execute(f"insert into especificacao_componente (nome_especificacao, valor, fk_componente) select 'Quantidade de núcleos fisicos', '{nucleosFisicos}', id from componente where tipo = 'CPU';")
conexao.commit()
cur.execute(f"insert into especificacao_componente (nome_especificacao, valor, fk_componente) select 'Quantidade de núcleos lógicos', '{nucleosLogicos}', id from componente where tipo = 'CPU';")
conexao.commit()
cur.execute(f"insert into especificacao_componente (nome_especificacao, valor, fk_componente) select 'Quantidade de partições', '{qtdParticoes}', id from componente where tipo = 'DISCO';")
conexao.commit()


for particao in Particoes:
    
    contador += 1
    total  = round(psutil.disk_usage("/").total / (1024**3),2)  
    print(f"QUantidade total da partição {contador}: {total}")

    usoDisco = psutil.disk_usage(particao.mountpoint)
    print(f"Endereço da partição: {particao.device}")
    print(f"Tipo do file system: {particao.fstype}")
    print(f"Endereço do mountpoint: {particao.mountpoint}")
    print(f"Opções da partição {particao.opts}")
    print(f"Uso da partição {round(usoDisco.total / (1024**3),2)}GB")

    cur.execute(f"insert into especificacao_componente (nome_especificacao, valor, fk_componente) select 'Espaço na partição {contador} (GB)', '{round(usoDisco.total / (1024**3),2)}', id from componente where tipo = 'DISCO';")
    conexao.commit()
    cur.execute("insert into especificacao_componente (nome_especificacao, valor, fk_componente) "
    "select %s, %s, id from componente where tipo = 'DISCO';",
    (f"MountPoint da partição {contador}", particao.mountpoint)
    )
    conexao.commit()


dados = {
    "Swap total ": swapTotal,
    "Ram total": ramTotal,
    "Quantidade de CPUs ": nucleosFisicos,
    "Quantidade de núcleos lógicos": nucleosLogicos,
    "Capacidade total do disco": discoTotal,
    "Quantidade de partições do disco": qtdParticoes,
    "Data e hora da captura": timestamp
}




data.append(dados)



df1 = pd.DataFrame(data = data)

df1.to_csv('EspecificacoesHardware.csv',sep=';')

print("------- Especificações capturadas -------")

# Fim do script de captura de especificações