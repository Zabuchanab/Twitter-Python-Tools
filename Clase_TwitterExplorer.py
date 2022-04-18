import pandas as pd
import numpy as np
import re
from time import strptime
from datetime import datetime
import plotly.express as px
import tweepy
from wordcloud import WordCloud, STOPWORDS
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import CountVectorizer,TfidfTransformer
from importlib.resources import path
from io import open_code
import pathlib
import os
from importlib.resources import path
import os
import pathlib
import shutil


class TwitterExplorer():

    def __init__(self,consumer_key,consumer_secret,access_token,access_token_secret):
        
        cosumer_key = str(consumer_key)
        consumer_secret = str(consumer_secret)
        
        access_token = str(access_token)
        access_token_secret = str(access_token_secret)

        #Autenticacion
        autenticacion = tweepy.OAuthHandler(consumer_key=consumer_key,consumer_secret=consumer_secret)

        #Objeto API
        self.api = tweepy.API(autenticacion,wait_on_rate_limit=True)


    def ObjetoUsuario(self,usuario):
        usuario = self.api.get_user(screen_name=usuario)
        return usuario 

    def DatoUsuario(self,usuario):
    
        claves = ('id','name','screen_name','location',
                  'description','url','followers_count',
                  'friends_count','created_at','verified')
              
        filtrador = lambda x,y: dict([(i,x[i]) for i in x if i in set(y)])
    
        return pd.DataFrame(filtrador(self.ObjetoUsuario(usuario)._json,claves),index=[0])\
                .transpose()\
                    .rename(columns={0:'Resultados'})

    def TotalTweets(self,usuario):
        
        total_tweets = f"El usuario {usuario} escribio {len(self.ExtraccionTweets(usuario))} tweets"

        return total_tweets

    def FechaConversor(self,fecha):
    
        dia_numerico = re.search(r"[0-9]{2}",fecha)[0]

        dia_nominal = re.findall("[a-zA-Z]{3}" ,fecha)[0]

        mes_numerico = str(strptime(re.findall("[a-zA-Z]{3}" ,fecha)[1].upper(),"%b").tm_mon)

        if len(mes_numerico)==2:
            pass
        else:
            mes_numerico = str('0')+mes_numerico

        año_numerico = fecha[-4:]

        hora = re.findall("[0-9]{2}\:[0-9]{2}\:+[0-9]{2}",fecha)[0]

        dict_month = {}

        nueva_fecha = datetime.strptime(f'{dia_numerico}-{mes_numerico}-{año_numerico} {hora}','%d-%m-%Y %H:%M:%S')

        return nueva_fecha


    def ExtraccionTweets(self,usuario):

        try:

            resultados = self.api.user_timeline(screen_name=usuario,\
                count=1)

            historicos = []

            id_viejo = resultados[-1].id

            while True:

                    tweets = self.api.user_timeline(screen_name =usuario,
                        count=200,
                        include_rts = False,
                        max_id=id_viejo-1,
                        tweet_mode='extended'
                        )

                    if len(tweets)==0:
                        break
                    id_viejo = tweets[-1].id
                    historicos.extend(tweets)

                    print(f'Hasta ahora se descargaron {len(historicos)} tweets del usuario {usuario.upper()}')


            data = pd.DataFrame(data=[tweet.id for tweet in historicos],\
                columns=['id'])


            data['fecha'] = [tweet._json['created_at'] for tweet in historicos]

            data['fecha'] = data['fecha'].apply(self.FechaConversor)

            data['tweet'] = [tweet.full_text for tweet in historicos]

            data['retweets'] = [tweet.retweet_count for tweet in historicos]

            data['likes'] = [tweet.favorite_count for tweet in historicos]

            print(f'Se descargaron {len(data)} tweets')

            return data

        except:

            return 'No se pudo realizar la descarga'

    def ExtractorRespuestasTweet(self,usuario,tweet_id):

        respuestas = []

        for respuesta_tweet in tweepy.Cursor(self.api.search_tweets,
                                         q=f'to:{usuario}',result_type='recent').items(1000):

            if hasattr(respuesta_tweet,'in_reply_to_status_id_str'):

                if (respuesta_tweet.in_reply_to_status_id_str==tweet_id):

                    lista = [respuesta_tweet._json['text'],tweet_id]

                    respuestas.append(lista)

        return pd.DataFrame(respuestas), print(f'Se agregaron {len(respuestas)} comentarios')

    def BaseRespuestasTweetsHistorico(self,usuario):

        base_id_tweets = self.ExtraccionTweets(usuario)['id']

        listado_respuestas = []
        
        for id in base_id_tweets:
            extraccion = self.ExtractorRespuestasTweet(usuario,str(id))
            listado_respuestas.append(extraccion)

        listado_respuestas = pd.DataFrame(listado_respuestas)

        return listado_respuestas

    def GeneradorCSVRespuestas(self,usuario):

        data = self.BaseRespuestasTweetsHistorico(usuario)

        try: 
            data.to_csv(f'tabla{len(data)}_respuestas_{usuario}')

        except:

            return 'No se pudo generar la base'

    def GeneracionCSV(self,usuario):

        data = pd.DataFrame(self.ExtraccionTweets(usuario))
        try:
            data.to_csv(f'tabla_{len(data)}_tweets_{usuario}')
            
            return f'Se creó la tabla con {len(data)} del usuario {usuario}'

        except:

            return 'No se pudo crear la base'

    def VizSerieTweets(self,usuario):

        data = self.ExtraccionTweets(usuario)

        figura = px.line(data,x='fecha',
                            y=['likes','retweets'],
                                hover_data=['tweet'],
                                    title=f'Evolucion de Tweets y Likes de {usuario}',
                                        labels=dict(x='Fecha',y='Cantidad absoluta',color='Place'),
                                        template='ggplot2',
                                                                                ) 

        figura.update_xaxes(title_text='Fecha - Barra de ajuste temporal',
                            rangeslider_visible=True,
                            rangeselector=dict(
                                buttons=list(
                                    [
                                        dict(count=7,label='Última semana',step='day',stepmode='backward'),
                                        dict(count=1,label='Último mes',step='month',stepmode='backward'),
                                        dict(count=6,label='Últimos seis meses',step='month',stepmode='backward'),
                                        dict(count=1,label='Último año',step='year',stepmode='backward'),
                                        dict(label='todo',step='all')
                                    ]
                                )
                            ))

        figura.update_yaxes(title_text='Cantidad absoluta',ticks='outside',tickwidth=2,tickcolor='black')

        figura.update_layout(legend=dict(orientation='h',yanchor='bottom',y=1.02,xanchor='right',x=1),legend_title_text='')

        return figura

    def VizRankingTweets(self,usuario):

        data = self.ExtraccionTweets(str(usuario))

        figura = px.bar(data_frame=data.sort_values(by='likes',ascending=False)[0:10],
                    x=[x[0:30] for x in data.sort_values(by='likes',ascending=False)[0:10]['tweet']],
                    y=['likes','retweets'],
                    barmode='group',
                    text_auto='.2s',
                    title=f'Ranking de los 10 mejores tweets del usuario {usuario}')

        return figura

    def LimpiadorTweets(self,texto):

        texto = re.sub(r"@","",texto)
        texto = re.sub(r"#","",texto) 
        texto = re.sub(r"RT[\s]+","",texto) 
        texto = re.sub(r"https?:\/\/\S+","",texto)
        
        return texto

    def SegmentacionPeriodos(self,data):

        data['periodo'] = data['fecha'].apply(lambda fecha: datetime.strftime(fecha,'%B, %Y'))
        data['año'] = data['fecha'].apply(lambda fecha: datetime.strftime(fecha,'%Y'))

        return data


    def BolsadePalabras(self):

        ruta = str(pathlib.Path().absolute()) + '/stop_words_spanish.txt'
        archivo = open(ruta,'r')
        stopwords = archivo.readlines()
        stopwords2 = []
        for elemento in stopwords:
            stopwords2.append(elemento.replace('\n',''))
        bolsa = set(STOPWORDS)
        bolsa.update(stopwords2)
        archivo.close()
        bolsa.update(['Conferencia','matutina','Prensa','Palacio','Na'])

        return bolsa


    def CrearDirectorio(self,usuario):

        if not os.path.isdir(f'./extracciones_usuarios'):
            os.mkdir('./extracciones_usuarios')
            print(f'Directorio_extracciones_creado')
        else:
            print('la carpeta extraccion de usuarios ya existe')
        

        if not os.path.isdir(f'./{usuario}'):
            os.mkdir(f'./extracciones_usuarios/{usuario}')
            print(f'Directorio_{usuario}_creado')
        else:
            print(f'la carpeta {usuario} ya existe')
        

    def VisualizacionWordClouds(self,data,usuario):

        periodos = data['año'].unique()
        
        for periodo in periodos:
            datos = data[data['año']==periodo]
            nuevas_palabras = ' '.join(datos['tweet'])
            wordcloud = WordCloud(stopwords=self.BolsadePalabras(),
                      width=3000,
                      height=2000,
                      collocations=False,
                      background_color='white',
                      min_font_size=10).generate(nuevas_palabras)

            plt.figure(figsize=(15,10))
            plt.imshow(wordcloud,interpolation='bilinear')
            plt.axis('off')

            plt.savefig(f'extracciones_usuarios/{usuario}/figura_{periodo}')

    def ProcesoETLWordCloud(self,usuario):
        try:
            data = self.ExtraccionTweets(usuario)
            print(f'Se extrajo la data del usuario {usuario}')
        except:
            print('No se pudo hacer la extracción')

        try:
            self.CrearDirectorio(usuario)
        except:
            print('Error al crear el directorio ')

        data['tweet'] = data['tweet'].apply(self.LimpiadorTweets)
        data = self.SegmentacionPeriodos(data)

        return self.VisualizacionWordClouds(data,usuario)
        
        
#Se deben generar credenciales mediante una cuenta de Twitter-Developer 
from credenciales import twitter_consumer_key,twitter_consumer_secret,twitter_access_token,twitter_access_token_secret

te = TwitterExplorer(consumer_key=twitter_consumer_key,
                                    consumer_secret=twitter_consumer_secret,
                                    access_token=twitter_access_token,
                                    access_token_secret=twitter_access_token_secret
                                    )