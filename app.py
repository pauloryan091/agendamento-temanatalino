from flask import Flask, request, jsonify, render_template, session, redirect, url_for, send_from_directory
import sqlite3
import os
from datetime import datetime
import base64

app = Flask(__name__, template_folder='.', static_folder='static')
app.secret_key = 'sua_chave_secreta_aqui_123456'

# Configurações do banco de dados
DATABASE = 'banco.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with app.app_context():
        conn = get_db_connection()
        
        # Tabela de usuários
        conn.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                senha TEXT NOT NULL,
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabela de clientes
        conn.execute('''
            CREATE TABLE IF NOT EXISTS clientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                telefone TEXT,
                email TEXT,
                usuario_id INTEGER,
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
            )
        ''')
        
        # Tabela de serviços
        conn.execute('''    
            CREATE TABLE IF NOT EXISTS servicos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                descricao TEXT,
                imagem TEXT,
                usuario_id INTEGER,
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
            )
        ''')
        
        # Tabela de agendamentos
        conn.execute('''
            CREATE TABLE IF NOT EXISTS agendamentos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente_id INTEGER,
                servico_id INTEGER,
                data_agendamento DATE NOT NULL,
                hora_agendamento TIME NOT NULL,
                status TEXT DEFAULT 'pendente',
                usuario_id INTEGER,
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (cliente_id) REFERENCES clientes (id),
                FOREIGN KEY (servico_id) REFERENCES servicos (id),
                FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
            )
        ''')
        
        conn.commit()
        conn.close()

# Inicializar banco de dados
init_db()

# =====================
# ROTAS PRINCIPAIS (PÁGINAS HTML)
# =====================

@app.route('/')
def index():
    if 'usuario_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/cadastro')
def cadastro_page():
    return render_template('cadastro.html')

@app.route('/dashboard')
def dashboard():
    if 'usuario_id' not in session:
        return redirect(url_for('index'))
    return render_template('dashboard.html')

@app.route('/servicos')
def servicos():
    if 'usuario_id' not in session:
        return redirect(url_for('index'))
    return render_template('servicos.html')

@app.route('/clientes')
def clientes():
    if 'usuario_id' not in session:
        return redirect(url_for('index'))
    return render_template('clientes.html')

@app.route('/agendamentos')
def agendamentos():
    if 'usuario_id' not in session:
        return redirect(url_for('index'))
    return render_template('agendamentos.html')

@app.route('/perfil')
def perfil():
    if 'usuario_id' not in session:
        return redirect(url_for('index'))
    return render_template('perfil.html')

# =====================
# API - AUTENTICAÇÃO
# =====================

@app.route('/api/cadastro', methods=['POST'])
def cadastro():
    try:
        data = request.get_json()
        nome = data.get('nome')
        email = data.get('email')
        senha = data.get('senha')
        
        if not nome or not email or not senha:
            return jsonify({'success': False, 'message': 'Todos os campos são obrigatórios'})
        
        conn = get_db_connection()
        
        # Verificar se email já existe
        usuario_existente = conn.execute(
            'SELECT id FROM usuarios WHERE email = ?', (email,)
        ).fetchone()
        
        if usuario_existente:
            conn.close()
            return jsonify({'success': False, 'message': 'Email já cadastrado'})
        
        # Inserir novo usuário
        conn.execute(
            'INSERT INTO usuarios (nome, email, senha) VALUES (?, ?, ?)',
            (nome, email, senha)
        )
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Cadastro realizado com sucesso!'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro no servidor: {str(e)}'})

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        email = data.get('email')
        senha = data.get('senha')
        
        conn = get_db_connection()
        usuario = conn.execute(
            'SELECT * FROM usuarios WHERE email = ? AND senha = ?', (email, senha)
        ).fetchone()
        conn.close()
        
        if usuario:
            session['usuario_id'] = usuario['id']
            session['usuario_nome'] = usuario['nome']
            session['usuario_email'] = usuario['email']
            return jsonify({'success': True, 'message': 'Login realizado com sucesso!'})
        else:
            return jsonify({'success': False, 'message': 'Email ou senha incorretos'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro no servidor: {str(e)}'})

@app.route('/api/logout')
def logout():
    session.clear()
    return jsonify({'success': True, 'message': 'Logout realizado com sucesso!'})

# =====================
# API - SERVIÇOS
# =====================

@app.route('/api/servicos', methods=['GET', 'POST'])
def api_servicos():
    if 'usuario_id' not in session:
        return jsonify({'error': 'Não autorizado'}), 401
    
    usuario_id = session['usuario_id']
    conn = get_db_connection()
    
    if request.method == 'GET':
        servicos = conn.execute(
            'SELECT * FROM servicos WHERE usuario_id = ? ORDER BY nome', 
            (usuario_id,)
        ).fetchall()
        conn.close()
        
        servicos_list = []
        for servico in servicos:
            servicos_list.append({
                'id': servico['id'],
                'nome': servico['nome'],
                'descricao': servico['descricao'],
                'imagem': servico['imagem']
            })
        
        return jsonify(servicos_list)
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            nome = data.get('nome')
            descricao = data.get('descricao')
            imagem = data.get('imagem')
            
            if not nome:
                return jsonify({'success': False, 'message': 'Nome é obrigatório'})
            
            conn.execute(
                'INSERT INTO servicos (nome, descricao, imagem, usuario_id) VALUES (?, ?, ?, ?)',
                (nome, descricao, imagem, usuario_id)
            )
            conn.commit()
            conn.close()
            
            return jsonify({'success': True, 'message': 'Serviço adicionado com sucesso!'})
        
        except Exception as e:
            conn.close()
            return jsonify({'success': False, 'message': f'Erro ao adicionar serviço: {str(e)}'})

@app.route('/api/servicos/<int:servico_id>', methods=['GET', 'PUT', 'DELETE'])
def api_servico(servico_id):
    if 'usuario_id' not in session:
        return jsonify({'error': 'Não autorizado'}), 401
    
    usuario_id = session['usuario_id']
    conn = get_db_connection()
    
    try:
        # Verificar se o serviço pertence ao usuário
        servico = conn.execute(
            'SELECT * FROM servicos WHERE id = ? AND usuario_id = ?', 
            (servico_id, usuario_id)
        ).fetchone()
        
        if not servico:
            conn.close()
            return jsonify({'error': 'Serviço não encontrado'}), 404
        
        if request.method == 'GET':
            servico_data = {
                'id': servico['id'],
                'nome': servico['nome'],
                'descricao': servico['descricao'],
                'imagem': servico['imagem']
            }
            conn.close()
            return jsonify(servico_data)
        
        elif request.method == 'PUT':
            data = request.get_json()
            nome = data.get('nome')
            descricao = data.get('descricao')
            imagem = data.get('imagem')
            
            if not nome:
                return jsonify({'success': False, 'message': 'Nome é obrigatório'})
            
            conn.execute(
                'UPDATE servicos SET nome = ?, descricao = ?, imagem = ? WHERE id = ?',
                (nome, descricao, imagem, servico_id)
            )
            conn.commit()
            conn.close()
            
            return jsonify({'success': True, 'message': 'Serviço atualizado com sucesso!'})
        
        elif request.method == 'DELETE':
            conn.execute('DELETE FROM servicos WHERE id = ?', (servico_id,))
            conn.commit()
            conn.close()
            
            return jsonify({'success': True, 'message': 'Serviço excluído com sucesso!'})
    
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': f'Erro ao processar serviço: {str(e)}'})

# =====================
# API - CLIENTES
# =====================

@app.route('/api/clientes', methods=['GET', 'POST'])
def api_clientes():
    if 'usuario_id' not in session:
        return jsonify({'error': 'Não autorizado'}), 401
    
    usuario_id = session['usuario_id']
    conn = get_db_connection()
    
    if request.method == 'GET':
        clientes = conn.execute(
            'SELECT * FROM clientes WHERE usuario_id = ? ORDER BY nome', 
            (usuario_id,)
        ).fetchall()
        conn.close()
        
        clientes_list = []
        for cliente in clientes:
            clientes_list.append({
                'id': cliente['id'],
                'nome': cliente['nome'],
                'telefone': cliente['telefone'],
                'email': cliente['email']
            })
        
        return jsonify(clientes_list)
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            nome = data.get('nome')
            telefone = data.get('telefone')
            email = data.get('email')
            
            if not nome:
                return jsonify({'success': False, 'message': 'Nome é obrigatório'})
            
            conn.execute(
                'INSERT INTO clientes (nome, telefone, email, usuario_id) VALUES (?, ?, ?, ?)',
                (nome, telefone, email, usuario_id)
            )
            conn.commit()
            conn.close()
            
            return jsonify({'success': True, 'message': 'Cliente adicionado com sucesso!'})
        
        except Exception as e:
            conn.close()
            return jsonify({'success': False, 'message': f'Erro ao adicionar cliente: {str(e)}'})

@app.route('/api/clientes/<int:cliente_id>', methods=['PUT', 'DELETE'])
def api_cliente(cliente_id):
    if 'usuario_id' not in session:
        return jsonify({'error': 'Não autorizado'}), 401
    
    usuario_id = session['usuario_id']
    conn = get_db_connection()
    
    try:
        # Verificar se o cliente pertence ao usuário
        cliente = conn.execute(
            'SELECT * FROM clientes WHERE id = ? AND usuario_id = ?', 
            (cliente_id, usuario_id)
        ).fetchone()
        
        if not cliente:
            conn.close()
            return jsonify({'error': 'Cliente não encontrado'}), 404
        
        if request.method == 'PUT':
            data = request.get_json()
            nome = data.get('nome')
            telefone = data.get('telefone')
            email = data.get('email')
            
            if not nome:
                return jsonify({'success': False, 'message': 'Nome é obrigatório'})
            
            conn.execute(
                'UPDATE clientes SET nome = ?, telefone = ?, email = ? WHERE id = ?',
                (nome, telefone, email, cliente_id)
            )
            conn.commit()
            conn.close()
            
            return jsonify({'success': True, 'message': 'Cliente atualizado com sucesso!'})
        
        elif request.method == 'DELETE':
            conn.execute('DELETE FROM clientes WHERE id = ?', (cliente_id,))
            conn.commit()
            conn.close()
            
            return jsonify({'success': True, 'message': 'Cliente excluído com sucesso!'})
    
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': f'Erro ao processar cliente: {str(e)}'})

# =====================
# API - AGENDAMENTOS (CORRIGIDA)
# =====================

@app.route('/api/agendamentos', methods=['GET', 'POST'])
def api_agendamentos():
    if 'usuario_id' not in session:
        return jsonify({'error': 'Não autorizado'}), 401
    
    usuario_id = session['usuario_id']
    conn = get_db_connection()
    
    if request.method == 'GET':
        agendamentos = conn.execute('''
            SELECT a.*, c.nome as cliente_nome, c.telefone as cliente_telefone, 
                   s.nome as servico_nome, c.id as cliente_id, s.id as servico_id
            FROM agendamentos a 
            LEFT JOIN clientes c ON a.cliente_id = c.id 
            LEFT JOIN servicos s ON a.servico_id = s.id 
            WHERE a.usuario_id = ? 
            ORDER BY a.data_agendamento DESC, a.hora_agendamento DESC
        ''', (usuario_id,)).fetchall()
        conn.close()
        
        agendamentos_list = []
        for agendamento in agendamentos:
            agendamentos_list.append({
                'id': agendamento['id'],
                'cliente_id': agendamento['cliente_id'],
                'cliente_nome': agendamento['cliente_nome'],
                'cliente_telefone': agendamento['cliente_telefone'],
                'servico_id': agendamento['servico_id'],
                'servico_nome': agendamento['servico_nome'],
                'data_agendamento': agendamento['data_agendamento'],
                'hora_agendamento': agendamento['hora_agendamento'],
                'status': agendamento['status']
            })
        
        return jsonify(agendamentos_list)
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            cliente_id = data.get('cliente_id')
            servico_id = data.get('servico_id')
            data_agendamento = data.get('data_agendamento')
            hora_agendamento = data.get('hora_agendamento')
            status = data.get('status', 'pendente')
            
            if not cliente_id or not servico_id or not data_agendamento or not hora_agendamento:
                return jsonify({'success': False, 'message': 'Todos os campos são obrigatórios'})
            
            # Verificar se cliente e serviço pertencem ao usuário
            cliente = conn.execute(
                'SELECT id FROM clientes WHERE id = ? AND usuario_id = ?', 
                (cliente_id, usuario_id)
            ).fetchone()
            
            servico = conn.execute(
                'SELECT id FROM servicos WHERE id = ? AND usuario_id = ?', 
                (servico_id, usuario_id)
            ).fetchone()
            
            if not cliente:
                conn.close()
                return jsonify({'success': False, 'message': 'Cliente não encontrado'})
            
            if not servico:
                conn.close()
                return jsonify({'success': False, 'message': 'Serviço não encontrado'})
            
            conn.execute(
                'INSERT INTO agendamentos (cliente_id, servico_id, data_agendamento, hora_agendamento, status, usuario_id) VALUES (?, ?, ?, ?, ?, ?)',
                (int(cliente_id), int(servico_id), data_agendamento, hora_agendamento, status, usuario_id)
            )
            conn.commit()
            conn.close()
            
            return jsonify({'success': True, 'message': 'Agendamento realizado com sucesso!'})
        
        except Exception as e:
            conn.close()
            return jsonify({'success': False, 'message': f'Erro ao criar agendamento: {str(e)}'})

@app.route('/api/agendamentos/<int:agendamento_id>', methods=['PUT', 'DELETE'])
def api_agendamento(agendamento_id):
    if 'usuario_id' not in session:
        return jsonify({'error': 'Não autorizado'}), 401
    
    usuario_id = session['usuario_id']
    conn = get_db_connection()
    
    try:
        # Verificar se o agendamento pertence ao usuário
        agendamento = conn.execute(
            'SELECT * FROM agendamentos WHERE id = ? AND usuario_id = ?', 
            (agendamento_id, usuario_id)
        ).fetchone()
        
        if not agendamento:
            conn.close()
            return jsonify({'error': 'Agendamento não encontrado'}), 404
        
        if request.method == 'PUT':
            data = request.get_json()
            status = data.get('status')
            
            if status not in ['pendente', 'confirmado', 'cancelado', 'realizado']:
                conn.close()
                return jsonify({'success': False, 'message': 'Status inválido'})
            
            conn.execute(
                'UPDATE agendamentos SET status = ? WHERE id = ?',
                (status, agendamento_id)
            )
            conn.commit()
            conn.close()
            
            return jsonify({'success': True, 'message': 'Status do agendamento atualizado com sucesso!'})
        
        elif request.method == 'DELETE':
            conn.execute('DELETE FROM agendamentos WHERE id = ?', (agendamento_id,))
            conn.commit()
            conn.close()
            
            return jsonify({'success': True, 'message': 'Agendamento excluído com sucesso!'})
    
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': f'Erro ao processar agendamento: {str(e)}'})

# =====================
# API - RELATÓRIOS E ESTATÍSTICAS
# =====================

@app.route('/api/dashboard/estatisticas')
def api_dashboard_estatisticas():
    if 'usuario_id' not in session:
        return jsonify({'error': 'Não autorizado'}), 401
    
    usuario_id = session['usuario_id']
    conn = get_db_connection()
    
    try:
        # Data atual
        hoje = datetime.now().strftime('%Y-%m-%d')
        mes_atual = datetime.now().strftime('%Y-%m')
        
        # Agendamentos hoje
        agendamentos_hoje = conn.execute('''
            SELECT COUNT(*) as total FROM agendamentos 
            WHERE usuario_id = ? AND data_agendamento = ?
        ''', (usuario_id, hoje)).fetchone()['total']
        
        # Agendamentos este mês
        agendamentos_mes = conn.execute('''
            SELECT COUNT(*) as total FROM agendamentos 
            WHERE usuario_id = ? AND strftime('%Y-%m', data_agendamento) = ?
        ''', (usuario_id, mes_atual)).fetchone()['total']
        
        # Total de clientes
        total_clientes = conn.execute('''
            SELECT COUNT(*) as total FROM clientes WHERE usuario_id = ?
        ''', (usuario_id,)).fetchone()['total']
        
        # Total de serviços
        total_servicos = conn.execute('''
            SELECT COUNT(*) as total FROM servicos WHERE usuario_id = ?
        ''', (usuario_id,)).fetchone()['total']
        
        # Agendamentos por status
        agendamentos_pendentes = conn.execute('''
            SELECT COUNT(*) as total FROM agendamentos 
            WHERE usuario_id = ? AND status = 'pendente'
        ''', (usuario_id,)).fetchone()['total']
        
        agendamentos_confirmados = conn.execute('''
            SELECT COUNT(*) as total FROM agendamentos 
            WHERE usuario_id = ? AND status = 'confirmado'
        ''', (usuario_id,)).fetchone()['total']
        
        agendamentos_realizados = conn.execute('''
            SELECT COUNT(*) as total FROM agendamentos 
            WHERE usuario_id = ? AND status = 'realizado'
        ''', (usuario_id,)).fetchone()['total']
        
        agendamentos_cancelados = conn.execute('''
            SELECT COUNT(*) as total FROM agendamentos 
            WHERE usuario_id = ? AND status = 'cancelado'
        ''', (usuario_id,)).fetchone()['total']
        
        conn.close()
        
        return jsonify({
            'agendamentos_hoje': agendamentos_hoje,
            'agendamentos_mes': agendamentos_mes,
            'total_clientes': total_clientes,
            'total_servicos': total_servicos,
            'agendamentos_pendentes': agendamentos_pendentes,
            'agendamentos_confirmados': agendamentos_confirmados,
            'agendamentos_realizados': agendamentos_realizados,
            'agendamentos_cancelados': agendamentos_cancelados
        })
    
    except Exception as e:
        conn.close()
        return jsonify({'error': f'Erro ao carregar estatísticas: {str(e)}'}), 500

# =====================
# API - DADOS DO USUÁRIO
# =====================

@app.route('/api/usuario')
def api_usuario():
    if 'usuario_id' not in session:
        return jsonify({'error': 'Não autorizado'}), 401
    
    return jsonify({
        'id': session['usuario_id'],
        'nome': session['usuario_nome'],
        'email': session['usuario_email']
    })

# =====================
# ROTA PARA SERVIR ARQUIVOS ESTÁTICOS
# =====================

@app.route('/<path:filename>')
def serve_files(filename):
    try:
        return send_from_directory('.', filename)
    except:
        return "Arquivo não encontrado", 404

# Rota específica para arquivos CSS e JS
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

# =====================
# INICIALIZAÇÃO
# =====================

if __name__ == '__main__':
    # Criar diretório static se não existir
    if not os.path.exists('static'):
        os.makedirs('static')
    
    print("=== SISTEMA DE AGENDAMENTO ===")
    print("Servidor rodando em: http://localhost:5000")
    print("Banco de dados: banco.db")
    print("Rotas disponíveis:")
    print("  / - Login")
    print("  /cadastro - Cadastro de usuário")
    print("  /dashboard - Dashboard principal")
    print("  /servicos - Gerenciar serviços")
    print("  /clientes - Gerenciar clientes")
    print("  /agendamentos - Gerenciar agendamentos")
    print("  /perfil - Perfil do usuário")
    print("==============================")
    
    app.run(debug=True, host='0.0.0.0', port=5000)