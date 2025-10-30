import psutil
import platform
import pandas as pd
import mysql.connector as mysql
from datetime import datetime
import time
import socket
import boto3

# resgatando ip da maquina
ipmaq = 0.0
def obter_ip_maquina():
    # Função para pegar IP Ipv4 da máquina
    for interface, enderecos in psutil.net_if_addrs().items():
        for endereco in enderecos:
            if endereco.family == socket.AF_INET and not endereco.address.startswith('127.'):
                return endereco.address
    return None
# Exemplo de uso
ip = obter_ip_maquina()
if ip:
    print(f"O IP da sua máquina Ubuntu é: {ip}")
    ipmaq = ip
else:
    print("Não foi possível encontrar um endereço IP válido. Verifique se há uma conexão de rede ativa.")


print("Credenciais do banco de dados MySQL")
opcaouser = "aluno"
opcaopassword = "suasenha@"
opcaodatabase = "infomotion"

try:
    conexao = mysql.connect(
                host="localhost",      
                user=opcaouser,
                password=opcaopassword,
                database=opcaodatabase,
            )

    cur = conexao.cursor()


except mysql.Error as err:
    print(f"Erro ao conectar ao MySQL: {err}")
    exit()

print("\n")
print("\n=== Iniciando Captura de Servidor ===")
nomeMaquina = platform.node()
print(f"Nome da Máquina: {nomeMaquina}")
# Cadastra servidor no banco
cur.execute("SELECT id FROM servidor WHERE apelido = %s", (nomeMaquina,))
resultado_select = cur.fetchone()

if resultado_select:
    id_servidor = resultado_select[0]
    print(f"Servidor já cadastrado com ID {id_servidor}")
else:
    cur.execute("INSERT INTO servidor (apelido,ip) VALUES (%s, %s)", (nomeMaquina, ipmaq))
    conexao.commit()
    cur.execute("SELECT LAST_INSERT_ID()")
    id_servidor = cur.fetchone()[0]
    print(f"Servidor cadastrado com ID {id_servidor}")

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


# Modelado para bd Infomotion
sql = """
INSERT INTO infomotion.componentes 
(tipo, fk_servidor, numero_serie, apelido, ativo)
VALUES (%s, %s, %s, %s, %s)
"""

valores = ('CPU', id_servidor, 1, 'CPU_RYZEN5', 1)

cur.execute(sql, valores)
conexao.commit()

print("\n=== Componentes capturados ===")
#fim do script que captura informações do componente

time.sleep(1)


#Esse script pega as especificações dos componentes, como quantidade de total de ram e numero de nucléos
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

cur.execute(f"insert into especificacao_componente (nome_especificacao, valor, fk_componente) select 'Swap total (GB)', '{swapTotal}', id from componentes where tipo = 'DISCO';")
conexao.commit()
cur.execute(f"insert into especificacao_componente (nome_especificacao, valor, fk_componente) select 'Ram total (GB)', '{ramTotal}', id from componentes where tipo = 'RAM';")
conexao.commit()
cur.execute(f"insert into especificacao_componente (nome_especificacao, valor, fk_componente) select 'Capacidade total disco (GB)', '{discoTotal}', id from componentes where tipo = 'DISCO';")
conexao.commit()
cur.execute(f"insert into especificacao_componente (nome_especificacao, valor, fk_componente) select 'Quantidade de núcleos fisicos', '{nucleosFisicos}', id from componentes where tipo = 'CPU';")
conexao.commit()
cur.execute(f"insert into especificacao_componente (nome_especificacao, valor, fk_componente) select 'Quantidade de núcleos lógicos', '{nucleosLogicos}', id from componentes where tipo = 'CPU';")
conexao.commit()
cur.execute(f"insert into especificacao_componente (nome_especificacao, valor, fk_componente) select 'Quantidade de partições', '{qtdParticoes}', id from componentes where tipo = 'DISCO';")
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

    cur.execute(f"insert into especificacao_componente (nome_especificacao, valor, fk_componente) select 'Espaço na partição {contador} (GB)', '{round(usoDisco.total / (1024**3),2)}', id from componentes where tipo = 'DISCO';")
    conexao.commit()
    cur.execute("insert into especificacao_componente (nome_especificacao, valor, fk_componente) "
    "select %s, %s, id from componentes where tipo = 'DISCO';",
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

time.sleep(1)



#Inicio do script de metricas para o banco de dados
contador = 0

arquivo_csv = "dados.csv"
processos = "processos.csv"

processos = []
data = []

print("\nIniciando monitoramento...")
print("\n------- CAPTURA DE CPU, RAM E DISCO -------")

cur.execute("""
    DELETE FROM registro_servidor
    WHERE id NOT IN (
        SELECT id FROM (
            SELECT id FROM registro_servidor ORDER BY dt_registro DESC LIMIT 200
        ) as t
    )
""")
conexao.commit()
duracao = 0
while (duracao < 4):
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
        'fk_servidor': id_servidor
        ,'nomeMaquina': nomeMaquina
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
    time.sleep(2)
    print(f"\n ID Servidor: {id_servidor} | Usuário: {nomeMaquina} | {timestamp} | CPU: {cpu}% | RAM: {ram}% | Disco: {disco}% | Temperatura CPU: {temperatura_cpu_atual}ºC | Temperatura Disco: {temperatura_disco_atual}ºC | Memória Swap: {memoria_swap}% | Quantidade de processos: {quantidade_processos}")
  
    for proc in psutil.process_iter():
        dado = {
        'timestamp':timestamp
        ,'processo': proc.name()
        ,'pid': proc.pid
        ,'cpu':proc.cpu_percent()
        ,'ram': round(proc.memory_percent(),4)
    }
        processos.append(dado)

    # Modelado para bd Infomotion
    cur.execute(f"insert into registro_servidor (fk_servidor, uso_cpu, uso_ram, uso_disco, qtd_processos, temp_cpu, temp_disco) select 1, '{cpu}', {ram}, '{disco}', {quantidade_processos}, {temperatura_cpu_atual}, {temperatura_disco_atual}")
    conexao.commit()

    duracao+=1
    time.sleep(1)

    df1 = pd.DataFrame(data = data)

    df1.to_csv('data.csv',sep=';')

df = pd.DataFrame(data = processos)

df.to_csv('processos.csv',sep=';')

print("\n------- CAPTURA DE PROCESSOS -------\n")
print(df) 


print("Finalizando monitoramento...")
# Fim do script de capturar metricas
# Enviando o CSV para o bucket na ac2

s3 = boto3.client('s3')
# # Configurar a AWS Credentials antes de rodar, e criar bucket antes de tudo

nome_bucket = 's3-raw-infomotion'

s3.upload_file('data.csv', nome_bucket, 'data.csv')
s3.upload_file('processos.csv', nome_bucket, 'processos.csv')

print("CSV enviado com sucesso!!")

# CSV enviado para a pasta CSVs-registrados dentro do bucket RAW