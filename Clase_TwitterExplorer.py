import pandas as pd
import numpy as np
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

                    print(f'Hasta ahora se descargaron {len(historicos)} tweets')


            data = pd.DataFrame(data=[tweet.text for tweet in historicos],\
                columns=['texto-tweet'])

            data['fecha'] = [tweet._json['created_at'][0:30] for tweet in historicos]

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

TwitterExplorer = TwitterExplorer(consumer_key=twitter_consumer_key,
                                    consumer_secret=twitter_consumer_secret,
                                    access_token=twitter_access_token,
                                    access_token_secret=twitter_access_token_secret
                                    )