from flask import render_template, redirect, url_for, request, flash, make_response
from flask_login import login_required, current_user
from walletfinance.finance import bp
from walletfinance.finance.models import Transaction, Category
from walletfinance.finance.forms import TransactionForm
from walletfinance.finance.category_forms import CategoryForm
from walletfinance.extensions import db
from datetime import datetime
from walletfinance.finance.forms import ImportTransactionForm
import csv
import io

@bp.route('/dashboard')
@login_required
def dashboard():
    """# Exemplo: saldo, receitas, despesas, listagem
    transactions = Transaction.query.filter_by(user_id=current_user.id).all()
    saldo = sum(t.amount if t.type == 'income' else -t.amount for t in transactions)
    receitas = sum(t.amount for t in transactions if t.type == 'income')
    despesas = sum(t.amount for t in transactions if t.type == 'expense')
    return render_template('finance/dashboard.html', transactions=transactions, saldo=saldo, receitas=receitas, despesas=despesas)
"""
    # Captura o mês do filtro na URL (ex: /dashboard?month=Março)
    # 1. Filtro Global
    month_filter = request.args.get('month')
    
    query = Transaction.query.filter_by(user_id=current_user.id)
    if month_filter:
        query = query.filter_by(month=month_filter)
    
    transactions = query.all()
    
    # 2. Cálculos do Mês Selecionado (Cards, Pizza e Barras)
    saldo = sum(t.amount if t.type == 'income' else -t.amount for t in transactions)
    receitas = sum(t.amount for t in transactions if t.type == 'income')
    despesas = sum(t.amount for t in transactions if t.type == 'expense')
    
    # Tratando o expected_amount (caso seja nulo no banco, usamos 0)
    receitas_previstas = sum((t.expected_amount or 0) for t in transactions if t.type == 'income')
    despesas_previstas = sum((t.expected_amount or 0) for t in transactions if t.type == 'expense')
    
    # 3. Cálculos de Evolução Anual (Linhas) - Ignora o filtro de mês
    all_transactions = Transaction.query.filter_by(user_id=current_user.id).all()
    
    meses = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 
             'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
    
    # Dicionários para agrupar os totais de cada mês
    evolucao_rec = {m: 0.0 for m in meses}
    evolucao_desp = {m: 0.0 for m in meses}
    
    for t in all_transactions:
        if t.month in meses:
            if t.type == 'income':
                evolucao_rec[t.month] += float(t.amount)
            else:
                evolucao_desp[t.month] += float(t.amount)
                
    # Transforma os dicionários em listas ordenadas para o Chart.js
    linha_receitas = [evolucao_rec[m] for m in meses]
    linha_despesas = [evolucao_desp[m] for m in meses]

    # ==========================================
    # NOVOS CÁLCULOS: CATEGORIAS E STATUS
    # ==========================================
    
    # 1. Agrupando Despesas por Categoria
    categorias_dict = {}
    for t in transactions:
        if t.type == 'expense':
            # Se a categoria não existir no dict, inicia com 0 e soma o valor
            categorias_dict[t.category] = categorias_dict.get(t.category, 0) + float(t.amount)
            
    # Separando em duas listas para o Chart.js (Labels e Valores)
    cat_labels = list(categorias_dict.keys())
    cat_values = list(categorias_dict.values())

    # 2. Agrupando por Status (Pago vs Pendente)
    # Aqui podemos fazer do total geral ou só das despesas. Farei do Geral.
    total_pago = sum(t.amount for t in transactions if t.paid)
    total_pendente = sum(t.amount for t in transactions if not t.paid)
    
    return render_template(
        'finance/dashboard.html', 
        transactions=transactions, 
        saldo=saldo, 
        receitas=receitas, 
        despesas=despesas,
        receitas_previstas=receitas_previstas,
        despesas_previstas=despesas_previstas,
        linha_receitas=linha_receitas,
        linha_despesas=linha_despesas,
        meses=meses,
        month_filter=month_filter,
        cat_labels=cat_labels,
        cat_values=cat_values,
        total_pago=total_pago,
        total_pendente=total_pendente
    )


@bp.route('/transactions/add', methods=['GET', 'POST'])
@login_required
def add_transaction():
    """categories = Category.query.filter_by(user_id=current_user.id).all()
    form = TransactionForm()
    
    # MUDANÇA 1: Em vez de (c.name, c.name), agora enviamos (ID, Nome). 
    # O WTForms exige que o ID seja convertido para string na lista suspensa.
    form.category.choices = [('', 'Selecione uma categoria')] + [(str(c.id), c.name) for c in categories]"""

    categories = Category.query.filter_by(user_id=current_user.id).all()
    form = TransactionForm()
    form.category.choices = [('', 'Selecione uma categoria')] + [(str(c.id), c.name) for c in categories]
    
    # NOVO: Cria um mapa invisível para o JS (Ex: {"1": "income", "2": "expense"})
    category_mapping = {str(c.id): c.type for c in categories}
    
    if form.validate_on_submit():
        # MUDANÇA 2: Recuperamos o objeto da categoria usando o ID que veio do form
        # Isso garante que a transação saiba exatamente com quem ela está se relacionando
        cat_id = int(form.category.data)
        categoria_selecionada = Category.query.filter_by(id=cat_id, user_id=current_user.id).first()
        
        transaction = Transaction(
            description=form.description.data,
            expected_amount=form.expected_amount.data,
            amount=form.amount.data,
            category=categoria_selecionada.name,      # Mantemos o nome preenchido por garantia/histórico
            category_id=categoria_selecionada.id,     # AQUI ESTÁ A MÁGICA: A relação forte!
            month=form.month.data,
            type=form.type.data,
            paid=form.paid.data,
            due_date=form.due_date.data,
            user_id=current_user.id
        )
        db.session.add(transaction)
        db.session.commit()
        flash('Transação adicionada com sucesso!', 'success')
        return redirect(url_for('finance.list_transactions'))
        
    return render_template('finance/add_transaction.html', form=form, category_mapping=category_mapping)

# OBS: Os outros métodos de edição e listagem de transações também precisam ser ajustados para lidar com a nova forma de salvar a categoria (com ID). Mas isso é algo que podemos fazer depois, pois o mais importante era garantir que a criação da transação estivesse correta e robusta.

"""@bp.route('/transactions/add', methods=['GET', 'POST'])
@login_required
def add_transaction():
    categories = Category.query.filter_by(user_id=current_user.id).all()
    form = TransactionForm()
    form.category.choices = [('', 'Selecione uma categoria')] + [(c.name, c.name) for c in categories]
    if form.validate_on_submit():
        transaction = Transaction(
            description=form.description.data,
            expected_amount=form.expected_amount.data,
            amount=form.amount.data,
            category=form.category.data,
            month=form.month.data,
            type=form.type.data,
            paid=form.paid.data,
            due_date=form.due_date.data,
            user_id=current_user.id
        )
        db.session.add(transaction)
        db.session.commit()
        flash('Transação adicionada com sucesso!', 'success')
        return redirect(url_for('finance.dashboard'))
    return render_template('finance/add_transaction.html', form=form)"""


@bp.route('/transactions')
@login_required
def list_transactions():
    # 1. Captura todos os parâmetros da URL (Se não existir, assume vazio '')
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search', '').strip()
    month_filter = request.args.get('month', '')
    type_filter = request.args.get('type', '')
    status_filter = request.args.get('status', '')
    
    # 2. Inicia a query base
    query = Transaction.query.filter_by(user_id=current_user.id)
    
    # 3. O Funil de Filtros (Adiciona as regras dinamicamente)
    
    # Filtro de Texto (Descrição ou Categoria)
    if search_query:
        query = query.filter(db.or_(
            Transaction.description.ilike(f'%{search_query}%'),
            Transaction.category.ilike(f'%{search_query}%')
        ))
        
    # Filtro de Mês exato
    if month_filter:
        query = query.filter_by(month=month_filter)
        
    # Filtro de Tipo (income = Receita / expense = Despesa)
    if type_filter in ['income', 'expense']:
        query = query.filter_by(type=type_filter)
        
    # Filtro de Status (1 = Pago / 0 = Pendente)
    if status_filter in ['1', '0']:
        is_paid = True if status_filter == '1' else False
        query = query.filter_by(paid=is_paid)
    
    # 4. Finaliza ordenando e paginando os resultados do funil
    pagination = query.order_by(Transaction.id.desc()).paginate(page=page, per_page=50, error_out=False)
    transactions = pagination.items
    
    # 5. Envia as variáveis de volta pro HTML para manter os selects marcados com o que o usuário escolheu
    return render_template('finance/list_transactions.html', 
                           transactions=transactions, 
                           pagination=pagination,
                           search_query=search_query,
                           month_filter=month_filter,
                           type_filter=type_filter,
                           status_filter=status_filter)
                           

"""@bp.route('/transactions')
@login_required
def list_transactions():
    query = Transaction.query.filter_by(user_id=current_user.id)
    search = request.args.get('search', '').strip()
    category = request.args.get('category', '')
    month = request.args.get('month', '')
    type_ = request.args.get('type', '')
    status = request.args.get('status', '')

    if search:
        query = query.filter(Transaction.description.ilike(f"%{search}%"))
    if category:
        query = query.filter_by(category=category)
    if month:
        query = query.filter_by(month=month)
    if type_:
        query = query.filter_by(type=type_)
    if status:
        if status == 'paid':
            query = query.filter_by(paid=True)
        elif status == 'pending':
            query = query.filter_by(paid=False)

    transactions = query.order_by(Transaction.due_date.desc()).all()
    categories = Category.query.filter_by(user_id=current_user.id).all()
    months = [
        'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio',
        'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro',
        'Novembro', 'Dezembro'
    ]
    return render_template(
        'finance/list_transactions.html',
        transactions=transactions,
        categories=categories,
        months=months,
        search=search,
        category=category,
        month=month,
        type_=type_,
        status=status,
    )"""

@bp.route('/transactions/edit/<int:transaction_id>', methods=['GET', 'POST'])
@login_required
def edit_transaction(transaction_id):
    transaction = Transaction.query.filter_by(id=transaction_id, user_id=current_user.id).first_or_404()
    form = TransactionForm(obj=transaction)
    
    categories = Category.query.filter_by(user_id=current_user.id).all()
    
    # 1. Mudança nas choices (Enviando o ID da categoria)
    form.category.choices = [('', 'Selecione uma categoria')] + [(str(c.id), c.name) for c in categories]
    
    # ==========================================
    # A MÁGICA PARA O JAVASCRIPT AQUI:
    # Mapeia o ID de cada categoria para o tipo dela (income/expense)
    category_mapping = {str(c.id): c.type for c in categories}
    # ==========================================
    
    # 2. Truque de Sênior: Lidar com dados "Legados" no carregamento da tela (GET)
    if request.method == 'GET':
        if transaction.category_id:
            form.category.data = str(transaction.category_id)
        else:
            # Se for uma transação antiga que ainda não tem o ID gravado
            cat_legada = Category.query.filter_by(name=transaction.category, user_id=current_user.id).first()
            if cat_legada:
                form.category.data = str(cat_legada.id)

    if form.validate_on_submit():
        # 3. Salvando a relação forte
        cat_id = int(form.category.data)
        categoria_selecionada = Category.query.filter_by(id=cat_id, user_id=current_user.id).first()
        
        transaction.description = form.description.data
        transaction.expected_amount = form.expected_amount.data
        transaction.amount = form.amount.data
        transaction.category = categoria_selecionada.name
        transaction.category_id = categoria_selecionada.id  # Garante a relacao 
        transaction.month = form.month.data
        transaction.type = form.type.data
        transaction.paid = form.paid.data
        transaction.due_date = form.due_date.data
        
        db.session.commit()
        flash('Transação atualizada com sucesso!', 'success')
        return redirect(url_for('finance.list_transactions'))
        
    # ==========================================
    # ENVIO DA VARIÁVEL PARA O HTML:
    # Adicionamos o category_mapping=category_mapping aqui no final
    # ==========================================
    return render_template('finance/edit_transaction.html', form=form, category_mapping=category_mapping)


# OBS: O método de edição é um pouco mais complexo porque precisamos lidar com o fato de que as transações antigas podem não ter o category_id preenchido, apenas o nome da categoria. Então, no carregamento da tela (GET), fazemos uma busca para tentar preencher o dropdown corretamente. Já no salvamento (POST), garantimos que a relação forte seja mantida, atualizando tanto o category_id quanto o campo category (nome) para manter a compatibilidade com dados legados e garantir a integridade dos dados futuros.

"""@bp.route('/transactions/edit/<int:transaction_id>', methods=['GET', 'POST'])
@login_required
def edit_transaction(transaction_id):
    transaction = Transaction.query.filter_by(id=transaction_id, user_id=current_user.id).first_or_404()
    form = TransactionForm(obj=transaction)
    
    categories = Category.query.filter_by(user_id=current_user.id).all()
    
    # 1. Mudança nas choices (Igual fizemos no add)
    form.category.choices = [('', 'Selecione uma categoria')] + [(str(c.id), c.name) for c in categories]
    
    # 2. Truque de Sênior: Lidar com dados "Legados" no carregamento da tela (GET)
    if request.method == 'GET':
        if transaction.category_id:
            form.category.data = str(transaction.category_id)
        else:
            # Se for uma transação antiga que ainda não tem o ID gravado, 
            # nós buscamos a categoria pelo nome para preencher o dropdown corretamente
            cat_legada = Category.query.filter_by(name=transaction.category, user_id=current_user.id).first()
            if cat_legada:
                form.category.data = str(cat_legada.id)

    if form.validate_on_submit():
        # 3. Salvando a relação forte
        cat_id = int(form.category.data)
        categoria_selecionada = Category.query.filter_by(id=cat_id, user_id=current_user.id).first()
        
        transaction.description = form.description.data
        transaction.expected_amount = form.expected_amount.data
        transaction.amount = form.amount.data
        transaction.category = categoria_selecionada.name
        transaction.category_id = categoria_selecionada.id  # Garante a relação!
        transaction.month = form.month.data
        transaction.type = form.type.data
        transaction.paid = form.paid.data
        transaction.due_date = form.due_date.data
        
        db.session.commit()
        flash('Transação atualizada com sucesso!', 'success')
        return redirect(url_for('finance.list_transactions'))
        
    return render_template('finance/edit_transaction.html', form=form)"""

# OBS: O método de edição é um pouco mais complexo porque precisamos lidar com o fato de que as transações antigas podem não ter o category_id preenchido, apenas o nome da categoria. Então, no carregamento da tela (GET), fazemos uma busca para tentar preencher o dropdown corretamente. Já no salvamento (POST), garantimos que a relação forte seja mantida, atualizando tanto o category_id quanto o campo category (nome) para manter a compatibilidade com dados legados e garantir a integridade dos dados futuros.

"""@bp.route('/transactions/edit/<int:transaction_id>', methods=['GET', 'POST'])
@login_required
def edit_transaction(transaction_id):
    transaction = Transaction.query.filter_by(id=transaction_id, user_id=current_user.id).first_or_404()
    categories = Category.query.filter_by(user_id=current_user.id).all()
    form = TransactionForm(obj=transaction)
    form.category.choices = [('', 'Selecione uma categoria')] + [(c.name, c.name) for c in categories]
    if form.validate_on_submit():
        form.populate_obj(transaction)
        db.session.commit()
        flash('Transação atualizada com sucesso!', 'success')
        return redirect(url_for('finance.list_transactions'))
    return render_template('finance/edit_transaction.html', form=form, transaction=transaction)"""

@bp.route('/transactions/delete/<int:transaction_id>', methods=['POST'])
@login_required
def delete_transaction(transaction_id):
    transaction = Transaction.query.filter_by(id=transaction_id, user_id=current_user.id).first_or_404()
    db.session.delete(transaction)
    db.session.commit()
    flash('Transação excluída com sucesso!', 'success')
    return redirect(url_for('finance.list_transactions'))

@bp.route('/categories')
@login_required
def list_categories():
    categories = Category.query.filter_by(user_id=current_user.id).all()
    return render_template('finance/list_categories.html', categories=categories)

@bp.route('/categories/add', methods=['GET', 'POST'])
@login_required
def add_category():
    form = CategoryForm()
    if form.validate_on_submit():
        category = Category(
            name=form.name.data,
            type=form.type.data,
            user_id=current_user.id
        )
        db.session.add(category)
        db.session.commit()
        flash('Categoria adicionada com sucesso!', 'success')
        return redirect(url_for('finance.list_categories'))
    return render_template('finance/add_category.html', form=form)

@bp.route('/categories/edit/<int:category_id>', methods=['GET', 'POST'])
@login_required
def edit_category(category_id):
    category = Category.query.filter_by(id=category_id, user_id=current_user.id).first_or_404()
    
    # 1. Guardamos o nome antigo ANTES do formulário sobrescrever o objeto
    nome_antigo = category.name 
    
    form = CategoryForm(obj=category)
    if form.validate_on_submit():
        novo_nome = form.name.data
        
        form.populate_obj(category) # Atualiza o objeto Categoria com os dados da tela
        
        # 2. Sincronização em Massa (O Update Relacional)
        if nome_antigo != novo_nome:
            # Busca todas as transações que pertencem a essa categoria (seja pelo ID novo ou pelo nome velho)
            transacoes_vinculadas = Transaction.query.filter(
                db.or_(
                    Transaction.category_id == category.id,
                    Transaction.category == nome_antigo
                ),
                Transaction.user_id == current_user.id
            ).all()
            
            for t in transacoes_vinculadas:
                t.category = novo_nome       # Atualiza o texto na transação
                t.category_id = category.id  # Aproveita para consertar o ID de transações legadas!
                
        db.session.commit()
        flash('Categoria e transações vinculadas atualizadas com sucesso!', 'success')
        return redirect(url_for('finance.list_categories'))
        
    return render_template('finance/edit_category.html', form=form, category=category)

# OBS: A edição de categoria é um pouco mais complexa porque precisamos garantir que, se o usuário mudar o nome da categoria, todas as transações que estavam vinculadas a ela (seja pelo nome ou pelo ID) sejam atualizadas para refletir essa mudança. Assim, mantemos a integridade dos dados e evitamos que transações fiquem "órfãs" ou com categorias desatualizadas.

"""@bp.route('/categories/edit/<int:category_id>', methods=['GET', 'POST'])
@login_required
def edit_category(category_id):
    category = Category.query.filter_by(id=category_id, user_id=current_user.id).first_or_404()
    form = CategoryForm(obj=category)
    if form.validate_on_submit():
        form.populate_obj(category)
        db.session.commit()
        flash('Categoria atualizada com sucesso!', 'success')
        return redirect(url_for('finance.list_categories'))
    return render_template('finance/edit_category.html', form=form, category=category)"""

@bp.route('/categories/delete/<int:category_id>', methods=['POST'])
@login_required
def delete_category(category_id):
    category = Category.query.filter_by(id=category_id, user_id=current_user.id).first_or_404()
    db.session.delete(category)
    db.session.commit()
    flash('Categoria excluída com sucesso!', 'success')
    return redirect(url_for('finance.list_categories'))

@bp.route('/transactions/import/template')
@login_required
def download_import_template():
    """Gera um CSV de exemplo na hora para o usuário baixar"""
    # Usamos io.StringIO para criar o arquivo em memória
    si = io.StringIO()
    # Separador ponto e vírgula é o padrão do Excel PT-BR
    cw = csv.writer(si, delimiter=';') 
    
    # Cabeçalho exato que vamos exigir
    cw.writerow(['Descrição', 'Categoria', 'Mês', 'Tipo', 'Valor Previsto', 'Valor Realizado', 'Status', 'Vencimento'])
    
    # Linhas de exemplo
    cw.writerow(['Exemplo Salário', 'Salário', 'Março', 'income', '5000,00', '5000,00', 'Pago', '05/03/2026'])
    cw.writerow(['Exemplo Conta de Luz', 'Moradia', 'Março', 'expense', '150,00', '162,50', 'Pendente', '10/03/2026'])
    
    response = make_response(si.getvalue().encode('utf-8-sig')) # utf-8-sig ajuda o Excel a ler acentos
    response.headers["Content-Disposition"] = "attachment; filename=template_importacao.csv"
    response.headers["Content-type"] = "text/csv"
    
    return response

@bp.route('/transactions/import', methods=['GET', 'POST'])
@login_required
def import_transactions():
    form = ImportTransactionForm()
    
    if form.validate_on_submit():
        file = form.file.data
        
        try:
            # Lê o arquivo em memória decodificando de bytes para string
            stream = io.StringIO(file.stream.read().decode("utf-8-sig"), newline=None)
            # DictReader mapeia as colunas do cabeçalho automaticamente
            csv_reader = csv.DictReader(stream, delimiter=';')
            
            registros_adicionados = 0
            
            for row in csv_reader:
                # 1. Sanitização dos valores financeiros (troca , por . e ignora R$)
                val_previsto_str = row.get('Valor Previsto', '0').replace('R$', '').replace('.', '').replace(',', '.').strip()
                val_realizado_str = row.get('Valor Realizado', '0').replace('R$', '').replace('.', '').replace(',', '.').strip()
                
                val_previsto = float(val_previsto_str) if val_previsto_str else 0.0
                val_realizado = float(val_realizado_str) if val_realizado_str else 0.0
                
                # 2. Sanitização de Status e Datas
                status_pago = True if str(row.get('Status')).strip().lower() == 'pago' else False
                tipo = str(row.get('Tipo')).strip().lower()
                
                vencimento_str = str(row.get('Vencimento')).strip()
                vencimento = None
                if vencimento_str:
                    try:
                        vencimento = datetime.strptime(vencimento_str, '%d/%m/%Y').date()
                    except ValueError:
                        pass # Se a data for inválida, fica None
                
                # 3. Criação Dinâmica de Categoria (se não existir)
                cat_nome = str(row.get('Categoria')).strip()
                categoria_obj = Category.query.filter_by(name=cat_nome, user_id=current_user.id).first()
                
                if not categoria_obj:
                    categoria_obj = Category(name=cat_nome, type=tipo, user_id=current_user.id)
                    db.session.add(categoria_obj)
                    db.session.flush() # Salva temporariamente para gerar o ID antes do commit final

                # 4. Criação da Transação
                nova_transacao = Transaction(
                    description=str(row.get('Descrição')).strip(),
                    expected_amount=val_previsto,
                    amount=val_realizado,
                    category=categoria_obj.name,
                    category_id=categoria_obj.id,
                    month=str(row.get('Mês')).strip(),
                    type=tipo,
                    paid=status_pago,
                    due_date=vencimento,
                    user_id=current_user.id
                )
                db.session.add(nova_transacao)
                registros_adicionados += 1
                
            db.session.commit()
            flash(f'{registros_adicionados} transações importadas com sucesso!', 'success')
            return redirect(url_for('finance.list_transactions'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao processar o arquivo. Verifique se o formato está idêntico ao template. Detalhe: {str(e)}', 'danger')

    return render_template('finance/import_transactions.html', form=form)

@bp.route('/transactions/export')
@login_required
def export_transactions():
    # Busca todas as transações do usuário atual
    transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.id.desc()).all()
    
    # Cria o arquivo em memória
    si = io.StringIO()
    # Usamos o ponto e vírgula pq o Excel no Brasil usa vírgula para casas decimais
    cw = csv.writer(si, delimiter=';') 
    
    # Escreve o Cabeçalho da planilha
    cw.writerow(['Descrição', 'Categoria', 'Mês', 'Tipo', 'Valor Previsto', 'Valor Realizado', 'Status', 'Vencimento'])
    
    # Escreve os dados linha a linha
    for t in transactions:
        # Formatações amigáveis para o Excel
        tipo_pt = 'Receita' if t.type == 'income' else 'Despesa'
        status_pt = 'Pago' if t.paid else 'Pendente'
        vencimento = t.due_date.strftime('%d/%m/%Y') if t.due_date else ''
        
        # Troca o ponto do banco de dados pela vírgula do Excel (ex: 1500.50 -> 1500,50)
        previsto = str(t.expected_amount).replace('.', ',') if t.expected_amount else '0,00'
        realizado = str(t.amount).replace('.', ',') if t.amount else '0,00'
        
        cw.writerow([
            t.description, 
            t.category, 
            t.month, 
            tipo_pt, 
            previsto, 
            realizado, 
            status_pt, 
            vencimento
        ])
        
    # Prepara a resposta forçando o download do arquivo
    # utf-8-sig é o truque de Sênior para o Excel não bugar a acentuação (ç, ã, é)
    response = make_response(si.getvalue().encode('utf-8-sig')) 
    
    # Gera um nome de arquivo dinâmico com a data de hoje
    data_hoje = datetime.now().strftime('%Y-%m-%d')
    response.headers["Content-Disposition"] = f"attachment; filename=meus_dados_financeiros_{data_hoje}.csv"
    response.headers["Content-type"] = "text/csv"
    
    return response