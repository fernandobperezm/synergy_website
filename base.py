from flask import Flask, session
from flask.ext.script import Manager, Server
from random import SystemRandom
from datetime import timedelta
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, MigrateCommand

app = Flask(__name__, static_url_path='')
manager = Manager(app)
manager.add_command("runserver", Server(
    use_debugger = True,
    use_reloader = True,
    host = '0.0.0.0', port = 8080)
)

@app.before_request
def make_session_permanent():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=45)
    session.modified = True

@app.route('/')
def root():
    return app.send_static_file('index.html')

#Application code starts here

# Código para la base de datos
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://synergy:lacontraseña@localhost/ci3715_db?client_encoding=utf8'
app.config['TESTING']=True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config.update(SECRET_KEY = repr(SystemRandom().random()))
db = SQLAlchemy(app)
migrate = Migrate(app, db)
manager.add_command('db', MigrateCommand)

#------------------------------------------------------------------------------

class Usuario(db.Model):
    __tablename__ = "usuario"
    nombre_usuario = db.Column(db.String, primary_key=True)
    nombre_completo = db.Column(db.String)
    correo = db.Column(db.String)
    clave = db.Column(db.String)

    def __init__(self, nombre_usuario, nombre_completo, correo, clave):
        self.nombre_usuario = nombre_usuario
        self.nombre_completo = nombre_completo
        self.correo = correo
        self.clave = clave


    def __repr__(self):
        return "<Usuario(nombre completo='%s', nombre de usuario='%s', correo='%s', clave='%s'>" %(
            self.nombre_completo, self.nombre_usuario, self.correo, self.clave)

#-------------------------------------------------------------------------------


class Amigo(db.Model):
    """docstring for Amigo"""

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    chat_id = db.Column(db.Integer, db.ForeignKey('chat.id'))
    amigo1 = db.Column(db.String, db.ForeignKey('usuario.nombre_usuario'))
    amigo2 = db.Column(db.String, db.ForeignKey('usuario.nombre_usuario'))

    def __init__(self, amigo1 ,amigo2,chat_id):
        self.amigo1 = amigo1
        self.amigo2 = amigo2
        self.chat_id = chat_id

#-------------------------------------------------------------------------------

class Pagina(db.Model):
    titulo = db.Column(db.String)
    contenido = db.Column(db.Text)
    id_usuario = db.Column(db.String, db.ForeignKey('usuario.nombre_usuario'), primary_key=True)
    usuario = db.relationship('Usuario',
        backref=db.backref('pagina', uselist=False), uselist=False)

    def __init__(self, titulo, contenido, usuario):
        self.titulo = titulo
        self.contenido = contenido
        self.id_usuario = usuario
        self.usuario = (db.session
            .query(Usuario)
            .filter_by(nombre_usuario=usuario)
            .first())

#-------------------------------------------------------------------------------

class Publicacion(db.Model):
    id = db.Column (db.Integer, primary_key=True, autoincrement=True)
    titulo = db.Column(db.String)
    fecha_creacion = db.Column(db.DateTime, server_default=db.func.now())
    contenido = db.Column(db.Text)
    autor_id = db.Column(db.String, db.ForeignKey('usuario.nombre_usuario'))
    eliminada = db.Column(db.Boolean, default=False)
    padre_id = db.Column(db.Integer, db.ForeignKey('publicacion.id'))
    padre = db.relationship('Publicacion',
                            backref=db.backref(
                                'hijos', 
                                order_by=lambda: db.asc(Publicacion.fecha_creacion)),
                            remote_side=[id])

    hilo = db.relationship('Hilo',
                            backref=db.backref('publicaciones'), uselist=False)
    hilo_id = db.Column(db.Integer, db.ForeignKey('hilo.id'))


    def __init__(self, titulo, contenido, usuario=None, hilo=None, padre=None):
        self.titulo = titulo
        self.contenido = contenido
        self.autor_id = usuario
        #self.responde_a = respondido.titulo
        self.hilo = hilo
        self.padre = padre
        
    def a_diccionario(self):
        return {
            'id' : self.id,
            'titulo' : self.titulo,
            'contenido' : self.contenido,
            'autor' : self.autor_id,
            'eliminada' : self.eliminada,
            'hijos' : [hijo.a_diccionario() for hijo in self.hijos]
        }


#-------------------------------------------------------------------------------

class Hilo(db.Model):
    id = db.Column (db.Integer, primary_key=True, autoincrement=True)
    foro_id = db.Column(db.String, db.ForeignKey('foro.titulo'))
    sitio_id = db.Column(db.String, db.ForeignKey('sitio.id'))

    fecha_creacion = db.Column(db.DateTime, server_default=db.func.now())

    sitio = db.relationship('Sitio',
                            backref=db.backref('hilo', uselist=False), uselist=False)
    foro = db.relationship('Foro',
                            backref=db.backref('hilos'), uselist=False)


    def __init__(self, foro=None, sitio=None):
        self.foro = foro
        self.sitio = sitio

    @property
    def raiz(self):
        for p in self.publicaciones:
            if p.padre is None:
                return p

#-------------------------------------------------------------------------------
class Foro(db.Model):
    titulo = db.Column(db.String, primary_key=True)
    fecha_creacion = db.Column(db.DateTime, server_default=db.func.now())

    autor_id = db.Column(db.String, db.ForeignKey('usuario.nombre_usuario'))

    def __init__(self, titulo, nombre_usuario):
        self.titulo = titulo
        self.autor_id = nombre_usuario

#-------------------------------------------------------------------------------

class Chat(db.Model):

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    mensajes = db.relationship('Mensaje',
        backref=db.backref('chat',uselist=False),
        order_by=lambda: db.desc(Mensaje.creado))

#-------------------------------------------------------------------------------

class Mensaje(db.Model):

    id = db.Column (db.Integer, primary_key=True, autoincrement=True)
    chat_id =  db.Column(db.Integer, db.ForeignKey('chat.id'))
    contenido = db.Column(db.Text)
    creado = db.Column(db.DateTime, server_default=db.func.now())
    usuario_origen = db.Column(db.String, db.ForeignKey('usuario.nombre_usuario'))

    def __init__(self,usuario_origen,contenido,chat):
        self.usuario_origen = usuario_origen
        self.chat_id = chat
        #self.chat = chat
        self.contenido = contenido

#-------------------------------------------------------------------------------

miembrosGrupo = db.Table('miembrosGrupo', db.metadata,
    db.Column('grupo',db.Integer,db.ForeignKey('grupo.id'),primary_key=True),
    db.Column('usuario',db.String,
        db.ForeignKey('usuario.nombre_usuario'),
        primary_key=True)
)

class Grupo(db.Model):
    __tablename__ = 'grupo'
    id = db.Column (db.Integer, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String, nullable=False)
    id_admin = db.Column(db.String, db.ForeignKey('usuario.nombre_usuario'))
    admin = db.relationship('Usuario',
            backref=db.backref('admin_grupo'), uselist=False)
    miembros = db.relationship('Usuario',
               secondary=miembrosGrupo, # Hace que usen la tabla miembrosGrupo
               backref=db.backref('grupos', lazy="dynamic"))
    chat_id = db.Column(db.Integer, db.ForeignKey('chat.id'))
    chat = db.relationship('Chat', uselist=False)

    def __init__(self,nombre,admin,chat):        # es de muchos a muchos
        self.nombre = nombre
        self.admin = admin
        self.admin_id = admin.nombre_usuario
        self.chat_id = chat.id
        self.chat = chat
        
#-------------------------------------------------------------------------------
class Sitio(db.Model):
    id = db.Column(db.String, primary_key=True)
    titulo = db.Column(db.String)
    contenido = db.Column(db.String)
    imagenes = db.Column(db.String)
     
    def __init__(self, id, titulo = None, contenido = None, imagenes = None):
        self.id = id
        self.titulo = titulo
        self.contenido = contenido
        self.imagenes = imagenes
#Application code ends here

from app.socal.ident import ident
app.register_blueprint(ident)
from app.socal.paginas import paginas
app.register_blueprint(paginas)

from app.socal.chat import chat
app.register_blueprint(chat)

from app.socal.foro import foro
app.register_blueprint(foro)

if __name__ == '__main__':
    app.config.update(
      SECRET_KEY = repr(SystemRandom().random())
    )
    manager.run()
