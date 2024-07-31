from celery import Celery

def make_celery(app):
    celery = Celery(
        app.import_name,
        backend='mongodb://localhost:27017/celery',  # MongoDB for results
        broker='mongodb://localhost:27017/celery'    # MongoDB for broker
    )
    celery.conf.update(app.config)
    TaskBase = celery.Task

    class ContextTask(TaskBase):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask
    return celery
