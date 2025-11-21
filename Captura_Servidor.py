import psutil
import platform
import pandas as pd
import mysql.connector as mysql
from datetime import datetime
import time
import socket
import boto3
from geopy.geocoders import Nominatim
import requests
import random

# resgatando ip da maquina
ipmaq = 0.0
def obter_ip_maquina():
    # Função arap pegar IP Ipv4 da máquina
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
opcaouser = "root"
opcaopassword = "041316miralha"
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

id_empresa = 1
id_regiao = 4
id_gestor = 1

# Cadastra servidor no banco
cur.execute("SELECT id, fk_empresa, fk_regiao FROM servidor WHERE apelido = %s", (nomeMaquina,))

resultado_select = cur.fetchone()

if resultado_select:
    id_servidor = resultado_select[0]
    fk_empresa = resultado_select[1]
    fk_regiao = resultado_select[2]
    print(f"Servidor já cadastrado com ID {id_servidor}")

    if fk_regiao is None or fk_regiao != id_regiao: 
        cur.execute("UPDATE servidor SET fk_regiao = %s WHERE id = %s", (id_regiao, id_servidor))
        conexao.commit()

    if fk_empresa is None or fk_empresa != id_empresa: 
        cur.execute("UPDATE servidor SET fk_empresa = %s WHERE id = %s", (id_empresa, id_servidor))
        conexao.commit()

else:
    cur.execute("INSERT INTO servidor (apelido, ip, fk_empresa, ativo) VALUES (%s, %s, %s, %s)", (nomeMaquina, ipmaq, id_empresa, 1))
    conexao.commit()
    cur.execute("SELECT LAST_INSERT_ID()")
    id_servidor = cur.fetchone()[0]
    print(f"Servidor cadastrado com ID {id_servidor}")


sql_associacao = """
    INSERT INTO usuario_has_servidor (fk_usuario, fk_servidor) 
    VALUES (%s, %s)
    ON DUPLICATE KEY UPDATE fk_usuario = fk_usuario;
"""

cur.execute(sql_associacao, (id_gestor, id_servidor))
conexao.commit()

# buscando dados de região
cur.execute("select fk_regiao from servidor where id = %s",(id_servidor,))
resultado_select = cur.fetchone() 
regiao = resultado_select[0]

cur.execute("select cidade,pais,codigo_postal from regiao where id = %s",(regiao,))
resultado_select = cur.fetchone() 

cidade = resultado_select[0]
pais = resultado_select[1]
cep = resultado_select[2]


regiao_inteira = f"{cep},{cidade},{pais}"
geo = Nominatim(user_agent="agente_que_busca_coordenada")
coordenada = geo.geocode(regiao_inteira)
print(coordenada)
print(coordenada.latitude)
print(coordenada.longitude)

# open-meteo api para buscar dados de clima
def obter_clima(latitude, longitude):
    url_api_meteo = "https://api.open-meteo.com/v1/forecast?"

    params = {
	    "latitude":latitude ,
	    "longitude":longitude,
    	"hourly": ["precipitation", "precipitation_probability", "weather_code", "temperature_2m", "relative_humidity_2m"], 
        "past_days": 7,
        "forecast_days": 16,
              }
    try:
        resposta = requests.get(url_api_meteo, params=params)
        if resposta.status_code == 200:
            dados_clima = resposta.json()
            return dados_clima
        else:
            print("Erro ao receber dados")
            return None
    except requests.exceptions.RequestException  as e:
      print("Erro em obter clima" + e )
      return None


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

cur.execute("select * from componentes where fk_servidor = %s",(id_servidor,))
resultado_select = cur.fetchall()

param_cpu = '79'
param_ram = '61'
param_disco = '52'
duracao = '0'
unidade = '%'

if len(resultado_select) <= 0:

    sql = """
    INSERT INTO infomotion.componentes 
    (fk_servidor, tipo, numero_serie, apelido, ativo)
    VALUES (%s, %s, %s, %s, %s)
    """

    sql_parametro = """
    INSERT INTO infomotion.parametro_alerta 
    (fk_servidor, fk_componente, max, duracao_min, unidade_medida)
    VALUES (%s, %s, %s, %s, %s)
    """
    

    valores = (id_servidor, 'REDE', 72, 'Intel I350-T4', 1)
    cur.execute(sql, valores)
    conexao.commit()
    cur.execute("SELECT LAST_INSERT_ID()")
    id_componente_rede = cur.fetchone()[0]

    valores_parametro_rede = (id_servidor, id_componente_rede, 50000, 12, 'DOWNLOAD')
    cur.execute(sql_parametro, valores_parametro_rede)
    conexao.commit()

    valores_parametro_rede = (id_servidor, id_componente_rede, 50000, 12, 'UPLOAD')
    cur.execute(sql_parametro, valores_parametro_rede)
    conexao.commit()

    valores_parametro_rede = (id_servidor, id_componente_rede, 500, 12, 'PCKT_RCVD')
    cur.execute(sql_parametro, valores_parametro_rede)
    conexao.commit()
        
    valores_parametro_rede = (id_servidor, id_componente_rede, 500, 12, 'PCKT_SNT')
    cur.execute(sql_parametro, valores_parametro_rede)
    conexao.commit() 
    

    valores = (id_servidor, 'CPU', 1, 'CPU_ryzen5', 1)
    cur.execute(sql, valores)
    conexao.commit()
    cur.execute("SELECT LAST_INSERT_ID()")
    id_componente_cpu = cur.fetchone()[0]
    valores_parametro_cpu = (id_servidor, id_componente_cpu, param_cpu, duracao, unidade)
    cur.execute(sql_parametro, valores_parametro_cpu)
    conexao.commit()

    valores = (id_servidor, 'RAM', 1, 'RAM_slot1', 1)
    cur.execute(sql, valores)
    conexao.commit()
    cur.execute("SELECT LAST_INSERT_ID()")
    id_componente_ram = cur.fetchone()[0]
    valores_parametro_ram = (id_servidor, id_componente_ram, param_ram, duracao, unidade)
    cur.execute(sql_parametro, valores_parametro_ram)
    conexao.commit()

    valores = (id_servidor, 'DISCO', 1, 'DISCO_SATA1', 1)
    cur.execute(sql, valores)
    conexao.commit()
    cur.execute("SELECT LAST_INSERT_ID()")
    id_componente_disco = cur.fetchone()[0]
    valores_parametro_disco = (id_servidor, id_componente_disco, param_disco, duracao, unidade)
    cur.execute(sql_parametro, valores_parametro_disco)
    conexao.commit()

print("\n=== Componentes capturados ===")
#fim do script que captura informações do componente

time.sleep(1)


#Esse script pega as especificações dos componentes, como quantidade de total de ram e numero de nucléos
contador = 1
qtdParticoes = 0
data = []

print("\n------- Iniciando Captura de Especificações de Hardware -------")
print(id_servidor)
cur.execute("select nome_especificacao from especificacao_componente inner join componentes on componentes.id = especificacao_componente.fk_componente where fk_servidor = %s",(id_servidor,))
resultado_select = cur.fetchall() 

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

if len(resultado_select) <= 0:
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

    if len(resultado_select) <= 0:
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

df1.to_csv(f'EspecificacoesHardware{id_servidor}.csv',sep=';')

print("------- Especificações capturadas -------")
# Fim do script de captura de especificações

time.sleep(1)



#Inicio do script de metricas para o banco de dados
contador = 0


processos = []
data = []
data_conex = []


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
temp_cpu_base = 45.0
temp_disco_base = 35.0
while (duracao < 20):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cpu = psutil.cpu_percent()  
    ram = psutil.virtual_memory().percent  
    disco = psutil.disk_usage("/").percent  
    variacao_cpu = random.uniform(-2.0, 5.0)
    temperatura_cpu_atual = round(temp_cpu_base + variacao_cpu + (cpu * 0.2), 2)
    variacao_disco = random.uniform(-1.0, 2.0)
    temperatura_disco_atual = round(temp_disco_base + variacao_disco, 2)
    memoria_swap = round(psutil.swap_memory().used / (1024 * 1024), 2)
    processos_maquina = psutil.process_iter()
    processos_list = list(processos_maquina)
    quantidade_processos = len(processos_list)
    net = psutil.net_io_counters(pernic=True)
    bytes_recebidos =  net['Wi-Fi'].bytes_recv 
    bytes_enviados = net['Wi-Fi'].bytes_sent
    pacotes_recebidos =  net['Wi-Fi'].packets_recv
    pacotes_enviados =  net['Wi-Fi'].packets_sent
    dropin = net["Wi-Fi"].dropin
    dropout = net["Wi-Fi"].dropout
    leitura_escrita_disco = psutil.disk_io_counters(perdisk=False, nowrap=True)
    numero_leituras = leitura_escrita_disco.read_count
    numero_escritas = leitura_escrita_disco.write_count
    bytes_lidos = leitura_escrita_disco.read_bytes
    bytes_escritos = leitura_escrita_disco.write_bytes
    tempo_leitura = leitura_escrita_disco.read_time
    tempo_escrita = leitura_escrita_disco.write_time
    

   
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
        ,'donwload_bytes':bytes_recebidos
        ,'upload_bytes':bytes_enviados
        ,'pacotes_recebidos' : pacotes_recebidos
        ,'pacotes_enviados':pacotes_enviados  
        ,'dropin':dropin
        ,'dropout':dropout
        ,'numero_leituras':numero_leituras
        ,'numero_escritas':numero_escritas
        ,'bytes_lidos':bytes_lidos
        ,'bytes_escritos':bytes_escritos
        ,'tempo_leitura':tempo_leitura
        ,'tempo_escrita':tempo_escrita

    }
 
    # Salva no CSV
    data.append(dado)
    time.sleep(2)
    print(f"\n ID Servidor: {id_servidor} | Usuário: {nomeMaquina} | {timestamp} | CPU: {cpu}% | RAM: {ram}% | Disco: {disco}% | Temperatura CPU: {temperatura_cpu_atual}ºC | Temperatura Disco: {temperatura_disco_atual}ºC | Memória Swap: {memoria_swap}% | Quantidade de processos: {quantidade_processos} | Velocidade de Download: {bytes_recebidos} | Velocidade de Upload: {bytes_enviados}") 
    for proc in psutil.process_iter():
        try:
            dado_proc = {
                'fk_servidor': id_servidor
                ,'timestamp':timestamp
                ,'processo': proc.name()
                ,'pid': proc.pid
                ,'cpu': proc.cpu_percent()
                ,'ram': round(proc.memory_percent(),4)
            }
            processos.append(dado_proc)
        except psutil.NoSuchProcess:
            continue
        except Exception as e:
            print(f"Aviso: Erro inesperado ao coletar dado do processo {proc.pid}: {e}")
            continue

    # Modelado para bd Infomotion
    sql_insert_registro = """
        INSERT INTO registro_servidor (
            fk_servidor, uso_cpu, uso_ram, uso_disco, qtd_processos, 
            temp_cpu, temp_disco, upload, download, dt_registro
        ) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    
    valores_registro = (
        id_servidor, cpu,         
        ram, disco, quantidade_processos, 
        temperatura_cpu_atual, temperatura_disco_atual, 
        bytes_enviados, bytes_recebidos, timestamp
    )
    
    cur.execute(sql_insert_registro, valores_registro)
    conexao.commit()

    duracao+=1
    time.sleep(1)

    df= pd.DataFrame(data = data)

    data_arquivo = datetime.now().strftime("%Y-%m-%d")

    df.to_csv(f'data{id_servidor}.csv',sep=';')
    df.to_csv(f'data{id_servidor}-{data_arquivo}.csv')
print(df) 


df1 = pd.DataFrame(data = processos)

df1.to_csv(f'processos{id_servidor}.csv',sep=';')
df1.to_csv(f'processos{id_servidor}-{data_arquivo}.csv')
print(df1) 


for c in psutil.net_connections(kind='inet'):
    if c.family == socket.AF_INET and c.type == socket.SOCK_STREAM:
        conex = {
            'fk_servidor':id_servidor
            ,'timestamp':timestamp
            ,'pid':c.pid
            ,'familia':c.family
            ,'tipo':c.type
            ,'laddr':c.laddr
            ,'status':c.status
        }
        data_conex.append(conex)
df2 = pd.DataFrame(data = data_conex)

df2.to_csv(f'conexoes{id_servidor}.csv',sep=';')
df2.to_csv(f'conexoes{id_servidor}-{data_arquivo}.csv',sep=';')

print(df2) 

print("\n------- CAPTURA DE PROCESSOS -------\n")


lat = coordenada.latitude
lon = coordenada.longitude
clima = obter_clima(lat,lon)
hourly = clima['hourly']
hourly["latitude"] = lat
hourly["longitude"] = lon
hourly["regiao"] = regiao
    
df3 = pd.DataFrame(data = hourly)
df3.to_csv(f'clima{id_servidor}.csv',sep=';')
print(df3)

print("Finalizando monitoramento...")
# Fim do script de capturar metricas
# Enviando o CSV para o bucket na ac2

s3 = boto3.client('s3')
# # # Configurar a AWS Credentials antes de rodar, e criar bucket antes de tudo

bucket_raw = 's3-raw-infomotion-1'
bucket_trusted = 's3-trusted-infomotion-1'

s3.upload_file(f'data{id_servidor}.csv', bucket_raw, f'data{id_servidor}.csv')
s3.upload_file(f'data{id_servidor}-{data_arquivo}.csv', bucket_raw, f'data{id_servidor}-{data_arquivo}.csv')
s3.upload_file(f'processos{id_servidor}.csv', bucket_raw, f'processos{id_servidor}.csv')
s3.upload_file(f'clima{id_servidor}.csv', bucket_trusted, f'clima{id_servidor}.csv')
s3.upload_file(f'conexoes{id_servidor}.csv', bucket_raw, f'conexoes{id_servidor}.csv')
s3.upload_file(f'EspecificacoesHardware{id_servidor}.csv', bucket_raw, f'EspecificacoesHardware{id_servidor}.csv')
print("CSV enviado com sucesso!")

# CSV enviado para a pasta CSVs-registrados dentro do bucket RAW
