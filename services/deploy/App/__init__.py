import os
import time
from os import environ
from flask import Flask
from celery import Celery
from celery.schedules import crontab
import App.celeryConfig as celeryConfig

app = Flask(__name__)
app.config['SECRET_KEY'] = '4973490d9fdsf-0dr-340-348347850450'

app.config['BROKER_URL'] = 'amqp://guest:guest@ec2-3-224-229-110.compute-1.amazonaws.com:5672//'


def makeCelery(app):
    # create context tasks in celery

    celery = Celery(app.import_name, broker=app.config['BROKER_URL'], CELERY_RESULT_BACKEND = "amqp")

    celery.conf.update(app.config)
    celery.config_from_object(celeryConfig)
    

    TaskBase = celery.Task

    class ContextTask(TaskBase):

        abstract = True

        def __call__(self, *args, **kwargs):

            with app.app_context():

                return TaskBase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask

    return celery


celery = makeCelery(app)


import App.route
