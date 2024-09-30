# bibliotecas em uso
from flask import Flask
from flask import render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, ForeignKey, func, distinct
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import timedelta
from math import ceil

# difiniçao da aplicaçao e banco de dados
app = Flask(__name__)
app.secret_key = 'receitasregionais'
app.permanent_session_lifetime = timedelta(days=365*100)
app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///bd_tcc.sqlite3'
db = SQLAlchemy(app)

# listas

lista_ingredientes = []
lista_ingredientes_invalidos = []
lista_ingredientes_manter = []
lista_mostrar_receitas = []
lista_ingredientes_consulta = []
ing_proibidos_encontrados = []
lista_proibidos_formatada = []

# TABELAS ----------------------------------------------------------------------------------------#
# tbIngredientes
class ingredientes(db.Model):
    __tablename__ = 'ingredientes'
    idIngrediente = db.Column(Integer, primary_key=True, autoincrement=True)
    quantidade = db.Column(String(100))
    nomeIngrediente = db.Column(String(30)) 
    idReceita = db.Column(Integer, ForeignKey('receitas.idReceita'), nullable=False)
    receita = relationship('receitas', back_populates='ingredientes')
    
    def __init__(self, nomeIngrediente, idReceita, quantidade):
        self.nomeIngrediente = nomeIngrediente
        self.quantidade = quantidade
        self.idReceita = idReceita


# tbReceitas
class receitas(db.Model):
  __tablename__ = 'receitas'
  idReceita = db.Column(Integer, primary_key=True, autoincrement=True)
  nomeReceita = db.Column(String(30))
  preparo = db.Column(String(760))
  imagem = db.Column(db.String(120))
  tempo = db.Column(db.String(50))
  descricao = db.Column(db.String(50))
  ingredientes = relationship('ingredientes', back_populates='receita')
  
  def __init__(self, nomeReceita, preparo, imagem, tempo, descricao):
      self.nomeReceita = nomeReceita
      self.preparo = preparo
      self.imagem = imagem
      self.tempo = tempo
      self.descricao = descricao
#--------------------------------------------------------------------------------------------------#



# CONSULTAS ---------------------------------------------------------------------------------------#
# busca todas receitas existentes
def getTodasReceitas():
  todasReceitas = receitas.query.all()

  return todasReceitas


# busca todos ingredientes existentes
def getTodosIngredientes():
  todosIngredientes = ingredientes.query.all()

  return todosIngredientes


# busca todas receitas e seus respectivos ingredientes
def getTodasReceitasComIngredientes():
    consulta = db.session.query(receitas.idReceita, receitas.nomeReceita, receitas.preparo, receitas.imagem, receitas.descricao,
      func.group_concat(ingredientes.nomeIngrediente)).\
    join(ingredientes).group_by(receitas.idReceita).all()

    return consulta


# busca uma receita utilizando seu id como parametro
def getReceitaComIngredientesPorId(idReceita):
    consulta = db.session.query(receitas, ingredientes.nomeIngrediente, ingredientes.quantidade).\
        join(ingredientes).\
        filter(receitas.idReceita == idReceita).\
        all()
    
    # agrupa os ingredientes para a receita
    receitas_com_ingredientes = {}
    for receita, ingrediente, quantidade in consulta:
        if receita.idReceita not in receitas_com_ingredientes:
            receitas_com_ingredientes[receita.idReceita] = {
                'receita': receita,
                'ingredientes': []
            }
        receitas_com_ingredientes[receita.idReceita]['ingredientes'].append({
            'nomeIngrediente': ingrediente,
            'quantidade': quantidade
        })

    return list(receitas_com_ingredientes.values())

#---------------------------------------------------------------------------------------------------#



# ROTAS --------------------------------------------------------------------------------------------#

# index
@app.route('/')
def index():
  receitas_no_banco = getTodasReceitas()

  return render_template('index.html', receitas=receitas_no_banco)


# rota que irá mostrar a receita que o usuário clicar para visualizar
@app.route('/receita/<int:idReceita>', methods=['GET', 'POST'])
def receita(idReceita):
  receitasComIngredientes = getReceitaComIngredientesPorId(idReceita)
  return render_template('receita.html', receitasComIngredientes = receitasComIngredientes)



# rota que irá permitir com que o usuário possa pesquisar por receitas que contenham os ingredientes de seu estoque/despensa
@app.route('/estoque_usuario', methods=['GET', 'POST'])
def cadastroIngrediente():

    global lista_ingredientes
    global lista_proibidos_formatada
    global ing_proibidos_encontrados
    
    repetido = False
    vazio = False
    
    #Recebe o ingrediente do usuario e o formata, convertendo-o para minusculo e removendo epaços em branco no começo e no fim
    #Verifica se o ingredinete já foi inserido, para evitar repetiçoes

    if request.method == 'POST': 
        ingrediente = request.form['ingrediente']
        
        repetido = any(ingrediente.replace(" ", "").lower() == ingrediente_na_lista.replace(" ", "").lower()
                        for ingrediente_na_lista in lista_ingredientes)
        vazio = ingrediente.strip() == ""

        if repetido:
            flash(f"{ingrediente.capitalize()} já foi inserido anteriormente \U0001F914")
        elif vazio:
            flash("Parece que você não digitou o nome do ingrediente \U0001F914")
        else:
            flash(f"{ingrediente.strip().capitalize()} adicionado(a) com sucesso \U0001F60E\U0001F44C")  
            lista_ingredientes.append(ingrediente.lower().strip())

        return redirect(url_for('cadastroIngrediente'))
    
    #Faz uma busca no banco de todos os ingredientes, para recomendar na página estoqueUsuario.html, através do JavaScript

    ingredientes_no_banco = db.session.query(ingredientes.nomeIngrediente).distinct().all()

    ingredientes_no_banco = [ingrediente[0] for ingrediente in ingredientes_no_banco]
    
    return render_template('estoqueUsuario.html', lista_ingredientes=lista_ingredientes, ingredientes_no_banco=ingredientes_no_banco)



#Remove os ingredientes do estoque do usuario, caso ele clique na lixeira de algum em específico
@app.route('/remover_ingrediente', methods=['POST', 'GET'])
def remover_ingrediente():
    global lista_ingredientes
    ingrediente_remover = request.form.get('ingrediente_remover')
    if ingrediente_remover and ingrediente_remover in lista_ingredientes:
        lista_ingredientes.remove(ingrediente_remover)
        flash(f"{ingrediente_remover.capitalize()} removido(a) com sucesso \U0001F60E\U0001F44D")
        
    return redirect(url_for('cadastroIngrediente', lista_ingredientes=lista_ingredientes))       


#Rota que irá mostrar as receitas encontradas de acordo com os ingredientes do estoque do usuário
@app.route('/receitas_mostrar', methods=['POST', 'GET'])
def get_receita_estoque():
    global lista_ingredientes
    global lista_ingredientes_invalidos

    page = request.args.get('page', 1, type=int)
    per_page = 4

    msg=""

    #Normalizar ingredientes para minúsculas antes da consulta, por precaução
    lista_ingredientes_normalizada = [ingrediente.lower() for ingrediente in lista_ingredientes]
    

    #Consulta SQL para encontrar IDs de receitas que possuem pelo menos um ingrediente da lista fornecida
    ids_receitas_com_ingredientes = db.session.query(receitas.idReceita).\
        join(ingredientes).\
        filter(func.lower(ingredientes.nomeIngrediente).in_(lista_ingredientes_normalizada)).\
        group_by(receitas.idReceita).\
        having(func.count(receitas.idReceita) == len(lista_ingredientes)).\
        subquery()

    #Consulta para recuperar as receitas completas usando os IDs encontrados
    receitas_com_ingredientes = receitas.query.filter(receitas.idReceita.in_(ids_receitas_com_ingredientes)).\
        paginate(page=page, per_page=per_page, error_out=False)

    # Lista dos ingredientes presentes nas receitas encontradas no banco de dados
    ingredientes_nas_receitas = set()
    for receita in receitas_com_ingredientes.items:
        for ingrediente in receita.ingredientes:
            ingredientes_nas_receitas.add(ingrediente.nomeIngrediente.lower())

    # Lista dos ingredientes presentes na lista Python, mas não no banco de dados
    lista_ingredientes_invalidos = [ingrediente for ingrediente in lista_ingredientes_normalizada if ingrediente not in ingredientes_nas_receitas]

    #Caso nenhuma receita foi encontrada, este bloco será executado
    if lista_ingredientes_invalidos:
        invalidos_formatados = ', '.join([ingrediente.capitalize() for ingrediente in lista_ingredientes_invalidos])
        msg = f'Não foi possível encontrar uma receita que contenha {invalidos_formatados} em si'

    return render_template('receitasEncontradas.html', receitas=receitas_com_ingredientes, msg=msg, lista_ingredientes_invalidos=lista_ingredientes_invalidos)




# form. de adiçao de novas receitas
@app.route('/adicionar', methods=['GET', 'POST'])
def adicionar():
    msg = ""
    
    if request.method == 'POST':
        nomeReceita = request.form.get('nomeReceita')
        preparo = request.form.get('preparo')
        imagem = request.form.get('imagem')
        tempo = request.form.get('tempo')
        descricao = request.form.get('desc')
        listaIngredientes = request.form.getlist('ingredientes[]')
        listaQuantidades = request.form.getlist('quantidades[]')
        
        
        receita = receitas(nomeReceita, preparo, imagem, tempo, descricao)
        db.session.add(receita)
        db.session.commit()

        for ingrediente, quantidade in zip(listaIngredientes, listaQuantidades):       
            novo_ingrediente = ingredientes(nomeIngrediente=ingrediente.strip().lower(), quantidade=quantidade, idReceita=receita.idReceita)
            db.session.add(novo_ingrediente)
        db.session.commit()

        #Redirecionar para a página onde a receita irá aparecer, trabalhando com a paginação

        total_receitas = receitas.query.count()
        per_page = 4

        if (total_receitas + 1) % per_page == 0:
            nova_receita_pagina = ceil((total_receitas + 1) / per_page) 
        else:
            nova_receita_pagina = ceil((total_receitas) / per_page) 
        
        return redirect(url_for('lista', page=nova_receita_pagina))
    
    ingredientes_no_banco = db.session.query(ingredientes.nomeIngrediente).distinct().all()

    ingredientes_no_banco = [ingrediente[0] for ingrediente in ingredientes_no_banco]
    
    return render_template('adicionar.html', msg=msg, ingredientes_no_banco=ingredientes_no_banco)



# pag. de exibiçao das receitas e ingredientes quando o usuario clicar na página "Todas as receitas"
@app.route('/lista')
def lista():
    MAX_PAGES_DISPLAY = 5
    
    page = request.args.get('page', 1, type=int)
    per_page = 4
      
    receitasComIngredientes = receitas.query.paginate(page=page, per_page=per_page, error_out=False)

    # Criação da páginação de acordo com a quantidade de receitas cadastradas

    num_pages = receitasComIngredientes.pages
    current_page = receitasComIngredientes.page
    start_page = max(1, current_page - (MAX_PAGES_DISPLAY // 2))
    end_page = min(num_pages, start_page + MAX_PAGES_DISPLAY - 1)
    if end_page - start_page + 1 < MAX_PAGES_DISPLAY:
        start_page = max(1, end_page - MAX_PAGES_DISPLAY + 1)

    pages_to_display = range(start_page, end_page + 1)

    return render_template('lista.html', receitas=receitasComIngredientes, pages=pages_to_display)


# form. ediçao de receitas e ingredientes, atualiza dados no db
@app.route('/editar/<int:idReceita>', methods=['GET', 'POST'])
def editar(idReceita):
    receita = receitas.query.get(idReceita)
    ingredientes_receita = getReceitaComIngredientesPorId(idReceita)[0]

    if request.method == 'POST':
        receita.nomeReceita = request.form.get('nomeReceita')
        receita.preparo = request.form.get('preparo')
        receita.tempo = request.form.get('tempo')
        receita.imagem = request.form.get('imagem')
        receita.descricao = request.form.get('desc')
        ingredientes_form = request.form.getlist('ingredientes[]')
        quantidades_form = request.form.getlist('quantidades[]')

        # Atualizar ingredientes existentes
        for i, ingrediente_atual in enumerate(receita.ingredientes):
            if i < len(ingredientes_form):
                ingrediente_atual.nomeIngrediente = ingredientes_form[i].strip().lower()
                ingrediente_atual.quantidade = quantidades_form[i]
            else:
                # Se houver menos ingredientes no formulário do que na receita, remova os extras
                db.session.delete(ingrediente_atual)

        # Adicionar novos ingredientes, se houver
        for i in range(len(receita.ingredientes), len(ingredientes_form)):
          novo_ingrediente = ingredientes(nomeIngrediente=ingredientes_form[i].strip().lower(), quantidade=quantidades_form[i], idReceita=receita.idReceita)
          receita.ingredientes.append(novo_ingrediente)
          db.session.add(novo_ingrediente)

        db.session.commit()

        # Retornar para a página da receita selecionada
        todas_receitas_ordenadas = receitas.query.order_by(receitas.idReceita).all()
        
        index_receita_editada = todas_receitas_ordenadas.index(receita)
        
        per_page = 4
        pagina_receita_editada = ceil((index_receita_editada + 1) / per_page)

        return redirect(url_for('lista', page=pagina_receita_editada))
    
    ingredientes_no_banco = db.session.query(ingredientes.nomeIngrediente).distinct().all()
  
    return render_template('editar.html', receita=receita, ingredientes_receita=ingredientes_receita)



# requisiçao para exclusao de uma receita, caso o usuario clicar no botão excluir, presente na guia de editar a receita selecionada
@app.route('/deletar/<int:idReceita>')
def deletar(idReceita):
  receita = receitas.query.get(idReceita)
  
  for ingrediente in receita.ingredientes:
    db.session.delete(ingrediente)

  db.session.delete(receita)
  db.session.commit()

  return redirect(url_for('lista'))

#--------------------------------------------------------------------------------------------------#


# criacao do banco de dados e ativacao do modo debug
if __name__ == "__main__":
  with app.app_context():
    db.create_all()
  app.run(debug=True)