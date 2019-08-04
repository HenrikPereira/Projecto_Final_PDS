# -*- coding: utf-8 -*-
#%%
### Library with pre processing functions

# Import packges
import datetime as dt
import pandas as pd
import numpy as np
import requests as requests
import re
from bs4 import BeautifulSoup as bs 

#%% Auxiliar Functions  
    
# Recebe uma epoca (e.g. 98/99 ou 02/03) e retorna o ano -> último ano da época
def fct_aux_epoca_ano(epoca):

    epoca_ano = epoca.split('/')
    if(int(epoca_ano[1]) > 50): #se o ano for maior que 50
        ano = int('19' + epoca_ano[1])
    else:
        ano = int('20' + epoca_ano[1])

    return ano


# Funcao auxiliar para corrigir epocas (e.g. que foram importadas como datas)
def fct_aux_visitors_epoca(x):
    result = x
    if type(x) is dt.datetime:
        if x.year == 2019:
            result = x.strftime('%d/%m')
        else:
            result = x.strftime('%m/%y')
            
    return result


# Função auxiliar para corrigir inteiros que foram importados com pontos
# e por isso ficaram objetos(+ que 1 ponto) ou floats
def fct_aux_visitors_val(x):
    
    if type(x) is object or type(x) is str:
        return int(x.replace('.',''))

    elif type(x) is float:
        
        # Verifica se os decimais são todos 0
        if int((x-int(x))*1000) is 0:
            return int(x)
        else:
            return int(x)*1000 + int(round(x-int(x), 4)*1000)

    else:
        return x

# Function to set year index
def year_as_index(dataset_name,column_to_index):
    dataset_name.set_index(column_to_index,inplace=True)
    dataset_name.index.name = 'Ano'
    dataset_name.index = dataset_name.index.map(int) 

#%% Function to Pre Process Champions dataset
def get_champions(path):
    
    #Request to website
    siteFZZ = requests.get(path).text
    bsFZZ = bs(siteFZZ, 'html.parser')
    #Find table
    tabelaFZZ = bsFZZ.find('table',{'class':'zztable stats'})
    #Get do conteudo
    conteudo = []
    for i in tabelaFZZ:
        conteudo.append(i.getText().split('\n')[0])
    futebolZZ = pd.DataFrame(conteudo)
    #Seleccao a partir da 2a linha
    futebolZZ = futebolZZ.iloc[2:,:]
    #Split e tratamento da informacao
    futebolZZ = futebolZZ[0].astype(str).str.split('^(.......)', n = 1, expand = True)
    futebolZZ[1] = futebolZZ[1].str.extract('^(....)', expand = False)
    futebolZZ[3] = futebolZZ[2].str.extract('(\d.)', expand = True)
    futebolZZ[3] = futebolZZ[3].str.split('e', expand = True)
    futebolZZ[2] = futebolZZ[2].str.split('#', expand = True)
    #Anos das epocas
    futebolZZ[4] = futebolZZ[1].astype(int) + 1
    futebolZZ[1] = futebolZZ[1].astype(int)
    futebolZZ[3] = futebolZZ[3].astype(int)
    futebolZZ = futebolZZ.iloc[:,1:]
    futebolZZ.rename(columns={1:'AnoInicio',2:'EquipaVencedora',3:'NrConquistas',4:'Ano'}, inplace=True)
    #Definicao de ano (final da epoca) como index
    year_as_index(futebolZZ,'Ano')
    
    return futebolZZ

#%%Function to get data from Transfermarkt
def get_transfermarkt(path1,path2):
    
    #Transfermarkt
    url_transfermarkt_1 = path1
    url_transfermarkt_2 = path2
    header = {
      "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.75 Safari/537.36",
      "X-Requested-With": "XMLHttpRequest"
    }
    r_transfmarkt_1 = requests.get(url_transfermarkt_1, headers=header)
    r_transfmarkt_2 = requests.get(url_transfermarkt_2, headers=header)
    
    bsTM1 = bs(r_transfmarkt_1.content,'html.parser')
    tableTM1 = bsTM1.find_all('table')[2]
    l_1 = []
    table_rows = tableTM1.find_all('tr')
    for tr in table_rows:
        td = tr.find_all('td')
        row = [tr.text for tr in td]
        l_1.append(row)
    transfermarkt_1 = pd.DataFrame(l_1)
        
    bsTM2 = bs(r_transfmarkt_2.content,'html.parser')
    tableTM2 = bsTM2.find_all('table')[3] 
    l_2 = []
    table_rows = tableTM2.find_all('tr')
    for tr in table_rows:
        td = tr.find_all('td')
        row = [tr.text for tr in td]
        l_2.append(row)
    transfermarkt_2 = pd.DataFrame(l_2)
    
    #Drop de linhas com None
    transfermarkt_1.drop(0,axis=0,inplace=True)
    transfermarkt_1.drop(5,axis=1,inplace=True)
    #Renomear colunas
    transfermarkt_1.columns = ['Epoca','Jogos','Espetadores','Media','JogosLotEsgot','MaisEspetadores','Espetadores_Media']
    

    #Drop de colunas com NaN e 1a coluna
    transfermarkt_2.drop(0,axis=0,inplace=True)
    transfermarkt_2.drop(0,axis=1,inplace=True)
    transfermarkt_2.drop(1,axis=1,inplace=True)
    #Renomear colunas
    transfermarkt_2.columns = ['Clube','Jogos','Vitorias','Empates','Derrotas','GoalAverage','Pontos']
    
     #Divisao entre ano de inicio da epoca e ano do fim da epoca
    Inicio_Epoca_1 = transfermarkt_1.Epoca.str.split('/',expand=True)[0]
    Final_Epoca_1  = transfermarkt_1.Epoca.str.split('/',expand=True)[1]
    
    transfermarkt_1.loc[:,"Ano_Inicio_Epoca"] = Inicio_Epoca_1
    transfermarkt_1.loc[:,"Ano_Final_Epoca"] = Final_Epoca_1
    transfermarkt_1.loc[:,"Ano_Inicio_Epoca"] = transfermarkt_1.loc[:,"Ano_Inicio_Epoca"].map(lambda x:'20'+ x)
    transfermarkt_1.loc[:,"Ano_Final_Epoca"] = transfermarkt_1.loc[:,"Ano_Final_Epoca"].map(lambda x:'20'+ x)
    
    #Formatação colunas transfermarket 1
    transfermarkt_1.loc[:,"Ano_Inicio_Epoca"] = transfermarkt_1.loc[:,"Ano_Inicio_Epoca"].astype('int64')
    transfermarkt_1.loc[:,"Ano_Final_Epoca"] = transfermarkt_1.loc[:,"Ano_Final_Epoca"].astype('int64')
    transfermarkt_1.loc[:,"Espetadores"] = transfermarkt_1.loc[:,"Espetadores"].map(lambda x: int(str(x).replace('.','')))
    transfermarkt_1.loc[:,"Media"] = transfermarkt_1.loc[:,"Media"].map(lambda x: int(str(x).replace('.','')))
    transfermarkt_1.loc[:,"Espetadores_Media"] = transfermarkt_1.loc[:,"Espetadores_Media"].map(lambda x: int(str(x).replace('.','')))
    #Formatação colunas transfermarket 2
    transfermarkt_2.loc[:,"GoalAverage"] = transfermarkt_2.loc[:,"GoalAverage"].map(lambda x: int(str(x).replace('.','')))
    transfermarkt_2.loc[:,"Pontos"] = transfermarkt_2.loc[:,"Pontos"].map(lambda x: int(str(x).replace('.','')))
    #Definicao de ano (final da epoca) como index
    year_as_index(transfermarkt_1,'Ano_Final_Epoca')
    
    return transfermarkt_1,transfermarkt_2

#%%Function to get PIB evolution
def get_pib_per_capita(path):
    pib_per_capita = pd.read_excel(path)
    #Drop de colunas constituidas apenas por NaN
    pib_per_capita.dropna(axis=1, how='all', inplace=True)
    #Seleccao de colunas com informacao relevante
    pib_per_capita = pib_per_capita.iloc[:,0:2]
    #Drop de linhas constituidas c/ NaN
    pib_per_capita.dropna(inplace=True)
    #Renomear colunas
    pib_per_capita.columns = ['Ano','PIB_per_capita']
    pib_per_capita.drop(5, axis=0, inplace=True)
    #Reset dos indice do dataframe
    pib_per_capita.reset_index(drop=True, inplace=True)
    #Eliminar linhas com lixo
    pib_per_capita.loc[:,'Ano'] = pd.to_numeric(pib_per_capita.Ano, errors='coerce')
    pib_per_capita.loc[:,'PIB_per_capita'] = pd.to_numeric(pib_per_capita.PIB_per_capita, errors='coerce')
    pib_per_capita.dropna(inplace=True)
    pib_per_capita.loc[:,'Ano'] = pib_per_capita.Ano.astype(int)
    
    #Definicao de ano como index
    year_as_index(pib_per_capita,'Ano')
    
    return pib_per_capita

 #%%Function to get PIB rate growth
def get_pib_rate(path):
    taxa_crescimento_pib = pd.read_excel('Datasets/taxa_crescimento_pib.xlsx')
    #Drop de colunas constituidas apenas por NaN
    taxa_crescimento_pib.dropna(axis=1, how='all', inplace=True)
    #Seleccao de colunas com informacao relevante
    taxa_crescimento_pib = taxa_crescimento_pib.iloc[:,0:2]
    #Drop de linhas constituidas c/ NaN
    taxa_crescimento_pib.dropna(inplace=True)
    #Renomear colunas
    taxa_crescimento_pib.columns = ['Ano','Tx_Cresc_Real_PIB']
    #Eliminar o index 5
    taxa_crescimento_pib.drop(5, axis=0, inplace=True)
    #Reset dos indice do dataframe
    taxa_crescimento_pib.reset_index(drop=True, inplace=True)
    #Eliminar linhas com lixo
    taxa_crescimento_pib.loc[:,'Ano'] = pd.to_numeric(taxa_crescimento_pib.Ano, errors='coerce')
    taxa_crescimento_pib.loc[:,'Tx_Cresc_Real_PIB'] = pd.to_numeric(taxa_crescimento_pib.Tx_Cresc_Real_PIB, errors='coerce')
    taxa_crescimento_pib = taxa_crescimento_pib.dropna()
    taxa_crescimento_pib.loc[:,'Ano'] = taxa_crescimento_pib.Ano.astype(int)    
    
    #Definicao de ano como index
    year_as_index(taxa_crescimento_pib,'Ano')
    
    return taxa_crescimento_pib

#%%Function to get data from population
def get_population_info(path1,path2,path3,path4):
    
    pop_grupo_etario = pd.read_excel(path1)
    pop_grupo_etario_m = pd.read_excel(path2)
    pop_grupo_etario_f = pd.read_excel(path3)
    pop_genero = pd.read_excel(path4)
    
    #Drop de colunas constituidas apenas por NaN
    pop_grupo_etario.dropna(axis=1, how='all', inplace=True)
    pop_grupo_etario_m.dropna(axis=1, how='all', inplace=True)
    pop_grupo_etario_f.dropna(axis=1, how='all', inplace=True)
    #Drop de linhas constituidas c/ NaN
    pop_grupo_etario.dropna(inplace=True)
    pop_grupo_etario_m.dropna(inplace=True)
    pop_grupo_etario_f.dropna(inplace=True)
    
    pop_grupo_etario = pop_grupo_etario.apply(pd.to_numeric, errors='coerce')
    pop_grupo_etario_m = pop_grupo_etario_m.apply(pd.to_numeric, errors='coerce')
    pop_grupo_etario_f = pop_grupo_etario_f.apply(pd.to_numeric, errors='coerce')
    
    #Renomear colunas
    pop_grupo_etario.columns = ['Ano','PopTotal','PopIdadeZero_Quatro','PopIdadeCinco_Nove','PopIdadeDez_Quatorze','PopIdadeQuinze_Dezanove','PopIdadeVinte_VinteQuatro','PopIdadeVinteCinco_VinteNove','PopIdadeTrina_TrintaQuatro','PopIdadeTrintaCinco_TrintaNove','PopIdadeQuarenta_QuarentaQuatro','PopIdadeQuarentaCinco_QuarentaNove','PopIdadeCinquenta_CinquentaQuatro','PopIdadeCinquentaCinco_CinquentaNove','PopIdadeSessenta_SessentaQuatro','PopIdadeSessentaCinco_SessentaNove','PopIdadeSetenta_SetentaQuatro','PopIdadeSetentaCinco_SetentaNove','PopIdadeOitenta_OitentaQuatro','PopIdadeMais_OitentaCinco']
    pop_grupo_etario_m.columns = ['Ano','PopTotalM','PopMIdadeZero_Quatro','PopMIdadeCinco_Nove','PopMIdadeDez_Quatorze','PopMIdadeQuinze_Dezanove','PopMIdadeVinte_VinteQuatro','PopMIdadeVinteCinco_VinteNove','PopMIdadeTrina_TrintaQuatro','PopMIdadeTrintaCinco_TrintaNove','PopMIdadeQuarenta_QuarentaQuatro','PopMIdadeQuarentaCinco_QuarentaNove','PopMIdadeCinquenta_CinquentaQuatro','PopMIdadeCinquentaCinco_CinquentaNove','PopMIdadeSessenta_SessentaQuatro','PopMIdadeSessentaCinco_SessentaNove','PopMIdadeSetenta_SetentaQuatro','PopMIdadeSetentaCinco_SetentaNove','PopMIdadeOitenta_OitentaQuatro','PopMIdadeMais_OitentaCinco']
    pop_grupo_etario_f.columns = ['Ano','PopTotalF','PopFIdadeZero_Quatro','PopFIdadeCinco_Nove','PopFIdadeDez_Quatorze','PopFIdadeQuinze_Dezanove','PopFIdadeVinte_VinteQuatro','PopFIdadeVinteCinco_VinteNove','PopFIdadeTrina_TrintaQuatro','PopFIdadeTrintaCinco_TrintaNove','PopFIdadeQuarenta_QuarentaQuatro','PopFIdadeQuarentaCinco_QuarentaNove','PopFIdadeCinquenta_CinquentaQuatro','PopFIdadeCinquentaCinco_CinquentaNove','PopFIdadeSessenta_SessentaQuatro','PopFIdadeSessentaCinco_SessentaNove','PopFIdadeSetenta_SetentaQuatro','PopFIdadeSetentaCinco_SetentaNove','PopFIdadeOitenta_OitentaQuatro','PopFIdadeMais_OitentaCinco']
    
    #Drop de colunas constituidas apenas por NaN
    pop_genero.dropna(axis=1, how='all', inplace=True)
    #Seleccao de colunas com informacao relevante
    pop_genero = pop_genero.iloc[:,0:4]
    #Drop de linhas constituidas c/ NaN
    pop_genero.dropna(inplace=True)
    #RenomearColunas
    pop_genero.columns = ['Ano','TotalPop','PopMasculino','PopFeminino']
    #Eliminar linhas com lixo
    pop_genero.loc[:,'Ano'] = pd.to_numeric(pop_genero.Ano, errors='coerce')
    pop_genero.loc[:,'TotalPop'] = pd.to_numeric(pop_genero.TotalPop, errors='coerce')
    pop_genero.loc[:,'PopMasculino'] = pd.to_numeric(pop_genero.PopMasculino, errors='coerce')
    pop_genero.loc[:,'PopFeminino'] = pd.to_numeric(pop_genero.PopFeminino, errors='coerce')
    pop_genero = pop_genero.dropna()
    #Alteracao Datatype
    pop_genero.loc[:,'Ano'] = pop_genero.Ano.astype(int)
    pop_genero.loc[:,'TotalPop'] = pop_genero.TotalPop.astype(int)
    pop_genero.loc[:,'PopMasculino'] = pop_genero.PopMasculino.astype(int)
    pop_genero.loc[:,'PopFeminino'] = pop_genero.PopFeminino.astype(int)
    #Alteracao Unidades das colunas
    pop_genero.loc[:,'TotalPop'] = pop_genero.TotalPop*1000
    pop_genero.loc[:,'PopMasculino'] = pop_genero.PopMasculino*1000
    pop_genero.loc[:,'PopFeminino'] = pop_genero.PopFeminino*1000
    
    #Definicao de ano como index
    year_as_index(pop_grupo_etario,'Ano')
    #Definicao de ano como index
    year_as_index(pop_grupo_etario_m,'Ano')
    #Definicao de ano como index
    year_as_index(pop_grupo_etario_f,'Ano')
    #Definicao de ano como index
    year_as_index(pop_genero,'Ano')
    
    
    
    return pop_grupo_etario,pop_grupo_etario_m,pop_grupo_etario_f,pop_genero

#%% Function to Pre Process visitors dataset
        
# Função utilizada para carregar e pre-processar dados sobre expectadores de jogos
def get_visitors (path):
    
    # Carrega espectadores do ficheiro base (Excel - xlsx)
    visitors = pd.read_excel(path)

    # Elimina coluna wappen (está vazia)
    visitors.drop('wappen', axis=1, inplace=True)

    # Renomeida colunas
    visitors.columns = ['Epoca', 'Jogos', 'TotalEspetadores','MediaEspetadores', 'FlagEsgotado', 'Equipa', 'MaxEspetadores']

    # Corrigir formato dos valores da epoca
    epoca = pd.Series([fct_aux_visitors_epoca(x) for x in visitors.loc[:,'Epoca']]) #copia e corrige valores
    visitors['Epoca'] = epoca # Substituir valores corrigidos

    # Corrigor formato dos valores TotalEspetadores
    total_espetadores = pd.Series([fct_aux_visitors_val(x) for x in visitors.loc[:,'TotalEspetadores']]) #copia e corrige valores
    visitors['TotalEspetadores'] = total_espetadores # Substituir valores corrigidos
    
    # Corrigor formato dos valores MediaEspetadores
    media_espetadores = pd.Series([fct_aux_visitors_val(x) for x in visitors.loc[:,'MediaEspetadores']]) #copia e corrige valores
    visitors['MediaEspetadores'] = media_espetadores # Substituir valores corrigidos   
    
    # Corrigor formato dos valores MaxEspetadores
    max_espetadores = pd.Series([fct_aux_visitors_val(x) for x in visitors.loc[:,'MaxEspetadores']]) #copia e corrige valores
    visitors['MaxEspetadores'] = max_espetadores # Substituir valores corrigidos
    
    # Adicionar nova coluna com o ano (id)
    visitors['Ano'] = pd.Series([fct_aux_epoca_ano(epoca) for epoca in visitors.loc[:,'Epoca']])
    visitors.set_index('Ano', inplace=True)
    
    return visitors


#%% Function to Pre Process euribor dataset
    
# Função utilizada para carregar e pre-processar dados sobre euribor
def get_euribor(path):
    
    # Carrega euribor do ficheiro base (Excel - xlsx)
    euribor = pd.read_excel(path)
        
    # Seleciona da tabela as linhas e colunas com dados
    euribor = euribor.iloc[5:25,0:4]

    # Renomear colunas
    euribor.rename(columns={'Unnamed: 0':'Ano', 'Unnamed: 1':'Euribor 3 meses', 'Unnamed: 2':'Euribor 6 meses', 'Unnamed: 3':'Euribor 12 meses'}, inplace=True)
    
    # Adicionar nova coluna com o ano (id)
    euribor.set_index('Ano', inplace=True)
    
    # Converter todos os valores em 'float'
    euribor = euribor.apply(pd.to_numeric, errors='coerce')
    
    euribor.dropna(axis=0, how='all', inplace=True)
    
    return euribor


#%% Function to Pre Process PSI20
    
# Função utilizada para carregar e pre-processar dados sobre PSI20
def get_psi20(path):
    
    # Carrega psi20 do ficheiro base (Excel - xlsx)
    psi20 = pd.read_excel(path)
    
    # Elimina a última linha (apenas contém estatísticas)
    psi20.drop(psi20.tail(1).index, inplace=True)
        
    # Cria coluna Ano e Mês
    psi20['Ano'] = psi20['Data'].map(lambda x: x.year)
    psi20['Mes'] = psi20['Data'].map(lambda x: x.month)
    
    # Parse para float da vareável Úlimo
    psi20['Último'] = psi20['Último'].map(
        lambda x: float(x.split(',')[0].replace('.','') + '.' + x[-2:] if x != '-' else x))
    
    # Parse para float da vareável Abertura
    psi20['Abertura'] = psi20['Abertura'].map(
        lambda x: float(x.split(',')[0].replace('.','') + '.' + x[-2:] if x != '-' else x))
    
    # Parse para float da vareável Alta
    psi20['Alta'] = psi20['Alta'].map(
        lambda x: float(x.split(',')[0].replace('.','') + '.' + x[-2:] if x != '-' else x))
    
    # Parse para float da vareável Baixa
    psi20['Baixa'] = psi20['Baixa'].map(
        lambda x: float(x.split(',')[0].replace('.','') + '.' + x[-2:] if x != '-' else x))
    
    # Parse para float da vareável Volume (em Bilião) (retirar B e M | se em M -> /100)
    psi20['Vol.'] = psi20['Vol.'].map(
        lambda x: round(float(x[:-1].replace(',','.')),2) if x[-1]=='B' else round(float(x[:-1].replace(',','.'))/100,2) if x[-1]=='M' else 0.0)

    # Cria dataframe com linha por ano e com o Volume [Sumar Volumes]
    vol = psi20.loc[:,['Ano', 'Vol.']]
    vol.index = vol['Ano']
    psi20_ano = vol.groupby(by=vol.index).sum().drop(columns='Ano').rename(columns = {'Vol.':'Volume'})
        
    # Adiciona Ultimo (valor do último mês do ano)
    max = psi20.loc[:,['Ano', 'Mes']].groupby(by='Ano').max() # Determina o último mês de cada ano
    ultimo_max = max.merge(psi20, on=['Ano', 'Mes']).loc[:,['Ano', 'Último']] # Faz o join do max com PSI20 e obtem valor do Último PSI20 para os ultimos meses 
    psi20_ano = psi20_ano.join(ultimo_max.set_index('Ano')).rename(columns={'Último':'Ultimo'}) # Adiciona à tabela resultado
    
    # Adiciona Abertura (valor do primeiro mês do ano)
    min = psi20.loc[:,['Ano', 'Mes']].groupby(by='Ano').min() # Determina o primeiro mês de cada ano
    abertura_min = min.merge(psi20, on=['Ano', 'Mes']).loc[:,['Ano', 'Abertura']] # Faz o join do min com PSI20 e obtem valor de abertura do PSI20 para o primeiro mês 
    psi20_ano = psi20_ano.join(abertura_min.set_index('Ano'))

    # Adiciona Baixa (valor minímo da Baixa no ano)
    baixa = psi20.loc[:,['Ano', 'Baixa']].groupby(by='Ano').min() # Determina o valor de PSI20 mais baixo por ano
    psi20_ano = psi20_ano.join(baixa) 
    
    # Adiciona Alta (valor maximo da Alta do ano)
    alta = psi20.loc[:,['Ano', 'Alta']].groupby(by='Ano').max() # Determina o valor de PSI20 mais elevado por ano
    psi20_ano = psi20_ano.join(alta)

    # Adiciona Variacao = ((ultimo*100)/último do ano anterior)-100
    variacao = pd.Series(index = psi20_ano.index, name='Variacao') # Cria estrutura da variacao
    
    # Para cada ano
    for index, row in psi20_ano.iterrows():
        
        # Calcula a variacao
        if(index == psi20_ano.index[0]): # Se for o 1º ano
            var = round(((row['Ultimo'] * 100) / row['Abertura']) - 100, 2) # Usa abertura do ano           
        else: # Se não usa o último do ano anterior
            var = round(((row['Ultimo'] * 100) / psi20_ano.loc[index-1, 'Ultimo']) - 100, 2)
                
        # Adiciona à lista de variações a do respetivo ano
        variacao[index] = var
    
    # Adiciona as variações à tabela resultado
    psi20_ano = psi20_ano.join(variacao)
    
    # Renomeida colunas
    #psi20.columns = ['Ano', 'PSI20_Volume', 'PSI20_Ultimo', 'PSI20_Abertura','PSI20_Baixa', 'PSI20_Alta', 'PSI20_Variacao']
    psi20_ano.rename(columns={'Volume':'PSI20_Volume', 'Ultimo':'PSI20_Ultimo', 'Abertura':'PSI20_Abertura','Baixa':'PSI20_Baixa', 'Alta':'PSI20_Alta', 'Variacao':'PSI20_Variacao'}, inplace=True)

    return psi20_ano

#%% 
def get_totalAnoGenero_Ganho(path):
    #Leitura do ficheiro
    ganho_sexo = pd.read_excel(r'Datasets/ganho_por_sexo.xlsx')

    #Selecção das colunas de interesse e renomeação das mesmas
    ganho_sexo = ganho_sexo.iloc[:,:4]
    ganho_sexo.columns = ['Ano','TotalIncome','MascIncome','FemIncome']

    #Eliminação das linhas de dados sem interesse e correção dados
    ganho_sexo = ganho_sexo[pd.to_numeric(ganho_sexo['Ano'], errors='coerce').notnull()]
    ganho_sexo['Ano'].astype(int)
    ganho_sexo['TotalIncome'] = ganho_sexo['TotalIncome'].astype(float)
    ganho_sexo['MascIncome'] = ganho_sexo['MascIncome'].astype(float)
    ganho_sexo['FemIncome'] = ganho_sexo['FemIncome'].astype(float)
    ganho_sexo = ganho_sexo[ganho_sexo['TotalIncome']>0.0]
    
    #Correção do indice
    year_as_index(ganho_sexo,'Ano')
  
    return ganho_sexo

#%% 

def get_totalAnoGenero_Remuneracao(path):
    #Leitura do ficheiro
    rem_sexo = pd.read_excel(r'Datasets/remuneracao_por_sexo.xlsx')

    #Selecção das colunas de interesse e renomeação das mesmas
    rem_sexo = rem_sexo.iloc[:,:4]
    rem_sexo.columns = ['Ano','TotalOrdenado','MascOrdenado','FemOrdenado']

    #Eliminação das linhas de dados sem interesse e correção dados
    rem_sexo = rem_sexo[pd.to_numeric(rem_sexo['Ano'], errors='coerce').notnull()]
    rem_sexo['Ano'].astype(int)
    rem_sexo['TotalOrdenado'] = rem_sexo['TotalOrdenado'].astype(float)
    rem_sexo['MascOrdenado'] = rem_sexo['MascOrdenado'].astype(float)
    rem_sexo['FemOrdenado'] = rem_sexo['FemOrdenado'].astype(float)
    rem_sexo = rem_sexo[rem_sexo['TotalOrdenado']>0.0]
    
    #Correção do indice
    year_as_index(rem_sexo,'Ano')

    return rem_sexo

#%% 
    
def get_rendimentoPIBpercent(path):
    #Leitura do ficheiro
    rendPIB = pd.read_excel(r'Datasets/rendimento_empercentagem_pib.xlsx')

    #Selecção das colunas de interesse e renomeação das mesmas
    rendPIB = rendPIB.iloc[:,:3]
    rendPIB.columns = ['Ano','RendBrutoPCT_PIB','RendDisponivelPCT_PIB']

    #Eliminação das linhas de dados sem interesse e correção dados
    rendPIB = rendPIB[pd.to_numeric(rendPIB['Ano'], errors='coerce').notnull()]
    rendPIB['Ano'].astype(int)
    rendPIB['RendBrutoPCT_PIB'] = rendPIB['RendBrutoPCT_PIB'].astype(float)/100
    rendPIB['RendDisponivelPCT_PIB'] = rendPIB['RendDisponivelPCT_PIB'].astype(float)/100
    rendPIB = rendPIB[rendPIB['RendBrutoPCT_PIB']>0.0]
    
    #Correção do indice
    year_as_index(rendPIB,'Ano')
    
    return rendPIB

#%%
    
def get_consumo_privado(path) :
    
    #Ler o excel no path
    consumo_privado = pd.read_excel(path)

    #Seleccao de colunas com informacao relevante
    consumo_privado = consumo_privado.iloc[:,0:2]

    #Renomear colunas
    consumo_privado.columns = ['Ano','Consumo_Privado_em_Pct_PIB']
    
    #Drop linha com os nomes das colunas
    consumo_privado.drop(4, axis=0, inplace=True)

    #Eliminar linhas com lixo - Colocar NA onde não for um ano numerico
    consumo_privado.loc[:,'Ano'] = pd.to_numeric(consumo_privado.Ano, errors='coerce')

    # eliminar linhas com lixo 2
    consumo_privado.loc[:,'Consumo_Privado_em_Pct_PIB'] = pd.to_numeric(consumo_privado.Consumo_Privado_em_Pct_PIB, errors='coerce')
    
    #Drop de linhas constituidas c/ NaN
    consumo_privado.dropna(inplace=True)

    #Reset dos indice do dataframe
    consumo_privado.reset_index(drop=True, inplace=True)

    #Colocar os anos em int e sem casas decimais
    consumo_privado.loc[:,'Ano'] = consumo_privado.Ano.astype(int)
    
    #Colocar Anos como index
    consumo_privado.set_index('Ano', inplace=True)
    
    #Colocar o Consumo_Privado_em_Pct_PIB em float
    consumo_privado.loc[:,'Consumo_Privado_em_Pct_PIB'] = consumo_privado.Consumo_Privado_em_Pct_PIB.astype(float)

    #dividir o valor da percentagem por 100 para ficar em valor percentual
    consumo_privado.Consumo_Privado_em_Pct_PIB =  consumo_privado.Consumo_Privado_em_Pct_PIB/100
    
    return consumo_privado

#%%

def get_desemprego_pct(path):
    
    #Ler o excel no path
    desemprego_pct = pd.read_excel(path)

    #Seleccao de colunas com informacao relevante
    desemprego_pct = desemprego_pct.iloc[:,0:4]

    #Renomear colunas
    desemprego_pct.columns = ['Ano','DesempregoPCT_Total','DesempregoPCT_Masculino','DesempregoPCT_Feminino']

    #Drop linha com os nomes das colunas
    desemprego_pct.drop([4,5], axis=0, inplace=True)

    #Eliminar linhas com lixo - Colocar NA onde não for um ano numerico
    desemprego_pct.loc[:,'Ano'] = pd.to_numeric(desemprego_pct.Ano, errors='coerce')

    # eliminar linhas com lixo 2
    desemprego_pct.loc[:,'DesempregoPCT_Total'] = pd.to_numeric(desemprego_pct.DesempregoPCT_Total, errors='coerce')

    # eliminar linhas com lixo 3
    desemprego_pct.loc[:,'DesempregoPCT_Masculino'] = pd.to_numeric(desemprego_pct.DesempregoPCT_Masculino, errors='coerce')

    # eliminar linhas com lixo 4
    desemprego_pct.loc[:,'DesempregoPCT_Feminino'] = pd.to_numeric(desemprego_pct.DesempregoPCT_Feminino, errors='coerce')
    
    #Drop de linhas constituidas c/ NaN
    desemprego_pct.dropna(inplace=True)

    #Reset dos indice do dataframe
    desemprego_pct.reset_index(drop=True, inplace=True)

    #Colocar os anos em int e sem casas decimais
    desemprego_pct.loc[:,'Ano'] = desemprego_pct.Ano.astype(int)
    
    #Colocar Anos como index
    desemprego_pct.set_index('Ano', inplace=True)

    #dividir o valor da percentagem por 100 para ficar em valor percentual
    desemprego_pct.DesempregoPCT_Total =  desemprego_pct.DesempregoPCT_Total/100
    desemprego_pct.DesempregoPCT_Masculino =  desemprego_pct.DesempregoPCT_Masculino/100
    desemprego_pct.DesempregoPCT_Feminino =  desemprego_pct.DesempregoPCT_Feminino/100
  
    return desemprego_pct

#%%

def get_inflacao(path) :
    
    #Ler o excel no path
    inflacao = pd.read_excel(path)

    #Seleccao de colunas com informacao relevante
    inflacao = inflacao.iloc[:,0:15]

    #Renomear colunas
    inflacao.columns = ['Ano',
                        'Inflacao_Total',
                        'Inflacao_Total_excepto_produtos_alimentares_não_transformados_produtos_energéticos',
                        'Inflacao_Produtos_alimentares_bebidas_não_alcoólicas',
                        'Inflacao_Bebidas_alcoólicas_e_tabaco',
                        'Inflacao_Vestuário_calçado',
                        'Inflacao_Habitação_água_electricidade_gás_outros_combustíveis',
                        'Inflacao_Acessórios_para_o_lar_equipamento_doméstico_manutenção_corrente_habitação',
                        'Inflacao_Saúde',
                        'Inflacao_Transportes',
                        'Inflacao_Comunicações',
                        'Inflacao_Lazer_recreação_cultura',
                        'Inflacao_Educação',
                        'Inflacao_Restaurantes_hotéis',
                        'Inflacao_Bens_serviços_diversos']

    #Eliminar linhas com lixo - Colocar NA onde não for um ano numerico
    inflacao.loc[:,'Ano'] = pd.to_numeric(inflacao.Ano, errors='coerce')

    # eliminar linhas com lixo 2 - Colocar NA onde não for um valor numerico
    for i in range(15) : 
        inflacao.iloc[:,i] =  pd.to_numeric(inflacao.iloc[:,i], errors='coerce')   
    
    #Drop de linhas constituidas c/ NaN
    inflacao.dropna(inplace=True)

    #Reset dos indice do dataframe
    inflacao.reset_index(drop=True, inplace=True)

    #Colocar todas as colunas em float
    inflacao.loc[:,:] = inflacao.astype(float)

    #Colocar os anos em int e sem casas decimais
    inflacao.loc[:,'Ano'] = inflacao.Ano.astype(int)
    
    #dividir o valor da percentagem por 100 para ficar em valor percentual
    for i in range(1,15) : 
        inflacao.iloc[:,i] =  inflacao.iloc[:,i]/100
        
    #Colocar Anos como index
    inflacao.set_index('Ano', inplace=True) 
    
    return inflacao

#%%


    
