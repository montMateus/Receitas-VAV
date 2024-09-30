# ReceitasVav

Essa aplicação web fornece sugestões de receitas baseadas nos alimentos disponíveis em sua casa com foco para produtos in natura ou pouco processados.


## Instalação

Para executar este projeto, você precisará ter o Python _v3.11_, Flask e SQLAlchemy instalados. Você pode instalar as dependências com os seguintes comandos:
```bash

pip install Flask==3.0.3
pip install -U Flask-SQLAlchemy==3.1.0
```

Após instalar as dependências, você pode iniciar a aplicação executando o seguinte comando no terminal:
```bash 

python app.py
```


## Estrutura do Projeto
```
└── receitasvav/
    ├── app.py
    ├── README.md
    ├── instance/
    │   └── db.sqlite3
    ├── templates/
    │   └── index.html
    │   └── base.html
    │   └── receita.html
    │   └── lista.html
    │   └── adicionar.html
    │   └── editar.html
    ├── static/
    │   └── ReceitasVav.png
```
