import pandas as pd
import numpy as np
import re
from time import strptime
from datetime import datetime
import plotly.express as px
import tweepy

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

                    tweets = self.api.user_timeline(screen_name = usuario,
                        count=200,
                        include_rts = False,
                        max_id=id_viejo-1)

                    if len(tweets)==0:
                        break
                    id_viejo = tweets[-1].id
                    historicos.extend(tweets)

                    print(f'Hasta ahora se descargaron {len(historicos)} tweets del usuario {usuario.upper()}')


            data = pd.DataFrame(data=[tweet.text for tweet in historicos],\
                columns=['tweet'])

            data['fecha'] = [tweet._json['created_at'] for tweet in historicos]

            data['fecha'] = data['fecha'].apply(self.FechaConversor)

            data['id'] = [tweet.id for tweet in historicos]

            data['retweets'] = [tweet.retweet_count for tweet in historicos]

            data['likes'] = [tweet.favorite_count for tweet in historicos]

            print(f'Se descargaron {len(data)} tweets')

            return data

        except:

            return 'No se pudo realizar la descarga'

    def GeneracionCSV(self,usuario):

        data = self.ExtraccionTweets(usuario)
        
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
                            ticks='outside',tickwidth=2,tickcolor='black',
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

from credenciales import twitter_consumer_key,twitter_consumer_secret,twitter_access_token,twitter_access_token_secret

TwitterExplorer = TwitterExplorer(consumer_key=twitter_consumer_key,
                                    consumer_secret=twitter_consumer_secret,
                                    access_token=twitter_access_token,
                                    access_token_secret=twitter_access_token_secret
                                    )